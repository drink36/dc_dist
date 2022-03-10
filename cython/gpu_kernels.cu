#import <stdio.h>
#include <cuda.h>
#include <cuda_runtime.h>
#import "gpu_kernels.h"
#import "GPU_utils.cuh"


__global__
void kernel() {
    printf("hello from the kernel!\n");
}

void gpuf() {
    printf("hello from the gpu file!\n");
    cudaDeviceSynchronize();
    kernel<<<1, 1>>>();
    cudaDeviceSynchronize();
}

#include <cuda.h>
#include <cuda_runtime.h>
#include <curand_kernel.h>
#include <curand.h>

#define BLOCK_SIZE 1024

/// https://github.com/rapidsai/cuml/blob/branch-22.04/cpp/src/umap/runner.cuh

__device__
float sqrd_dist(float *d_D, int dims, int i, int j) {
    float distance = 0.;
    for (int l = 0; l < dims; l++) {
        float diff = d_D[i * dims + l] - d_D[j * dims + l];
        distance += diff * diff;
    }
    return distance;
}

__device__
float q(float distance) {
    return 1 / (1 + distance * distance);
}

__global__
void init_random(curandState *d_random) {
    //initialize d_random
    int id = threadIdx.x + blockDim.x * blockIdx.x;
    int seed = id; // different seed per thread
    curand_init(seed, id, 0, &d_random[id]);
}

/// only for k = 1
//__global__
//void compute_grads(float *d_grads, float *d_P, int n, int *d_N, int k, float *d_D_embed,
//                   int dims_embed, float lr, curandState *d_random) {
//    int id = threadIdx.x + blockDim.x * blockIdx.x;
//
//    for (int i = threadIdx.x + blockIdx.x * blockDim.x; i < n; i += blockDim.x * gridDim.x) {
//        for (int l = 0; l < k; l++) {
//            int j = d_N[i * k + l];
//
//            int g = curand(&d_random[id]) % n;//random int
//
//            float attr = q(dist(d_D_embed, dims_embed, i, j));
//            attr = attr * attr * d_P[i * k + j];
//
//            float rep = q(dist(d_D_embed, dims_embed, i, g));
//            rep = rep * rep * rep;
//
//            for (int h = 0; h < dims_embed; h++) {
//                d_grads[i * dims_embed + h] +=
//                        lr * (attr * (d_D_embed[i * dims_embed + h] - d_D_embed[j * dims_embed + h]) -
//                              rep * (d_D_embed[i * dims_embed + h] - d_D_embed[g * dims_embed + h]));
//            }
//        }
//    }
//}

__device__
int get_start(int *d_ends, int i) {
    return i == 0 ? 0 : d_ends[i - 1];
}

__device__
int get_end(int *d_ends, int i) {
    return d_ends[i];
}

__device__
double fast_pow(double a, double b) {
    union {
        double d;
        int x[2];
    } u = {a};
    if (b == 1.0) {
        return a;
    }
    u.x[1] = (int) (b * (u.x[1] - 1072632447) + 1072632447);
    u.x[0] = 0;
    return u.d;
}

__device__
float umap_attraction_grad(float dist_squared, float a, float b) {
    float grad_scalar = 0.0;
    grad_scalar = 2.0 * a * b * fast_pow(dist_squared, b - 1.0);
    grad_scalar /= a * fast_pow(dist_squared, b) + 1.0;
    return grad_scalar;
}

__device__
float kernel_function(float dist_squared, float a, float b) {
    if (b <= 1)
        return 1 / (1 + a * fast_pow(dist_squared, b));
    return fast_pow(dist_squared, b - 1) / (1 + a * fast_pow(dist_squared, b));
}

__device__
float attractive_force_func(
        int normalized,
        float dist_squared,
        float a,
        float b,
        float edge_weight
) {
    float edge_force;
    if (normalized == 0)
        edge_force = umap_attraction_grad(dist_squared, a, b);
    else
        edge_force = kernel_function(dist_squared, a, b);

    return edge_force * edge_weight;
}

__device__
float norm_rep_force(
//        float* rep_func_outputs,
        float dist_squared,
        float a,
        float b,
        float cell_size
) {
    float kernel, q_ij, repulsive_force;

    kernel = kernel_function(dist_squared, a, b);
    q_ij = cell_size * kernel; // Collect the q_ij's contributions into Z
    repulsive_force = cell_size * kernel * kernel;

    return repulsive_force;
//    rep_func_outputs[0] = repulsive_force;
//    rep_func_outputs[1] = q_ij;
}

__device__
float umap_repulsion_grad(float dist_squared, float a, float b) {
    float phi_ijZ = 0.0;
    phi_ijZ = 2.0 * b;
    phi_ijZ /= (0.001 + dist_squared) * (a * fast_pow(dist_squared, b) + 1);
    return phi_ijZ;
}

__device__
float unnorm_rep_force(
//        float *rep_func_outputs,
        float dist_squared,
        float a,
        float b,
        float cell_size,
        float average_weight
) {
    float kernel, repulsive_force;
    // Realistically, we should use the actual weight on
    //   the edge e_{ik}, but we have not gone through
    //   and calculated this value for each weight. Instead,
    //   we have only calculated them for the nearest neighbors.
    kernel = umap_repulsion_grad(dist_squared, a, b);
    repulsive_force = cell_size * kernel * (1 - average_weight);

    return repulsive_force;
//    rep_func_outputs[0] = repulsive_force;
//    rep_func_outputs[1] = 1; // Z is not gathered in unnormalized setting
}

__device__
float repulsive_force_func(
//        float* rep_func_outputs,
        int normalized,
        float dist_squared,
        float a,
        float b,
        float cell_size,
        float average_weight
) {
    if (normalized)
        return norm_rep_force(
//                rep_func_outputs,
                dist_squared,
                a,
                b,
                cell_size
        );
    else
        return unnorm_rep_force(
//                rep_func_outputs,
                dist_squared,
                a,
                b,
                cell_size,
                average_weight
        );
}

// for any k
__global__
void
compute_grads(int normalized, float *d_grads, float *d_weights, int n, int *d_N, int *d_neighbor_ends, float *d_D_embed,
              float a, float b, int dims_embed, curandState *d_random) {
    int id = threadIdx.x + blockDim.x * blockIdx.x;

    for (int i_point = threadIdx.x + blockIdx.x * blockDim.x; i_point < n; i_point += blockDim.x * gridDim.x) {
        for (int i_edge = get_start(d_neighbor_ends, i_point); i_edge < get_end(d_neighbor_ends, i_point); i_edge++) {
            int j = d_N[i_edge];

//            float attr = q(sqrd_dist(d_D_embed, dims_embed, i, j));
//            attr = attr * attr * d_weight[l];

            float dist_squared = sqrd_dist(d_D_embed, dims_embed, i_point, j);
            float attr = attractive_force_func(
                    normalized,
                    dist_squared,
                    a,
                    b,
                    d_weights[i_edge]
            );

            for (int h = 0; h < dims_embed; h++) {
                d_grads[i_point * dims_embed + h] -=
                        attr * (d_D_embed[i_point * dims_embed + h] - d_D_embed[j * dims_embed + h]);
            }

            int g = curand(&d_random[id]) % n;//random int
//            float rep = q(sqrd_dist(d_D_embed, dims_embed, i_point, g));
//            rep = rep * rep * rep;

            dist_squared = sqrd_dist(d_D_embed, dims_embed, i_point, g);
            float rep = repulsive_force_func(
//                    rep_func_outputs,
                    normalized,
                    dist_squared,
                    a,
                    b,
                    1.0,
                    0.3 // FIXME -- make avg_weight
            );


            for (int h = 0; h < dims_embed; h++) {
                d_grads[i_point * dims_embed + h] +=
                        rep * (d_D_embed[i_point * dims_embed + h] - d_D_embed[g * dims_embed + h]);

            }
        }
    }
}


//// for any k
//__global__
//void compute_grads_head_tail(float *d_grads, float *d_P, int n_edges, int n_vertices, int *d_heads, int *d_tails,
//                             float *d_D_embed, int dims_embed, float lr, curandState *d_random) {
//    int id = threadIdx.x + blockDim.x * blockIdx.x;
//
//    for (int i_edge = threadIdx.x + blockIdx.x * blockDim.x; i_edge < n_edges; i_edge += blockDim.x * gridDim.x) {
//        int i = d_heads[i_edge];
//        int j = d_tails[i_edge];
//        float attr = q(dist(d_D_embed, dims_embed, i, j));
//        attr = attr * attr * d_P[i_edge];
//        for (int h = 0; h < dims_embed; h++) {
//            d_grads[i * dims_embed + h] +=
//                    lr * attr * (d_D_embed[i * dims_embed + h] - d_D_embed[j * dims_embed + h]);
//        }
//
//        int g = curand(&d_random[id]) % n_vertices;//random int
//        float rep = q(dist(d_D_embed, dims_embed, i, g));
//        rep = rep * rep * rep;
//        for (int h = 0; h < dims_embed; h++) {
//            d_grads[i * dims_embed + h] -=
//                    lr * rep * (d_D_embed[i * dims_embed + h] - d_D_embed[g * dims_embed + h]);
//
//        }
//    }
//}

__global__
void apply_grads(float *d_D_embed, float *d_grads, int n, int dims_embed, float lr) {
    for (int i = threadIdx.x + blockIdx.x * blockDim.x; i < n; i += blockDim.x * gridDim.x) {
        for (int h = 0; h < dims_embed; h++) {
            d_D_embed[i * dims_embed + h] += lr * d_grads[i * dims_embed + h];
        }
    }
}

float get_lr(float initial_lr, int i_epoch, int n_epochs) {
    return initial_lr * (1.0 - (((float) i_epoch) / ((float) n_epochs)));
}

//void gpu_umap_old(int n, float *h_D_embed, int dims_embed, int *h_N, int k, float *h_P, int epochs,
//                  float init_lr, int neg_samples) {
//
//    //allocated and copy memory to the gpu
//    float *d_D_embed = copy_H_to_D(h_D_embed, n * dims_embed);
//    int *d_N = copy_H_to_D(h_N, n * k);
//    float *d_P = copy_H_to_D(h_P, n * k);
//    float *d_grads = gpu_malloc_float_zero(n * dims_embed);
//
//    //random
//    int number_of_threads = min(n, 32768);
//    int number_of_blocks = number_of_threads / BLOCK_SIZE;
//    if (number_of_threads % BLOCK_SIZE) number_of_blocks++;
//    curandState *d_random;
//    cudaMalloc((void **) &d_random, number_of_threads * sizeof(curandState));
//    init_random << < number_of_blocks, BLOCK_SIZE >> > (d_random);
//
//    for (int epoch = 0; epoch < epochs; epoch++) {
//        float lr = get_lr(init_lr, epoch, epochs);
//        cudaMemset(d_grads, 0, n * dims_embed * sizeof(float));
//        compute_grads << < number_of_blocks, BLOCK_SIZE >> >
//        (d_grads, d_P, n, d_N, k, d_D_embed, dims_embed, lr, neg_samples, d_random);
//        apply_grads << < number_of_blocks, BLOCK_SIZE >> > (d_D_embed, d_grads, n, dims_embed);
//    }
//
//    //copy back and delete
//    cudaMemcpy(h_D_embed, d_D_embed, n * dims_embed * sizeof(float), cudaMemcpyDeviceToHost);
//    cudaFree(d_D_embed);
//    cudaFree(d_N);
//    cudaFree(d_P);
//    cudaFree(d_grads);
//    cudaFree(d_random);
//}


//void
//gpu_umap_head_tail(int n_edges, int n_vertices, float *h_D_embed, int dims_embed, int *h_heads, int *h_tails,
//                   float *h_P, int epochs, float init_lr) {
//
//    //allocated and copy memory to the gpu
//    float *d_D_embed = copy_H_to_D(h_D_embed, n_vertices * dims_embed);
//    int *d_heads = copy_H_to_D(h_heads, n_edges);
//    int *d_tails = copy_H_to_D(h_tails, n_edges);
//    float *d_P = copy_H_to_D(h_P, n_edges);
//    float *d_grads = gpu_malloc_float_zero(n_vertices * dims_embed);
//
//    //random
//    int number_of_threads = min(n_vertices, 32768);
//    int number_of_blocks = number_of_threads / BLOCK_SIZE;
//    if (number_of_threads % BLOCK_SIZE) number_of_blocks++;
//    curandState *d_random;
//    cudaMalloc((void **) &d_random, number_of_threads * sizeof(curandState));
//    init_random << < number_of_blocks, BLOCK_SIZE >> > (d_random);
//
//    for (int epoch = 0; epoch < epochs; epoch++) {
//        float lr = get_lr(init_lr, epoch, epochs);
//        cudaMemset(d_grads, 0, n_vertices * dims_embed * sizeof(float));
//        compute_grads_head_tail << < number_of_blocks, BLOCK_SIZE >> >
//        (d_grads, d_P, n_edges, n_vertices, d_heads, d_tails, d_D_embed, dims_embed, lr, d_random);
//        apply_grads << < number_of_blocks, BLOCK_SIZE >> > (d_D_embed, d_grads, n_vertices, dims_embed);
//    }
//
//    //copy back and delete
//    cudaMemcpy(h_D_embed, d_D_embed, n_vertices * dims_embed * sizeof(float), cudaMemcpyDeviceToHost);
//    cudaFree(d_D_embed);
//    cudaFree(d_heads);
//    cudaFree(d_tails);
//    cudaFree(d_P);
//    cudaFree(d_grads);
//    cudaFree(d_random);
//}

__global__
void convert(int *d_dst_int, long *d_src_long, int n) {

    for (int i = threadIdx.x + blockIdx.x * blockDim.x; i < n; i += blockDim.x * gridDim.x) {
        d_dst_int[i] = (int) d_src_long[i];
    }
}

//void gpu_umap_2(int normalized, int n, float *h_D_embed, int dims_embed, int *h_N, long *h_neighbor_counts, int k,
//           float *h_P, int epochs, float init_lr, int neg_samples) {

void gpu_umap_2(int normalized, // unused
                int sym_attraction, // unused
                int momentum, // unused
                float *h_D_embed, //head_embedding,
                float *h_D_embed_other, //tail_embedding,
                int *h_N, //head,
                int *tail, // im not using this
                float *h_weights,//weights,
                long *h_neighbor_counts, //neighbor_counts,
                float *all_updates, // unused
                float *gains, // unused
                float a, // unused
                float b, // unused
                int dims_embed, //dim,
                int n_vertices,
                float init_lr,
                int n_epochs,
                int n_edges
) {

    //allocated and copy memory to the gpu
    float *d_D_embed = copy_H_to_D(h_D_embed, n_vertices * dims_embed);
    int *d_N = copy_H_to_D(h_N, n_edges);
    long *d_neighbor_counts_long = copy_H_to_D(h_neighbor_counts, n_vertices);
    int *d_neighbor_counts = gpu_malloc_int(n_vertices);
    int *d_neighbor_ends = gpu_malloc_int_zero(n_vertices);
    float *d_weights = copy_H_to_D(h_weights, n_edges);
    float *d_grads = gpu_malloc_float_zero(n_vertices * dims_embed);


    //random
    int number_of_threads = min(n_vertices, 32768);
    int number_of_blocks = number_of_threads / BLOCK_SIZE;
    if (number_of_threads % BLOCK_SIZE) number_of_blocks++;
    curandState *d_random;
    cudaMalloc((void **) &d_random, number_of_threads * sizeof(curandState));
    init_random << < number_of_blocks, BLOCK_SIZE >> > (d_random);

    convert<<<number_of_blocks, BLOCK_SIZE>>>(d_neighbor_counts, d_neighbor_counts_long, n_vertices);
    inclusive_scan(d_neighbor_counts, d_neighbor_ends, n_vertices);

    for (int i_epoch = 0; i_epoch < n_epochs; i_epoch++) {
        float lr = get_lr(init_lr, i_epoch, n_epochs);
        cudaMemset(d_grads, 0, n_vertices * dims_embed * sizeof(float));
        compute_grads << < number_of_blocks, BLOCK_SIZE >> >
        (normalized, d_grads, d_weights, n_vertices, d_N, d_neighbor_ends, d_D_embed, a, b, dims_embed, d_random);
        apply_grads << < number_of_blocks, BLOCK_SIZE >> > (d_D_embed, d_grads, n_vertices, dims_embed, lr);
    }

    //copy back and delete
    cudaMemcpy(h_D_embed, d_D_embed, n_vertices * dims_embed * sizeof(float), cudaMemcpyDeviceToHost);
    cudaFree(d_D_embed);
    cudaFree(d_N);
    cudaFree(d_neighbor_counts);
    cudaFree(d_weights);
    cudaFree(d_grads);
    cudaFree(d_random);
}

void gpu_umap(
        int normalized,
        int sym_attraction,
        int momentum,
        float *head_embedding,
        float *tail_embedding,
        int *head,
        int *tail,
        float *weights,
        long *neighbor_counts,
        float *all_updates,
        float *gains,
        float a,
        float b,
        int dim,
        int n_vertices,
        float initial_lr,
        int n_edges,
        int n_epochs
) {
    int k = n_edges / n_vertices;
//    gpu_umap_2(normalized, n_vertices, head_embedding, dim, head, neighbor_counts, n_edges / n_vertices, weights,
//               n_epochs,
//               initial_lr, 1);
    gpu_umap_2(
            normalized, // unused
            sym_attraction, // unused
            momentum, // unused
            head_embedding,
            tail_embedding,
            head,
            tail,
            weights,
            neighbor_counts,
            all_updates, // unused
            gains, // unused
            a, // unused
            b, // unused
            dim,
            n_vertices,
            initial_lr,
            n_epochs,
            n_edges
    );
//    printf("head: ");
//    for (int i = 0; i < 30; i++) {
//        printf("%d ", head[i]);
//    }
//    printf("\n");
//    printf("tail: ");
//    for (int i = 0; i < 30; i++) {
//        printf("%d ", tail[i]);
//    }
//    printf("\n");
}
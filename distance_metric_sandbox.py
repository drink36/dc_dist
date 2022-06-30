import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from tqdm.auto import tqdm
from experiment_utils.get_data import get_dataset

def distance_metric(points):
    """
    We define the distance from x_i to x_j as min(max(P(x_i, x_j))), where 
        - P(x_i, x_j) is any path from x_i to x_j
        - max(P(x_i, x_j)) is the largest edge weight in the path
        - min(max(P(x_i, x_j))) is the smallest largest edge weight

    We do this through the following pseudocode:
    -------------------------------------------
        Start with:
            - the pairwise Euclidean distance matrix D
            - an empty adjacency matrix A
        Returns:
            - density-distance matrix C

        for i < n^2:
            epsilon <- i-th smallest distance in D(X)
            Put epsilon into A in the same position as it is in D(X)
            for each pair of points without a density-connected distance x_i, x_j in X:
                Find the shortest path in A from x_i to x_j
                If such a path exists, the density-connected distance from x_i to x_j is epsilon
    """
    num_points = int(points.shape[0])
    density_connections = np.zeros([num_points, num_points])
    A = np.zeros([num_points, num_points])
    D = np.zeros([num_points, num_points])

    for i in range(num_points):
        x = points[i]
        for j in range(i+1, num_points):
            y = points[j]
            dist = np.sqrt(np.sum(np.square(x - y)))
            D[i, j] = dist
            D[j, i] = dist

    flat_D = np.reshape(D, [num_points * num_points])
    argsort_inds = np.argsort(flat_D)

    # FIXME -- this is slow because the same distance gets handled multiple times.
    #          Should instead do one iteration for each unique pairwise distance
    for step in tqdm(range(num_points * num_points)):
        i_index = int(argsort_inds[step] / num_points)
        j_index = argsort_inds[step] % num_points
        epsilon = D[i_index, j_index]
        A[i_index, j_index] = epsilon

        graph = nx.from_numpy_array(A)
        paths = nx.shortest_path(graph)
        has_zeros = False
        for i in range(num_points):
            for j in range(i+1, num_points):
                if density_connections[i, j] == 0:
                    has_zeros = True
                    if i in paths:
                        if j in paths[i]:
                            density_connections[i, j] = epsilon
                            density_connections[j, i] = epsilon
        if not has_zeros:
            break

    return density_connections


def subsample_points(points, labels, num_classes, points_per_class):
    all_classes = np.unique(labels)
    class_samples = np.random.choice(all_classes, num_classes, replace=False)
    sample_indices = np.concatenate(
        [np.where(labels == sampled_class) for sampled_class in class_samples]
    )
    total_points_per_class = int(sample_indices.shape[-1])
    if points_per_class < total_points_per_class:
        stride_rate = float(total_points_per_class) / points_per_class
        class_subsample_indices = np.arange(0, total_points_per_class, step=stride_rate).astype(np.int32)
        sample_indices = sample_indices[:, class_subsample_indices]

    sample_indices = np.reshape(sample_indices, -1)
    points = points[sample_indices]
    labels = labels[sample_indices]
    return points, labels

def uniform_line_example():
    points = np.stack([np.arange(50), np.zeros(50)], axis=1)
    pairwise_dists = distance_metric(points)
    pairwise_dists = np.reshape(pairwise_dists, [-1])
    plt.hist(pairwise_dists)
    plt.show()
    plt.close()

def linear_growth_example():
    pass
    plt.hist(pairwise_dists)
    plt.show()
    plt.close()

def coil_example():
    points, labels = get_dataset('coil', num_points=-1)
    points, labels = subsample_points(
        points,
        labels,
        num_classes=2,
        points_per_class=36
    )
    pairwise_dists = distance_metric(points)
    pairwise_dists = np.reshape(pairwise_dists, [-1])
    plt.hist(pairwise_dists, bins=50)
    plt.show()
    plt.close()

if __name__ == '__main__':
    # uniform_line_example()
    coil_example()

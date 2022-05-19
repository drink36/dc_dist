import argparse
import os
import copy
import time
from tqdm import tqdm
import numpy as np
from experiment_utils.metrics import classifier_accuracy, cluster_quality, cluster_distances
from experiment_utils.general_utils import get_ab, make_plot
from experiment_utils.get_data import get_dataset
from experiment_utils.get_algorithm import get_algorithm

def gpu_analysis():
    datasets = [
        'mnist',
        'fashion_mnist',
        'swiss_roll',
        'coil',
        'google_news',
    ]
    num_points_list = [
        60000,
        60000,
        5000,
        7200,
        350000,
    ]

    experiment_params = {
        'recreate_tsne_gpu': {
            'optimize_method': 'gidr_dun',
            'n_neighbors': 15,
            'random_init': False,
            'umap_metric': False,
            'tsne_symmetrization': False,
            'neg_sample_rate': 1,
            'n_epochs': 500,
            'normalized': True, # Also set amplify_grads to True
            'sym_attraction': False,
            'frobenius': False,
            'angular': False,
            'tsne_scalars': True,
            'gpu': True,
            'torch': False,
            'num_threads': -1,
            'numba': False
        },
        'recreate_umap_gpu': {
            'optimize_method': 'gidr_dun',
            'n_neighbors': 15,
            'random_init': False,
            'umap_metric': False,
            'tsne_symmetrization': False,
            'neg_sample_rate': 1,
            'n_epochs': 500,
            'normalized': False, # Also set amplify_grads to True
            'sym_attraction': False,
            'frobenius': False,
            'angular': False,
            'tsne_scalars': True,
            'gpu': True,
            'torch': False,
            'num_threads': -1,
            'numba': False
        },
        ### RAPIDS UMAP
        'rapids_umap': {
            'n_neighbors': 15,
            'random_init': False,
            'neg_sample_rate': 5,
            'n_epochs': 500,
            'normalized': False, # Also set amplify_grads to True
        },

        ### RAPIDS TSNE
        'rapids_tsne': {
            'n_neighbors': 90,
            'n_epochs': 500,
            'normalized': False, # Also set amplify_grads to True
        },
    }

    outputs_path = os.path.join('outputs', 'gpu')
    pbar = tqdm(enumerate(datasets), total=len(datasets))
    for data_i, dataset in pbar:
        try:
            points, labels = get_dataset(dataset, num_points_list[data_i])
        except Exception as E:
            print('Could not find dataset %s' % dataset)
            print('Error raised was:', str(E))
            print('Continuing')
            print('.')
            print('.')
            print('.')
            print('\n')
            break

        dataset_output_path = os.path.join(outputs_path, dataset)
        if not os.path.isdir(dataset_output_path):
            os.makedirs(dataset_output_path, exist_ok=True)

        for experiment in experiment_params:
            experiment_path = os.path.join(dataset_output_path, experiment)
            if not os.path.isdir(experiment_path):
                os.makedirs(experiment_path, exist_ok=True)
            print(experiment_path)
            try:
                instance_params = copy.copy(experiment_params[experiment])
                instance_params['amplify_grads'] = instance_params['normalized'] # normalized and amplify_grads go together

                # google-news dataset requires cosine distance and is too big for Lap. Eigenmaps initialization
                if dataset == 'google_news':
                    instance_params['random_init'] = True
                    instance_params['angular'] = True

                instance_params['a'] = 1
                instance_params['b'] = 1

                algorithm_str = 'gidr_dun'
                if 'rapids' in experiment:
                    algorithm_str = experiment
                    if dataset == 'coil':
                        continue

                dr = get_algorithm(algorithm_str, instance_params, verbose=False)

                start = time.time()
                embedding = dr.fit_transform(points)
                end = time.time()
                total_time = end - start
                try:
                    # opt_time = embedding.opt_time
                    opt_time = dr.opt_time
                except AttributeError:
                    opt_time = -1

                times = {
                    'opt_time': opt_time,
                    'total_time': total_time
                }
                print(experiment + " on " + dataset + " opt time " + str(opt_time) + " total time " + str(total_time))
                np.save(os.path.join(experiment_path, "times.npy"), times)
                np.save(os.path.join(experiment_path, "embedding.npy"), embedding)
                np.save(os.path.join(experiment_path, "labels.npy"), labels)
            except Exception as E:
                print('Could not run analysis for %s gpu experiment on %s dataset' % (experiment, dataset))
                print('The following exception was raised:')
                print(str(E))
                print('continuing')
                print('.')
                print('.')
                print('.')
                continue


def dim_timings():
    datasets = [
        'mnist',
    ]
    num_points_list = [
        60000,
    ]
    dims_list = [
        100,
        400,
        1600,
        3200,
        12800,
        51200
    ]

    experiment_params = {
        'recreate_tsne_gpu': {
            'optimize_method': 'gidr_dun',
            'n_neighbors': 15,
            'random_init': True,
            'umap_metric': False,
            'tsne_symmetrization': False,
            'neg_sample_rate': 1,
            'n_epochs': 500,
            'normalized': True,
            'sym_attraction': False,
            'frobenius': False,
            'angular': False,
            'tsne_scalars': True,
            'gpu': True,
            'torch': False,
            'num_threads': -1,
            'numba': False
        },
        'recreate_umap_gpu': {
            'optimize_method': 'gidr_dun',
            'n_neighbors': 15,
            'random_init': True,
            'umap_metric': False,
            'tsne_symmetrization': False,
            'neg_sample_rate': 1,
            'n_epochs': 500,
            'normalized': False,
            'sym_attraction': False,
            'frobenius': False,
            'angular': False,
            'tsne_scalars': True,
            'gpu': True,
            'torch': False,
            'num_threads': -1,
            'numba': False
        },
        ### RAPIDS UMAP
        'rapids_umap': {
            'n_neighbors': 15,
            'random_init': False,
            'neg_sample_rate': 5,
            'n_epochs': 500,
            'normalized': False, # Also set amplify_grads to True
        },

        ### RAPIDS TSNE
        'rapids_tsne': {
            'n_neighbors': 90,
            'n_epochs': 500,
            'normalized': False, # Also set amplify_grads to True
        },
    }

    outputs_path = os.path.join('outputs', 'dim_timing')
    pbar = tqdm(enumerate(datasets), total=len(datasets))
    for data_i, dataset in pbar:
        dataset_output_path = os.path.join(outputs_path, dataset)
        if not os.path.isdir(dataset_output_path):
            os.makedirs(dataset_output_path, exist_ok=True)
        for dim in dims_list:
            try:
                num_points = num_points_list[data_i]
                points, labels = get_dataset(dataset, num_points, desired_dim=dim)
                print(points.shape)
            except Exception as E:
                print('Could not find dataset %s' % dataset)
                print('Error raised was:', str(E))
                print('Continuing')
                print('.')
                print('.')
                print('.')
                print('\n')
            dim_path = os.path.join(dataset_output_path, '%s_dim' % str(dim))
            if not os.path.isdir(dim_path):
                os.makedirs(dim_path, exist_ok=True)
            for experiment in experiment_params:
                experiment_path = os.path.join(dim_path, experiment)
                if not os.path.isdir(experiment_path):
                    try:
                        os.makedirs(experiment_path, exist_ok=True)
                        print(experiment_path)

                        instance_params = copy.copy(experiment_params[experiment])
                        instance_params['amplify_grads'] = instance_params['normalized'] # normalized and amplify_grads go together
                        if dataset == 'google_news':
                            instance_params['random_init'] = True
                            instance_params['angular'] = True
                        instance_params['a'] = 1
                        instance_params['b'] = 1

                        algorithm_str = 'gidr_dun'
                        if 'rapids' in experiment:
                            algorithm_str = experiment
                            if dataset == 'coil':
                                continue

                        dr = get_algorithm(algorithm_str, instance_params, verbose=False)

                        start = time.time()
                        embedding = dr.fit_transform(points)
                        end = time.time()
                        total_time = end - start
                        try:
                            opt_time = embedding.opt_time
                        except AttributeError:
                            opt_time = -1

                        times = {
                            'opt_time': opt_time,
                            'total_time': total_time
                        }
                        np.save(os.path.join(experiment_path, "times.npy"), times)
                    except Exception as E:
                        print('Could not run analysis for %s dim experiment on %s dataset' % (experiment, dataset))
                        print('The following exception was raised:')
                        print(str(E))
                        print('continuing')
                        print('.')
                        print('.')
                        print('.')
                        continue

def data_size_timings():
    datasets = [
        'mnist',
        'google_news',
    ]
    num_points_list = [
        1000,
        2000,
        4000,
        8000,
        16000,
        32000,
        64000,
        128000,
        256000,
        512000
    ]

    experiment_params = {
        'recreate_tsne_gpu': {
            'optimize_method': 'gidr_dun',
            'n_neighbors': 15,
            'random_init': True,
            'umap_metric': False,
            'tsne_symmetrization': False,
            'neg_sample_rate': 1,
            'n_epochs': 500,
            'normalized': True,
            'sym_attraction': False,
            'frobenius': False,
            'angular': False,
            'tsne_scalars': True,
            'gpu': True,
            'torch': False,
            'num_threads': -1,
            'numba': False
        },
        'recreate_umap_gpu': {
            'optimize_method': 'gidr_dun',
            'n_neighbors': 15,
            'random_init': True,
            'umap_metric': False,
            'tsne_symmetrization': False,
            'neg_sample_rate': 1,
            'n_epochs': 500,
            'normalized': False,
            'sym_attraction': False,
            'frobenius': False,
            'angular': False,
            'tsne_scalars': True,
            'gpu': True,
            'torch': False,
            'num_threads': -1,
            'numba': False
        },
        ### RAPIDS UMAP
        'rapids_umap': {
            'n_neighbors': 15,
            'random_init': False,
            'neg_sample_rate': 5,
            'n_epochs': 500,
            'normalized': False, # Also set amplify_grads to True
        },

        ### RAPIDS TSNE
        'rapids_tsne': {
            'n_neighbors': 90,
            'learning_rate': 1.0,
            'n_epochs': 500,
            'normalized': False, # Also set amplify_grads to True
        },
    }

    outputs_path = os.path.join('outputs', 'data_size_timing')
    pbar = tqdm(enumerate(datasets), total=len(datasets))
    for data_i, dataset in pbar:
        dataset_output_path = os.path.join(outputs_path, dataset)
        if not os.path.isdir(dataset_output_path):
            os.makedirs(dataset_output_path, exist_ok=True)
        for num_points in num_points_list:
            try:
                points, labels = get_dataset(dataset, num_points)
            except Exception as E:
                print('Could not find dataset %s' % dataset)
                print('Error raised was:', str(E))
                print('Continuing')
                print('.')
                print('.')
                print('.')
                print('\n')
            num_points_path = os.path.join(dataset_output_path, '%s_points' % str(num_points))
            if not os.path.isdir(num_points_path):
                os.makedirs(num_points_path, exist_ok=True)
            for experiment in experiment_params:
                experiment_path = os.path.join(num_points_path, experiment)
                if not os.path.isdir(experiment_path):
                    try:
                        os.makedirs(experiment_path, exist_ok=True)
                        print(experiment_path)

                        instance_params = copy.copy(experiment_params[experiment])
                        instance_params['amplify_grads'] = instance_params['normalized'] # normalized and amplify_grads go together
                        if dataset == 'google_news':
                            instance_params['random_init'] = True
                            instance_params['angular'] = True
                        instance_params['a'] = 1
                        instance_params['b'] = 1

                        algorithm_str = 'gidr_dun'
                        if 'rapids' in experiment:
                            algorithm_str = experiment
                            if dataset == 'coil':
                                continue

                        dr = get_algorithm(algorithm_str, instance_params, verbose=False)

                        start = time.time()
                        embedding = dr.fit_transform(points)
                        end = time.time()
                        total_time = end - start
                        try:
                            opt_time = embedding.opt_time
                        except AttributeError:
                            opt_time = -1

                        times = {
                            'opt_time': opt_time,
                            'total_time': total_time
                        }
                        np.save(os.path.join(experiment_path, "times.npy"), times)
                    except Exception as E:
                        print('Could not run analysis for %s data_size experiment on %s dataset' % (experiment, dataset))
                        print('The following exception was raised:')
                        print(str(E))
                        print('continuing')
                        print('.')
                        print('.')
                        print('.')
                        continue



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--analysis-type',
        choices=['runtimes', 'data_size_sweep', 'dim_size_sweep'],
        required=True,
    )
    args = parser.parse_args()
    if args.analysis_type == 'runtimes':
        gpu_analysis()
    elif args.analysis_type == 'data_size_sweep':
        data_size_timings()
    elif args.analysis_type == 'dim_size_sweep':
        dim_timings()
    else:
        raise ValueError('Unknown experiment type')

import numpy as np
from tensorflow import keras as tfk
from umap_ import UMAP
import argparse
from sklearn.manifold import TSNE
from matplotlib import pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument(
    '--random-init',
    action='store_true',
    help='whether to initialize randomly'
)
parser.add_argument(
    '--tsne-symmetrization',
    action='store_true',
    help='whether to symmetrize akin to tSNE method'
)
parser.add_argument(
    '--ignore-umap-metric',
    action='store_true',
    help='If true, do NOT subtract rho\'s in the umap pseudo-distance metric'
)
parser.add_argument(
    '--optimize-method',
    choices=[
        'umap_sampling',
        'umap_uniform',
        'barnes_hut_tsne',
        'barnes_hut_umap'
    ],
    default='umap_sampling',
    help='Which optimization algorithm to use'
)
parser.add_argument(
    '--weight-scaling',
    choices=['tsne', 'umap'],
    default='umap',
    help='Which optimization algorithm to use'
)
parser.add_argument(
    '--downsample-stride',
    type=int,
    default=15
)
parser.add_argument(
    '--tsne-weights',
    action='store_true',
    help='If present, set a and b to tSNE values'
)
parser.add_argument(
    '--dr-algorithm',
    choices=['umap', 'tsne'],
    default='umap',
    help='Which algorithm to use to save images'
)
parser.add_argument(
    '--n-neighbors',
    type=int,
    default=15
)
parser.add_argument(
    '--n-epochs',
    type=int,
    default=500
)
args = parser.parse_args()

init = 'spectral'
if args.random_init:
    init = 'random'

print('Loading MNIST data...')
train, _ = tfk.datasets.mnist.load_data(path='mnist.npz')
x_train, y_train = train
x_train, y_train = x_train[::args.downsample_stride], y_train[::args.downsample_stride]
num_samples = int(x_train.shape[0])
x_train = np.reshape(x_train, [num_samples, -1])

if args.tsne_weights:
    a, b = 1, 1
else:
    a, b = None, None

if args.dr_algorithm == 'umap':
    dr = UMAP(
            n_neighbors=args.n_neighbors,
            n_epochs=args.n_epochs,
            random_state=12345,
            init=init,
            pseudo_distance=(not args.ignore_umap_metric),
            tsne_symmetrization=args.tsne_symmetrization,
            optimize_method=args.optimize_method,
            weight_scaling=args.weight_scaling,
            a=a,
            b=b,
        )
else:
    dr = TSNE(random_state=12345)

print('fitting...')
projection = dr.fit_transform(x_train)

plt.scatter(projection[:, 0], projection[:, 1], c=y_train, s=1)
plt.show()

Code to recreate the experiments from the paper ''Connecting the Dots: density-connectivity distance unifies DBSCAN, k-center and spectral clustering.''

The distance metric is calculated in `distance_metric.py`. The k-center clustering on the dc-dist is given in `density_tree.py` and `cluster_tree.py`. We provide an
implementation of DBSCAN\* in `DBSCAN.py`. Furthermore, our implementation of Ultrametric Spectral Clustering is given in `SpectralClustering.py`.

The code to calculate the distance measure can be found in `distance_metric.py`. Experiment scripts are then located in
 - `k_vs_epsilon.py` fig(7) in essay
 - `noise_robustness.py` fig(5) in essay
 - `distances_plot.py` fig(2) in essay
 - `compare_clustering.py` fig(3) in essay

If you would like to mess around with the clusterings and assert for yourself that they are equivalent, we recommend the sandbox file `cluster_dataset.py`.

We provide an ultrametric visualization tool in the file `tree_plotting.py`. This allows you to look at the tree of dc-distances given by a specific dataset.

You will have to download the coil-100 dataset from [here](https://www.kaggle.com/datasets/jessicali9530/coil100) and unpack it
into the path `data/coil-100`.

Feel free to email if you have any questions -- draganovandrew@cs.au.dk

Change from drink36(YU)
Some experiment report at [here](https://hackmd.io/VqRnOvy6TZOZLfMs1GwdhA)
Some experiment scripts are then located in 
- `TestIndividalClusterings.py` fig(6) in essay
- `RealDataClusterings.py` fig(6) in essay
I have changed the plot function in these two functions. If you add more datasets, you might need to change it.
More data for `RealDataClusterings.py` and `TestIndividalClusterings.py` after generate at [here](https://drive.google.com/drive/folders/1Dl4O_RMQRdS8ZzK4wzJjzX4APnRykDNW?usp=drive_link) and [here](https://drive.google.com/drive/folders/1vwBz9zoKR_zxGbajncxDQ9ZRg_El1pl2?usp=drive_link). You can also find `data/synth` at [here](https://drive.google.com/drive/folders/1RpShN-3fgjeCI1QN1PuFRbmslunR7lzv?usp=drive_link) 
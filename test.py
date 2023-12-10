import numpy as np
from sklearn.manifold import MDS
X = np.array([[0, 0, 0], [0, 0, 1], [1, 1, 1], [0, 1, 0], [0, 1, 1],[1, 1, 0]])
mds = MDS(random_state=0)
X_transform = mds.fit_transform(X)
print(X_transform)

mds_1 = MDS(n_components=1,random_state=0)
X_transform_1 = mds_1.fit_transform(X)
print(X_transform_1)
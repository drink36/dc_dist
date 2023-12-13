import numpy as np
from experiment_utils.get_data import get_dataset, make_circles
from testcompare import compare_clusterings

#points,labels = get_dataset("synth")
#print(np.size(points))
#print(np.size(labels))
#print(labels)
compare_clusterings()
#no_structure = np.random.rand(500, 2), None
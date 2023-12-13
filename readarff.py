from scipy.io import arff
import numpy as np

# 讀取ARFF檔案
def read_arff(arff_file):
    data, meta = arff.loadarff(arff_file)
    return data

# 提取X和y變數
def extract_xy(arff_data):
    # 提取X變數（二維座標）
    X = np.column_stack((arff_data['x'], arff_data['y']))  # 假設座標列分別為'X1'和'X2'

    # 提取y變數（標籤）
    y = arff_data['class']  # 假設標籤列為'label'

    return X, y
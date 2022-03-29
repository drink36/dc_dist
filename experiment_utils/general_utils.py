from matplotlib import pyplot as plt

def get_ab(tsne_scalars):
    if tsne_scalars:
        return 1, 1
    return None, None

def make_plot(embedding, labels, save_path=None, show_plot=False):
    plt.scatter(embedding[:, 0], embedding[:, 1], c=labels, s=0.1, alpha=0.8)
    if save_path is not None:
        plt.savefig(save_path)
    if show_plot:
        plt.show()

    plt.close()

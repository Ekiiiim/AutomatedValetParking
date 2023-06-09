from animation.animation import ploter, plt
import argparse
from config import read_config
from map import costmap
import os


def main(file, config):
    # create the park map
    park_map = costmap.Map(
        file=file, discrete_size=config['map_discrete_size'])
    ploter.plot_obstacles(map=park_map)
    # save img
    fig_name = args.case_name + 'Map.png'
    fig_path = config['pic_path']
    if not os.path.exists(fig_path):
        os.makedirs(fig_path)
    save_fig = os.path.join(fig_path, fig_name)
    plt.savefig(save_fig, dpi=600)
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='hybridAstar')
    parser.add_argument("--config_name", type=str, default="config")
    parser.add_argument("--case_name", type=str, default="Case1")
    args = parser.parse_args()

    # initial
    # load configure file to a dict
    config = read_config.read_config(config_name=args.config_name)

    # read benchmark case
    case_name = args.case_name + '.csv'
    file = os.path.join(config['Benchmark_path'], case_name)

    main(file=file, config=config)
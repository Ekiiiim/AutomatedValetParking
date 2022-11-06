'''
Author: wenqing-hnu
Date: 2022-10-20
LastEditors: wenqing-hnu
LastEditTime: 2022-11-06
FilePath: /Automated Valet Parking/main.py
Description: the main file of the hybrid a star algorithm for parking

Copyright (c) 2022 by wenqing-hnu, All Rights Reserved. 
'''


from path_planner import path_planner
from animation.animation import ploter, plt
from animation.record_solution import DataRecorder
from map import costmap
from velocity_planner import velocity_plan
from interpolation import path_interpolation
from optimization import path_optimazition, ocp_optimization
from config import read_config

import yaml
import os
import copy

import argparse


def main(file, config):
    # create the park map
    park_map = costmap._map(
        file=file, discrete_size=config['map_discrete_size'])

    # create vehicle
    ego_vehicle = costmap.Vehicle()

    # create path planner
    planner = path_planner.path_planner(config=config,
                                        map=park_map,
                                        vehicle=ego_vehicle)

    # create path optimizer
    path_optimizer = path_optimazition.path_opti(park_map, ego_vehicle, config)

    # create path interpolation
    interplotor = path_interpolation.interpolation(
        config=config, map=park_map, vehicle=ego_vehicle)

    # create velocity planner
    velocity_planner = velocity_plan.velocity_planner(vehicle=ego_vehicle,
                                                      velocity_func_type=config['velocity_func_type'])

    # create path optimization planner
    ocp_planner = ocp_optimization.ocp_optimization(
        park_map=park_map, vehicle=ego_vehicle, config=config)

    # rapare memory to store path
    final_opt_path = []  # store the optimization path
    final_insert_path = []  # store the interpolation path
    final_ocp_path = []  # store ocp path

    # path planning
    optimal_tf = 0
    t = 0
    optimal_time_info = []
    original_path, path_info, split_path = planner.path_planning()
    for path_i in split_path:
        # optimize path
        opti_path, forward = path_optimizer.get_result(path_i)

        # cubic fitting
        path_arc_length, path_i_info = interplotor.cubic_fitting(opti_path)

        # velocity planning
        v_acc_func, terminiate_time = velocity_planner.solve_nlp(
            arc_length=path_arc_length)

        # insert points
        insert_path = interplotor.cubic_interpolation(
            path=opti_path, path_i_info=path_i_info, v_a_func=v_acc_func, forward=forward, terminate_t=terminiate_time, path_arc_length=path_arc_length)

        # ocp problem solve
        ocp_traj, optimal_ti, optimal_dt = ocp_planner.solution(
            path=insert_path)
        optimal_time_info.append([optimal_ti, optimal_dt])
        # add time information
        for ocp_i in ocp_traj:
            t += optimal_dt
            ocp_i.append(t)
        optimal_tf += optimal_ti

        final_opt_path.extend(opti_path)
        final_insert_path.extend(insert_path)
        final_ocp_path.extend(ocp_traj)

    # save traj into a csv file
    DataRecorder.record(save_path=config['save_path'],
                        save_name=case_name, trajectory=final_ocp_path)

    # animation
    print('trajectory_time:', optimal_tf)
    ploter.plot_obstacles(map=park_map)
    # park_map.visual_cost_map()
    ploter.plot_final_path(path=original_path, label='Hybrid A*',
                           color='green', show_car=False)
    ploter.plot_final_path(path=final_opt_path, label='Optimized Path',
                           color='blue', show_car=False)
    ploter.plot_final_path(path=final_insert_path, label='Interpolation Traj',
                           color='red', show_car=False)
    ploter.plot_final_path(path=final_ocp_path, label='Optimized Traj',
                           color='gray', show_car=True)
    plt.legend()
    fig_name = args.case_name + '.png'
    fig_path = config['pic_path']
    if not os.path.exists(fig_path):
        os.makedirs(fig_path)
    save_fig = os.path.join(fig_path, fig_name)
    plt.savefig(save_fig, dpi=600)
    plt.close()
    gif_name = args.case_name + '.gif'
    save_gif_name = os.path.join(fig_path, gif_name)
    ploter.save_gif(path=final_ocp_path, color='gray', map=park_map,
                    show_car=True, save_gif_name=save_gif_name)
    print('solved')


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

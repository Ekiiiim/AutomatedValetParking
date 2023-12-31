'''
Author: wenqing-hnu
Date: 2022-10-20
LastEditors: wenqing-hnu
LastEditTime: 2022-11-12
FilePath: /Automated Valet Parking/path_plan/hybrid_a_star.py
Description: hybrid a star 

Copyright (c) 2022 by wenqing-hnu, All Rights Reserved. 
'''

import numpy as np
import math
import queue
from map.costmap import Map, Vehicle
from collision_check import collision_check
from path_plan.compute_h import Dijkstra
from path_plan import rs_curve
from animation.animation import *


class Node:
    '''
    Node contains: 
                position(x,y);
                vehicle heading theta;
                node index;
                node father index;
                node child index;
                is forward: true or false
                steering angle: rad
                f,g,h value
    '''

    def __init__(self,
                 index: np.int32 = None,
                 grid_index: np.int32 = None,
                 x: np.float64 = 0.0,
                 y: np.float64 = 0.0,
                 theta: np.float64 = 0.0,
                 parent_index: np.int32 = None,
                 child_index: np.int32 = None,
                 is_in_openlist: bool = False,
                 is_in_closedlist: bool = False,
                 is_forward: bool = None,
                 steering_angle: np.float64 = None) -> None:

        self.index = index
        self.grid_index = grid_index
        self.x = x
        self.y = y
        self.theta = theta
        self.parent_index = parent_index
        self.child_index = child_index
        self.in_open = is_in_openlist
        self.in_closed = is_in_closedlist
        self.forward = is_forward
        self.steering_angle = steering_angle
        self.h = 0
        self.g = 0
        self.f = 0

    def __lt__(self, other):
        '''
        revise compare function for PriorityQueue
        '''
        result = False
        if self.f < other.f:
            result = True
        return result


class hybrid_a_star:
    def __init__(self,
                 config: dict,
                 park_map: Map,
                 vehicle: Vehicle) -> None:

        # create vehicle
        self.vehicle = vehicle

        # discrete steering angle
        self.steering_angle = np.linspace(- self.vehicle.max_steering_angle,
                                          self.vehicle.max_steering_angle,
                                          config['steering_angle_num'])  # rad

        # park_map
        self.park_map = park_map

        # caculate heuristic and store h value
        self.heuristic = Dijkstra(park_map)
        _, self.h_value_list = self.heuristic.compute_path(
            node_x=park_map.case.x0, node_y=park_map.case.y0)

        # default settings
        self.global_index = 0
        self.config = config
        self.open_list = queue.PriorityQueue()
        self.closed_list = []
        self.dt = config['dt']
        self.ddt = config['trajectory_dt']

        # initial node
        self.initial_node = Node(x=park_map.case.x0,
                                 y=park_map.case.y0,
                                 index=0,
                                 grid_index=park_map.convert_position_to_index(park_map.case.x0, park_map.case.y0),
                                 theta=rs_curve.pi_2_pi(park_map.case.theta0))
        # final node
        self.goal_node = Node(x=park_map.case.xf,
                              y=park_map.case.yf,
                              grid_index=park_map.convert_position_to_index(park_map.case.xf, park_map.case.yf),
                              theta=rs_curve.pi_2_pi(park_map.case.thetaf))

        # max delta heading
        self.max_delta_heading = self.vehicle.max_v * \
            np.tan(self.vehicle.max_steering_angle) / self.vehicle.lw * self.dt

        # create collision checker
        if self.config['collision_check'] == 'circle':
            self.collision_checker = collision_check.two_circle_checker(
                vehicle=self.vehicle, map=self.park_map, config=config)
        else:
            self.collision_checker = collision_check.distance_checker(
                vehicle=self.vehicle, map=self.park_map, config=config)
        
        # create goal_node_list (nodes that are N steps from goal_node)
        self.goal_list_mode = self.config['goal_list_mode']
        if self.goal_list_mode:
            self.open_list.put(self.goal_node)
            self.goal_node_list = self.create_goal_node_list(config['goal_list_size'])
            self.open_list.queue.clear()
            assert self.open_list.empty()
        else:
            self.goal_node_list = [self.goal_node]
            assert len(self.goal_node_list) == 1
            ploter.plot_obstacles(self.park_map)

        self.open_list.put(self.initial_node)
        self.initial_node.in_open = True

    def create_goal_node_list(self, step_num):
        ploter.plot_obstacles(self.park_map)
        goal_node_list = []
        for i in range(step_num):
            if self.open_list.empty():
                break
            current_node = self.open_list.get()
            goal_node_list.append(current_node)
            ploter.plot_goal_node(current_node)
            child_group = self.expand_node(current_node, True)
        return goal_node_list


    def expand_node(self,
                    current_node: Node,
                    finding_goal_list=False) -> queue.PriorityQueue:
        # caculate <x,y,theta> of the next node
        # next_index = 9 or 10(the first expansion)
        child_group = queue.PriorityQueue()
        next_index = 0
        travle_distance = 0  # v_max * dt
        next_index = int(2 * self.config['steering_angle_num'])
        for i in range(next_index):
            # caculate steering angle and gear
            steering_angle = self.steering_angle[i %
                                                 self.config['steering_angle_num']]
            if i < next_index / 2:
                speed = self.vehicle.max_v
                is_forward = True
            else:
                speed = - self.vehicle.max_v
                is_forward = False

            travle_distance = speed * self.dt
            theta_ = current_node.theta + \
                (self.vehicle.max_v * np.tan(steering_angle)) / \
                self.vehicle.lw * self.dt
            theta_ = rs_curve.pi_2_pi(theta_)
            x_ = current_node.x + travle_distance * np.cos(theta_)
            y_ = current_node.y + travle_distance * np.sin(theta_)

            # if the node is in closedlist or this node beyond the boundary, continue
            find_closednode = False
            for closednode_i in self.closed_list:
                if closednode_i.grid_index == self.park_map.convert_position_to_index(x_, y_) and abs(closednode_i.theta - theta_) == 0:
                    # print(abs(closednode_i.theta - theta_))
                    find_closednode = True
                    break
                # if beyond the boundary
                elif x_ > self.park_map.boundary[1] or x_ < self.park_map.boundary[0] or \
                        y_ > self.park_map.boundary[3] or y_ < self.park_map.boundary[2]:
                    find_closednode = True
                    break
            if find_closednode == True:
                continue
            else:
                find_opennode = False
                # find node in the open list
                for opennode_i in self.open_list.queue:
                    # if opennode_i.x == x_ and opennode_i.y == y_ and opennode_i.theta == theta_:
                    if opennode_i.grid_index == self.park_map.convert_position_to_index(x_, y_) and abs(opennode_i.theta - theta_) == 0:
                        # print(abs(opennode_i.theta - theta_))
                        child_node = opennode_i
                        find_opennode = True

            # if the node is firstly visited
            if find_opennode == False:
                # generate new node
                child_node = Node(x=x_,
                                  y=y_,
                                  theta=theta_,
                                  index=self.global_index + i + 1,
                                  grid_index=self.park_map.convert_position_to_index(x_, y_),
                                  parent_index=current_node.index,
                                  is_forward=is_forward,
                                  steering_angle=steering_angle)
                # draw on map
                ploter.plot_child_node(child_node)
                # collision check
                for i in range(math.ceil(self.dt / self.ddt)):
                    # discrete trajectory for collision check
                    # i : 0-9
                    travle_distance_i = speed * self.ddt * (i+1)
                    theta_i = current_node.theta + \
                        (self.vehicle.max_v * np.tan(steering_angle)) / \
                        self.vehicle.lw * self.ddt * (i+1)
                    theta_i = rs_curve.pi_2_pi(theta_i)
                    x_i = current_node.x + travle_distance_i * np.cos(theta_i)
                    y_i = current_node.y + travle_distance_i * np.sin(theta_i)

                    # collision check
                    collision = self.collision_checker.check(
                        node_x=x_i, node_y=y_i, theta=theta_i)

                    if collision:
                        # put the node into the closedlist
                        self.closed_list.append(child_node)
                        child_node.in_closed = True
                        break

                if not collision:
                    # caculate cost
                    child_node.g = self.calc_node_cost(
                        child_node, father_theta=current_node.theta, father_gear=current_node.forward)
                    # print(f"cost: {child_node.g}")
                # caculate heuristic
                    child_node.h = self.calc_node_heuristic(child_node, finding_goal_list)
                    # print(f"heuristic: {child_node.h}")
                # caculate f value
                    child_node.f = child_node.g + child_node.h
                # add this node into openlist
                    self.open_list.put(child_node)
                    child_node.in_open = True

            # if this node has been explored
            else:
                new_h = self.calc_node_heuristic(child_node, finding_goal_list)
                new_g = self.calc_node_cost(
                    child_node, father_theta=current_node.theta, father_gear=current_node.forward)
                new_f = new_h + new_g
                if new_f < child_node.f:
                    child_node.f = new_f
                    child_node.g = new_g
                    child_node.h = new_h
                    child_node.parent_index = current_node.index
                    child_node.forward = is_forward
                    child_node.steering_angle = steering_angle
            if child_node.in_closed == False and child_node.in_open == True:
                child_group.put(child_node)

        # put the current node into closed list
        current_node.in_closed = True
        current_node.in_open = False
        self.closed_list.append(current_node)

        self.global_index += next_index

        return child_group

    def calc_node_cost(self, node: Node, father_theta, father_gear) -> np.float64:
        '''
        input: child node
        output: the cost value of this node
        We consider two factors, gear and the delta of heading
        '''
        cost = 0
        cost_gear = 0
        gear = node.forward
        # print(f"gear: {gear}; father_gear: {father_gear}")
        if father_gear == None or gear != father_gear:
            cost_gear = self.config['cost_gear']

        cost_heading = abs(node.theta - father_theta)

        cost = cost_gear + self.config['cost_heading_change'] * cost_heading

        return self.config['cost_scale'] * cost

    def calc_node_heuristic(self, current_node: Node, finding_goal_list=False) -> np.float64:
        '''
        We use Dijkstra algorithm and RS curve length to calculate the heuristic value 
        '''
        # convert node to grid
        # grid_x = np.float64("%.1f" % (current_node.x + 0.05))
        # grid_y = np.float64("%.1f" % (current_node.y + 0.05))
        _grid_id = self.park_map.convert_position_to_index(grid_x=current_node.x,
                                                           grid_y=current_node.y)
        h_value = 0
        find_grid = False
        for i in range(len(self.h_value_list)):
            # find_x = self.h_value_list[i].grid_x == grid_x
            # find_y = self.h_value_list[i].grid_y == grid_y
            find_id = self.h_value_list[i].grid_id == _grid_id
            # if find_x and find_y:
            if find_id:
                find_grid = True
                h_value_1 = self.h_value_list[i].distance
                # print(f"wanted id: {_grid_id}; self.h_value_list[i].grid_id: {self.h_value_list[i].grid_id}")
                break
        if find_grid == False:
            # print("didn't find grid")
            h_value_1, self.h_value_list = self.heuristic.compute_path(
                node_x=current_node.x, node_y=current_node.y)

        max_c = 1 / self.vehicle.min_radius_turn
        min_L = -1
        if finding_goal_list or not self.goal_list_mode:
            rs_path = rs_curve.calc_optimal_path(sx=current_node.x,
                                                sy=current_node.y,
                                                syaw=current_node.theta,
                                                gx=self.goal_node.x,
                                                gy=self.goal_node.y,
                                                gyaw=self.goal_node.theta,
                                                maxc=max_c)
            min_L = rs_path.L
        else:
            for goal_node in self.goal_node_list:
                rs_path = rs_curve.calc_optimal_path(sx=current_node.x,
                                                    sy=current_node.y,
                                                    syaw=current_node.theta,
                                                    gx=goal_node.x,
                                                    gy=goal_node.y,
                                                    gyaw=goal_node.theta,
                                                    maxc=max_c)
                if min_L < 0 or rs_path.L < min_L:
                    min_L = rs_path.L
        
        assert min_L >= 0
        h_value_2 = min_L
        h_value_1 = h_value_1 / 100
        print(f"h_value_2: {h_value_2}  h_value_1: {h_value_1}")
        h_value = max(h_value_1, h_value_2)

        return h_value

    def try_reach_goal(self, current_node: Node) -> bool:
        '''
        if node is near the goal node, we check whether the rs curve could reach it
        '''
        # print("Entering try_reach_goal")
        collision = False
        rs_path = None
        in_radius = False
        collision_p = None
        distance = min(np.sqrt((current_node.x - goal_node.x)
                           ** 2+(current_node.y-goal_node.y)**2) for goal_node in self.goal_node_list)
        if distance < self.config['flag_radius']:
            in_radius = True
            rs_path, collision, collision_p = self.try_rs_curve(current_node)

        info = {'in_radius': in_radius,
                'collision_position': collision_p}

        return rs_path, collision, info

    def try_rs_curve(self, current_node: Node):
        '''
        generate rs curve and collision check
        return: rs_path is a class and collision is true or false
        '''
        for goal_node in self.goal_node_list:
            # print(f"trying rs curve for reaching ({goal_node.x}, {goal_node.y})")
            collision = False
            # generate max curvature based on min turn radius
            max_c = 1 / self.vehicle.min_radius_turn
            rs_path = rs_curve.calc_optimal_path(sx=current_node.x,
                                                sy=current_node.y,
                                                syaw=current_node.theta,
                                                gx=goal_node.x,
                                                gy=goal_node.y,
                                                gyaw=goal_node.theta,
                                                maxc=max_c)

            # collision check
            for i in range(len(rs_path.x)):
                path_x = rs_path.x[i]
                path_y = rs_path.y[i]
                path_theta = rs_path.yaw[i]
                path_theta = rs_curve.pi_2_pi(path_theta)
                collision = self.collision_checker.check(
                    node_x=path_x, node_y=path_y, theta=path_theta)

                if collision:
                    collision_position = [path_x, path_y, path_theta]
                    break
                else:
                    collision_position = None
            # TODO: if no collision, return current path
            if collision_position == None:
                node = goal_node
                while node.index != self.goal_node.index:
                    rs_path.x.append(node.x)
                    rs_path.y.append(node.y)
                    rs_path.yaw.append(node.theta)
                    parent_index = node.parent_index
                    for node_i in self.closed_list:
                        if node_i.index == parent_index:
                            node = node_i
                            break
                rs_path.x.append(node.x)
                rs_path.y.append(node.y)
                rs_path.yaw.append(node.theta)
                break

        return rs_path, collision, collision_position

    def finish_path(self, current_node: Node):
        node = current_node
        all_path_node = []
        while node.index != self.initial_node.index:
            all_path_node.append(node)
            parent_index = node.parent_index
            for node_i in self.closed_list:
                if node_i.index == parent_index:
                    node = node_i
                    break
        all_path_node.append(node)

        all_path = [[node.x, node.y, node.theta]]

        for i in range(len(all_path_node)):
            # k is index
            k = len(all_path_node) - 1 - i
            if k == 0:
                break
            for j in range(math.ceil(self.dt/self.ddt)):
                # discrete trajectory to store each waypoint
                # i : 0-9
                if all_path_node[k-1].forward:
                    speed = self.vehicle.max_v
                else:
                    speed = -self.vehicle.max_v

                td_j = speed * self.ddt * (j+1)
                theta_0 = all_path_node[k].theta
                steering_angle = all_path_node[k-1].steering_angle
                theta_j = theta_0 + \
                    (self.vehicle.max_v * np.tan(steering_angle)) / \
                    self.vehicle.lw * self.ddt * (j+1)
                theta_j = rs_curve.pi_2_pi(theta_j)
                x_j = all_path_node[k].x + td_j * np.cos(theta_j)
                y_j = all_path_node[k].y + td_j * np.sin(theta_j)
                all_path.append([x_j, y_j, theta_j])

        return all_path

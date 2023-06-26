'''
Author: wenqing-hnu
Date: 2022-10-20
LastEditors: wenqing-hnu
LastEditTime: 2022-11-11
FilePath: /Automated Valet Parking/path_planner/compute_h.py
Description: compute the heuristic value use dijkstra

Copyright (c) 2022 by wenqing-hnu, All Rights Reserved. 
'''


from matplotlib.pyplot import grid
import numpy as np
import queue
import math
from map.costmap import Map


class Grid:
    def __init__(self,
                 grid_id: int,
                 grid_x: np.float64,
                 grid_y: np.float64,
                 distance: int,
                 father_id: int) -> None:
        self.grid_id = grid_id
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.distance = distance
        self.father_id = father_id

    def __lt__(self, other):
        if self.distance == other.distance:
            result = self.grid_id < other.grid_id
        else:
            result = self.distance < other.distance
        return result


class Dijkstra:
    def __init__(self, map: Map) -> None:
        self.map = map
        self.final_point = (map.case.xf, map.case.yf, map.case.thetaf)
        self.open_list = queue.PriorityQueue()
        self.closedlist = []  # store Class Grid
        self.openlist_index = []
        self.find_terminate = False

    def initial_map(self, node_x, node_y):
        '''
        input: the node position
        '''
        # locate initial point grid
        # we set final node as the initial grid
        # and our goal is to find the distance(priority)
        # between the current node(terminate node) and the final node.
        # print(f"final point: ({self.final_point[0]}, {self.final_point[1]})")
        # print(f"initial_grid_x = {self.final_point[0]} - {(self.final_point[0] - self.map.boundary[0]) % self.map._discrete_x}")
        initial_grid_x = np.float64(self.final_point[0])
        initial_grid_y = np.float64(self.final_point[1])
        # initial_grid_x = self.final_point[0] - (self.final_point[0] - self.map.boundary[0]) % self.map._discrete_x
        # initial_grid_y = self.final_point[1] - (self.final_point[1] - self.map.boundary[2]) % self.map._discrete_y
        terminate_grid_x = np.float64(node_x)
        terminate_grid_y = np.float64(node_y)

        # Mike added
        # print(f"initial_grid_x: {initial_grid_x} _y: {initial_grid_y} terminate_grid_x: {terminate_grid_x} _y: {terminate_grid_y}")

        # initialize openlist and closedlist
        initial_grid_id = self.map.convert_position_to_index(initial_grid_x,
                                                             initial_grid_y)
        initial_grid = Grid(initial_grid_id, initial_grid_x, initial_grid_y,
                            distance=0, father_id=0)

        self.closedlist.append(initial_grid)
        self.terminate_grid_id = self.map.convert_position_to_index(
            terminate_grid_x, terminate_grid_y)

        return initial_grid

    def update_closedlist(self):
        # find the minimum distance in the openlist and
        # add it into the closedlist
        # print(self.open_list.empty())
        next_grid = self.open_list.get()
        if next_grid.grid_id == self.terminate_grid_id:
            self.find_terminate = True
            print("found terminate")
        
        self.closedlist.append(next_grid)

        return next_grid

    def update_openlist(self, current_grid: Grid = None):
        # compute the near grids info
        for i in range(8):
            # left upper grid
            if i == 0:
                # print(f"current grid x: {current_grid.grid_x}  current grid y: {current_grid.grid_y}")
                grid_x = current_grid.grid_x - self.map._discrete_x
                grid_y = current_grid.grid_y + self.map._discrete_y
                # check is obstacle
                if self.is_obstacle(grid_x, grid_y):
                    continue
                # check the grid whether in the map
                if grid_x >= self.map.boundary[0] and \
                   grid_y <= self.map.boundary[3]:
                    priority = current_grid.distance + 14
                    self.add_grid_to_openlist(gridx=grid_x, gridy=grid_y,
                                              priority=priority,
                                              father_id=current_grid.grid_id)

            # upper grid
            if i == 1:
                grid_x = current_grid.grid_x
                grid_y = current_grid.grid_y + self.map._discrete_y
                # check is obstacle
                if self.is_obstacle(grid_x, grid_y):
                    continue
                # check the grid whether in the map
                if grid_y <= self.map.boundary[3]:
                    priority = current_grid.distance + 10
                    self.add_grid_to_openlist(gridx=grid_x, gridy=grid_y,
                                              priority=priority,
                                              father_id=current_grid.grid_id)

            # right upper grid
            if i == 2:
                grid_x = current_grid.grid_x + self.map._discrete_x
                grid_y = current_grid.grid_y + self.map._discrete_y
                if self.is_obstacle(grid_x, grid_y):
                    continue
                # check the grid whether in the map
                if grid_x <= self.map.boundary[1] and \
                   grid_y <= self.map.boundary[3]:
                    priority = current_grid.distance + 14
                    self.add_grid_to_openlist(gridx=grid_x, gridy=grid_y,
                                              priority=priority,
                                              father_id=current_grid.grid_id)

            # left grid
            if i == 3:
                grid_x = current_grid.grid_x - self.map._discrete_x
                grid_y = current_grid.grid_y
                if self.is_obstacle(grid_x, grid_y):
                    continue
                # check the grid whether in the map
                if grid_x >= self.map.boundary[0]:
                    priority = current_grid.distance + 10
                    self.add_grid_to_openlist(gridx=grid_x, gridy=grid_y,
                                              priority=priority,
                                              father_id=current_grid.grid_id)

            # right grid
            if i == 4:
                grid_x = current_grid.grid_x + self.map._discrete_x
                grid_y = current_grid.grid_y
                if self.is_obstacle(grid_x, grid_y):
                    continue
                # check the grid whether in the map
                if grid_x <= self.map.boundary[1]:
                    priority = current_grid.distance + 10
                    self.add_grid_to_openlist(gridx=grid_x, gridy=grid_y,
                                              priority=priority,
                                              father_id=current_grid.grid_id)

            # left bottom grid
            if i == 5:
                grid_x = current_grid.grid_x - self.map._discrete_x
                grid_y = current_grid.grid_y - self.map._discrete_y
                if self.is_obstacle(grid_x, grid_y):
                    continue
                # check the grid whether in the map
                if grid_x >= self.map.boundary[0] and \
                   grid_y >= self.map.boundary[2]:
                    priority = current_grid.distance + 14
                    self.add_grid_to_openlist(gridx=grid_x, gridy=grid_y,
                                              priority=priority,
                                              father_id=current_grid.grid_id)

            # bottom grid
            if i == 6:
                grid_x = current_grid.grid_x
                grid_y = current_grid.grid_y - self.map._discrete_y
                if self.is_obstacle(grid_x, grid_y):
                    continue
                # check the grid whether in the map
                if grid_y >= self.map.boundary[2]:
                    priority = current_grid.distance + 10
                    self.add_grid_to_openlist(gridx=grid_x, gridy=grid_y,
                                              priority=priority,
                                              father_id=current_grid.grid_id)

            # right bottom grid
            if i == 7:
                grid_x = current_grid.grid_x + self.map._discrete_x
                grid_y = current_grid.grid_y - self.map._discrete_y
                if self.is_obstacle(grid_x, grid_y):
                    continue
                # check the grid whether in the map
                if grid_x <= self.map.boundary[1] and \
                   grid_y >= self.map.boundary[2]:
                    priority = current_grid.distance + 14
                    self.add_grid_to_openlist(gridx=grid_x, gridy=grid_y,
                                              priority=priority,
                                              father_id=current_grid.grid_id)

    # run this function to get the heuristic value
    def compute_path(self, node_x, node_y):
        '''
        input:  the current node in park map 
        return: the heuristic value and the closedlist
        Note:   closedlist contains the info(mainly distance) 
                about those grid has been explored
        '''
        # initial map
        self.find_terminate = False
        current_grid = self.initial_map(node_x, node_y)
        while not self.find_terminate:
            # expand grid and update openlist
            self.update_openlist(current_grid)
            # get the next grid
            current_grid = self.update_closedlist()

        return current_grid.distance, self.closedlist

    def add_grid_to_openlist(self, gridx, gridy, priority, father_id):
        index = self.map.convert_position_to_index(gridx, gridy)
        # check this grid is firstly visited or not
        # if it exits, change its value
        if self.openlist_index.count(index):
            # find the previous priority
            for i in range(self.open_list.queue.__len__()):
                if self.open_list.queue[i].grid_id == index:
                    pre_priority = self.open_list.queue[i].distance
                    if pre_priority > priority:
                        self.open_list.queue[i].distance = priority
                        self.open_list.queue[i].father_id = father_id
                    break
        else:
            grid_node = Grid(grid_id=index, grid_x=gridx,
                             grid_y=gridy, distance=priority,
                             father_id=father_id)

            self.open_list.put(grid_node)
            self.openlist_index.append(index)

    def is_obstacle(self, grid_x, grid_y):
        # check collision
        x_index = math.floor(
            (grid_x - self.map.boundary[0]) / self.map._discrete_x)
        y_index = math.floor(
            (grid_y - self.map.boundary[2]) / self.map._discrete_y)
        # print(f"{self.map.boundary[0]}, {self.map.boundary[1]}, {self.map.boundary[2]}, {self.map.boundary[3]}")
        # print(f"max x value: {self.map.boundary[1]}  max x index: {round((self.map.boundary[1] - self.map.boundary[0]) / self.map._discrete_x)}")
        # print(f"next x value: {grid_x} next x index: {x_index}")
        # print(f"_discrete_x: {self.map._discrete_x}")
        # print(f"({self.map.boundary[1]} - {self.map.boundary[0]}) / {self.map._discrete_x} = {round((self.map.boundary[1] - self.map.boundary[0]) / self.map._discrete_x)}")
        max_x_index = math.ceil(
            (self.map.boundary[1] - self.map.boundary[0]) / self.map._discrete_x)
        max_y_index = math.ceil(
            (self.map.boundary[3] - self.map.boundary[2]) / self.map._discrete_y)
        # print(max_x_index)
        if x_index == max_x_index:
            x_index = max_x_index - 1
        if y_index == max_y_index:
            y_index = max_y_index - 1
        is_obstacle = False
        if int(self.map.cost_map[x_index][y_index]) == 255:
            is_obstacle = True

        return is_obstacle

# -------------------------------------------------------------------------------
# Name:        X2PLdata.py
# Purpose:      generator of random data
#
# Author:      ifragkos
#
# Created:     17/10/2014
# Copyright:   (c) ifragkos 2014
# Licence:     <your licence>
# -------------------------------------------------------------------------------
# noinspection PyUnresolvedReferences
import random as rnd

import numpy as np

import const


const.PERIODS = 4
rnd.seed(0)  # Change this in the future so that we generate many datasets
np.random.seed(3)  # Debugged seeds: 10


class X2PLdata:
    """
    The main data class.
    """

    def __init__(self, data_file_name):
        with open(data_file_name) as data_file:
            X2PLdata._itemsRange = np.array([int(i) for i in data_file.readline().split()[:2]])
            X2PLdata._capacityRange = np.array([float(i) for i in data_file.readline().split()[:2]])
            X2PLdata._demandRange = np.array([float(i) for i in data_file.readline().split()[:2]])
            X2PLdata._bigMrange = np.array([float(i) for i in data_file.readline().split()[:2]])
            # number of points to separate
            X2PLdata.pointsToSeparate = int(data_file.readline()[:1])
            # range of production & inventory variables of points to be separated
            X2PLdata._productionRange = np.array([float(i) for i in data_file.readline().split()[:2]])
            X2PLdata._inventoryRange = np.array([float(i) for i in data_file.readline().split()[:2]])
        X2PLdata.PI = rnd.randint(X2PLdata._itemsRange[0], X2PLdata._itemsRange[1])
        X2PLdata.PI = 3  # Only for debuggig, remove later
        X2PLdata.Periods = const.PERIODS
        X2PLdata.capacity = np.array([rnd.randint(X2PLdata._capacityRange[0], X2PLdata._capacityRange[1])
                                      for _ in range(const.PERIODS)])
        X2PLdata.demand = make_random_2d_array(X2PLdata._demandRange)
        X2PLdata.bigM = make_random_2d_array(X2PLdata._bigMrange)
        X2PLdata.production_cost = np.random.randint(1, 10, (X2PLdata.Periods, X2PLdata.PI))
        X2PLdata.setup_cost = np.random.randint(10, 100, (X2PLdata.Periods, X2PLdata.PI))
        X2PLdata.setup_time = np.zeros_like(X2PLdata.setup_cost)
        X2PLdata.inventory_cost = np.random.randint(10, 100, (X2PLdata.Periods, X2PLdata.PI)) / 10
        X2PLdata.inventory_cost[0, :] *= 1000
        create_points()
        X2PLdata.pointToSeparate = X2PLdata.allPoints[0]  # Just  leave it like this for now, needs to be updated
        X2PLdata.cum_demand = np.cumsum(X2PLdata.demand, 0)


class TrigeiroData:
    """
    Reads Data from a file with Trigeiro format (not the fortran one, the other)
    """

    def __init__(self, file_name):
        with open(file_name) as data_file:
            TrigeiroData.PI, TrigeiroData.Periods = [int(x) for x in data_file.readline().split()]
            item_range, period_range = range(TrigeiroData.PI), range(TrigeiroData.Periods)
            cap = [float(x) for x in data_file.readline().split()]
            TrigeiroData.capacity = np.array(cap) if len(cap) > 1 else np.array([cap[0] for _ in period_range])
            misc_data = np.array([[float(x) for x in data_file.readline().split()] for _ in item_range])
            TrigeiroData.demand = np.array([[float(x) for x in data_file.readline().split()] for _ in period_range])
        TrigeiroData.variable_time = np.tile(misc_data[:, 0], (TrigeiroData.Periods, 1))
        TrigeiroData.inventory_cost = np.tile(misc_data[:, 1], (TrigeiroData.Periods, 1))
        TrigeiroData.inventory_cost[0, :] *= 100
        TrigeiroData.setup_time = np.tile(misc_data[:, 3], (TrigeiroData.Periods, 1))
        TrigeiroData.setup_cost = np.tile(misc_data[:, 4], (TrigeiroData.Periods, 1))
        TrigeiroData.production_cost = np.zeros(shape=(TrigeiroData.Periods, TrigeiroData.PI))
        TrigeiroData.cum_demand = np.cumsum(TrigeiroData.demand, 0)
        total_item_demand = TrigeiroData.demand.sum(0)
        TrigeiroData.bigM = np.minimum(total_item_demand - TrigeiroData.cum_demand + TrigeiroData.demand,
                                       (np.tile(TrigeiroData.capacity, (TrigeiroData.PI, 1)).transpose() -
                                        TrigeiroData.setup_time) / TrigeiroData.variable_time)

        production, setup, inventory = np.empty((TrigeiroData.Periods, TrigeiroData.PI)), \
                                       np.empty((TrigeiroData.Periods, TrigeiroData.PI)), \
                                       np.empty((TrigeiroData.Periods, TrigeiroData.PI))

        TrigeiroData.pointToSeparate = Point(TrigeiroData)


def create_points():
    """
    Creates an nplist of points that need to be separated. Each element of the array
    is a Point object. This is useful for unit testing
    """
    X2PLdata.allPoints = np.empty(X2PLdata.pointsToSeparate, dtype=object)
    for i in range(X2PLdata.pointsToSeparate):
        X2PLdata.allPoints[i] = Point(X2PLdata, random=True)


def make_random_2d_array(this_array):
    """
    Used to populate the demand and bigM arrays. Returns a (PERIODS, PI) nparray
    whose elements are integers drawn from the uniform distribution
    [thisArray[0], thisArray[1]] * Capacity[t], where t = 1, ... , PERIODS
    """

    util_arr = np.array([np.random.random_integers(low=X2PLdata.capacity[t] * this_array[0],
                                                   high=X2PLdata.capacity[t] * this_array[1]) for t in
                         range(const.PERIODS) for _ in range(X2PLdata.PI)])
    return np.reshape(util_arr, (const.PERIODS, X2PLdata.PI))


class Point():
    """
    Defines a Point object (production, setup, and inventory variables)
    Inventory is derived from demand values of first period, in a random fashion
    """

    def __init__(self, data, random=False):

        """

        :rtype : Point object
        """
        if random:
            self.production = np.multiply(data.demand,
                                          (data._productionRange[1] - data._productionRange[0]) *
                                          np.random.random_sample((const.PERIODS, data.PI))).round()
            self.setup = np.random.random_sample((const.PERIODS, data.PI)).round(decimals=1)
            self.inventory = np.multiply(data.demand[0, :],
                                         (data._inventoryRange[1] - data._inventoryRange[0]) *
                                         np.random.random_sample(data.PI)).round()
        else:
            self.production, self.setup, self.inventory = np.empty((data.Periods, data.PI)), \
                                                          np.empty((data.Periods, data.PI)), \
                                                          np.empty((data.Periods, data.PI))


def test():
    data = TrigeiroData('CL34.in')
    print 'ok'


if __name__ == '__main__':
    test()
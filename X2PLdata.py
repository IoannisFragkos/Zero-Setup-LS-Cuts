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
rnd.seed(0)          # Change this in the future so that we generate many datasets
np.random.seed(10)   # Debugged seeds: 10


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
        X2PLdata.inventory_cost = np.random.randint(10, 100, (X2PLdata.Periods, X2PLdata.PI))/10
        X2PLdata.inventory_cost[0, :] *= 1000
        create_points()
        X2PLdata.pointToSeparate = X2PLdata.allPoints[0]  # Just  leave it like this for now, needs to be updated


def create_points():
    """
    Creates an nplist of points that need to be separated. Each element of the array
    is a Point object. This is useful for unit testing
    """
    X2PLdata.allPoints = np.empty(X2PLdata.pointsToSeparate, dtype=object)
    for i in range(X2PLdata.pointsToSeparate):
        X2PLdata.allPoints[i] = Point(X2PLdata)


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

    def __init__(self, X2PLdata):
        self.production = np.multiply(X2PLdata.demand,
                                      (X2PLdata._productionRange[1] - X2PLdata._productionRange[0]) *
                                      np.random.random_sample((const.PERIODS, X2PLdata.PI))).round()
        self.setup = np.random.random_sample((const.PERIODS, X2PLdata.PI)).round(decimals=1)
        self.inventory = np.multiply(X2PLdata.demand[0, :],
                                     (X2PLdata._inventoryRange[1] - X2PLdata._inventoryRange[0]) *
                                     np.random.random_sample(X2PLdata.PI)).round()
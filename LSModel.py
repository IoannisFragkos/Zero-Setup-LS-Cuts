# -------------------------------------------------------------------------------
# Name:        LSModel.py
# Purpose:     MIP formulation of Capacitated Lot Sizing.
#
# Author:      ifragkos
#
# Created:     03/03/2015
# -------------------------------------------------------------------------------
# noinspection PyUnresolvedReferences

__author__ = 'ioannis'
from collections import namedtuple

from gurobipy import GRB, Model, quicksum, GurobiError
import numpy as np

import X2PLdata as Cdata


model = Model("CLST")
Solution = namedtuple('Solution', 'objective production setup inventory')
production_var, setup_var, inventory_var = {}, {}, {}


def make_model(my_data, print_lp=False):
    for i in range(my_data.Periods):
        for j in range(my_data.PI):
            production_var[i, j] = \
                model.addVar(vtype=GRB.CONTINUOUS, obj=my_data.production_cost[i, j],
                             name='X.{0}{1}'.format(str(i), str(j)))
            inventory_var[i, j] = \
                model.addVar(vtype=GRB.CONTINUOUS, obj=my_data.inventory_cost[i, j],
                             name='S.{0}{1}'.format(str(i), str(j)))
            setup_var[i, j] = \
                model.addVar(vtype=GRB.BINARY, obj=my_data.setup_cost[i, j], name='Y.{0}{1}'.format(str(i), str(j)))
    model.update()
    for j in range(my_data.Periods):
        model.addConstr(quicksum(production_var[j, i]
                                 for i in range(my_data.PI)) <= my_data.capacity[j], name='capacity_{0}'.format(str(j)))
        for i in range(my_data.PI):
            model.addConstr(production_var[j, i] + inventory_var[j, i] == my_data.demand[j, i] +
                            int(j + 1 <= my_data.Periods - 1) * inventory_var[min(j + 1, my_data.Periods - 1), i],
                            name='production_{0}{1}'.format(str(j), str(i)))
            model.addConstr(production_var[j, i] <= my_data.bigM[j, i] * setup_var[j, i],
                            name='bigM_{0}{1}'.format(str(j), str(i)))
    model.update()
    if print_lp:
        write_lp()


def optimize(my_data, solve_relaxed=False, print_sol=False):
    """

    :rtype : returns a named tuple of type 'Solution',
    that carries the objective function value, and the optimal solution
    """
    try:
        mdl = model.relax() if solve_relaxed else model
        mdl.setParam('OutputFlag', False)
        mdl.optimize()
        production, setup, inventory = np.empty((my_data.Periods, my_data.PI)), \
                                       np.empty((my_data.Periods, my_data.PI)), \
                                       np.empty((my_data.Periods, my_data.PI))
        for i in range(my_data.Periods):
            for j in range(my_data.PI):
                production[i, j] = mdl.getVarByName('X.{0}{1}'.format(str(i), str(j))).X
                setup[i, j] = mdl.getVarByName('Y.{0}{1}'.format(str(i), str(j))).X
                inventory[i, j] = mdl.getVarByName('S.{0}{1}'.format(str(i), str(j))).X
        # Add one extra row to inventory variable, corresponding to zero inventory at the beginning of period T+1
        inventory = np.vstack((inventory, np.zeros(my_data.PI)))
        lp_solution = Solution(mdl.objVal, production, setup, inventory)
        if print_sol:
            print_solution(data=my_data, solution=lp_solution)
        return lp_solution
    except GurobiError, e:
        print e.message


def write_lp():
    model.write("CLST.lp")


def print_solution(data, solution):
    for i in range(data.Periods):
        for j in range(data.PI):
            print 'Period: {}, Item: {}, Production: {}, Setup: {}, Inventory: {}'.format(
                i, j, solution.production[i, j], solution.setup[i, j], solution.inventory[i, j])
    print 'Objective function: {}'.format(solution.objective)


def add_esc(my_data, cover, complement, period1, period2):
    """
    :param my_data: problem data
    :param cover: set of items that belong to the cover, should be a list
    :param complement: subset of the complement of the cover
    :param period1: period in which the cover refers to
    :param period2: period in which the inventory variable refers to
    :return: nothing
    The cover, complement and period are assumed to satisfy the cover conditions, therefore these conditions are not
    checked again. However, if cover is empty then we abort the subroutine.
    """
    if cover:
        llambda = my_data.demand[period1, cover].sum() - my_data.capacity[period1]
        setup_coeff = np.maximum(my_data.demand[period1, :] - llambda, 0)
        max_demand_in_cover = my_data.demand[period1, cover].max()
        dbar = np.maximum(max_demand_in_cover, my_data.demand[period1, :])

        model.addConstr(quicksum(inventory_var[period2, i] for i in cover) -
                        quicksum(production_var[period1, i] for i in (cover + complement)) +
                        quicksum(setup_coeff[i] * (setup_var[period1, i] - 1) for i in cover) +
                        quicksum((dbar[i] - llambda) * setup_var[period1, i] for i in complement) +
                        my_data.capacity[period1] >= 0)
        model.update()
        write_lp()


def test():
    data = Cdata.X2PLdata('Random_Parameters.txt')
    make_model(data)
    solution = optimize(data, solve_relaxed=False, print_sol=True)


if __name__ == 'main':
    test()
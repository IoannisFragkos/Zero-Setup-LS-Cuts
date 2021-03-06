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
model.params.preCrush = 1
model.params.Cuts = 0
model.params.Presolve = 0
model.params.NodeLimit = 1
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
    for j in xrange(my_data.Periods):
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
    return model


def optimize(my_data, model, solve_relaxed=False, print_sol=False, callback=None, log=False):
    """

    :rtype : returns a named tuple of type 'Solution',
    that carries the objective function value, and the optimal solution
    """
    try:
        mdl = model.relax() if solve_relaxed else model
        if not log:
            mdl.setParam('OutputFlag', True)
        mdl.update()
        if callback:
            mdl.optimize(callback)
        else:
            mdl.optimize()
        lp_solution = get_lp_solution(model=mdl, data=my_data, print_sol=print_sol)
        return lp_solution
    except GurobiError, e:
        print e.message


def get_lp_solution(data, model, callback=False, print_sol=False):
    periods, PI = data.Periods, data.PI

    try:
        if callback:
            production = np.array([model.cbGetNodeRel(x) for x in model.__vars if x.VarName[0] == 'X']).reshape(periods,
                                                                                                                PI)
            setup = np.array([model.cbGetNodeRel(x) for x in model.__vars if x.VarName[0] == 'Y']).reshape(periods, PI)
            inventory = np.array([model.cbGetNodeRel(x) for x in model.__vars if x.VarName[0] == 'S']).reshape(periods,
                                                                                                               PI)
            model._objective = np.multiply(production, data.production_cost).sum() + \
                               np.multiply(setup, data.setup_cost).sum() + np.multiply(inventory,
                                                                                       data.inventory_cost).sum()
        else:
            model._production = [x for x in model.getVars() if x.VarName[0] == 'X']
            model._setup = [x for x in model.getVars() if x.VarName[0] == 'Y']
            model._inventory = [x for x in model.getVars() if x.VarName[0] == 'S']

            production = np.array([model._production[i].X for i in xrange(data.Periods * data.PI)]).reshape(periods, PI)
            setup = np.array([model._setup[i].X for i in xrange(data.Periods * data.PI)]).reshape(periods, PI)
            inventory = np.array([model._inventory[i].X for i in xrange(data.Periods * data.PI)]).reshape(periods, PI)
            model._objective = model.objVal
    except GurobiError, e:
        print e.message

    # Add one extra row to inventory variable, corresponding to zero inventory at the beginning of period T+1
    inventory = np.vstack((inventory, np.zeros(data.PI)))
    lp_solution = Solution(model._objective, production, setup, inventory)
    if print_sol:
        print_solution(data=data, solution=lp_solution)
    return lp_solution


def write_lp():
    model.write("CLST.lp")


def print_solution(data, solution):
    for i in range(data.Periods):
        for j in range(data.PI):
            print 'Period: {}, Item: {}, Production: {}, Setup: {}, Inventory: {}'.format(
                i, j, solution.production[i, j], solution.setup[i, j], solution.inventory[i, j])
    print 'Objective function: {}'.format(solution.objective)


def add_esc(my_data, cover, complement, period, period1, period2, callback=False, print_diag=False):
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
        if print_diag:
            print 'Adding cut.. Period 1: {}, Period 2: {},  ' \
                  'Cover:{}, Complement: {} Period: {}'.format(period1, period2, cover,
                                                               complement, period)
        cum_dem = my_data.cum_demand[period2 - 1, :] - (my_data.cum_demand[period1 - 1, :]
                                                        if period1 > 0 else np.zeros(shape=my_data.PI, dtype=float))
        demand = np.vstack((cum_dem, my_data.demand[period2 - 1, :]))

        llambda = demand[0, cover].sum() - my_data.capacity[period1]
        setup_coeff = np.maximum(demand[0, :] - llambda, 0)
        max_demand_in_cover = demand[0, cover].max()
        dbar = np.maximum(max_demand_in_cover, demand[0, :])

        if callback:
            model.cbCut(quicksum(inventory_var[period2, i] for i in cover) -
                        quicksum(production_var[period1, i] for i in (cover + complement)) +
                        quicksum(setup_coeff[i] * (setup_var[period1, i] - 1) for i in cover) +
                        quicksum((dbar[i] - llambda) * setup_var[period1, i] for i in complement) +
                        quicksum(dbar[i] * setup_var[period2 - 1, i] - production_var[period2 - 1, i] for i in period) +
                        my_data.capacity[period1] >= 0)

        else:
            model.addConstr(quicksum(inventory_var[period2, i] for i in cover) -
                            quicksum(production_var[period1, i] for i in (cover + complement)) +
                            quicksum(setup_coeff[i] * (setup_var[period1, i] - 1) for i in cover) +
                            quicksum((dbar[i] - llambda) * setup_var[period1, i] for i in complement) +
                            quicksum(
                                dbar[i] * setup_var[period2 - 1, i] - production_var[period2 - 1, i] for i in period) +
                            my_data.capacity[period1] >= 0,
                            name='esc_{0}{1}_{2}.{3}'.format(''.join(str(ii) for ii in cover),
                                                             '.'.join(str(jj) for jj in complement),
                                                             str(period1), str(period2)))
            model.update()
        write_lp()


def test():
    data = Cdata.X2PLdata('Random_Parameters.txt')
    make_model(data)
    solution = optimize(data, solve_relaxed=False, print_sol=True)


if __name__ == 'main':
    test()
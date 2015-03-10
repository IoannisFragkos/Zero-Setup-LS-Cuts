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
from gurobipy import GRB, Model, quicksum
import X2PLdata as Cdata
import numpy as np

model = Model("CLST")
my_data = Cdata.X2PLdata('Random_Parameters.txt')

production_var, setup_var, inventory_var = {}, {}, {}
production, setup, inventory = np.empty((my_data.Periods, my_data.PI)), \
                               np.empty((my_data.Periods, my_data.PI)), \
                               np.empty((my_data.Periods, my_data.PI))


def optimize():
    model.optimize()
    my_data.pointToSeparate.production = np.empty_like(production)
    for i in range(my_data.Periods):
        for j in range(my_data.PI):
            production[i, j] = production_var[i, j].X
            setup[i, j] = setup_var[i, j].X
            inventory[i, j] = inventory_var[i, j].X


def write_lp():
    model.write("CLST.lp")


for i in range(my_data.Periods):
    for j in range(my_data.PI):
        production_var[i, j] = \
            model.addVar(vtype=GRB.CONTINUOUS, obj=my_data.production_cost[i, j],
                         name="X." + str(i) + str(j))
        inventory_var[i, j] = \
            model.addVar(vtype=GRB.CONTINUOUS, obj=my_data.inventory_cost[i, j],
                         name="S." + str(i) + str(j))
        setup_var[i, j] = \
            model.addVar(vtype=GRB.BINARY, obj=my_data.setup_cost[i, j], name="Y." + str(i) + str(j))
model.update()
for j in range(my_data.Periods):
    model.addConstr(quicksum(production_var[j, i]
                             for i in range(my_data.PI)) <= my_data.capacity[j], name="capacity_" + str(j))
    for i in range(my_data.PI):
        model.addConstr(production_var[j, i] + inventory_var[j, i] == my_data.demand[j, i] +
                        int(j + 1 <= my_data.PI - 1) * inventory_var[min(j + 1, my_data.Periods - 1), i],
                        name="production_" + str(i) + str(j))
        model.addConstr(production_var[j, i] <= my_data.bigM[j, i] * setup_var[j, i],
                        name="bigM_" + str(i) + str(j))

model.update()
optimize()
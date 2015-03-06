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


def main():
    my_data = Cdata.X2PLdata('Random_Parameters.txt')
    lm_model = LSModel(my_data)
    lm_model.model.write("CLST.lp")
    lm_model.model.optimize()


class LSModel:
    def __init__(self, my_data):
        self.model = Model("CLST")
        self.production, self.setup, self.inventory = {}, {}, {}
        for i in range(my_data.PI):
            for j in range(my_data.Periods):
                self.production[i, j] = \
                    self.model.addVar(vtype=GRB.CONTINUOUS, obj=my_data.production_cost[i, j],
                                      name="X." + str(i) + str(j))
                self.inventory[i, j] = \
                    self.model.addVar(vtype=GRB.CONTINUOUS, obj=my_data.production_cost[i, j],
                                      name="S." + str(i) + str(j))
                self.setup[i, j] = \
                    self.model.addVar(vtype=GRB.BINARY, obj=my_data.setup_cost[i, j], name="Y." + str(i) + str(j))
        self.model.update()
        for j in range(my_data.Periods):
            self.model.addConstr(quicksum(self.production[i, j]
                                          for i in range(my_data.PI)) <= my_data.capacity[j], name="capacity_" + str(j))
            for i in range(my_data.PI):
                self.model.addConstr(self.production[i, j] + self.inventory[i, j] == my_data.demand[i, j] +
                                     int(j + 1 <= my_data.PI - 1) * self.inventory[i, min(j + 1, my_data.Periods - 1)],
                                     name="production_" + str(i) + str(j))
                self.model.addConstr(self.production[i, j] <= my_data.bigM[i, j] * self.setup[i, j],
                                     name="bigM_" + str(i) + str(j))
        self.model.update()


if __name__ == '__main__':
    main()
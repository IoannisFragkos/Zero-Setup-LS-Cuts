# -------------------------------------------------------------------------------
# Name:        MainFile.py
# Purpose:     Branch and cut using X2PL, main file.
#
# Author:      ifragkos
#
# Created:     03/03/2015
# -------------------------------------------------------------------------------
# noinspection PyUnresolvedReferences
__author__ = 'ioannis'

from sys import argv

from gurobipy import GRB

import X2PLdata as Cdata
import esc
import LSModel as ls_Model


def main(filename, gurobi=False):
    my_data = Cdata.TrigeiroData(filename)

    model = ls_Model.make_model(my_data, print_lp=True)

    if gurobi:
        ls_Model.optimize(my_data, model, solve_relaxed=False, log=True)
        return

    esc_model = esc.ExtendedSimpleCovers()

    callback_closure(mdl=model, data=my_data, esc_model=esc_model)


def callback_closure(mdl, data, esc_model):
    def add_esc_callback(model, where):
        if where == GRB.callback.MIPNODE:
            status = model.cbGet(GRB.callback.MIPNODE_STATUS)
            if status == GRB.OPTIMAL:
                lp_solution = ls_Model.get_lp_solution(data, model, callback=True)
                for period1 in xrange(data.Periods - 1):
                    data.pointToSeparate.setup = lp_solution.setup
                    data.pointToSeparate.production = lp_solution.production
                    for period2 in xrange(period1 + 2, data.Periods):
                        data.period1 = period1
                        data.period2 = period2
                        data.pointToSeparate.inventory = lp_solution.inventory[period2, :]
                        if not esc_model.is_populated:
                            esc_model.populate_model(data)
                            esc_model.is_populated = True
                        else:
                            esc_model.update_model(data)
                        cover, complement, period = esc_model.optimize_model(write_lp=False, print_sol=False)
                        ls_Model.add_esc(data, cover, complement, period, period1, period2,
                                         callback=True, print_diag=True)

    mdl.optimize(add_esc_callback)

if __name__ == '__main__':
    if len(argv) > 1:
        main(argv[1], gurobi=argv[2] == 'True')
    else:
        main('instance_12_6_10.in', False)
        # 'instance_11_6_4.in'
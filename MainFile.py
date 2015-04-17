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

from gurobipy import GRB

import X2PLdata as Cdata
import esc
import LSModel as ls_Model


def main():
    my_data = Cdata.TrigeiroData('CL34.in')
    model = ls_Model.make_model(my_data, print_lp=True)
    # root_lp = ls_Model.optimize(my_data, solve_relaxed=True, print_sol=True)

    esc_model = esc.ExtendedSimpleCovers()

    callback_closure(mdl=model, data=my_data, esc_model=esc_model)

    # my_data.pointToSeparate.production = root_lp.production
    # my_data.pointToSeparate.setup = root_lp.setup
    #
    # # period1 signifies the main period in which the cut is generated (PIR_1)
    # # period2 signifies the period of inventory. Inventory is defined at the
    # # beginning of a period, therefore we should be looking at least two periods ahead
    # for period1 in range(my_data.Periods - 1):
    # for period2 in range(period1 + 2, my_data.Periods):
    #         my_data.period1 = period1
    #         my_data.period2 = period2
    #         my_data.pointToSeparate.inventory = root_lp.inventory[period2, :]
    #         if not esc_model.is_populated:
    #             esc_model.populate_model(my_data)
    #             esc_model.is_populated = True
    #         else:
    #             esc_model.update_model(my_data)
    #         cover, complement = esc_model.optimize_model(write_lp=True, print_sol=False)
    #         ls_Model.add_esc(my_data, cover, complement, period1, period2)
    #
    # root_lp_esc_cuts = ls_Model.optimize(my_data, solve_relaxed=False, print_sol=True)


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
                        cover, complement = esc_model.optimize_model(write_lp=False, print_sol=False)
                        ls_Model.add_esc(data, cover, complement, period1, period2, callback=True, print_diag=True)

    mdl.optimize(add_esc_callback)

if __name__ == '__main__':
    main()
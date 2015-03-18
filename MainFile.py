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

import X2PLdata as Cdata
import esc
import LSModel as ls_Model


def main():
    my_data = Cdata.TrigeiroData('CL34.in')
    ls_Model.make_model(my_data, print_lp=True)
    root_lp = ls_Model.optimize(my_data, solve_relaxed=True, print_sol=False)

    my_data.pointToSeparate.production = root_lp.production
    my_data.pointToSeparate.setup = root_lp.setup

    # period1 signifies the main period in which the cut is generated (PIR_1)
    # period2 signifies the period of inventory. Inventory is defined at the
    # beginning of a period, therefore we should be looking at least two periods ahead
    for period1 in range(my_data.Periods - 1):
        for period2 in range(period1 + 2, my_data.Periods):
            my_data.period1 = period1
            my_data.period2 = period2
            my_data.pointToSeparate.inventory = root_lp.inventory[period2, :]
            esc_model = esc.ExtendedSimpleCovers(my_data)
            cover, complement = esc_model.optimize_model(write_lp=False, print_sol=False)
            ls_Model.add_esc(my_data, cover, complement, period1, period2)

    root_lp_esc_cuts = ls_Model.optimize(my_data, solve_relaxed=True, print_sol=True)

if __name__ == '__main__':
    main()
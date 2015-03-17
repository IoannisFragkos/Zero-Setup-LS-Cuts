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
    my_data = Cdata.X2PLdata('Random_Parameters.txt')
    ls_Model.make_model(my_data, print_lp=False)
    root_lp = ls_Model.optimize(my_data, solve_relaxed=True, print_sol=True)

    my_data.pointToSeparate.production = root_lp.production
    my_data.pointToSeparate.setup = root_lp.setup

    for period in range(my_data.Periods - 1):
        my_data.period = period
        my_data.pointToSeparate.inventory = root_lp.inventory[period + 2, :]
        esc_model = esc.ExtendedSimpleCovers(my_data)
        cover, complement = esc_model.optimize_model(write_lp=True, print_sol=True)
        ls_Model.add_esc(my_data, cover, complement, period, period + 1)


if __name__ == '__main__':
    main()
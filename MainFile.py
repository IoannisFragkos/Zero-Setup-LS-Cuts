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
    ls_Model.optimize()

    for period in range(my_data.Periods - 1):
        my_data.period = period
        my_data.pointToSeparate.production = ls_Model.production[:, period]
        my_data.pointToSeparate.inventory = ls_Model.inventory[:, period + 1]
        my_data.pointToSeparate.setup = ls_Model.setup[:, period]
        esc_model = esc.ExtendedSimpleCovers(my_data)
        esc_model.optimize_model()


if __name__ == '__main__':
    main()
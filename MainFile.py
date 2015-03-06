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


def main():
    my_data = Cdata.X2PLdata('Random_Parameters.txt')
    my_data.period = 0
    esc_model = esc.ExtendedSimpleCovers(my_data)
    esc_model.optimize_model()

if __name__ == '__main__':
    main()
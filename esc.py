# -------------------------------------------------------------------------------
# Name:        esc.py
# Purpose:     Extended simple cover inequalities separation MIP.
# More details to follow!
#
# Author:      ifragkos
#
# Created:     17/10/2014
# -------------------------------------------------------------------------------
# noinspection PyUnresolvedReferences
import sys
import gurobipy as grb
import X2PLdata as Cdata


def main():
    my_data = Cdata.X2PLdata('Random_Parameters.txt')
    my_data.period = 0
    esc_mip = ExtendedSimpleCovers(my_data)
    print 'Here'


class ExtendedSimpleCovers():
    """
    Holds the Extended simple covers model
    It creates only one model upon initialization. Then, it just changes the model
    data
    """
    is_initialized = False

    def __init__(self, my_data):
        if self.is_initialized:
            self.update_model(my_data)
        else:
            self.populate_model(my_data)

    def populate_model(self, my_data):
        point_to_separate = my_data.pointToSeparate
        try:
            grb_model = grb.Model("Extended Simple Covers")
            w_s = [grb_model.addVar(lb=0.0, ub=1.0, name="w_s" + str(i),
                                    obj=point_to_separate.inventory[i] - point_to_separate.production[my_data.period,i])
                   for i in range(my_data.PI)]

        except grb.GurobiError:
            print 'Error reported'

    def update_model(self, my_data):
        pass


if __name__ == '__main__':
    main()
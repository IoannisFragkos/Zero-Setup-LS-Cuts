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
import numpy as np
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
        pnt = my_data.pointToSeparate
        t = my_data.period
        cap = my_data.capacity[t]
        try:
            grb_model = grb.Model("Extended Simple Covers")
            w_s = [grb_model.addVar(vtype=grb.GRB.BINARY, name="w_s" + str(i),
                                    obj=pnt.inventory[i] - pnt.production[t,i])
                   for i in range(my_data.PI)]
            w_s = np.array(w_s)
            w_k = [grb_model.addVar(vtype=grb.GRB.BINARY, name='w_k' + str(i),
                                    obj=-pnt.production[t,i]-cap*pnt.setup[t,i])]
            w_k = np.array(w_k)
            grb_model.update()
        except grb.GurobiError:
            print 'Error reported'

    def update_model(self, my_data):
        pass


if __name__ == '__main__':
    main()
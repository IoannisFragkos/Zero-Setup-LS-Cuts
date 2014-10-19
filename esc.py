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
            w_s = add_var_array(grb_model, grb.GRB.BINARY, "w_s", pnt.inventory - pnt.production[t, :])
            w_k = add_var_array(grb_model, grb.GRB.BINARY, "w_k", -pnt.production[t, :] - cap * pnt.setup[t, :])
            q_s = add_var_array(grb_model, grb.GRB.CONTINUOUS, "q_s", pnt.setup[t, :] - 1)
            grb_model.update()
        except grb.GurobiError:
            print 'Error reported'

    def update_model(self, my_data):
        pass


def add_var_array(model, var_type, var_name, obj_val):
    """
    :param model:       gurobi model
    :param var_type:    type of variable (eg. gurobipy.GRB.BINARY)
    :param var_name:    string
    :param obj_val:     numpy array
    :return:            numpy array of the pending variable
    """
    temp_var = [model.addVar(vtype=var_type, name=var_name + str(i), obj=obj_val[i]) for i in range(obj_val.size)]
    return temp_var

if __name__ == '__main__':
    main()
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

import const
import X2PLdata as Cdata


const.EPSILON = 0.0001
PI = 0


def main():
    my_data = Cdata.X2PLdata('Random_Parameters.txt')

    my_data.period = 0
    esc_mip = ExtendedSimpleCovers(my_data)
    esc_mip.optimize_model(write_lp=True, print_sol=True)


class ExtendedSimpleCovers:
    """
    Holds the Extended simple covers model
    It creates only one model upon initialization. Then, it just changes the model
    data
    """

    def __init__(self, my_data):
        if my_data.period1 != 0 or my_data.period2 != 2:
            self.update_model(my_data)
        else:
            self.grb_model = grb.Model("Extended Simple Covers")
            self.populate_model(my_data)

    def populate_model(self, my_data):
        pnt = my_data.pointToSeparate
        t = my_data.period1
        t2 = my_data.period2
        cap = my_data.capacity[t]
        cum_dem = my_data.cum_demand[t2 - 1, :] - (my_data.cum_demand[t - 1, :] if t > 0 else 0)
        demand = np.vstack((cum_dem, my_data.demand[t2 - 1, :]))
        global PI
        PI = my_data.PI
        try:
            m = self.grb_model
            w_s = add_var_array1d(m, grb.GRB.BINARY, "w_s", pnt.inventory - pnt.production[t, :])
            w_k = add_var_array1d(m, grb.GRB.BINARY, "w_k", -pnt.production[t, :] + cap * pnt.setup[t, :])
            b_s = add_var_array1d(m, grb.GRB.BINARY, "b_s", np.zeros(PI))
            b_k = add_var_array1d(m, grb.GRB.BINARY, "b_k", np.zeros(PI))
            z_s = add_var_array1d(m, grb.GRB.BINARY, "z_s", np.zeros(PI))
            t_ks = add_var_array2d(m, grb.GRB.BINARY, "t_ks", pnt.setup[t, :], demand[0, :])
            q_s = add_var_array1d(m, grb.GRB.CONTINUOUS, "q_s", pnt.setup[t, :] - 1)
            d_s = add_var_array1d(m, grb.GRB.CONTINUOUS, "d_s", pnt.setup[t, :])
            lambda_t = m.addVar(vtype=grb.GRB.CONTINUOUS, name="lambda_t", obj=0.)
            d_bar = m.addVar(vtype=grb.GRB.CONTINUOUS, name="d_bar", obj=0.)

            objective = m.getObjective()
            objective += cap
            m.setObjective(objective, grb.GRB.MINIMIZE)
            m.update()

            max_demand = np.max(demand[0, :])
            total_demand = np.sum(demand[0, :])
            items_set = range(PI)
            # max demand excluding item i
            max_demand_arr = [np.max(np.ma.masked_equal(demand[0, :], demand[0, i])) for i in items_set]

            m.addConstr(lambda_t == grb.quicksum(demand[0][i] * w_s[i] for i in items_set) - cap, "Lambda_Definition")
            m.addConstr(lambda_t >= const.EPSILON, "Strictly_Positive_Cover")
            m.addConstr(grb.quicksum(b_s[i] for i in items_set) == 1, "sum_of_b_s")
            m.addConstr(d_bar >= lambda_t, "d_bar_lambda_t")
            for i in items_set:
                m.addConstr(w_k[i] + w_s[i] <= 1, "In_S_or_in_K_" + str(i))
                m.addConstr(w_k[i] * my_data.bigM[t, i] <= d_s[i], "big_M" + str(i))
                m.addConstr(d_bar >= demand[0, i] * w_s[i], "d_tilda_lb_" + str(i))
                m.addConstr(d_bar <= demand[0, i] * b_s[i] + max_demand_arr[i] * (1 - b_s[i]), "d_tilda_ub_" + str(i))
                m.addConstr(b_s[i] <= w_s[i], "b_s_w_s_" + str(i))
                m.addConstr(d_s[i] <= max_demand * w_k[i], "d_s_first_ub_" + str(i))
                m.addConstr(d_s[i] <= d_bar + max_demand * (1 - b_k[i]), "d_s_second_ub_" + str(i))
                m.addConstr(d_s[i] <= demand[0, i] * w_k[i] + max_demand * b_k[i], "d_s_third_ub_" + str(i))
                m.addConstr(d_s[i] >= d_bar - max_demand * (1 - w_k[i]), "d_s_first_lb_" + str(i))
                m.addConstr(d_s[i] >= demand[0, i] * w_k[i], "d_s_second_lb_" + str(i))
                m.addConstr(q_s[i] >= demand[0, i] * w_s[i] + cap -
                            grb.quicksum(demand[0, j] * w_s[j] for j in items_set), "q_s_first" + str(i))
                m.addConstr(q_s[i] <= demand[0, i] * z_s[i] + cap -
                            grb.quicksum(demand[0, j] * w_s[j] for j in items_set) +
                            (total_demand - cap) * (1 - z_s[i]), "q_s_second" + str(i))
                m.addConstr(q_s[i] <= (demand[0, i] + cap - np.min(demand[0, :])) * z_s[i], "q_s_third" + str(i))
                m.addConstr(z_s[i] <= w_s[i], "z_s_and_w_s" + str(i))
                for j in items_set:
                    m.addConstr(t_ks[j * PI + i] <= w_s[j], "1t_ij_with_w_s_{0}{1}".format(str(i), str(j)))
                    m.addConstr(t_ks[j * PI + i] <= w_k[i], "2t_ij_with_w_s_{0}{1}".format(str(i), str(j)))
                    m.addConstr(t_ks[j * PI + i] >= w_k[i] + w_s[j] - 1, "3t_ij_with_w_s_{0}{1}".format(str(i), str(j)))
            m.update()
            m.setParam('OutputFlag', False)
        except grb.GurobiError, e:
            print e.message

    def update_model(self, my_data):
        pass

    def optimize_model(self, write_lp=False, print_sol=False):
        """
        Solves the extended simple covers model and returns the cover items
        and the subset of the complement items (both in lists).
        If the cut is positive, it returns two empty lists
        """
        model = self.grb_model
        model.optimize()
        if write_lp:
            model.write("test.lp")
        status = model.status
        if status == grb.GRB.status.OPTIMAL:
            cover, complement = [], []
            if print_sol:
                for v in model.getVars():
                    print v.VarName, v.x
            if model.objVal < -const.EPSILON:
                print "adding new cut"
                for i in range(PI):
                    if model.getVarByName('w_s{}'.format(str(i))).X > 0.5:
                        cover.append(i)
                    if model.getVarByName('w_k{}'.format(str(i))).X > 0.5:
                        complement.append(i)
            return cover, complement


def add_var_array1d(model, var_type, var_name, obj_val, size=1):
    """
    :param model:       gurobi model
    :param var_type:    type of variable (eg. gurobipy.GRB.BINARY)
    :param var_name:    string
    :param obj_val:     numpy array
    :return:            1d list of the pending variable
    """
    if is_np_array(obj_val):
        temp_var = [model.addVar(vtype=var_type, name=var_name + str(i), obj=obj_val[i])
                    for i in range(obj_val.size)]
    else:
        temp_var = [model.addVar(vtype=var_type, name=var_name + str(i), obj=obj_val)
                    for i in range(size)]
    return temp_var


def is_np_array(obj):
    """
    Checks if object is numpy array
    :param obj:         any object
    :return:            boolean
    """
    return type(obj).__module__ == np.__name__


def add_var_array2d(model, var_type, var_name, obj_val1, obj_val2):
    """
    :param model:       gurobi model
    :param var_type:    type of variable (string)
    :param var_name:    name of variable (string)
    :param obj_val1:    objective function is tensor product of obj_val1 and obj_val2
    :param obj_val2:
    :return:            2d list of gurobi variables
    """
    temp_var = [model.addVar(vtype=var_type, name=var_name + str(i) + str(j), obj=obj_val1[i] * obj_val2[j])
                for i in range(obj_val1.size) for j in range(obj_val2.size)]
    return temp_var


if __name__ == '__main__':
    main()
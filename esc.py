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

    def __init__(self):
        self.grb_model = grb.Model("Extended Simple Covers")
        self.is_populated = False

    def populate_model(self, my_data):
        pnt = my_data.pointToSeparate
        t = my_data.period1
        t2 = my_data.period2
        cap = my_data.capacity[t]
        cum_dem = my_data.cum_demand[t2 - 1, :] - (my_data.cum_demand[t - 1, :]
                                                   if t > 0 else np.zeros(shape=my_data.PI, dtype=float))
        demand = np.vstack((cum_dem, my_data.demand[t2 - 1, :]))
        self.PI = my_data.PI
        PI = self.PI
        try:
            m = self.grb_model
            w_s = add_var_array1d(m, grb.GRB.BINARY, "w_s", pnt.inventory - pnt.production[t, :])
            w_k = add_var_array1d(m, grb.GRB.BINARY, "w_k", -pnt.production[t, :] + cap * pnt.setup[t, :])
            w_p = add_var_array1d(m, grb.GRB.BINARY, "w_p",
                                  demand[1, :] * pnt.setup[t2 - 1, :] - pnt.production[t2 - 1., :])
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
                m.addConstr(w_p[i] <= w_s[i], "Period_extension_" + str(i))
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

        t = my_data.period1
        t2 = my_data.period2
        cap = my_data.capacity[t]
        pnt = my_data.pointToSeparate
        PI = self.PI
        cum_dem = my_data.cum_demand[t2 - 1, :] - (my_data.cum_demand[t - 1, :]
                                                   if t > 0 else np.zeros(shape=my_data.PI, dtype=float))
        demand = np.vstack((cum_dem, my_data.demand[t2 - 1, :]))
        items_set = xrange(PI)
        max_demand = np.max(demand[0, :])
        arg_max_demand = np.argmax(demand[0, :])
        max_demand2 = np.max([demand[0, i] if i != arg_max_demand else 0 for i in items_set])
        total_demand = np.sum(demand[0, :])
        # max demand excluding item i
        max_demand_arr = np.array([max_demand if i != arg_max_demand else max_demand2 for i in items_set])

        m = self.grb_model

        objective = cap

        constraint = m.getConstrByName("Lambda_Definition")
        constraint.setAttr("rhs", -cap)

        # For each variable, loop through all constraints and update their coefficients
        for i in items_set:

            objective += m.getVarByName('w_s' + str(i)) * (pnt.inventory[i] - pnt.production[t, i])
            objective += m.getVarByName('w_k' + str(i)) * (-pnt.production[t, i] + cap * pnt.setup[t, i])
            objective += m.getVarByName('w_p' + str(i)) * (-pnt.production[t2 - 1, i] +
                                                           demand[1, i] * pnt.setup[t2 - 1, i])
            objective += m.getVarByName('q_s' + str(i)) * (pnt.setup[t, i] - 1)
            objective += m.getVarByName('d_s' + str(i)) * pnt.setup[t, i]
            for j in items_set:
                objective += m.getVarByName('t_ks' + str(i) + str(j)) * (-pnt.setup[t, i] * demand[0, i])

            m.chgCoeff(constraint, m.getVarByName('w_s' + str(i)), -demand[0][i])

            m.chgCoeff(m.getConstrByName("big_M" + str(i)), m.getVarByName("w_k" + str(i)), my_data.bigM[t, i])

            m.chgCoeff(m.getConstrByName("d_tilda_lb_" + str(i)), m.getVarByName("w_s" + str(i)), -demand[0, i])

            m.getConstrByName("d_tilda_ub_" + str(i)).setAttr("rhs", max_demand_arr[i])
            m.chgCoeff(m.getConstrByName("d_tilda_ub_" + str(i)), m.getVarByName("b_s" + str(i)),
                       -demand[0, i] + max_demand_arr[i])

            m.chgCoeff(m.getConstrByName("d_s_first_ub_" + str(i)), m.getVarByName("w_k" + str(i)), -max_demand)

            m.getConstrByName("d_s_second_ub_" + str(i)).setAttr("rhs", max_demand)
            m.chgCoeff(m.getConstrByName("d_s_second_ub_" + str(i)), m.getVarByName("b_k" + str(i)), max_demand)

            m.chgCoeff(m.getConstrByName("d_s_third_ub_" + str(i)), m.getVarByName("b_k" + str(i)), -max_demand)
            m.chgCoeff(m.getConstrByName("d_s_third_ub_" + str(i)), m.getVarByName("w_k" + str(i)), -demand[0, i])

            m.getConstrByName("d_s_first_lb_" + str(i)).setAttr("rhs", -max_demand)
            m.chgCoeff(m.getConstrByName("d_s_first_lb_" + str(i)), m.getVarByName("w_k" + str(i)), -max_demand)

            m.chgCoeff(m.getConstrByName("d_s_second_lb_" + str(i)), m.getVarByName("w_k" + str(i)), -demand[0, i])

            m.getConstrByName("q_s_first" + str(i)).setAttr("rhs", cap)
            for j in items_set:
                m.chgCoeff(m.getConstrByName("q_s_first" + str(i)), m.getVarByName("w_s" + str(j)), demand[0, j])

            m.getConstrByName("q_s_second" + str(i)).setAttr("rhs", total_demand)
            m.chgCoeff(m.getConstrByName("q_s_second" + str(i)),
                       m.getVarByName("z_s" + str(i)), total_demand - demand[0, i] - cap)
            for j in items_set:
                m.chgCoeff(m.getConstrByName("q_s_second" + str(i)), m.getVarByName("w_s" + str(j)), demand[0, j])

            m.chgCoeff(m.getConstrByName("q_s_third" + str(i)),
                       m.getVarByName("z_s" + str(i)), np.min(demand[0, :]) - cap - demand[0, i])

        m.setObjective(objective)

        m.update()

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
            cover, complement, period = [], [], []
            if print_sol:
                print 'esc objective: {}'.format(model.objVal)
                for v in model.getVars():
                    if v.x > const.EPSILON:
                        print v.VarName, v.x
            if model.objVal < -0.1:
                for i in range(self.PI):
                    if model.getVarByName('w_s{}'.format(str(i))).X > 0.5:
                        cover.append(i)
                    if model.getVarByName('w_k{}'.format(str(i))).X > 0.5:
                        complement.append(i)
                    if model.getVarByName('w_p{}'.format((str(i)))).X > 0.5:
                        period.append(i)
            return cover, complement, period
        elif model.status == grb.GRB.status.INF_OR_UNBD:
            model.computeIIS()
            model.write('test.ilp')


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
    temp_var = [model.addVar(vtype=var_type, name=var_name + str(i) + str(j), obj=-obj_val1[i] * obj_val2[j])
                for i in range(obj_val1.size) for j in range(obj_val2.size)]
    return temp_var


if __name__ == '__main__':
    main()
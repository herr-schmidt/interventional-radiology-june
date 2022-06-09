from __future__ import division
import logging
import time
import pyomo.environ as pyo
import plotly.express as px

from model import Patient


class Planner:

    def __init__(self, timeLimit, gap, solver):
        self.model = pyo.AbstractModel()
        self.modelInstance = None
        self.solver = pyo.SolverFactory(solver)
        self.MPModel = pyo.AbstractModel()
        self.MPInstance = None
        self.SPModel = pyo.AbstractModel()
        self.SPInstance = None
        self.solver = pyo.SolverFactory(solver)
        if(solver == "cplex"):
            self.solver.options['timelimit'] = timeLimit
            self.solver.options['mipgap'] = gap
            self.solver.options['emphasis'] = "mip 2"
            self.solver.options['mip'] = "strategy probe 3"
            self.solver.options['mip'] = "cuts all 2"
        if(solver == "gurobi"):
            self.solver.options['timelimit'] = timeLimit
            self.solver.options['mipgap'] = gap
            self.solver.options['mipfocus'] = 2
        if(solver == "cbc"):
            self.solver.options['seconds'] = timeLimit
            self.solver.options['ratiogap'] = gap
            self.solver.options['heuristics'] = "on"
            # self.solver.options['round'] = "on"
            # self.solver.options['feas'] = "on"
            self.solver.options['cuts'] = "on"
            self.solver.options['preprocess'] = "on"
            # self.solver.options['printingOptions'] = "normal"

    @staticmethod
    def objective_function(model):
        # N = 1/(1 + sum(model.d[i] for i in model.i))
        return sum(model.r[i] * model.x[i, k, t] for i in model.i for k in model.k for t in model.t) # + N * sum(model.d[i] * model.x[i, k, t] for i in model.i for k in model.k for t in model.t)

    # one surgery per patient, at most
    @staticmethod
    def single_surgery_rule(model, i):
        return sum(model.x[i, k, t] for k in model.k for t in model.t) <= 1

    # estimated surgery times cannot exceed operating room/surgical team time availability
    @staticmethod
    def surgery_time_rule(model, k, t):
        return sum(model.p[i] * model.x[i, k, t] for i in model.i) <= model.s[k, t]

    # each patient must be assigned to a room matching her specialty need
    @staticmethod
    def specialty_assignment_rule(model, j, k, t):
        return sum(model.x[i, k, t] for i in model.i if model.specialty[i] == j) <= model.bigM[1] * model.tau[j, k, t]

    def build_common_model(self):
        self.define_common_variables_and_params()
        self.define_common_constraints()

    def define_common_constraints(self):
        self.model.single_surgery_constraint = pyo.Constraint(
            self.model.i,
            rule=self.single_surgery_rule)
        self.model.surgery_time_constraint = pyo.Constraint(
            self.model.k,
            self.model.t,
            rule=self.surgery_time_rule)
        self.model.specialty_assignment_constraint = pyo.Constraint(
            self.model.j,
            self.model.k,
            self.model.t,
            rule=self.specialty_assignment_rule)

    def define_common_variables_and_params(self):
        self.model.I = pyo.Param(within=pyo.NonNegativeIntegers)
        self.model.J = pyo.Param(within=pyo.NonNegativeIntegers)
        self.model.K = pyo.Param(within=pyo.NonNegativeIntegers)
        self.model.T = pyo.Param(within=pyo.NonNegativeIntegers)
        self.model.M = pyo.Param(within=pyo.NonNegativeIntegers)

        self.model.i = pyo.RangeSet(1, self.model.I)
        self.model.j = pyo.RangeSet(1, self.model.J)
        self.model.k = pyo.RangeSet(1, self.model.K)
        self.model.t = pyo.RangeSet(1, self.model.T)
        self.model.bigMRangeSet = pyo.RangeSet(1, self.model.M)

        self.model.x = pyo.Var(self.model.i,
                               self.model.k,
                               self.model.t,
                               domain=pyo.Binary)

        self.model.p = pyo.Param(self.model.i)
        # self.model.m = pyo.Param(self.model.i)
        # self.model.l = pyo.Param(self.model.i)
        # self.model.L = pyo.Param(self.model.i)
        self.model.r = pyo.Param(self.model.i)
        self.model.d = pyo.Param(self.model.i)
        self.model.s = pyo.Param(self.model.k, self.model.t)
        # self.model.a = pyo.Param(self.model.i)
        self.model.c = pyo.Param(self.model.i)
        self.model.u = pyo.Param(self.model.i, self.model.i)
        self.model.tau = pyo.Param(self.model.j, self.model.k, self.model.t)
        self.model.specialty = pyo.Param(self.model.i)
        self.model.precedence = pyo.Param(self.model.i)
        self.model.bigM = pyo.Param(self.model.bigMRangeSet)

    def define_gamma_variables(self):
        self.model.gamma = pyo.Var(self.model.i, domain=pyo.NonNegativeReals)

    def define_objective(self):
        self.model.objective = pyo.Objective(
            rule=self.objective_function,
            sense=pyo.maximize)

    def create_model_instance(self, data):
        print("Creating model instance...")
        t = time.time()
        self.modelInstance = self.model.create_instance(data)
        elapsed = (time.time() - t)
        print("Model instance created in " + str(round(elapsed, 2)) + "s")
        logging.basicConfig(filename='times.log', encoding='utf-8', level=logging.INFO)
        logging.info("Model instance created in " + str(round(elapsed, 2)) + "s")

    def common_extract_solution(self, modelInstance):
        dict = {}
        for k in modelInstance.k:
            for t in modelInstance.t:
                patients = []
                for i in modelInstance.i:
                    if(round(modelInstance.x[i, k, t].value) == 1):
                        p = modelInstance.p[i]
                        c = modelInstance.c[i]
                        # a = modelInstance.a[i]
                        order = round(modelInstance.gamma[i].value)
                        specialty = modelInstance.specialty[i]
                        priority = modelInstance.r[i]
                        precedence = modelInstance.precedence[i]
                        patients.append(
                            Patient(i, priority, k, specialty, t, p, c, precedence, None, None, order))
                patients.sort(key=lambda x: x.order)
                dict[(k, t)] = patients
        return dict

    def common_print_solution(self, modelInstance):
        solution = self.common_extract_solution(modelInstance)
        operatedPatients = 0
        for t in modelInstance.t:
            for k in modelInstance.k:
                print("Day: " + str(t) + "; Operating Room: S" + str(k) + "\n")
                for patient in solution[(k, t)]:
                    print(patient)
                    operatedPatients += 1
                print("\n")
        print("Total number of operated patients: " + str(operatedPatients))


class StartingMinutePlanner(Planner):

    # ensure gamma plus operation time does not exceed end of day
    @staticmethod
    def end_of_day_rule(model, i, k, t):
        if(model.find_component('xParam') and model.xParam[i, k, t] == 0):
            return pyo.Constraint.Skip
        return model.gamma[i] + model.p[i] <= model.s[k, t]

    # ensure that patient i1 terminates operation before i2, if y_12kt = 1
    @staticmethod
    def time_ordering_precedence_rule(model, i1, i2, k, t):
        if(i1 == i2 or (model.find_component('xParam') and model.xParam[i1, k, t] + model.xParam[i2, k, t] < 2)):
            return pyo.Constraint.Skip
        return model.gamma[i1] + model.p[i1] <= model.gamma[i2] + model.bigM[5] * (3 - model.x[i1, k, t] - model.x[i2, k, t] - model.y[i1, i2, k, t])

    @staticmethod
    def start_time_ordering_priority_rule(model, i1, i2, k, t):
        if(i1 == i2 or model.u[i1, i2] == 0 or (model.find_component('xParam') and model.xParam[i1, k, t] + model.xParam[i2, k, t] < 2)):
            return pyo.Constraint.Skip
        return model.gamma[i1] * model.u[i1, i2] <= model.gamma[i2] * (1 - model.u[i2, i1]) + model.bigM[2] * (2 - model.x[i1, k, t] - model.x[i2, k, t])

    # either i1 comes before i2 in (k, t) or i2 comes before i1 in (k, t)
    @staticmethod
    def exclusive_precedence_rule(model, i1, i2, k, t):
        if(i1 >= i2 or (model.find_component('xParam') and model.xParam[i1, k, t] + model.xParam[i2, k, t] < 2)
        or(model.specialty[i1] != model.specialty[i2])):
            return pyo.Constraint.Skip
        return model.y[i1, i2, k, t] + model.y[i2, i1, k, t] == 1

    def define_y_variables(self):
        self.model.y = pyo.Var(self.model.i,
                               self.model.i,
                               self.model.k,
                               self.model.t,
                               domain=pyo.Binary)

    def define_end_of_day_constraint(self):
        self.model.end_of_day_constraint = pyo.Constraint(
            self.model.i,
            self.model.k,
            self.model.t,
            rule=self.end_of_day_rule)

    def define_priority_constraint(self):
        self.model.priority_constraint = pyo.Constraint(
            self.model.i,
            self.model.i,
            self.model.k,
            self.model.t,
            rule=self.start_time_ordering_priority_rule)

    def define_precedence_constraint(self):
        self.model.precedence_constraint = pyo.Constraint(
            self.model.i,
            self.model.i,
            self.model.k,
            self.model.t,
            rule=self.time_ordering_precedence_rule)

    def define_exclusive_precedence_constraint(self):
        self.model.exclusive_precedence_constraint = pyo.Constraint(
            self.model.i,
            self.model.i,
            self.model.k,
            self.model.t,
            rule=self.exclusive_precedence_rule)

    def fix_y_variables(self, modelInstance):
        print("Fixing y variables...")
        fixed = 0
        for k in modelInstance.k:
            for t in modelInstance.t:
                for i1 in range(2, self.modelInstance.I + 1):
                    for i2 in range(1, i1):
                        if(modelInstance.u[i1, i2] == 1):
                            modelInstance.y[i1, i2, k, t].fix(1)
                            modelInstance.y[i2, i1, k, t].fix(0)
                            fixed += 2
        print(str(fixed) + " y variables fixed.")


class SinglePhaseStartingMinutePlanner(StartingMinutePlanner):

    def __init__(self, timeLimit, gap, solver):
        super().__init__(timeLimit, gap, solver)
        self.define_model()

    def define_model(self):
        self.build_common_model()
        self.define_variables_and_params()
        self.define_constraints()
        self.define_objective()

    def define_variables_and_params(self):
        self.define_y_variables()
        self.define_gamma_variables()

    def define_constraints(self):
        self.define_end_of_day_constraint()
        self.define_priority_constraint()
        self.define_precedence_constraint()
        self.define_exclusive_precedence_constraint()

    def solve_model(self, data):
        self.create_model_instance(data)
        self.fix_y_variables(self.modelInstance)
        print("Solving model instance...")
        self.model.results = self.solver.solve(self.modelInstance, tee=True)
        print("\nModel instance solved.")
        print(self.model.results)

    def extract_solution(self):
        return super().common_extract_solution(self.modelInstance)

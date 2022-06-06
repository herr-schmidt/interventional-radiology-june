import logging
import sys
import time
from data_maker import DataDescriptor, DataMaker, TruncatedNormalParameters
from planners import SinglePhaseStartingMinutePlanner
from utils import SolutionVisualizer
if __name__ == '__main__':

    solvers = ["cplex"]
    size = [60]
    covid = [0.5]
    anesthesia = [0.5]
    anesthetists = [1]

    logging.basicConfig(filename='times.log', encoding='utf-8', level=logging.INFO)
    logging.info("Solver\tSize\tCovid\tAnesthesia\tAnesthetists\tMP_building_time\tSP_building_time\tTotal_run_time\tMP_Solver_time\tSP_Solver_time\tStatus_OK\tMP_Objective_Function_Value\tSP_Objective_Function_Value\tMP_Upper_Bound\tMP_Time_Limit_Hit\tSP_Time_Limit_Hit\tObjective_Function_LB")

    for solver in solvers:
        for s in size:
            for c in covid:
                for a in anesthesia:
                    for at in anesthetists:
                        
                        planner = SinglePhaseStartingMinutePlanner(timeLimit=300, gap = 0.005, solver=solver)

                        dataDescriptor = DataDescriptor()

                        dataDescriptor.patients = s
                        dataDescriptor.days = 5
                        dataDescriptor.anesthetists = at
                        dataDescriptor.covidFrequence = c
                        dataDescriptor.anesthesiaFrequence = a
                        dataDescriptor.specialtyBalance = 0.17
                        dataDescriptor.operatingDayDuration = 270
                        dataDescriptor.anesthesiaTime = 270
                        dataDescriptor.operatingTimeDistribution = TruncatedNormalParameters(low=30,
                                                                                                high=120,
                                                                                                mean=60,
                                                                                                stdDev=20)
                        dataDescriptor.priorityDistribution = TruncatedNormalParameters(low=1,
                                                                                        high=120,
                                                                                        mean=60,
                                                                                        stdDev=10)
                        dataMaker = DataMaker(seed=52876)
                        dataContainer = dataMaker.create_data_container(dataDescriptor)
                        dataDictionary = dataMaker.create_data_dictionary(
                            dataContainer, dataDescriptor)
                        print("Data description:\n")
                        print(dataDescriptor)
                        t = time.time()
                        # print("\nPatients to be operated:\n")
                        dataMaker.print_data(dataDictionary)
                        runInfo = planner.solve_model(dataDictionary)
                        elapsed = (time.time() - t)

                        solution = planner.extract_solution()

                        sv = SolutionVisualizer()
                        sv.print_solution(solution)
                        sv.plot_graph(solution)

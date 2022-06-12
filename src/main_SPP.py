import logging
import sys
import time
from data_maker import DataDescriptor, DataMaker, TruncatedNormalParameters
from planners import SinglePhaseStartingMinutePlanner
from utils import SolutionVisualizer
if __name__ == '__main__':

    solvers = ["cplex"]
    size = [60, 120]
    covid = [0.0, 0.2, 0.5, 0.8, 1.0]

    runDataLogger = logging.Logger("runDataLogger")
    runDataLogger.setLevel(logging.INFO)
    runDataFileHandler = logging.FileHandler("results.log")
    runDataFileHandler.setLevel(logging.INFO)
    runDataLogger.addHandler(runDataFileHandler)
    runDataLogger.info("Test_id\tSolver\tPatients\tCovid_frequency\tModel_building_time\tSolving_time\tOverall_time\tStatus_OK\tObjective_Function_Value\tTime_Limit_Hit\tGap\tSelected_patients\tSelected_patients_partitioning_by_precedence")

    id = 1
    for solver in solvers:
        for s in size:
            for c in covid:
                solutionLogger = logging.Logger("solutionLogger")
                solutionLogger.setLevel(logging.INFO)
                solutionFileHandler = logging.FileHandler("T_" + str(id) + ".log")
                solutionFileHandler.setLevel(logging.INFO)
                solutionLogger.addHandler(solutionFileHandler)


                planner = SinglePhaseStartingMinutePlanner(timeLimit=300, gap = None, solver=solver)

                dataDescriptor = DataDescriptor()

                dataDescriptor.patients = s
                dataDescriptor.days = 5
                dataDescriptor.anesthetists = "N/A"
                dataDescriptor.covidFrequence = c
                dataDescriptor.anesthesiaFrequence = "N/A"
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
                dataDictionary = dataMaker.create_data_dictionary(dataContainer, dataDescriptor)

                solutionLogger.info("Overall patients:\n")
                solutionLogger.info(dataMaker.data_as_string(dataDictionary))
                t = time.time()
                runInfo = planner.solve_model(dataDictionary)
                elapsed = (time.time() - t)

                solution = planner.extract_solution()
                sv = SolutionVisualizer()
                # sv.print_solution(solution)
                # sv.plot_graph(solution)

                solutionLogger.info("\n" + sv.solution_as_string(solution))


                runDataLogger.info("T_" + str(id) + "\t"
                                + solver + "\t"
                                + str(s) + "\t"
                                + str(c) + "\t"
                                + str(runInfo["Model_building_time"]) + "\t"
                                + str(runInfo["Solving_time"]) + "\t"
                                + str(round(elapsed, 2)) + "\t"
                                + str(runInfo["Status_OK"]) + "\t"
                                + str(runInfo["Objective_Function_Value"]) + "\t"
                                + str(runInfo["Time_Limit_Hit"]) + "\t"
                                + str(runInfo["Gap"]) + "\t"
                                + str(sv.count_operated_patients(solution)) + "\t"
                                + str(sv.compute_solution_partitioning_by_precedence(solution))
                )

                id += 1

                        


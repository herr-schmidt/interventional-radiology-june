import plotly.express as px
import pandas as pd
import datetime

from pyparsing import PrecededBy

class SolutionVisualizer:

    def __init__(self):
        pass

    def compute_solution_value(self, solution):
        KT = max(solution.keys())
        K = KT[0]
        T = KT[1]

        value = 0
        for t in range(1, T + 1):
            for k in range(1, K + 1):
                for patient in solution[(k, t)]:
                    value = value + patient.priority
        return value

    def print_solution(self, solution):
        if(solution is None):
            print("No solution was found!")
            return

        KT = max(solution.keys())
        K = KT[0]
        T = KT[1]

        print("Operated patients, for each day and for each room:\n")

        operatedPatients = 0
        for t in range(1, T + 1):
            for k in range(1, K + 1):
                print("Day: " + str(t) + "; Operating Room: S" + str(k))
                if(len(solution[(k, t)]) == 0):
                    print("---")
                for patient in solution[(k, t)]:
                    print(patient)
                    operatedPatients += 1
                print("\n")
        print("Total number of operated patients: " + str(operatedPatients))

    def plot_graph(self, solution):
        if(solution is None):
            print("No solution exists to be plotted!")
            return

        KT = max(solution.keys())
        K = KT[0]
        T = KT[1]

        dataFrames = []
        dff = pd.DataFrame([])
        for t in range(1, T + 1):
            df = pd.DataFrame([])
            for k in range(1, K + 1):
                patients = solution[(k, t)]
                for idx in range(0, len(patients)):
                    patient = patients[idx]
                    start = datetime.datetime(1970, 1, t, 8, 0, 0) + datetime.timedelta(minutes=round(patient.order))
                    finish = start + datetime.timedelta(minutes=round(patient.operatingTime))
                    room = "S" + str(k)
                    covid = "Y" if patient.covid == 1 else "N"
                    precedence = patient.precedence
                    if(precedence == 1):
                        precedence = "PO"
                    elif(precedence == 2):
                        precedence = "PR"
                    elif(precedence == 3):
                        precedence = "SO"
                    elif(precedence == 4):
                        precedence = "SR"
                    elif(precedence == 5):
                        precedence = "CO"
                    elif(precedence == 6):
                        precedence = "CR"
                    anesthesia = "Y" if patient.anesthesia == 1 else "N"
                    anesthetist = "A" + str(patient.anesthetist) if patient.anesthetist != 0 else ""
                    dataFrameToAdd = pd.DataFrame([dict(Start=start, Finish=finish, Room=room, Covid=covid, Precedence=precedence, Anesthesia=anesthesia, Anesthetist=anesthetist)])
                    df = pd.concat([df, dataFrameToAdd])
            dataFrames.append(df)
            dff = pd.concat([df, dff])

        color_discrete_map = {'PO': '#4191fa', 'PR': '#57d2f7', 'SO': '#44db71', 'SR': '#e0e058', 'CO': '#f5844c', 'CR': '#f54c4c'}
        fig = px.timeline(dff,
                          x_start="Start",
                          x_end="Finish",
                          y="Room",
                          color="Precedence",
                          text="Anesthetist",
                          labels={"Start": "Surgery start", "Finish": "Surgery end", "Room": "Operating room",
                                  "Covid": "Covid patient", "Precedence": "Surgery Type and Delay", "Anesthesia": "Need for anesthesia", "Anesthetist": "Anesthetist"},
                          hover_data=["Anesthesia", "Anesthetist", "Precedence", "Covid"],
                          color_discrete_map=color_discrete_map,
                          )

        fig.update_xaxes(
        rangebreaks=[
        dict(bounds=['1970-01-01 12:30:00','1970-01-02 08:00:00']),
        dict(bounds=['1970-01-02 12:30:00','1970-01-03 08:00:00']),
        dict(bounds=['1970-01-03 12:30:00','1970-01-04 08:00:00']),
        dict(bounds=['1970-01-04 12:30:00','1970-01-05 08:00:00'])
        ]
        )

        fig.add_vline(x='1970-01-01 08:00:00', line_width=1, line_dash="solid", line_color="black")
        fig.add_vline(x='1970-01-02 08:00:00', line_width=1, line_dash="solid", line_color="black")
        fig.add_vline(x='1970-01-03 08:00:00', line_width=1, line_dash="solid", line_color="black")
        fig.add_vline(x='1970-01-04 08:00:00', line_width=1, line_dash="solid", line_color="black")
        fig.add_vline(x='1970-01-05 08:00:00', line_width=1, line_dash="solid", line_color="black")
        fig.add_vline(x='1970-01-05 12:30:00', line_width=1, line_dash="solid", line_color="black")

        fig.update_layout(xaxis=dict(title='Timetable', tickformat='%H:%M:%S',))
        fig.show()
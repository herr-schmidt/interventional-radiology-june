from enum import Enum
import math
from scipy.stats import truncnorm
from scipy.stats import binom
from scipy.stats import uniform
import numpy as np
from tenacity import retry_unless_exception_type

from model import Patient


class TruncatedNormalParameters:
    def __init__(self, low, high, mean, stdDev):
        self.low = low
        self.high = high
        self.mean = mean
        self.stdDev = stdDev


class DataDescriptor:
    """Used to define properties of the sample to be generated."""

    def __init__(self):
        self._patients = None
        self._specialties = 2
        self._operatingRooms = 4
        self._days = None
        self._anesthetists = None
        self._covidFrequence = None
        self._anesthesiaFrequence = None
        self._specialtyBalance = None
        self._operatingDayDuration = None
        self._anesthesiaTime = None
        self._operatingTimeDistribution = None
        self._priorityDistribution = None

    @property
    def patients(self):
        """Get number of patients."""
        return self._patients

    @patients.setter
    def patients(self, value):
        self._patients = value

    @property
    def specialties(self):
        """Get number of specialties."""
        return self._specialties

    @property
    def operatingRooms(self):
        """Get number of operating rooms."""
        return self._operatingRooms

    @property
    def days(self):
        """Get number of days in the planning horizon."""
        return self._days

    @days.setter
    def days(self, value):
        self._days = value

    @property
    def anesthetists(self):
        """Get number of anesthetists."""
        return self._anesthetists

    @anesthetists.setter
    def anesthetists(self, value):
        self._anesthetists = value

    @property
    def covidFrequence(self):
        """Get Covid infection frequency."""
        return self._covidFrequence

    @covidFrequence.setter
    def covidFrequence(self, value):
        self._covidFrequence = value

    @property
    def anesthesiaFrequence(self):
        """Get anesthesia need frequency."""
        return self._anesthesiaFrequence

    @anesthesiaFrequence.setter
    def anesthesiaFrequence(self, value):
        self._anesthesiaFrequence = value

    @property
    def specialtyBalance(self):
        """Get specialty balance."""
        return self._specialtyBalance

    @specialtyBalance.setter
    def specialtyBalance(self, value):
        self._specialtyBalance = value

    @property
    def operatingDayDuration(self):
        """Get operating day duration."""
        return self._operatingDayDuration

    @operatingDayDuration.setter
    def operatingDayDuration(self, value):
        self._operatingDayDuration = value

    @property
    def anesthesiaTime(self):
        """Get anesthesia time at disposal for each anesthetist."""
        return self._anesthesiaTime

    @anesthesiaTime.setter
    def anesthesiaTime(self, value):
        self._anesthesiaTime = value

    @property
    def operatingTimeDistribution(self):
        """Get parameters of the Truncated Normal Distribution for generating operating times."""
        return self._operatingTimeDistribution

    @operatingTimeDistribution.setter
    def operatingTimeDistribution(self, value):
        self._operatingTimeDistribution = value

    @property
    def priorityDistribution(self):
        """Get parameters of the Truncated Normal Distribution for generating priorities."""
        return self._priorityDistribution

    @priorityDistribution.setter
    def priorityDistribution(self, value):
        self._priorityDistribution = value

    def initialize(self, patients, days, anesthetists, covidFrequence, anesthesiaFrequence, specialtyBalance, operatingTimeDistribution, priorityDistribution):
        self.patients = patients
        self.days = days
        self.anesthetists = anesthetists
        self.covidFrequence = covidFrequence
        self.anesthesiaFrequence = anesthesiaFrequence
        self.specialtyBalance = specialtyBalance
        self.operatingTimeDistribution = operatingTimeDistribution
        self.priorityDistribution = priorityDistribution

    def __str__(self):
        return f'Patients:{self.patients:17}\nDays:{self.days:21}\nAnesthetists:{self.anesthetists:13}\nCovid frequence:{self.covidFrequence:10}\nAnesthesia frequence:{self.anesthesiaFrequence:5}\nSpecialty balance:{self.specialtyBalance:8}\n\
Distributions for operating times and priorities are Truncated Normal Distributions with parameters:\n\
\tOperating times:\n\
\t\tLow:{self.operatingTimeDistribution.low:20}\n\
\t\tHigh:{self.operatingTimeDistribution.high:19}\n\
\t\tMean:{self.operatingTimeDistribution.mean:19}\n\
\t\tStandard deviation:{self.operatingTimeDistribution.stdDev:5}\n\
\tPriorities:\n\
\t\tLow:{self.priorityDistribution.low:20}\n\
\t\tHigh:{self.priorityDistribution.high:19}\n\
\t\tMean:{self.priorityDistribution.mean:19}\n\
\t\tStandard deviation:{self.priorityDistribution.stdDev:5}'

class DataContainer:
    def __init__(self, operatingRoomTimes, anesthetistsTimes, operatingTimes, surgeriyIds, priorities, anesthesiaFlags, covidFlags, specialties):
        self.operatingRoomTimes = operatingRoomTimes
        self.anesthetistsTimes = anesthetistsTimes
        self.operatingTimes = self.sample_list_to_dict(operatingTimes)
        self.surgeriyIds = self.sample_list_to_dict(surgeriyIds)
        self.priorities = self.sample_list_to_dict(priorities)
        self.anesthesiaFlags = self.sample_list_to_dict(anesthesiaFlags)
        self.covidFlags = self.sample_list_to_dict(covidFlags)
        self.specialties = self.sample_list_to_dict(specialties)
        self.ids = self.sample_list_to_dict([i for i in range(1, len(operatingTimes) + 1)])

    def asList(self, sampleDictionary):
        sampleAsList = []
        for key, value in sampleDictionary.items():
            sampleAsList.append(value)
        return sampleAsList

    def sample_list_to_dict(self, sample):
        dict = {}
        idx = 1
        for s in sample:
            dict[(str(idx))] = s
            idx += 1
        return dict

class SurgeryType(Enum):
    CLEAN = 1
    DIRTY = 2
    COVID = 3

class DataMaker:
    def __init__(self, seed):
        np.random.seed(seed=seed)
        # 1 if surgery is dirty; 0 else
        self.dirtySurgeryMapping = {
            "100000000000000000000": 1,
            "010000000000000000000": 0,
            "001000000000000000000": 0,
            "000100000000000000000": 1,
            "000010000000000000000": 0,
            "000001000100000000000": 1,
            "000001010000000000000": 1,
            "000000100000000000000": 1,
            "000000100010000000000": 1,
            "000000000000001000000": 1,
            "100000100000000000000": 1,
            "000000001000000000000": 1,
            "000001100000000000000": 1,
            "000000000000000100000": 1,
            "000100100000000000000": 1,
            "100001000000000001100": 1,
            "100001100000000000000": 1,
            "000000101000000000000": 1,
            "000000000000001000010": 1,
            "000001100100000100000": 1,
            "000001000000000100000": 1,
            "000000000010000000000": 1,
            "000000000001100000000": 0,
            "000000010000000010000": 1,
            "000000000000000000101": 0,
            "100000101000000000000": 1,
            "000000000001110000000": 0,
            "000000000000000000100": 0
        }
        self.surgeryFrequencyMapping = {
            "000000100000000000000" : 0.2571428571,
            "000100000000000000000" : 0.1047619048,
            "000000000001110000000" : 0.07619047619,
            "000000000000000100000" : 0.07619047619,
            "100000000000000000000" : 0.06666666667,
            "001000000000000000000" : 0.04761904762,
            "100000100000000000000" : 0.0380952381,
            "000000001000000000000" : 0.0380952381,
            "010000000000000000000" : 0.02857142857,
            "000000000000001000000" : 0.02857142857,
            "000000000010000000000" : 0.02857142857,
            "000001010000000000000" : 0.01904761905,
            "000000100010000000000" : 0.01904761905,
            "000100100000000000000" : 0.01904761905,
            "100001100000000000000" : 0.01904761905,
            "000001000000000100000" : 0.01904761905,
            "000010000000000000000" : 0.009523809524,
            "000001000100000000000" : 0.009523809524,
            "000001100000000000000" : 0.009523809524,
            "100001000000000001100" : 0.009523809524,
            "000000101000000000000" : 0.009523809524,
            "000000000000001000010" : 0.009523809524,
            "000001100100000100000" : 0.009523809524,
            "000000000001100000000" : 0.009523809524,
            "000000010000000010000" : 0.009523809524,
            "000000000000000000101" : 0.009523809524,
            "100000101000000000000" : 0.009523809524,
            "000000000000000000100" : 0.009523809524
        }
        self.surgeryRoomOccupancyMapping = {
            "100000000000000000000": 50,
            "010000000000000000000": 30,
            "001000000000000000000": 90,
            "000100000000000000000": 30,
            "000010000000000000000": 60,
            "000001000100000000000": 80,
            "000001010000000000000": 80,
            "000000100000000000000": 50,
            "000000100010000000000": 65,
            "000000000000001000000": 50,
            "100000100000000000000": 70,
            "000000001000000000000": 50,
            "000001100000000000000": 70,
            "000000000000000100000": 60,
            "000100100000000000000": 65,
            "100001000000000001100": 160,
            "100001100000000000000": 90,
            "000000101000000000000": 70,
            "000000000000001000010": 65,
            "000001100100000100000": 130,
            "000001000000000100000": 80,
            "000000000010000000000": 40,
            "000000000001100000000": 90,
            "000000010000000010000": 90,
            "000000000000000000101": 120,
            "100000101000000000000": 90,
            "000000000001110000000": 180,
            "000000000000000000100": 90
        }
        self.delayFrequencyByOperation = {
            "000000100000000000000": 0.7407407407,
            "000100000000000000000": 0.4545454545,
            "000000000001110000000": 0.0,
            "000000000000000100000": 1.0,
            "100000000000000000000": 0.5714285714,
            "001000000000000000000": 1.0,
            "010000000000000000000": 0.75,
            "100000100000000000000": 0.25,
            "000000001000000000000": 1.0,
            "000000000000001000000": 1.0,
            "000000000010000000000": 1.0,
            # from now on, statistic was too uncertain (< 3 patients per operation): flip a coin
            "000001010000000000000": 0.5,
            "000000100010000000000": 0.5,
            "000100100000000000000": 0.5,
            "100001100000000000000": 0.5,
            "000001000000000100000": 0.5,
            "000010000000000000000": 0.5,
            "000001000100000000000": 0.5,
            "000001100000000000000": 0.5,
            "100001000000000001100": 0.5,
            "000000101000000000000": 0.5,
            "000000000000001000010": 0.5,
            "000001100100000100000": 0.5,
            "000000000001100000000": 0.5,
            "000000010000000010000": 0.5,
            "000000000000000000101": 0.5,
            "100000101000000000000": 0.5,
            "000000000000000000100": 0.5
        }

    def generate_truncnorm_sample(self, patients, lower, upper, mean, stdDev):
        a = (lower - mean) / stdDev
        b = (upper - mean) / stdDev
        truncatedNormal = truncnorm(a, b, loc=mean, scale=stdDev)
        sample = truncatedNormal.rvs(patients)
        return sample

    def generate_binomial_sample(self, patients, p, isSpecialty):
        sample = binom.rvs(1, p, size=patients)
        if(isSpecialty):
            sample = sample + 1
        return sample

    def create_dictionary_entry(self, sample, isTime):
        dict = {}
        for i in range(0, len(sample)):
            if(isTime):
                dict[(i + 1)] = int(sample[i])
            else:
                dict[(i + 1)] = int(sample[i])
        return dict

    def create_room_timetable(self, K, T, operatingDayDuration):
        dict = {}
        for k in range(0, K):
            for t in range(0, T):
                dict[(k + 1, t + 1)] = operatingDayDuration
        return dict

    def create_anestethists_timetable(self, A, T, anesthesiaTime):
        dict = {}
        for a in range(0, A):
            for t in range(0, T):
                dict[(a + 1, t + 1)] = anesthesiaTime
        return dict

    def create_patient_specialty_table(self, I, J, specialtyLabels):
        dict = {}
        for i in range(0, I):
            for j in range(0, J):
                if(specialtyLabels[(i + 1)] == j + 1):
                    dict[(i + 1, j + 1)] = 1
                else:
                    dict[(i + 1, j + 1)] = 0
        return dict

    def create_room_specialty_assignment(self, J, K, T):
        dict = {}
        for j in range(0, J):
            for k in range(0, K):
                for t in range(0, T):
                    if((j + 1 == 1 and (k + 1 == 1 or k + 1 == 2)) or (j + 1 == 2 and (k + 1 == 3 or k + 1 == 4))):
                        dict[(j + 1, k + 1, t + 1)] = 1
                    else:
                        dict[(j + 1, k + 1, t + 1)] = 0
        return dict

    def create_precedence(self, precedences):
        dict = {}
        for i1 in range(1, len(precedences) + 1):
            for i2 in range(1, len(precedences) + 1):
                dict[(i1, i2)] = 0
                dict[(i2, i1)] = 0
                if(i1 == i2):
                    continue
                if(precedences[i1 - 1] < precedences[i2 - 1]):
                    dict[(i1, i2)] = 1
                    continue
                if(precedences[i2 - 1] < precedences[i1 - 1]):
                    dict[(i2, i1)] = 1
                    continue
        return dict

    def generate_data(self, dataDescriptor: DataDescriptor):
        dataContainer = self.create_data_container(dataDescriptor)
        return self.create_data_dictionary(dataContainer, dataDescriptor)
        
    def create_data_container(self, dataDescriptor: DataDescriptor) -> DataContainer:
        operatingRoomTimes = self.create_room_timetable(dataDescriptor.operatingRooms,
                                                        dataDescriptor.days,
                                                        dataDescriptor.operatingDayDuration)
        anesthetistsTimes = self.create_anestethists_timetable(dataDescriptor.anesthetists,
                                                               dataDescriptor.days,
                                                               dataDescriptor.anesthesiaTime)
        operatingTimesAndSurgeryIds = self.draw_operating_times_and_surgery_ids(dataDescriptor.patients)
        operatingTimes = operatingTimesAndSurgeryIds[0]
        surgeriyIds = operatingTimesAndSurgeryIds[1]
        priorities = self.generate_truncnorm_sample(dataDescriptor.patients,
                                                    dataDescriptor.priorityDistribution.low,
                                                    dataDescriptor.priorityDistribution.high,
                                                    dataDescriptor.priorityDistribution.mean,
                                                    dataDescriptor.priorityDistribution.stdDev)
        anesthesiaFlags = self.generate_binomial_sample(dataDescriptor.patients,
                                                        dataDescriptor.anesthesiaFrequence,
                                                        isSpecialty=False)
        covidFlags = self.generate_binomial_sample(dataDescriptor.patients,
                                                   dataDescriptor.covidFrequence,
                                                   isSpecialty=False)
        specialties = self.generate_binomial_sample(dataDescriptor.patients,
                                                    dataDescriptor.specialtyBalance,
                                                    isSpecialty=True)
        return DataContainer(operatingRoomTimes, anesthetistsTimes, operatingTimes, surgeriyIds, priorities, anesthesiaFlags, covidFlags, specialties)

    def create_data_dictionary(self, dataContainer: DataContainer, dataDescriptor: DataDescriptor):
        operatingRoomTimes = dataContainer.operatingRoomTimes
        anesthetistsTimes = dataContainer.anesthetistsTimes
        operatingTimes = dataContainer.asList(dataContainer.operatingTimes)
        surgeryIds = dataContainer.asList(dataContainer.surgeriyIds)
        priorities = dataContainer.asList(dataContainer.priorities)
        anesthesiaFlags = dataContainer.asList(dataContainer.anesthesiaFlags)
        covidFlags = dataContainer.asList(dataContainer.covidFlags)
        specialties = dataContainer.asList(dataContainer.specialties)
        ids = dataContainer.asList(dataContainer.ids)
        maxOperatingRoomTime = 270

        surgeryTypes = self.compute_surgery_types(surgeryIds, covidFlags)
        delayFlags = self.draw_delay_flags(surgeryIds)
        precedences = self.compute_precedences(surgeryTypes, delayFlags)
        return {
            None: {
                'I': {None: dataDescriptor.patients},
                'J': {None: dataDescriptor.specialties},
                'K': {None: dataDescriptor.operatingRooms},
                'T': {None: dataDescriptor.days},
                'A': {None: dataDescriptor.anesthetists},
                'M': {None: 7},
                's': operatingRoomTimes,
                'An': anesthetistsTimes,
                'tau': self.create_room_specialty_assignment(dataDescriptor.specialties, dataDescriptor.operatingRooms, dataDescriptor.days),
                'p': self.create_dictionary_entry(operatingTimes, isTime=False),
                'r': self.create_dictionary_entry(priorities, isTime=False),
                'a': self.create_dictionary_entry(anesthesiaFlags, isTime=False),
                'c': self.create_dictionary_entry(covidFlags, isTime=False),
                'u': self.create_precedence(precedences),
                'patientId': self.create_dictionary_entry(ids, isTime=False),
                'specialty': self.create_dictionary_entry(specialties, isTime=False),
                'rho': self.create_patient_specialty_table(dataDescriptor.patients, dataDescriptor.specialties, self.create_dictionary_entry(specialties, isTime=False)),
                'precedence': self.create_dictionary_entry(precedences, isTime=False),
                'bigM': {
                    1: math.floor(maxOperatingRoomTime/min(operatingTimes)),
                    2: maxOperatingRoomTime,
                    3: maxOperatingRoomTime,
                    4: maxOperatingRoomTime,
                    5: maxOperatingRoomTime,
                    6: dataDescriptor.patients
                }
            }
        }   

    def print_data(self, data):
        patientNumber = data[None]['I'][None]
        for i in range(0, patientNumber):
            id = i + 1
            priority = data[None]['r'][(i + 1)]
            specialty = data[None]['specialty'][(i + 1)]
            operatingTime = data[None]['p'][(i + 1)]
            covid = data[None]['c'][(i + 1)]
            precedence = data[None]['precedence'][(i + 1)]
            anesthesia = data[None]['a'][(i + 1)]
            print(Patient(id=id,
                          priority=priority,
                          specialty=specialty,
                          operatingTime=operatingTime,
                          covid=covid,
                          precedence=precedence,
                          anesthesia=anesthesia,
                          room="N/A",
                          day="N/A",
                          anesthetist="N/A",
                          order="N/A"
                          ))
        print("\n")

    def draw_operating_times_and_surgery_ids(self, n):
        surgeryIds = list(self.surgeryFrequencyMapping.keys())
        surgeryIdsFrequencies = list(self.surgeryFrequencyMapping.values())
        cumulativeSum = np.cumsum(surgeryIdsFrequencies)
        draws = uniform.rvs(size=n)
        times = np.zeros(n) - 1
        surgeries = []
        for i in range(0, len(draws)):
            for j in range(0, len(cumulativeSum)):
                if(draws[i] <= cumulativeSum[j]):
                    times[i] = self.surgeryRoomOccupancyMapping[surgeryIds[j]]
                    surgeries.append(surgeryIds[j])
                    break
            if(times[i] == -1):
                times[i] = self.surgeryRoomOccupancyMapping[surgeryIds[-1]]
                surgeries.append(surgeryIds[-1])
        return (times, surgeries)

    def draw_delay_flags(self, patientSurgeryIds):
        draws = uniform.rvs(size=len(patientSurgeryIds))
        delayFlags = []
        for i in range(0, len(draws)):
            if(draws[i] <= self.delayFrequencyByOperation[patientSurgeryIds[i]]):
                delayFlags.append(1)
            else:
                delayFlags.append(0)
        return delayFlags

    def compute_surgery_types(self, surgeryIds, covidFlags):
        surgeryTypes = []
        for i in range(0, len(surgeryIds)):
            if(covidFlags[i] == 1):
                surgeryTypes.append(SurgeryType.COVID)
                continue
            if(self.dirtySurgeryMapping[surgeryIds[i]] == 1):
                surgeryTypes.append(SurgeryType.DIRTY)
                continue
            surgeryTypes.append(SurgeryType.CLEAN)
        return surgeryTypes

    def compute_precedences(self, surgeryTypes, delayFlags):
        precedences = []
        for i in range(0, len(surgeryTypes)):
            if(surgeryTypes[i] == SurgeryType.CLEAN and delayFlags[i] == 0):
                precedences.append(1)
            if(surgeryTypes[i] == SurgeryType.CLEAN and delayFlags[i] == 1):
                precedences.append(2)
            if(surgeryTypes[i] == SurgeryType.DIRTY and delayFlags[i] == 0):
                precedences.append(3)
            if(surgeryTypes[i] == SurgeryType.DIRTY and delayFlags[i] == 1):
                precedences.append(4)
            if(surgeryTypes[i] == SurgeryType.COVID and delayFlags[i] == 0):
                precedences.append(5)
            if(surgeryTypes[i] == SurgeryType.COVID and delayFlags[i] == 1):
                precedences.append(6)
        return precedences
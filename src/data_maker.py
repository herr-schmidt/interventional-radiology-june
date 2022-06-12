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
        self._delayWeight = None

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

    @property
    def delayWeight(self):
        """Get delay weight."""
        return self._delayWeight

    @delayWeight.setter
    def delayWeight(self, value):
        self._delayWeight = value

    def initialize(self, patients, days, anesthetists, covidFrequence, anesthesiaFrequence, specialtyBalance, operatingTimeDistribution, priorityDistribution, delayWeight):
        self.patients = patients
        self.days = days
        self.anesthetists = anesthetists
        self.covidFrequence = covidFrequence
        self.anesthesiaFrequence = anesthesiaFrequence
        self.specialtyBalance = specialtyBalance
        self.operatingTimeDistribution = operatingTimeDistribution
        self.priorityDistribution = priorityDistribution
        self.delayWeight = delayWeight

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
    def __init__(self, operatingRoomTimes, anesthetistsTimes, operatingTimes, surgeriyIds, UOIds, priorities, anesthesiaFlags, covidFlags, specialties):
        self.operatingRoomTimes = operatingRoomTimes
        self.anesthetistsTimes = None
        self.operatingTimes = self.sample_list_to_dict(operatingTimes)
        self.surgeriyIds = self.sample_list_to_dict(surgeriyIds)
        self.UOIds = self.sample_list_to_dict(UOIds)
        self.priorities = self.sample_list_to_dict(priorities)
        self.anesthesiaFlags = None
        self.covidFlags = self.sample_list_to_dict(covidFlags)
        self.specialties = self.sample_list_to_dict(specialties)
        self.ids = self.sample_list_to_dict(
            [i for i in range(1, len(operatingTimes) + 1)])

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
            "000000100000000000000": 0.2571428571,
            "000100000000000000000": 0.1047619048,
            "000000000001110000000": 0.07619047619,
            "000000000000000100000": 0.07619047619,
            "100000000000000000000": 0.06666666667,
            "001000000000000000000": 0.04761904762,
            "100000100000000000000": 0.0380952381,
            "000000001000000000000": 0.0380952381,
            "010000000000000000000": 0.02857142857,
            "000000000000001000000": 0.02857142857,
            "000000000010000000000": 0.02857142857,
            "000001010000000000000": 0.01904761905,
            "000000100010000000000": 0.01904761905,
            "000100100000000000000": 0.01904761905,
            "100001100000000000000": 0.01904761905,
            "000001000000000100000": 0.01904761905,
            "000010000000000000000": 0.009523809524,
            "000001000100000000000": 0.009523809524,
            "000001100000000000000": 0.009523809524,
            "100001000000000001100": 0.009523809524,
            "000000101000000000000": 0.009523809524,
            "000000000000001000010": 0.009523809524,
            "000001100100000100000": 0.009523809524,
            "000000000001100000000": 0.009523809524,
            "000000010000000010000": 0.009523809524,
            "000000000000000000101": 0.009523809524,
            "100000101000000000000": 0.009523809524,
            "000000000000000000100": 0.009523809524
        }
        self.UOFrequencyMapping = {
            "01Chirurgia Universitaria": 0.01923076923,
            "01Medicina": 0.01923076923,
            "0901 - Chirurgia Generale d'Urgenza e PS 3 - Degenza Ordinaria": 0.009615384615,
            "0905 - Chirurgia Generale 1 U - Degenza Ordinaria ABEGG": 0.01923076923,
            "0910 - Chirurgia Generale 2 U - Day Hospital": 0.03846153846,
            "0910 - Chirurgia Generale 2 U - Degenza Ordinaria": 0.07692307692,
            "0910Trapianti - Chirurgia Generale 2 U - Trapianti Fegato": 0.02884615385,
            "0912 - Chirurgia Oncologica - Degenza Ordinaria": 0.009615384615,
            "1902 - Dietetica e Nutrizione Clinica - Day Hospital": 0.009615384615,
            "2609 - Medicina Interna 3 U - Degenza Ordinaria": 0.009615384615,
            "2610 - Medicina Interna 2 U - Degenza Ordinaria": 0.02884615385,
            "2639D - Day Hospital Unificato Medicine": 0.009615384615,
            "2666 - Medicina Interna 4 U - Degenza Ordinaria": 0.009615384615,
            "2901 - Nefrologia Dialisi e Trapianto U - Degenza Ordinaria": 0.02884615385,
            "3207 - Neurologia 1 U - Degenza Ordinaria": 0.009615384615,
            "3702 - Ginecologia e Ostetricia 4 S.Anna": 0.01923076923,
            "3706 - Ginecologia e Ostetricia 1 U S.Anna": 0.009615384615,
            "3707 - Servizio Unificato per I.V.G. S.Anna": 0.009615384615,
            "3710 - Ginecologia e Ostetricia 2 U S.Anna": 0.009615384615,
            "4303 - Urologia U - Degenza Ordinaria": 0.01923076923,
            "4303B - Week Surgery Urologia U": 0.2211538462,
            "4802 - Trapianto Renale - Degenza Ordinaria": 0.01923076923,
            "4907D - Anest. e Rianim. 1U - PS - Degenza di Rianimazione": 0.009615384615,
            "5801 - Gastroenterologia U - Degenza Ordinaria": 0.09615384615,
            "5807 - Insufficienza Epatica e Trapianto Epatico - Degenza Ordinaria": 0.03846153846,
            "6402 - Oncologia Medica 1 - Degenza Ordinaria": 0.03846153846,
            "6421 - Oncologia Medica 2 - Degenza Ordinaria": 0.01923076923,
            "6903-0202DH Radiodiagnostica 3": 0.009615384615,
            "6904 - Radiologia 1 U": 0.1538461538
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
        self.delayFrequencyByUO = {
            "4303B - Week Surgery Urologia U": 0.5217391304,
            "6904 - Radiologia 1 U": 0.5294117647,
            "5801 - Gastroenterologia U - Degenza Ordinaria": 0.5,
            "0910 - Chirurgia Generale 2 U - Degenza Ordinaria": 1,
            "0910 - Chirurgia Generale 2 U - Day Hospital": 0.4,
            "5807 - Insufficienza Epatica e Trapianto Epatico - Degenza Ordinaria": 1,
            "6402 - Oncologia Medica 1 - Degenza Ordinaria": 0.75,
            "0910Trapianti - Chirurgia Generale 2 U - Trapianti Fegato": 0.3333333333,
            "2610 - Medicina Interna 2 U - Degenza Ordinaria": 1,
            "2901 - Nefrologia Dialisi e Trapianto U - Degenza Ordinaria": 0.6666666667,
            # from now on, statistic was too uncertain (< 3 patients per operation): flip a coin
            "01Chirurgia Universitaria": 0.5,
            "01Medicina": 0.5,
            "0905 - Chirurgia Generale 1 U - Degenza Ordinaria ABEGG": 0.5,
            "3702 - Ginecologia e Ostetricia 4 S.Anna": 0.5,
            "4303 - Urologia U - Degenza Ordinaria": 0.5,
            "4802 - Trapianto Renale - Degenza Ordinaria": 0.5,
            "6421 - Oncologia Medica 2 - Degenza Ordinaria": 0.5,
            "0901 - Chirurgia Generale d'Urgenza e PS 3 - Degenza Ordinaria": 0.5,
            "0912 - Chirurgia Oncologica - Degenza Ordinaria": 0.5,
            "1902 - Dietetica e Nutrizione Clinica - Day Hospital": 0.5,
            "2609 - Medicina Interna 3 U - Degenza Ordinaria": 0.5,
            "2639D - Day Hospital Unificato Medicine": 0.5,
            "2666 - Medicina Interna 4 U - Degenza Ordinaria": 0.5,
            "3207 - Neurologia 1 U - Degenza Ordinaria": 0.5,
            "3706 - Ginecologia e Ostetricia 1 U S.Anna": 0.5,
            "3707 - Servizio Unificato per I.V.G. S.Anna": 0.5,
            "3710 - Ginecologia e Ostetricia 2 U S.Anna": 0.5,
            "4907D - Anest. e Rianim. 1U - PS - Degenza di Rianimazione": 0.5,
            "6903-0202DH Radiodiagnostica 3": 0.5,
        }

        self.operationGivenUO = {
            "01Chirurgia Universitaria": {
                "000000010000000010000": 0.5,
                "000000100010000000000": 0.5,
            },
            "01Medicina": {"000000100000000000000": 1},
            "0901 - Chirurgia Generale d'Urgenza e PS 3 - Degenza Ordinaria": {
                "000000000000001000000": 1
            },
            "0905 - Chirurgia Generale 1 U - Degenza Ordinaria ABEGG": {
                "000000100000000000000": 1
            },
            "0910 - Chirurgia Generale 2 U - Day Hospital": {
                "000000000000000100000": 0.2,
                "000000000001110000000": 0.6,
                "000100000000000000000": 0.2,
            },
            "0910 - Chirurgia Generale 2 U - Degenza Ordinaria": {
                "000000000000000000100": 0.125,
                "000000000000001000010": 0.125,
                "000000100000000000000": 0.125,
                "000010000000000000000": 0.125,
                "000100000000000000000": 0.375,
                "000100100000000000000": 0.125,
            },
            "0910Trapianti - Chirurgia Generale 2 U - Trapianti Fegato": {
                "000100000000000000000": 1
            },
            "0912 - Chirurgia Oncologica - Degenza Ordinaria": {"100000000000000000000": 1},
            "1902 - Dietetica e Nutrizione Clinica - Day Hospital": {
                "000000100000000000000": 1
            },
            "2609 - Medicina Interna 3 U - Degenza Ordinaria": {"000000100000000000000": 1},
            "2610 - Medicina Interna 2 U - Degenza Ordinaria": {
                "000000100000000000000": 0.6666666667,
                "000001000000000100000": 0.3333333333,
            },
            "2639D - Day Hospital Unificato Medicine": {"000001000000000100000": 1},
            "2666 - Medicina Interna 4 U - Degenza Ordinaria": {"000000100000000000000": 1},
            "2901 - Nefrologia Dialisi e Trapianto U - Degenza Ordinaria": {
                "000000001000000000000": 0.3333333333,
                "000000100000000000000": 0.3333333333,
                "000001100000000000000": 0.3333333333,
            },
            "3207 - Neurologia 1 U - Degenza Ordinaria": {"000000100010000000000": 1},
            "3702 - Ginecologia e Ostetricia 4 S.Anna": {
                "000000001000000000000": 0.5,
                "100001100000000000000": 0.5,
            },
            "3706 - Ginecologia e Ostetricia 1 U S.Anna": {"000000001000000000000": 1},
            "3707 - Servizio Unificato per I.V.G. S.Anna": {"000000100000000000000": 1},
            "3710 - Ginecologia e Ostetricia 2 U S.Anna": {"000000100000000000000": 1},
            "4303 - Urologia U - Degenza Ordinaria": {
                "000001000100000000000": 0.5,
                "100000101000000000000": 0.5,
            },
            "4303B - Week Surgery Urologia U": {
                "000000001000000000000": 0.04347826087,
                "000000100000000000000": 0.4782608696,
                "000000101000000000000": 0.04347826087,
                "100000000000000000000": 0.2608695652,
                "100000100000000000000": 0.1304347826,
                "100001100000000000000": 0.04347826087,
            },
            "4802 - Trapianto Renale - Degenza Ordinaria": {
                "000000100000000000000": 0.5,
                "100001000000000001100": 0.5,
            },
            "4907D - Anest. e Rianim. 1U - PS - Degenza di Rianimazione": {
                "000000000010000000000": 1
            },
            "5801 - Gastroenterologia U - Degenza Ordinaria": {
                "000000000000000100000": 0.3,
                "000000000001100000000": 0.1,
                "000000000001110000000": 0.5,
                "001000000000000000000": 0.1,
            },
            "5807 - Insufficienza Epatica e Trapianto Epatico - Degenza Ordinaria": {
                "001000000000000000000": 1
            },
            "6402 - Oncologia Medica 1 - Degenza Ordinaria": {
                "000000000000000100000": 0.25,
                "000000000000001000000": 0.25,
                "000001100100000100000": 0.25,
                "000100100000000000000": 0.25,
            },
            "6421 - Oncologia Medica 2 - Degenza Ordinaria": {"000000000010000000000": 1},
            "6903-0202DH Radiodiagnostica 3": {"000000000000000000101": 1},
            "6904 - Radiologia 1 U": {
                "000000000000000100000": 0.1875,
                "000000000000001000000": 0.0625,
                "000000100000000000000": 0.125,
                "000001010000000000000": 0.125,
                "000100000000000000000": 0.25,
                "010000000000000000000": 0.1875,
                "100000100000000000000": 0.0625,
            },
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

    def create_dictionary_entry(self, sample, toRound):
        dict = {}
        for i in range(0, len(sample)):
            if(toRound):
                dict[(i + 1)] = round(sample[i])
            else:
                dict[(i + 1)] = sample[i]
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
        UOs = self.draw_UO(dataDescriptor.patients)
        operations = self.draw_operations_given_UO(UOs)
        operatingTimes = self.compute_operating_times(operations)



        priorities = self.generate_truncnorm_sample(dataDescriptor.patients,
                                                    dataDescriptor.priorityDistribution.low,
                                                    dataDescriptor.priorityDistribution.high,
                                                    dataDescriptor.priorityDistribution.mean,
                                                    dataDescriptor.priorityDistribution.stdDev)
        covidFlags = self.generate_binomial_sample(dataDescriptor.patients,
                                                   dataDescriptor.covidFrequence,
                                                   isSpecialty=False)
        specialties = self.generate_binomial_sample(dataDescriptor.patients,
                                                    dataDescriptor.specialtyBalance,
                                                    isSpecialty=True)
        return DataContainer(operatingRoomTimes, None, operatingTimes, operations, UOs, priorities, None, covidFlags, specialties)

    def create_data_dictionary(self, dataContainer: DataContainer, dataDescriptor: DataDescriptor, delayEstimate):
        operatingRoomTimes = dataContainer.operatingRoomTimes
        operatingTimes = dataContainer.asList(dataContainer.operatingTimes)
        surgeryIds = dataContainer.asList(dataContainer.surgeriyIds)
        UOIds = dataContainer.asList(dataContainer.UOIds)
        priorities = dataContainer.asList(dataContainer.priorities)
        covidFlags = dataContainer.asList(dataContainer.covidFlags)
        specialties = dataContainer.asList(dataContainer.specialties)
        ids = dataContainer.asList(dataContainer.ids)
        maxOperatingRoomTime = 270
        delayWeight = dataDescriptor.delayWeight

        surgeryTypes = self.compute_surgery_types(surgeryIds, covidFlags)
        delayFlags = None
        if(delayEstimate == "UO"):
            delayFlags = self.draw_delay_flags_by_UO(UOIds)
        if(delayEstimate == "procedure"):
            delayFlags = self.draw_delay_flags_by_operation(surgeryIds)
        delayWeights = self.compute_delay_weights(delayFlags, delayWeight)
        precedences = self.compute_precedences(surgeryTypes, delayFlags)
        return {
            None: {
                'I': {None: dataDescriptor.patients},
                'J': {None: dataDescriptor.specialties},
                'K': {None: dataDescriptor.operatingRooms},
                'T': {None: dataDescriptor.days},
                'M': {None: 7},
                's': operatingRoomTimes,
                'tau': self.create_room_specialty_assignment(dataDescriptor.specialties, dataDescriptor.operatingRooms, dataDescriptor.days),
                'p': self.create_dictionary_entry(operatingTimes, toRound=False),
                'r': self.create_dictionary_entry(priorities, toRound=True),
                'd': self.create_dictionary_entry(delayWeights, toRound=False),
                'c': self.create_dictionary_entry(covidFlags, toRound=False),
                'u': self.create_precedence(precedences),
                'patientId': self.create_dictionary_entry(ids, toRound=False),
                'specialty': self.create_dictionary_entry(specialties, toRound=False),
                'rho': self.create_patient_specialty_table(dataDescriptor.patients, dataDescriptor.specialties, self.create_dictionary_entry(specialties, toRound=False)),
                'precedence': self.create_dictionary_entry(precedences, toRound=False),
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
            # anesthesia = data[None]['a'][(i + 1)]
            print(Patient(id=id,
                          priority=priority,
                          specialty=specialty,
                          operatingTime=operatingTime,
                          covid=covid,
                          precedence=precedence,
                          anesthesia="N/A",
                          room="N/A",
                          day="N/A",
                          anesthetist="N/A",
                          order="N/A"
                          ))
        print("\n")

    def data_as_string(self, data):
        result = ""
        patientNumber = data[None]['I'][None]
        for i in range(0, patientNumber):
            id = i + 1
            priority = data[None]['r'][(i + 1)]
            specialty = data[None]['specialty'][(i + 1)]
            operatingTime = data[None]['p'][(i + 1)]
            covid = data[None]['c'][(i + 1)]
            precedence = data[None]['precedence'][(i + 1)]
            # anesthesia = data[None]['a'][(i + 1)]
            result = result + str(Patient(id=id,
                          priority=priority,
                          specialty=specialty,
                          operatingTime=operatingTime,
                          covid=covid,
                          precedence=precedence,
                          anesthesia="N/A",
                          room="N/A",
                          day="N/A",
                          anesthetist="N/A",
                          order="N/A"
                          )) + "\n"
        return result

    def draw_UO(self, n):
        UOIds = list(self.UOFrequencyMapping.keys())
        UOIdsFrequencies = list(self.UOFrequencyMapping.values())
        cumulativeSum = np.cumsum(UOIdsFrequencies)
        draws = uniform.rvs(size=n)
        UOs = [""] * n
        for i in range(0, len(draws)):
            for j in range(0, len(cumulativeSum)):
                if(draws[i] <= cumulativeSum[j]):
                    UOs[i] = UOIds[j]
                    break
            if(UOs[i] == ""):
                UOs[i] = UOIds[-1]
        return UOs

    def draw_operations_given_UO(self, UOs):
        n = len(UOs)
        draws = uniform.rvs(size=n)
        operations = []
        for i in range(0, n):
            surgeryIds = list(self.operationGivenUO[UOs[i]].keys())
            surgeryIdsFrequencies = list(self.operationGivenUO[UOs[i]].values())
            cumulativeSum = np.cumsum(surgeryIdsFrequencies)
            times = np.zeros(n) - 1
            for j in range(0, len(cumulativeSum)):
                if(draws[i] <= cumulativeSum[j]):
                    times[i] = self.surgeryRoomOccupancyMapping[surgeryIds[j]]
                    operations.append(surgeryIds[j])
                    break
            if(times[i] == -1):
                times[i] = self.surgeryRoomOccupancyMapping[surgeryIds[-1]]
                operations.append(surgeryIds[-1])
        return operations

    def draw_delay_flags_by_UO(self, UOs):
        draws = uniform.rvs(size=len(UOs))
        delayFlags = []
        for i in range(0, len(draws)):
            if(draws[i] <= self.delayFrequencyByUO[UOs[i]]):
                delayFlags.append(1)
            else:
                delayFlags.append(0)
        return delayFlags

    def compute_operating_times(self, operations):
        times = []
        for operation in operations:
            times.append(self.surgeryRoomOccupancyMapping[operation])
        return times

    def draw_delay_flags_by_operation(self, patientSurgeryIds):
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

    def compute_delay_weights(self, delayFlags, delayWeight):
        delayWeights = []
        for df in delayFlags:
            if(df == 1):
                delayWeights.append(delayWeight)
            else:
                delayWeights.append(1.0)
        return delayWeights
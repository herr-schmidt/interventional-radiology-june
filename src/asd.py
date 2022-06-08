dict = {"01Chirurgia Universitaria": {"000000010000000010000":	0.5,
                                      "000000100010000000000":	0.5
                                      },
        "01Medicina": {"000000100000000000000": 1},
        "0901 - Chirurgia Generale d'Urgenza e PS 3 - Degenza Ordinaria": {"000000000000001000000": 1},
        "0905 - Chirurgia Generale 1 U - Degenza Ordinaria ABEGG": {"000000100000000000000": 1},
        "0910 - Chirurgia Generale 2 U - Day Hospital": {"000000000000000100000": 0.2,
                                                         "000000000001110000000": 0.6,
                                                         "000100000000000000000": 0.2},
        "0910 - Chirurgia Generale 2 U - Degenza Ordinaria": {
    "000000000000000000100": 	0.125,
    "000000000000001000010": 	0.125,
    "000000100000000000000": 	0.125,
    "000010000000000000000": 	0.125,
    "000100000000000000000": 	0.375,
    "000100100000000000000": 	0.125},
    "0910Trapianti - Chirurgia Generale 2 U - Trapianti Fegato": {"000100000000000000000": 1},
    "0912 - Chirurgia Oncologica - Degenza Ordinaria": {"100000000000000000000": 1},
    "1902 - Dietetica e Nutrizione Clinica - Day Hospital": {"000000100000000000000":	1},
    "2609 - Medicina Interna 3 U - Degenza Ordinaria": {"000000100000000000000": 1},
    "2610 - Medicina Interna 2 U - Degenza Ordinaria": {
    "000000100000000000000": 0.6666666667,
    "000001000000000100000": 0.3333333333
},
    "2639D - Day Hospital Unificato Medicine": {"000001000000000100000": 1},
    "2666 - Medicina Interna 4 U - Degenza Ordinaria": {"000000100000000000000":	1},
    "2901 - Nefrologia Dialisi e Trapianto U - Degenza Ordinaria": {
    "000000001000000000000":	0.3333333333,
    "000000100000000000000":	0.3333333333,
    "000001100000000000000":	0.3333333333},
    "3207 - Neurologia 1 U - Degenza Ordinaria": {"000000100010000000000": 1},
    "3702 - Ginecologia e Ostetricia 4 S.Anna": {
    "000000001000000000000":	0.5,
    "100001100000000000000":	0.5},
    "3706 - Ginecologia e Ostetricia 1 U S.Anna": {"000000001000000000000":	1},
    "3707 - Servizio Unificato per I.V.G. S.Anna": {"000000100000000000000":	1},
    "3710 - Ginecologia e Ostetricia 2 U S.Anna": {"000000100000000000000":	1},
    "4303 - Urologia U - Degenza Ordinaria": {
    "000001000100000000000":	0.5,
    "100000101000000000000":	0.5
},
    "4303B - Week Surgery Urologia U": {

    "000000001000000000000":	0.04347826087,
    "000000100000000000000":	0.4782608696,
    "000000101000000000000":	0.04347826087,
    "100000000000000000000":	0.2608695652,
    "100000100000000000000":	0.1304347826,
    "100001100000000000000":	0.04347826087
},
    "4802 - Trapianto Renale - Degenza Ordinaria": {
    "000000100000000000000":	0.5,
    "100001000000000001100":	0.5
},
    "4907D - Anest. e Rianim. 1U - PS - Degenza di Rianimazione": {"000000000010000000000":	1},
    "5801 - Gastroenterologia U - Degenza Ordinaria": {
    "000000000000000100000":	0.3,
    "000000000001100000000":	0.1,
    "000000000001110000000":	0.5,
    "001000000000000000000":	0.1},
    "5807 - Insufficienza Epatica e Trapianto Epatico - Degenza Ordinaria": {"001000000000000000000":	1},
    "6402 - Oncologia Medica 1 - Degenza Ordinaria": {
    "000000000000000100000": 	0.25,
    "000000000000001000000": 	0.25,
    "000001100100000100000": 	0.25,
    "000100100000000000000": 	0.25
},
    "6421 - Oncologia Medica 2 - Degenza Ordinaria": {"000000000010000000000":	1},
    "6903-0202DH Radiodiagnostica 3": {"000000000000000000101":	1},
    "6904 - Radiologia 1 U": {
    "000000000000000100000":	0.1875,
    "000000000000001000000":	0.0625,
    "000000100000000000000":	0.125,
    "000001010000000000000":	0.125,
    "000100000000000000000":	0.25,
    "010000000000000000000":	0.1875,
    "100000100000000000000":	0.0625
}
}




print(dict["6904 - Radiologia 1 U"]["000000000000001000000"])
print(list(dict.values()))
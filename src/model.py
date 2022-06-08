class Patient:
    def __init__(self, id, priority, room, specialty, day, operatingTime, covid, precedence, anesthesia, anesthetist, order):
        self.id = id
        self.priority = priority
        self.room = room
        self.specialty = specialty
        self.day = day
        self.operatingTime = operatingTime
        self.covid = covid
        self.precedence = precedence
        self.anesthesia = anesthesia
        self.anesthetist = anesthetist
        self.order = order

    def __str__(self):
        return f'id:{self.id:4}; priority:{self.priority:4}; room:{self.room:2}; specialty:{self.specialty:2}; day:{self.day:2}; operatingTime:{self.operatingTime:4}; covid:{self.covid:2}; precedence:{self.precedence:2}; anesthesia:{self.none_to_empty(self.anesthesia):2}; anesthetist:{self.none_to_empty(self.anesthetist):2}; order:{self.order:6};'

    def none_to_empty(self, s):
        if(s is None):
            return ""
        return str(s)
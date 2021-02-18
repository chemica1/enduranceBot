class indicator():
    def __init__(self, list):
        self.list = list

    def movingAvg(self, days):
        return sum(self.list[-days:]) / days


from py_stealth import *
from datetime import datetime as dt

START_X = GetX(Self())
START_Y = GetY(Self())


def train_hiding():
    while not Hidden():
        _started = dt.now()
        UseSkill("Hiding")
        WaitJournalLine(_started, "не удалось|сможешь сделать", 2000)

    while Hidden():
        _started = dt.now()
        UseSkill("Detect Hidden")
        WaitJournalLine(_started, "Ты обнаружил|You can see", 2000)


while not Dead():
    train_hiding()
    Wait(500)

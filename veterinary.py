from py_stealth import *
from datetime import timedelta, datetime as dt

TARGET = 0x00018EBF
BANDAGES = 0x0E21
while not Dead():
    if IsObjectExists(TARGET) and GetHP(TARGET) < GetMaxHP(TARGET):
        if FindType(BANDAGES, Backpack()):
            _started = dt.now()
            WaitTargetObject(TARGET)
            UseType(BANDAGES, 0xFFFF)
            WaitJournalLine(_started, "Вылечено|Не получилось|Цель не", 25000)
            Wait(1000)
        else:
            print("No more bandages left")
            exit()
    Wait(100)



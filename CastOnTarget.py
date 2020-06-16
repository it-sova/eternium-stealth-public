from py_stealth import *
from datetime import timedelta, datetime as dt

TARGET = 0x00018EBF
MANA_REQUIRED = 20
KEEP_HP = 10
# SPELL = "Magic Arrow"
SPELL = "Lightning"


while not Dead():
    while Mana() >= MANA_REQUIRED:
        if GetHP(TARGET) >= KEEP_HP:
            CastToObj(SPELL, TARGET)
            Wait(5000)

    while Mana() < MaxMana():
        SetWarMode(False)
        _started = dt.now()
        UseSkill("Meditation")
        Wait(1000)
        WaitJournalLine(_started, "Ты потерял|Ты полон", 30000)

    UOSay(".helpastral")
    Wait(100)

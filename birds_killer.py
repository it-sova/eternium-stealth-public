from py_stealth import *
from datetime import timedelta, datetime as dt
from Scripts.telegram import *
import re

DEBUG = 1
MAX_WEIGHT = 800
# Chest params
RESOURCE_CHEST = 0x40003022
RESOURCE_CHEST_PASSWORD = 3142
RESOURCE_CHEST_GUMP_ID = 0x00000400
#
# Runebook
RUNEBOOK_RUNE_SPOT = 1
RUNEBOOK_RUNE_HOME = 2
RUNEBOOK_CHARGES_MAX = 32
RUNEBOOK_GUMP_ID = 0x00000411
#
DELAY = 15
POINTS = [
    (1191, 1683),
    (1225, 1722)
]
REAGENTS = {
    0X0F7A: "Black pearl",
    0x0F7B: "Blood moss",
    0x0F86: "Mandrake roots",
    0x1F4C: "Recall scrolls"
}
CHARGEX_REGEX = re.compile(r"Charges:\s+(\d+)")
BIRDS = [
    0x00D0,  # A Chicken
]
FEATHERS = 0x1BD1



def dprint(message):
    if DEBUG == 1:
        print(message)


def find_gump(gump_id: int) -> bool:
    for _gump in range(0, GetGumpsCount()):
        if GetGumpID(_gump) == gump_id:
            return True
    return False


def open_password_chest():
    if IsObjectExists(RESOURCE_CHEST):
        UseObject(RESOURCE_CHEST)
        Wait(500)
        if find_gump(RESOURCE_CHEST_GUMP_ID):
            GumpAutoTextEntry(3, RESOURCE_CHEST_PASSWORD)
            WaitGump(4)
            Wait(500)
            unload()
        else:
            print("Failed to open chest")
    else:
        print("No chest found")


def recall(rune):
    _runebook = get_runebook()

    _current_x = GetX(Self())
    _current_y = GetY(Self())

    if _runebook > 0:
        UseObject(_runebook)
        Wait(500)
        if find_gump(RUNEBOOK_GUMP_ID):
            WaitGump(rune)
            Wait(15 * 1000)
            if _current_x == GetX(Self()) and _current_y == GetY(Self()):
                print("Recall failed")
        else:
            print("Failed to open runebook")
    else:
        exit()


def get_runebook():
    if FindTypeEx(0x0EFA, 0x0972, Backpack()):
        if len(GetFoundList()) > 1:
            print(f"{len(GetFoundList())} runebooks found, expecting 1")
            return 0
        else:
            print("Runebook found")
            return FindItem()
    else:
        print("No runebooks found")
        return 0


def get_runebook_charges():
    _runebook = get_runebook()
    if _runebook > 0:
        UseObject(_runebook)
        Wait(500)
        if find_gump(RUNEBOOK_GUMP_ID):
            _lines = GetGumpTextLines(GetGumpsCount() - 1)
            _charges_line = _lines[0]
            _matched = CHARGEX_REGEX.match(_charges_line)
            if _matched:
                return int(_matched.group(1))
        else:
            print("Failed to open runebook")


def find_targets() -> list:
    _found_targets = []
    for _bird in BIRDS:
        if FindType(_bird, Ground()):
            for _found_bird in GetFoundList():
                _found_targets.append(_found_bird)

    dprint(f"Found {len(_found_targets)} birds")
    return _found_targets


def kill_target(serial):
    while IsObjectExists(serial):
        NewMoveXY(GetX(serial), GetY(serial), True, 1, True)
        Attack(serial)
        Wait(500)
    cut_and_loot()


def wait_for_respawn():
    SetWarMode(False)
    while not Hidden():
        UseSkill("Stealth")
        Wait(2000)
    dprint(f"Waiting for {DELAY} minutes")
    Wait(DELAY * 60 * 1000)


def check_reagent(reagent_type, reagent_name):
    if Count(reagent_type) < 10:
        if FindType(reagent_type, RESOURCE_CHEST):
            if FindFullQuantity() > 10:
                telegram_message(f"{reagent_name} left in chest: {FindFullQuantity() - 10}")
                Grab(FindItem(), 10)
                Wait(500)
        else:
            telegram_message(f"No more {reagent_name} left")
            exit()


def refill_reagents():
    for _reagent_type in REAGENTS:
        check_reagent(_reagent_type, REAGENTS[_reagent_type])
    recharge_runebook()


def recharge_runebook():
    _charges = get_runebook_charges()
    if _charges < RUNEBOOK_CHARGES_MAX:
        FindType(0x1F4C, Backpack())
        MoveItem(FindItem(), RUNEBOOK_CHARGES_MAX - _charges, get_runebook(), 0, 0, 0)
        Wait(500)


def cut_and_loot():
    if FindType(0x2006, Ground()):
        _corpse = FindItem()
        NewMoveXY(GetX(_corpse), GetY(_corpse), True, 0, True)
        UseObject(ObjAtLayer(RhandLayer()))
        if WaitForTarget(1000):
            TargetToObject(_corpse)
            Wait(500)
            UseObject(_corpse)
            if FindType(FEATHERS, _corpse):
                Grab(FindItem(), -1)
                Wait(500)
                Ignore(_corpse)
        else:
            dprint("Failed to get target")


def unload():
    if FindType(FEATHERS, Backpack()):
        telegram_message(f"Feathers unloaded: {FindFullQuantity()}")
        MoveItem(FindItem(), 0, RESOURCE_CHEST, 0, 0, 0)
        Wait(500)
    refill_reagents()


SetFindDistance(35)
SetARStatus(True)
SetPauseScriptOnDisconnectStatus(True)
recall(RUNEBOOK_RUNE_SPOT)
while not Dead():
    for _point in POINTS:
        _point_x, _point_y = _point
        dprint(f"X: {_point_x}, Y: {_point_y}")
        newMoveXY(_point_x, _point_y, True, 1, True)
        for _target in find_targets():
            kill_target(_target)
            Wait(100)

    if Weight() >= MAX_WEIGHT:
        recall(RUNEBOOK_RUNE_HOME)
        open_password_chest()
        recall(RUNEBOOK_RUNE_SPOT)

    wait_for_respawn()

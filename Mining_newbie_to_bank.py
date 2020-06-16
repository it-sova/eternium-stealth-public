from py_stealth import *
from datetime import datetime as dt
from Scripts.helpers import Types

ORE_COLORS = {
    0x0000: "Iron",

}

SKIP_TILE_MESSAGES = [
    "There is nothing",
    "Ты не можешь копать",
    "Пробуй копать в другом"
]

NEXT_TRY_MESSAGES = [
    "Вы положили",
    "You loosen",
    "You decide not",  # Alt-tab protection
]

INGOTS = [
    0x1BE3,
    0x1BEF,
    0x1BE9
]

CAVE_TILES = range(1339, 1359)
TILE_SEARCH_RANGE = 50

BANK_COORDINATES = (4643, 288)
MINE_COORDINATES = (4600, 354)
FORGE_COORDINATES = (4593, 360)

SMELT_WEIGHT = MaxWeight() - 10
UNLOAD_WEIGHT = MaxWeight() - 50


def cancel_targets():
    CancelWaitTarget()
    if TargetPresent():
        CancelTarget()


def find_tiles(center_x, center_y, radius):
    _min_x, _min_y = center_x-radius, center_y-radius
    _max_x, _max_y = center_x+radius, center_y+radius
    _tiles_coordinates = []
    for _tile in CAVE_TILES:
        _tiles_coordinates += GetStaticTilesArray(_min_x, _min_y, _max_x, _max_y, WorldNum(), _tile)
    print("[FindTiles] Found "+str(len(_tiles_coordinates))+" tiles")
    _tiles_coordinates_reversed = _tiles_coordinates[::-1]
    return _tiles_coordinates_reversed


def check_hidden():
    while not Hidden():
        _started = dt.now()
        UseSkill("Hiding")
        WaitJournalLine(_started, "не удалось|сможешь сделать", 2000)


def smelt(return_to_x, return_to_y):
    _forge_x, _forge_y = FORGE_COORDINATES
    _try = 0
    while GetX(Self()) != _forge_x and GetY(Self()) != _forge_y:
        _try += 1
        if _try > 15:
            print("Failed to get to forge 15 times a row..")
            break
        newMoveXY(_forge_x, _forge_y, True, 0, True)
        Wait(500)

    FindType(Types.ORE, Backpack())
    for _ore in GetFindedList():
        UseObject(_ore)
        Wait(200)

    newMoveXY(return_to_x, return_to_y, True, 0, True)


def unload_to_bank(return_to_x, return_to_y):
    _bank_x, _bank_y = BANK_COORDINATES
    newMoveXY(_bank_x, _bank_y, True, 0, True)
    UOSay("Bank")
    Wait(500)
    for _ingot_type in INGOTS:
        FindType(_ingot_type, Backpack())
        for _ingot in GetFoundList():
            MoveItem(_ingot, 0, ObjAtLayer(BankLayer()), 0, 0, 0)
            Wait(500)

    newMoveXY(return_to_x, return_to_y, True, 0, True)


def mine():
    for _tile_data in find_tiles(GetX(Self()), GetY(Self()), TILE_SEARCH_RANGE):
        _tile, _x, _y, _z = _tile_data
        while not Dead():
            if newMoveXY(_x, _y, True, 1, True):
                if Weight() > SMELT_WEIGHT:
                    smelt(GetX(Self()), GetY(Self()))
                    if Weight() > UNLOAD_WEIGHT:
                        unload_to_bank(GetX(Self()), GetY(Self()))

                _started = dt.now()
                cancel_targets()
                UseType(Types.PICKAXE, 0xFFFF)
                WaitForTarget(2000)
                if TargetPresent():
                    WaitTargetTile(_tile, _x, _y, _z)
                    WaitJournalLine(_started, "|".join(SKIP_TILE_MESSAGES + NEXT_TRY_MESSAGES), 15000)

                if InJournalBetweenTimes("|".join(SKIP_TILE_MESSAGES), _started, dt.now()) > 0:
                    break
            else:
                print(f"Can't reach X: {_x} Y: {_y}")

        Wait(500)


# Initialization

mine_x, mine_y = MINE_COORDINATES
SetARStatus(True)
SetPauseScriptOnDisconnectStatus(True)
SetWarMode(False)
SetMoveThroughNPC(20)
newMoveXY(mine_x, mine_y, True, 0, True)

while not Dead():
    mine()
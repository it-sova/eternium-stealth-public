from py_stealth import *
from datetime import datetime as dt
from Scripts.helpers import Types
import re

# Serial сундука
HOME_CHEST = 0x40018746
# Коорды возле сундука
NEAR_HOME_POINT = (2009, 358)
# Коорды в шахте ( по центру )
MINE_COORDINATES = (1905, 368)


TOOLTIP_REGEX = re.compile(r"\s+(\w+ ore)\s+\|Amount:\s+(\d+)")

SKIP_TILE_MESSAGES = [
    "There is nothing",
    "Ты не можешь копать",
    "Пробуй копать в другом",
    "You have no line",
    "You decide not to mine"
]

NEXT_TRY_MESSAGES = [
    "Вы положили",
    "You loosen",
    "You decide not",  # Alt-tab protection
]

CAVE_TILES = range(1339, 1359)
TILE_SEARCH_RANGE = 10

UNLOAD_WEIGHT = MaxWeight() - 50


def cancel_targets():
    CancelWaitTarget()
    if TargetPresent():
        CancelTarget()


def statistics():
    _statistics = "\n"
    FindType(0xFFFF, Backpack())
    for _item in GetFoundList():
        _matched = TOOLTIP_REGEX.match(GetTooltip(_item))
        if _matched:
            _statistics += f"{_matched.group(1)}: +{_matched.group(2)}\n"
    print(_statistics)


def find_tiles(center_x, center_y, radius):
    _min_x, _min_y = center_x-radius, center_y-radius
    _max_x, _max_y = center_x+radius, center_y+radius
    _tiles_coordinates = []
    for _tile in CAVE_TILES:
        _tiles_coordinates += GetStaticTilesArray(
            _min_x, _min_y, _max_x, _max_y, WorldNum(), _tile)
    print("[FindTiles] Found "+str(len(_tiles_coordinates))+" tiles")
    return _tiles_coordinates


def find_gump(gump_id: int) -> bool:
    for _gump in range(0, GetGumpsCount()):
        if GetGumpID(_gump) == gump_id:
            return True
    return False


def wait_for_gump(button: int, gump_id: int) -> None:
    _try = 0
    while not find_gump(gump_id):
        _try += 1
        Wait(500)
        if _try > 30:
            # print("wat_for_gump timeout")
            return

    WaitGump(button)
    Wait(2000)


def unload(x, y):
    (_home_x, _home_y) = NEAR_HOME_POINT
    newMoveXY(_home_x, _home_y, True, 0, True)

    statistics()
    if FindType(Types.ORE, Backpack()):
        for _log in GetFindedList():
            MoveItem(_log, 0, HOME_CHEST, 0, 0, 0)
            Wait(500)
    Wait(500)
    newMoveXY(x, y, True, 0, True)


def mine():
    for _tile_data in find_tiles(GetX(Self()), GetY(Self()), TILE_SEARCH_RANGE):
        _tile, _x, _y, _z = _tile_data
        while not Dead():
            if newMoveXY(_x, _y, True, 1, True):
                if Weight() > UNLOAD_WEIGHT:
                    unload(GetX(Self()), GetY(Self()))

                _started = dt.now()
                cancel_targets()
                UseType(Types.PICKAXE, 0xFFFF)
                WaitForTarget(2000)
                if TargetPresent():
                    WaitTargetTile(_tile, _x, _y, _z)
                    WaitJournalLine(_started, "|".join(
                        SKIP_TILE_MESSAGES + NEXT_TRY_MESSAGES), 15000)

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

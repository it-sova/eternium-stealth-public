from py_stealth import *
from datetime import timedelta, datetime as dt

# Менять под себя /////////////////////
NEAR_HOME_POINT = (2010, 359)
HOME_CHEST = 0x40018746
POINTS = [
    (0, 1985, 352, 0),
    (1, 1986, 377, 3),
    (2, 2006, 380, 0),
    (3, 1967, 384, 3),
    (4, 1952, 406, 0),
    (5, 1970, 399, 0),
    (6, 1998, 398, 0),
    (7, 2017, 401, 0),
    (8, 2070, 411, 0),
    (9, 2080, 384, 0)
]
# /////////////////////////////////////
# Врядли стоит менять под себя
TREE_TILES = [
    3274, 3275, 3277, 3280,
    3283, 3286, 3288, 3290,
    3293, 3296, 3299, 3302,
    3320, 3323, 3326, 3329,
    3393, 3394, 3395, 3396,
    3415, 3416, 3417, 3418,
    3419, 3438, 3439, 3440,
    3441, 3442, 3460, 3461,
    3462, 3476, 3478, 3480,
    3482, 3484, 3492, 3496
]


LOG_COLORS = {
    0x0000: "Logs",
    0x05B0: "Arcane Logs",
    0x09B2: "Sarotin Logs",
    0x086E: "Forest Logs",
    0x0AE3: "Elven Logs"

}
# Common types
AXE = 0x0F43
LOGS = 0x1BDD


BAD_POINTS = []



# Messages to skip current tile (depleted, etc0
SKIP_TILE_MESSAGES = [
                "not enough",
                "You cannot",
                "Здесь нечего",
                "Ты не можешь рубить"
]
# Messages to continue chopping
NEXT_TRY_MESSAGES = [
                     "You hack at",
                     "You put",
                     "You chop",
                     "You have worn",
                     "Вы положили"


]
# Messages to mark tile as bad
BAD_POINT_MESSAGES = [
                        "You can't use",
                        "be seen",
                        "is too far",
                        "no line of",
                        "axe on that",
]


def statistics():
    _statistics = "\n"
    for _color in LOG_COLORS:
        if FindTypeEx(LOGS, _color, Backpack()):
            _statistics += f"{LOG_COLORS[_color]}: +{FindFullQuantity()} \n"
        Wait(100)

def find_tiles(center_x, center_y, radius):
    _min_x, _min_y = center_x-radius, center_y-radius
    _max_x, _max_y = center_x+radius, center_y+radius
    _tiles_coordinates = []
    for _tile in TREE_TILES:
        _tiles_coordinates += GetStaticTilesArray(_min_x, _min_y, _max_x, _max_y, WorldNum(), _tile)
    print("[FindTiles] Found "+str(len(_tiles_coordinates))+" tiles")
    return _tiles_coordinates

def move_to_point(x, y):
    _try = 0
    while not newMoveXY(x, y, True, 0, True):
        _try += 1
        if _try > 15:
            AddToSystemJournal(f"Failed to get to X:{x} Y:{y}")
            exit()
        newMoveXY(x, y, True, 0, True)
        AddToSystemJournal(f" Try: {_try}")


def unload(x, y):
    (_home_x, _home_y) = NEAR_HOME_POINT
    move_to_point(_home_x, _home_y)
    statistics()
    if FindType(LOGS, Backpack()):
        for _log in GetFindedList():
            MoveItem(_log, 0, HOME_CHEST, 0, 0, 0)
            Wait(500)
    Wait(500)
    move_to_point(x, y)


def cancel_targets():
    CancelWaitTarget()
    if TargetPresent():
        CancelTarget()

def lumberjacking(sorted_trees):
    for _t, _x, _y, _z in sorted_trees:
        if ([_x, _y] not in BAD_POINTS) and NewMoveXY(_x, _y, True, 1, True):
            _try = 0
            while not Dead():
                _try += 1
                if _try > 20:
                    print("Try limit exceeded, bugged tree?")
                    break

                # Preparations
                _starting_ts = dt.now()
                cancel_targets()
                # Check if we are overloaded
                # if Weight() > MaxWeight()-10:
                if Weight() > 400:
                    unload(GetX(Self()), GetY(Self()))
                #
                UseObject(ObjAtLayer(LhandLayer()))
                WaitForTarget(2000)
                if TargetPresent():

                    WaitTargetTile(_t, _x, _y, _z)
                    WaitJournalLine(_starting_ts, "|".join(NEXT_TRY_MESSAGES+SKIP_TILE_MESSAGES+BAD_POINT_MESSAGES),
                                    15000)

                    # If we waited full WaitJournalLine timeout, something went wrong
                    if dt.now() >= _starting_ts+timedelta(seconds=15):
                        print(f"{_x} {_y} WaitJournalLine timeout exceeded, bad tree?")
                        break

                    if InJournalBetweenTimes("|".join(BAD_POINT_MESSAGES), _starting_ts, dt.now()) > 0:
                        if [_x, _y] not in BAD_POINTS:
                            print(f"Added tree to bad points, trigger => {BAD_POINT_MESSAGES[FoundedParamID()]}")
                            BAD_POINTS.append([_x, _y])
                            break

                    if InJournalBetweenTimes("|".join(SKIP_TILE_MESSAGES), _starting_ts, dt.now()) > 0:
                        # print("Tile depleted, skipping")
                        break
                else:
                    print("No target present for some reason...")
                Wait(500)


# Start
ClearSystemJournal()
SetARStatus(True)
SetMoveOpenDoor(True)
SetPauseScriptOnDisconnectStatus(True)
while not Dead():
    for point in POINTS:
        (_, x, y, z) = point
        NewMoveXY(x, y, True, 0, True)
        lumberjacking(find_tiles(GetX(Self()), GetY(Self()), 20))
        Wait(1000)

SetARStatus(False)
Disconnect()

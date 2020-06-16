from py_stealth import *
from datetime import timedelta, datetime as dt
from Scripts.telegram import *

# Менять под себя /////////////////////
NEAR_HOME_POINT = (1347, 2844)
HOME_CHEST = 0x4004389C
POINTS = [
    (0, 1361, 2796, 5),
    (1, 1383, 2806, 0),
    (2, 1378, 2838, 0),
    (3, 1366, 2864, 0),
    (4, 1363, 2896, 0),
    (5, 1377, 2922, 0),
    (6, 1389, 2950, 0),
    (7, 1367, 2955, 0),
    (8, 1355, 2980, 0),
    (9, 1365, 2998, -8),
    (10, 1394, 2975, 0),
    (11, 1419, 2970, 0),
    (12, 1429, 2979, 0),
    (13, 1407, 3005, 0),
    (14, 1392, 3020, 0),
    (15, 1376, 3047, 0),

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
TINKER_TOOLS = 0x1EB8
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
    telegram_message(_statistics)


def sort_trees(trees):
    _trees_by_distance = {}
    _ordered_trees_list = []
    _prev_last_tree = (0, NEAR_HOME_POINT[0], NEAR_HOME_POINT[1])

    def _tree_dist(_tree1, _tree2):
        return Dist(_tree1[1], _tree1[2], _tree2[1], _tree2[2])

    for _tree in trees:
        _td = _tree_dist(_tree, _prev_last_tree)
        if _td % 2 == 0:
            _td -= 1
        _trees_group = _trees_by_distance.get(_td, [])
        _trees_group.append(_tree)
        _trees_by_distance[_td] = _trees_group

    for current_distance in _trees_by_distance:
        _trees = _trees_by_distance[current_distance]
        first_tree = last_tree = _trees[0]
        for tree1 in _trees:
            for tree2 in _trees:
                if _tree_dist(tree1, tree2) > _tree_dist(first_tree, last_tree):
                    first_tree, last_tree = tree1, tree2
        if _tree_dist(_prev_last_tree, last_tree) < _tree_dist(_prev_last_tree, first_tree):
            first_tree, last_tree = last_tree, first_tree
        _trees.sort(key=lambda _tree: _tree_dist(_tree, first_tree))
        _ordered_trees_list += _trees
        _prev_last_tree = last_tree

    return _ordered_trees_list


def find_tiles(center_x, center_y, radius):
    _min_x, _min_y = center_x-radius, center_y-radius
    _max_x, _max_y = center_x+radius, center_y+radius
    _tiles_coordinates = []
    for _tile in TREE_TILES:
        _tiles_coordinates += GetStaticTilesArray(_min_x, _min_y, _max_x, _max_y, WorldNum(), _tile)
    print("[FindTiles] Found "+str(len(_tiles_coordinates))+" tiles")
    return _tiles_coordinates


def populate_trees_array():
    _trees = []
    for point in POINTS:
        (_point_number, _x, _y, _z) = point
        if NewMoveXY(_x, _y, True, 0, True):
            for _tree_tuple in find_tiles(_x, _y, 18):
                _trees.append(_tree_tuple)
        else:
            print("Can't get to point location, skipping")
    return _trees


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


def remove_duplicates(array):
    return list(set([i for i in array]))


def get_sorted_trees():
    _result = sort_trees(remove_duplicates(populate_trees_array()))
    print(f"Trees after duplicate removal => {len(_result)}")
    return _result


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
sorted_trees_array = get_sorted_trees()
while not Dead():
    for point in POINTS:
        (_, x, y, z) = point
        NewMoveXY(x, y, True, 0, True)
        lumberjacking(find_tiles(GetX(Self()), GetY(Self()), 20))
        Wait(1000)

SetARStatus(False)
Disconnect()
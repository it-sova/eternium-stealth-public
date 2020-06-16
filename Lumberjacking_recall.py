from py_stealth import *
from datetime import timedelta, datetime as dt
from Scripts.telegram import *
import re

# Менять под себя /////////////////////
RUNEBOOK_GUMP_ID = 0x00000411
RESOURCE_CHEST_GUMP_ID = 0x00000400
# Chest params
RESOURCE_CHEST = 0x40003569
RESOURCE_CHEST_PASSWORD = 3142
#
# Runebook
RUNEBOOK_RUNE_SPOT = 1
RUNEBOOK_RUNE_HOME = 2
#
POINTS = [
    (1, 885, 1358, -90),
    (2, 896, 1329, -90),
    (3, 896, 1308, -90),
    (4, 918, 1312, -90),
    (5, 929, 1329, -90),
    (6, 926, 1361, -90),
    (7, 953, 1365, -88),
    (8, 957, 1375, -86),
    (9, 950, 1383, -86),
    (10, 972, 1397, -84),
    (11, 988, 1383, -87),
    (12, 1000, 1395, -85),
    (13, 1011, 1416, -83),
    (14, 974, 1444, -87),
    (15, 979, 1467, -88),
    (16, 943, 1473, -87),
    (17, 947, 1490, -85),
    (18, 928, 1504, -88),
    (19, 907, 1501, -90),
    (20, 886, 1514, -88),
    (21, 867, 1501, -85),
    (22, 864, 1473, -88),
    (23, 836, 1496, -83),
    (24, 834, 1468, -86),
    (25, 811, 1488, -83),
    (26, 816, 1462, -86),
    (27, 808, 1452, -87),
    (28, 820, 1437, -86)

]
# /////////////////////////////////////
# Врядли стоит менять под себя
CHARGEX_REGEX = re.compile(r"Charges:\s+(\d+)")
RUNEBOOK_CHARGES_MAX = 32
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
REAGENTS = {
    0X0F7A: "Black pearl",
    0x0F7B: "Blood moss",
    0x0F86: "Mandrake roots",
    0x1F4C: "Recall scrolls"
}

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

def find_gump(gump_id: int) -> bool:
    for _gump in range(0, GetGumpsCount()):
        if GetGumpID(_gump) == gump_id:
            return True
    return False


def close_gump(gump_id: int):
    for _gump in range(0, GetGumpsCount()):
        if GetGumpID(_gump) == gump_id:
            CloseSimpleGump(_gump)


def open_password_chest():
    if IsObjectExists(RESOURCE_CHEST):
        UseObject(RESOURCE_CHEST)
        Wait(1000)
        if find_gump(RESOURCE_CHEST_GUMP_ID):
            GumpAutoTextEntry(3, RESOURCE_CHEST_PASSWORD)
            Wait(500)
            WaitGump(4)
            Wait(1000)
            close_gump(RESOURCE_CHEST_GUMP_ID)
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
    _prev_last_tree = (0, trees[0][1], trees[0][2])

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


def unload():
    statistics()
    if FindType(LOGS, Backpack()):
        for _log in GetFindedList():
            MoveItem(_log, 0, RESOURCE_CHEST, 0, 0, 0)
            Wait(500)
    Wait(500)
    refill_reagents()


def cancel_targets():
    CancelWaitTarget()
    if TargetPresent():
        CancelTarget()


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
                #
                # if Weight() > 100:
                if Weight() > MaxWeight() - 10:
                    recall(RUNEBOOK_RUNE_HOME)
                    open_password_chest()
                    recall(RUNEBOOK_RUNE_SPOT)
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
recall(RUNEBOOK_RUNE_SPOT)
# sorted_trees_array = get_sorted_trees()
# sorted_trees_array = remove_duplicates(populate_trees_array())
while not Dead():
    for point in POINTS:
        (_, x, y, z) = point
        NewMoveXY(x, y, True, 0, True)
        lumberjacking(find_tiles(GetX(Self()), GetY(Self()), 20))
        Wait(1000)

SetARStatus(False)
Disconnect()
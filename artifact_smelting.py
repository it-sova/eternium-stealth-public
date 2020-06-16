from py_stealth import *
from datetime import timedelta, datetime as dt

# Type of bag ( on ground )
BAG_TYPE = 0x0E75
# Type of forge
FORGE_TYPE = 0x0FB1
# Container to unload ( serial )
UNLOAD_CONTAINER = 0x40033F0B
# What types to unload
UNLOAD_TYPES = [0x1BEF]
# Seconds
DELAY = 10 * 1000


def full_disconnect():
    print("Disconnected")
    SetARStatus(False)
    Disconnect()

def find_forges() -> list:
    _forges = []
    if FindType(FORGE_TYPE, Ground()):
        _forges = GetFoundList()
    else:
        print("No forges found, exiting")
        full_disconnect()

    print(f"Found {len(_forges)} forges")
    return _forges


def find_bags() -> list:
    _bags = []
    if FindType(BAG_TYPE, Ground()):
        _bags = GetFoundList()
    else:
        print("No bags on ground found, exiting")
        full_disconnect()

    print(f"Found {len(_bags)} bags on ground")
    return _bags


def find_items(bags: list) -> list:
    _items = []
    for _bag in bags:
        UseObject(_bag)
        Wait(1000)
        if FindType(-1, _bag):
            _items += GetFoundList()

    print(f"Found {len(_items)} items in bags")
    return _items


def smelt(item_serial: int, forge_serial: int):
    _start_time = dt.now()
    WaitTargetObject(item_serial)
    UseObject(forge_serial)
    WaitJournalLine(_start_time, "В сумке появились|Попытка", 20000)


def unload():
    for _item_type in UNLOAD_TYPES:
        if FindType(_item_type, Backpack()):
            for _item_serial in GetFoundList():
                MoveItem(_item_serial, 0, UNLOAD_CONTAINER, 0, 0 ,0)
                Wait(1000)

# Starting...
SetARStatus(True)
SetWarMode(False)
UseObject(UNLOAD_CONTAINER)
Wait(1000)
#


bags = find_bags()
forges = find_forges()
items = find_items(bags)

while len(items) > 0:
    for forge in forges:
        smelt(items[0], forge)
        items.pop(0)

    unload()
    print("Waiting...")
    Wait(DELAY)

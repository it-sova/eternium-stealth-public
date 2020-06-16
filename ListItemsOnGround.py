from py_stealth import *

if FindType(-1, Ground()):
    for _item_id in GetFoundList():
        # print(f"{GetName(_item_id)}: {Count(_item_id)}")
        print(GetTooltip(_item_id))
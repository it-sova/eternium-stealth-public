from py_stealth import *


class Helpers:

    @staticmethod
    def cancel_targets():
        CancelWaitTarget()
        if TargetPresent():
            CancelTarget()

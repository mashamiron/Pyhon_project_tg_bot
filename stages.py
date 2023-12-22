from enum import Enum


class Stages(Enum):
    NOT_FOUND = -1
    STARTED = 1
    MENU = 2
    ADDING = 3
    DELETE = 4
    CHECKING_RECIPIES = 5

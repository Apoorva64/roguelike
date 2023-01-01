from enum import Enum


class PlayerStatus(Enum):
    IDLE = 0
    WALKING = 1
    DASH = 2


class EnemyStatus(Enum):
    IDLE = 0
    WALKING = 1
    DASH = 2
    ATTACKING = 3


class ObjectType(Enum):
    """Base Enum for all objects"""
    EMPTY = 'empty'
    GROUND = 'ground'
    BORDER = 'border'
    PLAYER = 22
    ENEMY = 33
    BULLET = 44
    CHEST = 'chest'

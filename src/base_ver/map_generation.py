# Rogue V3 (c) Pascal URSO, Polytech, 2020
import random
import numpy as np
# from matrix_doubler import doubler
# import matplotlib.pyplot as plt

from base_ver.rogue5 import Map as RogueMap
from base_ver.rogue5 import Room as RogueRoom
from base_ver.rogue5 import Coord, Element, Hero


# from map_generation import CHUNK_SIZE,block_shaped


def getch():
    """Single char input, only works only on mac/linux/windows OS terminals"""
    try:
        import termios
        # POSIX system. Create and return a getch that manipulates the tty.
        import sys, tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch().decode('utf-8')


def sign(x):
    if x > 0:
        return 1
    return -1


# class Coord(object):
#     """Implementation of a game_map coordinate <x,y>"""
#
#     def __init__(self, x, y):
#         self.x = x
#         self.y = y
#
#     def __eq__(self, other):
#         return self.x == other.x and self.y == other.y
#
#     def __repr__(self):
#         return '<' + str(self.x) + ',' + str(self.y) + '>'
#
#     def __add__(self, other):
#         return Coord(self.x + other.x, self.y + other.y)
#
#     def __sub__(self, other):
#         return Coord(self.x - other.x, self.y - other.y)
#
#
# class Element(object):
#     """Base class for game elements.
#         Has a name."""
#
#     def __init__(self, name, abbrv=""):
#         self.name = name
#         if abbrv == "":
#             abbrv = name[0]
#         self.abbrv = abbrv
#
#     def __repr__(self):
#         return self.abbrv
#
#     def description(self):
#         """Description of the element"""
#         return "<" + self.name + ">"
#
#     def meet(self, hero):
#         """Makes the hero meet an element. The hero takes the element."""
#         hero.take(self)
#         return True
#
#
# class Creature(Element):
#     """A creature that occupies the dungeon.
#         Is an Element. Has hit points and strength."""
#
#     def __init__(self, name, hp, abbrv="", strength=1):
#         Element.__init__(self, name, abbrv)
#         self.hp = hp
#         self.strength = strength
#
#     def description(self):
#         """Description of the creature"""
#         return Element.description(self) + "(" + str(self.hp) + ")"
#
#     def meet(self, hero):
#         """The creature is encountered by the hero.
#             The hero hits the creature, if alive the creature strikes back."""
#         self.hp -= hero.strength
#         if self.hp > 0:
#             hero.hp -= self.strength
#             return False
#         return True
#
#
# class Hero(Creature):
#     """The hero of the game.
#         Is a creature. Has an inventory of elements. """
#
#     def __init__(self, name="Hero", hp=10, abbrv="@", strength=2):
#         Creature.__init__(self, name, hp, abbrv, strength)
#         self._inventory = []
#
#     def description(self):
#         """Description of the hero"""
#         return Creature.description(self) + str(self._inventory)
#
#     def take(self, elem):
#         """The hero takes adds the element to its inventory"""
#         self._inventory.append(elem)
#
#
class Room(RogueRoom):
    # """A rectangular room in the game_map"""
    #
    # def __init__(self, c1, c2):
    #     self.c1 = c1
    #     self.c2 = c2
    #
    # def __repr__(self):
    #     return "[" + str(self.c1) + ", " + str(self.c2) + "]"
    #
    # def __contains__(self, coord):
    #     return self.c1.x <= coord.x <= self.c2.x and self.c1.y <= coord.y <= self.c2.y
    #
    # def intersect(self, other):
    #     """Test if the room has an intersection with another room"""
    #     sc3 = Coord(self.c2.x, self.c1.y)
    #     sc4 = Coord(self.c1.x, self.c2.y)
    #     return self.c1 in other or self.c2 in other or sc3 in other or sc4 in other or other.c1 in self
    def randCoord(self):
        """A random coordinate inside the room"""
        return Coord(random.randint(self.c1.x, self.c2.x), random.randint(self.c1.y, self.c2.y))

    def randEmptyCoord(self, map):
        """A random coordinate inside the room which is free on the map."""
        c = self.randCoord()
        while map.get(c) != Map.ground or c == self.center():
            c = self.randCoord()
        return c

    def decorate(self, map, level):
        """Decorates the room by adding a random equipment and monster."""
        for loop in range(int(self.get_size() / 40) + 1):
            c = self.randEmptyCoord(map)
            # random element
            map._mat[c.y][c.x] = random.expovariate(1 / level) + 100
            # random equipment
            c = self.randEmptyCoord(map)
            map._mat[c.y][c.x] = random.expovariate(1 / level) + 1000

    def is_border(self, coord):
        if coord.x == self.c1.x or coord.x == self.c2.x or coord.y == self.c1.y or coord.y == self.c2.y:
            return True
        else:
            return False

    def center(self):
        """Returns the coordinates of the room center"""
        return Coord((self.c1.x + self.c2.x) // 2, (self.c1.y + self.c2.y) // 2)

    def get_size(self):
        return abs(self.c1.x - self.c2.x) + abs(self.c1.y - self.c2.y)


class Map(RogueMap):
    """A game_map of a game floor.
        Contains game elements."""

    ground = 4  # A walkable ground cell
    border = 0
    # dir = {'z': Coord(0, -1), 's': Coord(0, 1), 'd': Coord(1, 0), 'q': Coord(-1, 0)}  # four direction user keys
    empty = 10  # A non walkable cell

    def __init__(self, game,size=20, hero=None, rooms=7):
        self._mat = []
        self._elem = {}
        for i in range(size):
            self._mat.append([Map.empty] * size)

        self.game = game
        self._rooms = []
        self._roomsToReach = []
        pygame=game.pygame
        font=game.font
        screen=game.base_display
        rect=screen.get_rect()
        img = font.render(f"Generating Base Map", True, (255, 255, 255))
        screen.fill((0, 0, 0))
        img_rect = img.get_rect()
        img_rect.center = rect.center
        screen.blit(img, img_rect)
        pygame.event.get()
        pygame.display.flip()
        self.generateRooms(rooms)
        self.reachAllRooms(2)
        if hero is None:
            hero = Hero()
        self.hero = hero
        self.size = size
        level = 1
        for r in self._rooms:
            r.decorate(self, level)
        # c = self._rooms[0].center()
        # self._mat[c.y][c.x] = 50000

    def get_map(self):
        return self._mat

    def get_border_room(self):
        lowest_size = 100000
        lowest_room = None
        highest_size = 0
        highest_room = None

        for room in self._rooms:
            if room.get_size() < lowest_size:
                lowest_size = room.get_size()
                lowest_room = room
            if room.get_size() > highest_size:
                highest_size = room.get_size()
                highest_room = room
        return lowest_room, highest_room

    def addRoom(self, room):
        """Adds a room in the game_map."""
        self._roomsToReach.append(room)
        for y in range(room.c1.y, room.c2.y + 1):
            for x in range(room.c1.x, room.c2.x + 1):
                if self._mat[y][x] == Map.empty:
                    if y == room.c1.y or x == room.c1.x or y == room.c2.y or x == room.c2.x:
                        self._mat[y][x] = Map.border
                    else:
                        self._mat[y][x] = Map.ground

    def findRoom_all(self, coord):
        for r in self._roomsToReach:
            if coord in r and not r.is_border(coord):
                return True
        for r in self._rooms:
            if coord in r and not r.is_border(coord):
                return True
        return False

    def dig(self, coord, border=False):
        """Puts a ground cell at the given coord.
            If the coord corresponds to a room, considers the room reached."""
        if not self.findRoom_all(coord) and self._mat[coord.y][coord.x] != Map.ground:
            if border:
                self._mat[coord.y][coord.x] = Map.border
            else:
                self._mat[coord.y][coord.x] = Map.ground
        r = self.findRoom(coord)
        if r:
            self._roomsToReach.remove(r)
            self._rooms.append(r)

    def corridor(self, start, end, border_size, ground_size):
        """Digs a corridors from the coordinates cursor to the end, first vertically, then horizontally."""
        cursor = Coord(start.x, start.y)
        d = end - cursor
        self.dig(cursor)
        border_size = border_size + ground_size
        cursor.y += border_size * -sign(d.y)
        while cursor.y != end.y:
            cursor = cursor + Coord(0, sign(d.y))
            for loop in range(border_size):
                self.dig(cursor - Coord(loop, 0), border=True)
                self.dig(cursor + Coord(loop, 0), border=True)

        cursor.x += border_size * -sign(d.x)
        while cursor.x != end.x + sign(d.x):
            cursor = cursor + Coord(sign(d.x), 0)
            for loop in range(border_size):
                self.dig(cursor - Coord(0, loop), border=True)
                self.dig(cursor + Coord(0, loop), border=True)

        size = ground_size
        cursor = start
        d = end - cursor
        self.dig(cursor)
        cursor.y += size * -sign(d.y)
        while cursor.y != end.y:
            cursor = cursor + Coord(0, sign(d.y))
            for loop in range(size):
                self.dig(cursor - Coord(loop, 0), )
                self.dig(cursor + Coord(loop, 0), )
            self.dig(cursor)
        cursor.x += size * -sign(d.x)
        while cursor.x != end.x:
            cursor = cursor + Coord(sign(d.x), 0)
            for loop in range(size):
                self.dig(cursor - Coord(0, loop), )
                self.dig(cursor + Coord(0, loop), )
            self.dig(cursor)

    def reach(self, corridor_size):
        """Makes more rooms reachable.
            Start from one random reached room, and dig a corridor to an unreached room."""
        # print(self._roomsToReach)
        roomA = random.choice(self._rooms)
        roomB = random.choice(self._roomsToReach)
        self.corridor(roomA.center(), roomB.center(), 1, corridor_size + 1)

    def reachAllRooms(self, corridor_size):
        """Makes all rooms reachable.
            Start from the first room, repeats @reach until all rooms are reached."""
        self._rooms.append(self._roomsToReach.pop(0))
        while len(self._roomsToReach) > 0:
            self.reach(corridor_size)

    def randRoom(self, room_size_x=10, room_size_y=100):
        """A random room to be put on the game_map."""
        c1 = Coord(random.randint(0, len(self) - room_size_x), random.randint(0, len(self) - room_size_x))
        c2 = Coord(min(c1.x + random.randint(room_size_x, room_size_y), len(self) - 1),
                   min(c1.y + random.randint(room_size_x, room_size_y), len(self) - 1))
        return Room(c1, c2)

    # def generateRooms(self, n):
    #     """Generates n random rooms and adds them if non-intersecting."""
    #     for i in range(n):
    #         r = self.randRoom()
    #         if self.intersectNone(r):
    #             self.addRoom(r)
    #
    # def __len__(self):
    #     return len(self._mat)
    #
    # def __contains__(self, item):
    #     if isinstance(item, Coord):
    #         return 0 <= item.x < len(self) and 0 <= item.y < len(self)
    #     return item in self._elem
    #
    # def __repr__(self):
    #     s = ""
    #     for i in self._mat:
    #         for j in i:
    #             s += str(j)
    #         s += '\n'
    #     return s
    #
    # def checkCoord(self, c):
    #     if not isinstance(c, Coord):
    #         raise TypeError('Not a Coord')
    #     if c not in self:
    #         raise IndexError('Out of game_map coord')
    #
    # def checkElement(self, e):
    #     if not isinstance(e, Element):
    #         raise TypeError('Not a Element')
    #
    # def put(self, c: Coord, o: Element) -> None:
    #     """Puts an element o on the cell c"""
    #     self.checkCoord(c)
    #     self.checkElement(o)
    #     if self.get(c) != Map.ground:
    #         raise ValueError('Incorrect cell')
    #
    #     if self.pos(o) is not None:
    #         raise KeyError('Already placed')
    #
    #     self._mat[c.y][c.x] = o
    #     self._elem[o] = c


# random.seed(1829481465724978)
# np.set_printoptions(threshold=np.inf)
# game_map_object = Map(size=100, rooms=30)
# game_map = game_map_object._mat
# game_map = np.array(game_map)
# print(game_map)
#
# plt.imshow(game_map, interpolation='nearest')
# plt.show()


def block_shaped(arr, chunk_size_y, chunk_size_x):
    """
    https://stackoverflow.com/questions/16856788/slice-2d-array-into-smaller-2d-arrays
    Return an array of shape (n, chunk_size_y, chunk_size_x) where
    n * chunk_size_y * chunk_size_x = arr.size

    If arr is a 2D array, the returned array should look like n subblocks with
    each subblock preserving the "physical" layout of arr.
    """
    h, w = arr.shape
    assert h % chunk_size_y == 0, "{} rows is not evenly divisible by {}".format(h, chunk_size_y)
    assert w % chunk_size_x == 0, "{} cols is not evenly divisible by {}".format(w, chunk_size_x)
    return (arr.reshape(h // chunk_size_y, chunk_size_y, -1, chunk_size_x)
            .swapaxes(1, 2)
            .reshape(-1, chunk_size_y, chunk_size_x))

# list_arr = block_shaped(game_map, 10, 10)
# np.save(f'block_map{game_map_object.size}', list_arr)

# Rogue V3 (c) Pascal URSO, Polytech, 2020
import random
import copy

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


class Coord(object):
    """Implementation of a map coordinate <x,y>"""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return '<' + str(self.x) + ',' + str(self.y) + '>'

    def __add__(self, other):
        return Coord(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Coord(self.x - other.x, self.y - other.y)


class Element(object):
    """Base class for game elements.
        Has a name."""

    def __init__(self, name, abbrv=""):
        self.name = name
        if abbrv == "":
            abbrv = name[0]
        self.abbrv = abbrv

    def __repr__(self):
        return self.abbrv

    def description(self):
        """Description of the element"""
        return "<" + self.name + ">"

    def meet(self, hero):
        raise NotImplementedError('Not implemented yet')


class Equipment(Element):
    def __init__(self, name, abbrv=''):
        super().__init__(name, abbrv=abbrv)

    def meet(self, hero):
        """Makes the hero meet an element. The hero takes the element."""
        hero.take(self)
        theGame().addMessage(f"You pick up a {self.name}")
        return True


class Creature(Element):
    """A creature that occupies the dungeon.
        Is an Element. Has hit points and strength."""

    def __init__(self, name, hp, abbrv="", strength=1):
        Element.__init__(self, name, abbrv)
        self.hp = hp
        self.strength = strength

    def description(self):
        """Description of the creature"""
        return Element.description(self) + "(" + str(self.hp) + ")"

    def meet(self, hero):
        """The creature is encountered by the hero.
            The hero hits the creature, if alive the creature strikes back."""
        self.hp -= hero.strength
        theGame().addMessage(f"The {hero.name} hits the {self.description()}")

        if self.hp > 0:
            hero.hp -= self.strength
            theGame().addMessage(
                f"The {self.name} hits the {hero.description()}")
            return False

        return True


class Hero(Creature):
    """The hero of the game.
        Is a creature. Has an inventory of elements. """

    def __init__(self, name="Hero", hp=10, abbrv="@", strength=2):
        Creature.__init__(self, name, hp, abbrv, strength)
        self._inventory = []

    def description(self):
        """Description of the hero"""
        return Creature.description(self) + str(self._inventory)

    def take(self, elem):
        """The hero takes adds the element to its inventory"""
        if isinstance(elem, Equipment):
            self._inventory.append(elem)
        else:
            raise TypeError(f'{elem} not an equipment')


class Room(object):
    """A rectangular room in the map"""

    def __init__(self, c1, c2):
        self.c1 = c1
        self.c2 = c2

    def __repr__(self):
        return "[" + str(self.c1) + ", " + str(self.c2) + "]"

    def __contains__(self, coord):
        return self.c1.x <= coord.x <= self.c2.x and self.c1.y <= coord.y <= self.c2.y

    def intersect(self, other):
        """Test if the room has an intersection with another room"""
        sc3 = Coord(self.c2.x, self.c1.y)
        sc4 = Coord(self.c1.x, self.c2.y)
        return self.c1 in other or self.c2 in other or sc3 in other or sc4 in other or other.c1 in self

    def center(self):
        """Returns the coordinates of the room center"""
        return Coord((self.c1.x + self.c2.x) // 2, (self.c1.y + self.c2.y) // 2)

    def randCoord(self):
        x = random.randint(self.c1.x, self.c2.x)
        y = random.randint(self.c1.y, self.c2.y)
        return Coord(x, y)

    def randEmptyCoord(self, floor):
        coord = self.randCoord()
        while floor.get(coord) != Map.ground or coord == self.center():
            coord = self.randCoord()
        return coord

    def decorate(self, floor):
        pos_one = self.randEmptyCoord(floor)
        equip = theGame().randEquipment()
        floor.put(pos_one, equip)

        pos_two = self.randEmptyCoord(floor)
        monster = theGame().randMonster()
        floor.put(pos_two, monster)


class Map:
    ground = "."
    empty = " "
    dir = {
        "z": Coord(0, -1),
        "s": Coord(0, 1),
        "d": Coord(1, 0),
        "q": Coord(-1, 0)
    }

    def __init__(self, size=20, hero=None, nbrooms=7):
        if hero is None:
            hero = Hero()

        self._mat = [[Map.empty for _ in range(size)] for _ in range(size)]
        self._elem = {}
        self._roomsToReach = []
        self._rooms = []
        self.hero = hero

        self.generateRooms(nbrooms)
        self.reachAllRooms()

        start = self._rooms[0].center()
        self.put(start, self.hero)
        for room in self._rooms:
            room.decorate(self)

    def __repr__(self):
        res = ""
        for line in self._mat:
            res += ''.join(str(e) for e in line) + '\n'
        return res

    def __len__(self):
        return len(self._mat)

    def __contains__(self, item):
        if isinstance(item, Coord):
            return self.filled_pos(item)

        return item in self._elem

    def __getitem__(self, key):
        return self._get_or_pos(key)

    def __setitem__(self, key, value):
        if isinstance(key, Coord):
            self.put(key, value)

        self._put_or_move(key, value)

    def __delitem__(self, item):
        self.rm(item)

    def _get_or_pos(self, key):
        if isinstance(key, Coord):
            return self.get(key)

        return self.pos(key)

    def _put_or_move(self, e, pos):
        if e in self._elem:
            self.move(e, pos)
        else:
            self.put(pos, e)

    def valid_pos(self, pos):
        return pos.x in range(len(self)) and pos.y in range(len(self))

    def filled_pos(self, pos):
        empty = self.get(pos) == Map.empty
        return not empty and self.valid_pos(pos)

    def checkCoord(self, pos):
        if not isinstance(pos, Coord):
            raise TypeError("Not a Coord")

        if not self.valid_pos(pos):
            raise IndexError("Out of map coord")

    def checkElement(self, e):
        if not isinstance(e, Element):
            raise TypeError("Not a Element")

    def get(self, pos):
        self.checkCoord(pos)
        return self._mat[pos.y][pos.x]

    def pos(self, e):
        self.checkElement(e)
        return self._elem[e]

    def put(self, pos, e):
        self.checkCoord(pos)
        self.checkElement(e)

        val = self._mat[pos.y][pos.x]
        if val != Map.ground:
            raise ValueError("Incorrect cell")

        for l in self._mat:
            for obj in l:
                if obj is e:
                    raise KeyError("Already placed")

        self._elem[e] = pos
        self._mat[pos.y][pos.x] = e

    def rm(self, pos):
        e = self.get(pos)
        del self._elem[e]
        self._mat[pos.y][pos.x] = Map.ground

    def move(self, e, way):
        orig = self.pos(e)
        dest = orig + way
        if not self.filled_pos(dest):
            return
        dest_item = self.get(dest)
        if dest_item != Map.ground:
            if dest_item.meet(e):
                self.rm(dest)
        else:
            self.rm(orig)
            self.put(dest, e)

    def play(self):
        print("--- Welcome Hero! ---")
        while self.hero.hp > 0:
            print()
            print(self)
            print(self.hero.description())
            self.move(self.hero, Map.dir[getch()])
        print("--- Game Over ---")

    def addRoom(self, room):
        self._roomsToReach.append(room)
        for x in range(room.c1.x, room.c2.x + 1):
            for y in range(room.c1.y, room.c2.y + 1):
                self._mat[y][x] = Map.ground

    def findRoom(self, coord):
        for r in self._roomsToReach:
            if coord in r:
                return r
        return False

    def intersectNone(self, room):
        return not any(room.intersect(r) for r in self._roomsToReach)

    def dig(self, coord):
        self._mat[coord.y][coord.x] = Map.ground
        r = self.findRoom(coord)
        if r:
            self._roomsToReach.remove(r)
            self._rooms.append(r)

    def corridor(self, start, end):
        starty = min(start.y, end.y)
        startx = min(start.x, end.x)
        endy = max(start.y, end.y)
        endx = max(start.x, end.x)

        for y in range(starty, endy + 1):
            self.dig(Coord(start.x, y))

        for x in range(startx, endx + 1):
            self.dig(Coord(x, end.y))

    def reach(self):
        start = random.choice(self._rooms).center()
        end = random.choice(self._roomsToReach).center()
        self.corridor(start, end)

    def reachAllRooms(self):
        self._rooms.append(self._roomsToReach.pop(0))
        while len(self._roomsToReach):
            self.reach()

    def randRoom(self):
        x1 = random.randint(0, len(self) - 3)
        y1 = random.randint(0, len(self) - 3)

        largeur = random.randint(3, 8)
        hauteur = random.randint(3, 8)

        x2 = min((len(self) - 1), (x1 + largeur))
        y2 = min((len(self) - 1), (y1 + hauteur))

        return Room(Coord(x1, y1), Coord(x2, y2))

    def generateRooms(self, n):
        for _ in range(n):
            room = self.randRoom()
            if self.intersectNone(room):
                self.addRoom(room)


class Game:
    equipments = {0: [Equipment("potion", "!"), Equipment("gold", "o")],
                  1: [Equipment("sword"), Equipment("bow")],
                  2: [Equipment("chainmail")]}
    monsters = {0: [Creature("Goblin", 4), Creature("Bat", 2, "W")],
                1: [Creature("Ork", 6, strength=2), Creature("Blob", 10)],
                5: [Creature("Dragon", 20, strength=3)]}

    def __init__(self, hero=None, level=1, floor=None):
        if hero:
            self.hero = hero
        else:
            self.hero = Hero()
        self.level = level
        self.floor = floor
        self._message = []

    def buildFloor(self, *args, **kwargs):
        self.floor = Map(*args, **kwargs, hero=self.hero)

    def addMessage(self, msg):
        self._message.append(msg)

    def readMessages(self):
        string = '. '.join(self._message)
        if string != '':
            string += '. '
        self._message.clear()
        return string

    def randElement(self, collection):
        x = random.expovariate(1 / self.level)
        i = max(k for k in collection if k <= x)
        return copy.copy(random.choice(collection[i]))

    def randEquipment(self):
        return self.randElement(Game.equipments)

    def randMonster(self):
        return self.randElement(Game.monsters)


def theGame(game=Game()):
    return game

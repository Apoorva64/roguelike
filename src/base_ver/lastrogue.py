import copy
import math
import random


# exceptions


def _find_getch():
    """Single char input, only works only on mac/linux/windows OS terminals"""
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty

    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch


def sign(x):
    if x > 0:
        return 1
    return -1


def heal(creature):
    creature.hp += 3
    return True


def teleport(creature, unique):
    current_pos = theGame().floor.pos(creature)
    end_pos = theGame().floor.get_random_room().randEmptyCoord(theGame().floor)
    way = end_pos - current_pos
    theGame().floor.move(creature, way)
    if unique and isinstance(creature, Hero):
        for item in creature.get_inventory():
            if item.usage == teleport:
                creature.get_inventory().remove(item)
                break
    return unique


class Coord(object):
    """Implementation of a map coordinate"""

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

    def distance(self, other):
        return math.sqrt((other.x - self.x) ** 2 + (other.y - self.y) ** 2)

    def module(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def direction(self, other):
        d = self - other
        cos = d.x / math.sqrt(math.pow(d.x, 2) + math.pow(d.y, 2))
        if cos > 1 / math.sqrt(2):
            return Coord(-1, 0)
        elif cos < -1 / math.sqrt(2):
            return Coord(1, 0)
        elif d.y > 0:
            return Coord(0, -1)
        else:
            return Coord(0, 1)


class Element(object):
    """Base class for game elements. Have a name.
        Abstract class."""

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
        """Makes the hero meet an element. Not implemented. """
        raise NotImplementedError('Abstract Element')


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
        theGame().addMessage("The " + hero.name + " hits the " + self.description())
        if self.hp > 0:
            # theGame().addMessage("The " + self.name + " hits the " + hero.description())
            # # hero.hp -= self.strength
            return False
        return True


class Hero(Creature):
    """The hero of the game.
        Is a creature. Has an inventory of elements. """

    def __init__(self, name="Hero", hp=10, abbrv="@", strength=2):
        Creature.__init__(self, name, hp, abbrv, strength)
        self._inventory = []
        self._message = []

    def description(self):
        """Description of the hero"""
        return Creature.description(self) + str(self._inventory)

    def use(self, item):
        if not isinstance(item, Equipment):
            raise TypeError
        if item not in self._inventory:
            raise ValueError
        if item.use(self):
            self._inventory.remove(item)

    def get_inventory(self):
        return self._inventory

    def take(self, elem):
        """The hero takes adds the equipment to its inventory"""
        if not isinstance(elem, Equipment):
            raise TypeError('Not a Equipment')
        self._inventory.append(elem)

    def fullDescription(self):
        string = ''
        for key, item in self.__dict__.items():
            if "_" not in key:
                string += f'> {key} : {item}\n'
        string += f'> INVENTORY : {[x.name for x in self._inventory]}'
        return string


class Equipment(Element):
    def __init__(self, name, abbrv="", usage=None):
        Element.__init__(self, name, abbrv)
        self.usage = usage

    def use(self, creature):
        if self.usage:
            theGame().addMessage(f"The {creature.name} uses the {self.name}")
            return self.usage(self, creature)
        theGame().addMessage(f"The {self.name} is not usable")
        return False

    def meet(self, hero):
        """Makes the hero meet an element. The hero takes the element."""
        hero.take(self)
        theGame().addMessage("You pick up a " + self.name)
        return True


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
        """A random coordinate inside the room"""
        return Coord(random.randint(self.c1.x, self.c2.x), random.randint(self.c1.y, self.c2.y))

    def randEmptyCoord(self, map):
        """A random coordinate inside the room which is free on the map."""
        c = self.randCoord()
        while map.get(c) != Map.ground or c == self.center():
            c = self.randCoord()
        return c

    def decorate(self, map):
        """Decorates the room by adding a random equipment and monster."""
        map.put(self.randEmptyCoord(map), theGame().randEquipment())
        map.put(self.randEmptyCoord(map), theGame().randMonster())


class Map(object):
    """A map of a game floor.
        Contains game elements."""

    ground = '.'  # A walkable ground cell
    dir = {'z': Coord(0, -1), 's': Coord(0, 1), 'd': Coord(1, 0), 'q': Coord(-1, 0)}  # four direction user keys
    empty = ' '  # A non walkable cell

    def __init__(self, size=20, hero=None):
        self._mat = []
        self._elem = {}
        self._rooms = []
        self._roomsToReach = []

        for i in range(size):
            self._mat.append([Map.empty] * size)
        if hero is None:
            hero = Hero()
        self.hero = hero
        self.generateRooms(7)
        self.reachAllRooms()
        self.put(self._rooms[0].center(), hero)
        for r in self._rooms:
            r.decorate(self)

    def get_random_room(self):
        return random.choice(self._rooms)

    def moveAllMonsters(self):
        hero_pos = self.pos(self.hero)
        for item, position in self._elem.items():
            if isinstance(item, Creature):
                if item.name != 'Hero':
                    if position.distance(hero_pos) < 6:
                        self.move(item, position.direction(hero_pos))

    def addRoom(self, room):
        """Adds a room in the map."""
        self._roomsToReach.append(room)
        for y in range(room.c1.y, room.c2.y + 1):
            for x in range(room.c1.x, room.c2.x + 1):
                self._mat[y][x] = Map.ground

    def findRoom(self, coord):
        """If the coord belongs to a room, returns the room elsewhere returns None"""
        for r in self._roomsToReach:
            if coord in r:
                return r
        return None

    def intersectNone(self, room):
        """Tests if the room shall intersect any room already in the map."""
        for r in self._roomsToReach:
            if room.intersect(r):
                return False
        return True

    def dig(self, coord):
        """Puts a ground cell at the given coord.
            If the coord corresponds to a room, considers the room reached."""
        self._mat[coord.y][coord.x] = Map.ground
        r = self.findRoom(coord)
        if r:
            self._roomsToReach.remove(r)
            self._rooms.append(r)

    def corridor(self, cursor, end):
        """Digs a corridors from the coordinates cursor to the end, first vertically, then horizontally."""
        d = end - cursor
        self.dig(cursor)
        while cursor.y != end.y:
            cursor = cursor + Coord(0, sign(d.y))
            self.dig(cursor)
        while cursor.x != end.x:
            cursor = cursor + Coord(sign(d.x), 0)
            self.dig(cursor)

    def reach(self):
        """Makes more rooms reachable.
            Start from one random reached room, and dig a corridor to an unreached room."""
        roomA = random.choice(self._rooms)
        roomB = random.choice(self._roomsToReach)

        self.corridor(roomA.center(), roomB.center())

    def reachAllRooms(self):
        """Makes all rooms reachable.
            Start from the first room, repeats @reach until all rooms are reached."""
        self._rooms.append(self._roomsToReach.pop(0))
        while len(self._roomsToReach) > 0:
            self.reach()

    def randRoom(self):
        """A random room to be put on the map."""
        c1 = Coord(random.randint(0, len(self) - 3), random.randint(0, len(self) - 3))
        c2 = Coord(min(c1.x + random.randint(3, 8), len(self) - 1), min(c1.y + random.randint(3, 8), len(self) - 1))
        return Room(c1, c2)

    def generateRooms(self, n):
        """Generates n random rooms and adds them if non-intersecting."""
        for i in range(n):
            r = self.randRoom()
            if self.intersectNone(r):
                self.addRoom(r)

    def __len__(self):
        return len(self._mat)

    def __contains__(self, item):
        if isinstance(item, Coord):
            return 0 <= item.x < len(self) and 0 <= item.y < len(self)
        return item in self._elem

    def __repr__(self):
        s = ""
        for i in self._mat:
            for j in i:
                s += str(j)
            s += '\n'
        return s

    def checkCoord(self, c):
        """Check if the coordinates c is valid in the map."""
        if not isinstance(c, Coord):
            raise TypeError('Not a Coord')
        if not c in self:
            raise IndexError('Out of map coord')

    def checkElement(self, o):
        """Check if o is an Element."""
        if not isinstance(o, Element):
            raise TypeError('Not a Element')

    def put(self, c, o):
        """Puts an element o on the cell c"""
        self.checkCoord(c)
        self.checkElement(o)
        if self._mat[c.y][c.x] != Map.ground:
            raise ValueError('Incorrect cell')
        if o in self._elem:
            raise KeyError('Already placed')
        self._mat[c.y][c.x] = o
        self._elem[o] = c

    def get(self, c):
        """Returns the object present on the cell c"""
        self.checkCoord(c)
        return self._mat[c.y][c.x]

    def pos(self, o):
        """Returns the coordinates of an element in the map """
        self.checkElement(o)
        return self._elem[o]

    def rm(self, c):
        """Removes the element at the coordinates c"""
        self.checkCoord(c)
        del self._elem[self._mat[c.y][c.x]]
        self._mat[c.y][c.x] = Map.ground

    # def move(self, e, way):
    #     """Moves the element e in the direction way"""
    #     orig = self.pos(e)
    #     dest = orig + way
    #     if dest in self:
    #         if self.get(dest) == Map.ground:
    #             self._mat[orig.y][orig.x] = Map.ground
    #             self._mat[dest.y][dest.x] = e
    #             self._elem[e] = dest
    #         elif self.get(dest) != Map.empty and self.get(dest).meet(e):
    #             self.rm(dest)
    def move(self, e, way):
        """Moves the element e in the direction way."""
        orig = self.pos(e)
        dest = orig + way
        if dest in self:
            if self.get(dest) == Map.ground:
                self._mat[orig.y][orig.x] = Map.ground
                self._mat[dest.y][dest.x] = e
                self._elem[e] = dest
            elif self.get(dest) != Map.empty and self.get(dest).meet(e) and self.get(dest) != self.hero:
                self.rm(dest)


class Game(object):
    """ Class representing game state """

    """ available equipments """
    equipments = {0: [Equipment("potion", "!", usage=lambda self, hero: heal(hero)),
                      Equipment("gold", "o")],
                  1: [Equipment("sword"), Equipment("bow"),
                      Equipment("potion", "!", usage=lambda self, hero: teleport(hero, True))],
                  2: [Equipment("chainmail")], 3: [Equipment("portoloin", "w", usage=lambda self, hero: teleport(hero, False))]}
    """ available monsters """
    monsters = {0: [Creature("Goblin", 4), Creature("Bat", 2, "W")],
                1: [Creature("Ork", 6, strength=2), Creature("Blob", 10)], 5: [Creature("Dragon", 20, strength=3)]}

    _actions = {
        'z': lambda hero: theGame().floor.move(hero, Coord(0, -1)),
        's': lambda hero: theGame().floor.move(hero, Coord(0, 1)),
        'q': lambda hero: theGame().floor.move(hero, Coord(-1, 0)),
        'd': lambda hero: theGame().floor.move(hero, Coord(1, 0)),
        'i': lambda hero: theGame().addMessage(hero.fullDescription()),
        'k': lambda hero: hero.__setattr__('hp', 0),
        'u': lambda hero: hero.use(theGame().select(hero.get_inventory())),
        ' ': lambda hero: None,

    }

    def __init__(self, level=1, hero=None):
        self.level = level
        self._message = []
        if hero == None:
            hero = Hero()
        self.hero = hero
        self.floor = None

    def buildFloor(self):
        """Creates a map for the current floor."""
        self.floor = Map(hero=self.hero)

    def addMessage(self, msg):
        """Adds a message in the message list."""
        self._message.append(msg)

    def readMessages(self):
        """Returns the message list and clears it."""
        s = ''
        for m in self._message:
            s += m + '. '
        self._message.clear()
        return s

    def randElement(self, collect):
        """Returns a clone of random element from a collection using exponential random law."""
        x = random.expovariate(1 / self.level)
        for k in collect.keys():
            if k <= x:
                l = collect[k]
        return copy.copy(random.choice(l))

    def randEquipment(self):
        """Returns a random equipment."""
        return self.randElement(Game.equipments)

    def randMonster(self):
        """Returns a random monster."""
        return self.randElement(Game.monsters)

    def select(self, l):
        draw_l = l.copy()
        for i, ele in enumerate(draw_l):
            draw_l[i] = f"{i}: {ele.name}"
        print(f"Choose item> {str(draw_l)}")
        try:
            index = int(getch())
        except ValueError:
            return None
        try:
            return l[index]
        except IndexError:
            return None

    def play(self):
        """Main game loop"""
        self.buildFloor()
        print("--- Welcome Hero! ---")
        while self.hero.hp > 0:
            print()
            print(self.floor)
            print(self.hero.description())
            print(self.readMessages())
            c = getch()
            if c == 'p':
                break
            if c in Map.dir:
                self.floor.move(self.hero, Map.dir[c])
            self.floor.moveAllCreatures()
        print("--- Game Over ---")


def theGame(game=Game()):
    """Game singleton"""
    return game


p = list(filter(lambda x: x.name == 'portoloin', Game.equipments[3]))[0]
random.seed(44)
theGame().buildFloor()
h = theGame().hero
p1 = theGame().floor.pos(h)
h.take(p)
print(h.use(p))
print(theGame().hero.description())
print(theGame().readMessages())
p2 = theGame().floor.pos(h)
print(p1.x == p2.x and p2.y == p2.y)
print(theGame().floor.get(p2))

random.seed(44)
theGame().buildFloor()
print(theGame().floor.get(p2))
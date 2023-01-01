import numpy
import numpy as np
import pygame

from typing import Tuple, List
from load_settings import settings
import random

from multiprocessing import Process
import pathfinding_

from bodies import StaticObject, TILE_SIZE, ObjectType, Chest, Enemy, Boss, SucideEnemy
from base_ver.map_generation import Map as BaseMap
from base_ver.map_generation import block_shaped

# from pympler import asizeof
font = pygame.font.SysFont('', 24)
CHUNK_SIZE = settings['map_generation']["CHUNK_SIZE"]
MAP_SIZE = settings['map_generation']["MAP_SIZE"]
# MAP_SIZE = 400
PERLIN_FACTOR = 20
DATA_FOLDER = settings['map_generation']["DATA_FOLDER"]

ground_texture = pygame.image.load(f'{DATA_FOLDER}/animations/enviroment_textures/background/ezgif-frame-001.png')


class Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if isinstance(other, Coord):
            return self.x == other.x and self.y == other.y

    def __add__(self, other):
        if isinstance(other, Coord):
            return Coord(self.x + other.x, self.y + other.y)

    def __repr__(self):
        return f"<{self.x},{self.y}>"


class Map:
    CHUNK_SIZE = CHUNK_SIZE
    MAP_SIZE = MAP_SIZE
    TILE_SIZE = TILE_SIZE

    def __init__(self, game, map_level=0):
        """

        :param game: instance of the game
        """
        # random.seed(settings['map_generation']["seed"])
        self.room_number = settings['map_generation']["rooms"]
        base_map = BaseMap(game, size=MAP_SIZE, rooms=self.room_number)

        self.base_map_object = base_map
        self.base_map = np.array(base_map.get_map())
        self.map_level = map_level

        # game instance
        self.game = game
        # map data
        self._mat = {}
        # things of things to be drawn on map
        self.blit_list = None
        # current surface
        # self.surface = None
        # dict of part of the map rendered
        self.surface_dict = {}
        # elements
        self._elem = {}
        # multiprocessing dictionary to get the path with pathfinding
        self.multiprocessing_dict = game.multiprocessing_dict
        self.multiprocessing_dict['path'] = (())
        self.pathfinding_map = game.pathfinding_map
        self.processes = []
        # elements on the maps to update
        self.current_on_map_elements = []
        # surface to render on
        self.screen = game.screen
        # map for collisions for the bullets
        self.numpy_map = None

        self.enemy_base_coordinates = (0, 0)

        self.surface = pygame.Surface((1, 1))

        # self._mat[pos.y][pos.x] = self.hero
        # self._elem['@'] = self.hero_pos

    def get_map(self):
        return self._mat

    def rebuild_map(self, add_diff=True):
        self.pathfinding_map[0] = []
        for x in range(0, self.MAP_SIZE // CHUNK_SIZE):
            for y in range(0, self.MAP_SIZE // CHUNK_SIZE):
                for enemy in self._mat[(x, y)][ObjectType.ENEMY]:
                    enemy.hp_bar.kill()
        if add_diff:
            self.map_level += settings["map_generation"]["difficulty_increase"]
        # random.seed(1829481465724978)
        del self.base_map_object
        del self.base_map
        del self.numpy_map

        base_map = BaseMap(self.game, size=MAP_SIZE, rooms=self.room_number)
        self.base_map_object = base_map
        self.base_map = np.array(base_map.get_map())
        self._mat = {}
        # things of things to be drawn on map
        self.blit_list = None
        # current surface
        # self.surface = None
        # dict of part of the map rendered
        self.surface_dict = {}
        # elements
        self._elem = {}
        # multiprocessing dictionary to get the path with pathfinding
        self.multiprocessing_dict = self.game.multiprocessing_dict
        self.multiprocessing_dict['path'] = (())
        self.pathfinding_map = self.game.pathfinding_map
        for process in self.processes:
            process.join()
        self.processes.clear()
        # elements on the maps to update
        self.current_on_map_elements.clear()
        # surface to render on
        self.screen = self.game.screen
        # map for collisions for the bullets
        self.numpy_map = None
        self.enemy_base_coordinates = (0, 0)

    def clear_surfaces(self):
        self.surface_dict = {}

    def get_current_chests(self, index):
        return self._mat[index][ObjectType.CHEST]

    def get_current_enemy(self, index):
        try:
            return self._mat[index][ObjectType.ENEMY]
        except KeyError:
            return []

    def get_current_border(self, index):
        return self._mat[index][ObjectType.BORDER] + self.get_current_chests(index) + self.get_current_enemy(index)

    def get_chunks_border_objects(self, index, radius):
        physics_objects = []
        for loop in self.get_position(index, radius):
            physics_objects.extend(self.get_current_border(loop))
        return physics_objects

    def get_chunks_border_objects_no_environment(self, index, radius):
        physics_objects = []
        for _index in self.get_position(index, radius):
            physics_objects.extend(self.get_current_chests(_index) + self.get_current_enemy(_index))
        return physics_objects

    def get_chunks_chests_objects(self, index, radius):
        chests_objects = []
        for loop in self.get_position(index, radius):
            chests_objects.extend(self.get_current_chests(loop))
        return chests_objects

    def load_chunks(self, map_path=None):
        """
        loads the map and processes it
         - separate borders, normal tiles, air, etc... in a dictionary
        :param map_path: path of the map file
        :return: None
        """

        base_display = pygame.display.get_surface()
        img = font.render(f"loading Map", True, (255, 255, 255))
        base_display.fill((0, 0, 0))
        img_rect = img.get_rect()
        rect = base_display.get_rect()
        img_rect.center = rect.center
        base_display.blit(img, img_rect)
        pygame.display.flip()
        if map_path is None:
            load_map = block_shaped(self.base_map, self.CHUNK_SIZE, self.CHUNK_SIZE)
        else:
            load_map = np.load(map_path)
        self.numpy_map = load_map
        self._mat['size'] = (load_map.size, load_map[0].size)

        # generating map for pathfinding
        lines = []
        for loop in range(MAP_SIZE // CHUNK_SIZE):
            line = []
            for loop2 in range(MAP_SIZE // CHUNK_SIZE):
                line.append(self.numpy_map[loop2 + MAP_SIZE // CHUNK_SIZE * loop])
            lines.append(np.concatenate(line, axis=1), )

        full_map = np.concatenate(lines, axis=0)
        # print(full_map.shape)
        self.numpy_map = full_map
        self.numpy_map[self.numpy_map == 10] = 0
        # print(np.max(full_map))
        lowest_value = np.where(full_map == np.amax(full_map))
        # print('Tuple of arrays returned : ', lowest_value)
        # print('List of coordinates of minimum value in Numpy array : ')
        # zip the 2 arrays to get the exact coordinates
        # coordinates = list(zip(lowest_value[1], lowest_value[0]))
        coordinates = self.base_map_object.get_border_room()[1].center().x, self.base_map_object.get_border_room()[
            1].center().y
        # traverse over the list of coordinates
        # for cord in coordinates:
        #     print(cord)
        # self.enemy_base_coordinates = (
        #     coordinates[0][0] * TILE_SIZE,
        #     coordinates[0][1] * TILE_SIZE)
        self.enemy_base_coordinates = (
            coordinates[0] * TILE_SIZE,
            coordinates[1] * TILE_SIZE)
        # print(self.enemy_base_coordinates)

        self.numpy_map[self.numpy_map != 0] = 1
        self.pathfinding_map[0] = (self.numpy_map.tolist())
        # matrix = self.numpy_map
        # self.grid = Grid(matrix=matrix)

        # loading map
        x = y = 0

        self._mat['full_map'] = numpy.zeros(self.numpy_map.shape)
        self._mat['full_map'] = self._mat['full_map'].tolist()

        for index, chunk in enumerate(load_map.tolist()):

            self._mat[(x, y)] = {
                'objects': [],
                ObjectType.GROUND: [],
                ObjectType.BORDER: [],
                'not_empty': [],
                ObjectType.EMPTY: [],
                ObjectType.CHEST: [],
                ObjectType.ENEMY: []
            }

            map_length = MAP_SIZE // CHUNK_SIZE
            img = font.render(f"loading Map {100 * y / map_length}", True, (255, 255, 255))

            base_display.fill((0, 0, 0))
            if y % 10 == 0:
                pygame.event.get()
            img_rect = img.get_rect()
            rect = base_display.get_rect()
            img_rect.center = rect.center
            base_display.blit(img, img_rect)
            loading_bar_rect = pygame.Rect((0, 0), (300, 10))
            loading_bar_rect.midtop = img_rect.midbottom
            pygame.draw.rect(base_display, (255, 255, 255), loading_bar_rect, width=1)
            pygame.draw.rect(base_display, (255, 255, 255),
                             pygame.Rect(loading_bar_rect.left, loading_bar_rect.top, 300 * y // map_length,
                                         loading_bar_rect.height))
            pygame.display.update()

            for y_index, y_arr in enumerate(chunk):

                self._mat[(x, y)]['objects'].append([[] for _ in range(len(chunk))])
                for x_index, env_object in enumerate(y_arr):
                    # if x == y == 0:
                    #     self.numpy_map[CHUNK_SIZE * y + y_index][CHUNK_SIZE * x + x_index] = 1

                    if env_object == 10:
                        self._mat[(x, y)]['objects'][y_index][x_index] = StaticObject(
                            TILE_SIZE * CHUNK_SIZE * x + x_index * TILE_SIZE,
                            TILE_SIZE * CHUNK_SIZE * y + y_index * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                            object_type=ObjectType.GROUND)
                        # print(index, CHUNK_SIZE * y + y_index, CHUNK_SIZE * x + x_index)
                        self._mat['full_map'][CHUNK_SIZE * y + y_index][CHUNK_SIZE * x + x_index] = \
                            self._mat[(x, y)]['objects'][y_index][x_index]

                        self._mat[(x, y)][ObjectType.GROUND].append(self._mat[(x, y)]['objects'][y_index][x_index])
                        self._mat[(x, y)]['not_empty'].append(self._mat[(x, y)]['objects'][y_index][x_index])
                    elif env_object == 0:  # and (x_index != 0 or y_index != 0):
                        self._mat[(x, y)]['objects'][y_index][x_index] = StaticObject(
                            TILE_SIZE * CHUNK_SIZE * x + x_index * TILE_SIZE,
                            TILE_SIZE * CHUNK_SIZE * y + y_index * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                            object_type=ObjectType.BORDER)
                        self._mat['full_map'][CHUNK_SIZE * y + y_index][CHUNK_SIZE * x + x_index] = \
                            self._mat[(x, y)]['objects'][y_index][x_index]

                        self._mat[(x, y)][ObjectType.BORDER].append(self._mat[(x, y)]['objects'][y_index][x_index])
                        self._mat[(x, y)]['not_empty'].append(self._mat[(x, y)]['objects'][y_index][x_index])

                    elif 5000 > env_object > 1000:
                        self._mat[(x, y)]['objects'][y_index][x_index] = Chest(
                            TILE_SIZE * CHUNK_SIZE * x + x_index * TILE_SIZE,
                            TILE_SIZE * CHUNK_SIZE * y + y_index * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                            self, self.game)
                        self._mat['full_map'][CHUNK_SIZE * y + y_index][CHUNK_SIZE * x + x_index] = \
                            self._mat[(x, y)]['objects'][y_index][x_index]

                        self._mat[(x, y)][ObjectType.CHEST].append(self._mat[(x, y)]['objects'][y_index][x_index])

                    elif 1000 > env_object > 100:
                        vector_to_enemy_camp = (
                            self.enemy_base_coordinates[0] - TILE_SIZE * CHUNK_SIZE * x + x_index * TILE_SIZE,
                            self.enemy_base_coordinates[1] - TILE_SIZE * CHUNK_SIZE * y + y_index * TILE_SIZE)
                        # try:
                        # if random.randrange(
                        #         int(pygame.math.Vector2(vector_to_enemy_camp).magnitude() / (
                        #                 TILE_SIZE // 10))) < 1 and len(self.get_current_enemy((x, y))) < 4:

                        enemy = random.choice(self.game.enemies)
                        e = enemy('ennmy', TILE_SIZE * CHUNK_SIZE * x + x_index * TILE_SIZE,
                                  TILE_SIZE * CHUNK_SIZE * y + y_index * TILE_SIZE, 200, 200,
                                  ObjectType.ENEMY, self.game,
                                  level=numpy.interp(pygame.math.Vector2(vector_to_enemy_camp).magnitude(),
                                                     [0, self.MAP_SIZE * self.TILE_SIZE],
                                                     [self.map_level + settings["map_generation"]["difficulty"] + 1,
                                                      self.map_level + settings["map_generation"]["difficulty"]]))
                        self.put(e)
                        # except ValueError:
                        #     pass
                    else:
                        self._mat[(x, y)]['objects'][y_index][x_index] = StaticObject(
                            TILE_SIZE * CHUNK_SIZE * x + x_index * TILE_SIZE,
                            TILE_SIZE * CHUNK_SIZE * y + y_index * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                            object_type=ObjectType.EMPTY)
                        self._mat[(x, y)][ObjectType.EMPTY].append(self._mat[(x, y)]['objects'][y_index][x_index])
            x += 1
            if x == map_length:
                x = 0
                y += 1
        e = Boss('ennmy', self.enemy_base_coordinates[0],
                 self.enemy_base_coordinates[1], 700, 700,
                 ObjectType.ENEMY, self.game)
        self._mat['boss'] = e
        self.put(e)

    def get_boss(self):
        return self._mat['boss']

    def get_random_position(self):
        size = self.numpy_map.shape
        result = 0
        pos = (0, 0)
        while result == 0:
            pos = (random.randint(0, size[0] - 1), random.randint(0, size[1] - 1))
            result = self.numpy_map[pos]
        return pos[1] * TILE_SIZE, pos[0] * TILE_SIZE

    @staticmethod
    def get_index(_object):
        return int(_object.x // (TILE_SIZE * CHUNK_SIZE)), int(_object.y // (TILE_SIZE * CHUNK_SIZE))

    def get_random_elements(self, level, elements):
        """Returns a clone of random element from a collection using exponential random law."""
        x = random.expovariate(1 / level)
        l = None
        for k in elements.keys():
            if k <= x:
                l = elements[k]
        return random.choice(l)

    @staticmethod
    def convert_pos_to_index(x, y):
        return int(x // (TILE_SIZE * CHUNK_SIZE)), int(y // (TILE_SIZE * CHUNK_SIZE))

    def start_pathfinding(self, pos, end):
        if len(self.processes) == 0:
            p = Process(target=pathfinding_.get_path,
                        args=(self.multiprocessing_dict, self.pathfinding_map, pos, end))
            self.processes.append(p)
            p.start()
        self.processes[0].join(timeout=0)
        if not self.processes[0].is_alive():
            self.processes = []
            p = Process(target=pathfinding_.get_path,
                        args=(self.multiprocessing_dict, self.pathfinding_map, pos, end))
            self.processes.append(p)
            p.start()

    def draw_path(self, screen, scroll, lod):
        surface = pygame.transform.scale(pygame.Surface((TILE_SIZE, TILE_SIZE)), (TILE_SIZE // lod, TILE_SIZE // lod))
        surface.set_colorkey((0, 0, 0))
        pygame.draw.circle(surface, (255, 255, 255), surface.get_rect().center, surface.get_rect().centerx // 2,
                           width=2)
        for coordinate in self.multiprocessing_dict['path']:
            screen.blit(surface,
                        ((coordinate[0] * TILE_SIZE - scroll[0]) * 1 / lod,
                         (coordinate[1] * TILE_SIZE - scroll[1]) * 1 / lod))

    def __repr__(self):
        """representation of the map"""
        index = 0, 0
        string = ''
        for y in self._mat[index]['objects']:
            for x in y:
                if isinstance(x, StaticObject):
                    string += str(x)
            string += '\n'
        return string

    def __len__(self):
        return self.numpy_map.shape

    def __contains__(self, item):
        if isinstance(item, Coord):
            if 0 <= item.x < self.size and 0 <= item.y < self.size:
                return True
            else:
                return False
        else:
            for y in self._mat:
                for x in y:
                    if x == item:
                        return True
            return False

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.put(value, key)

    def get(self, coord):
        if isinstance(coord, Coord):
            try:
                return self._mat[coord.y][coord.x]
            except IndexError as e:
                print(e)

    def pos(self, element):
        for y, y_ele in enumerate(self._mat):
            for x, x_ele in enumerate(y_ele):
                if x_ele == element:
                    return Coord(x, y)

    def put(self, element):
        index = self.get_index(element)
        self._mat[index][element.object_type].append(element)

    def rm(self, item, index=None):
        if not index:
            index = self.get_index(item)
        x, y = index
        if item.object_type == ObjectType.CHEST:
            x_index = (item.x - TILE_SIZE * CHUNK_SIZE * x) // TILE_SIZE
            y_index = (item.y - TILE_SIZE * CHUNK_SIZE * y) // TILE_SIZE
            self._mat[(x, y)]['objects'][y_index][x_index] = StaticObject(
                TILE_SIZE * CHUNK_SIZE * x + x_index * TILE_SIZE,
                TILE_SIZE * CHUNK_SIZE * y + y_index * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
                object_type=ObjectType.EMPTY)
            self._mat[(x, y)][ObjectType.EMPTY].append(self._mat[(x, y)]['objects'][y_index][x_index])

        try:
            self._mat[(x, y)][item.object_type].remove(item)
        except ValueError or KeyError:
            print('enemy not in list?')
        self.update_drawing(self.game.lod, index)
        # if isinstance(coord, Coord):
        #     if self._mat[coord.y][coord.x] != self.ground:
        #         del self._elem[self._mat[coord.y][coord.x]]
        #         self._mat[coord.y][coord.x] = self.ground
        #     else:
        #         raise IndexError(f"{self._mat[coord.y][coord.x]} there is nothing here at {coord}")

    # def move(self, element, direction):
    #     position = self.pos(element)
    #     new_pos = position + direction
    #     if new_pos in self:
    #         if self._mat[new_pos.y][new_pos.x] == self.ground:
    #             self.rm(position)
    #             self.put(new_pos, element)

    def update_drawing(self, lod, _index):
        """
        updates a chunk in self.surface_dict
        :param lod: current level of detail
        :param _index: index of the chunk"""
        chunk_size = (
            CHUNK_SIZE * TILE_SIZE // lod + 1,
            CHUNK_SIZE * TILE_SIZE // lod + 1)

        self.blit_list = [
            (item.texture[lod],
             (int((item.rect.x - TILE_SIZE * CHUNK_SIZE * _index[0]) / lod),
              int((item.rect.y - TILE_SIZE * CHUNK_SIZE * _index[1]) / lod))) for
            item
            in self._mat[_index]['not_empty']]
        self.surface_dict[_index] = pygame.Surface(chunk_size)
        self.surface_dict[_index].fill((0, 0, 0))
        # self.surface_dict[_index].set_colorkey((0,0,0))
        self.surface = self.surface_dict[_index]
        self.surface.blit(pygame.transform.scale(ground_texture, (chunk_size[0], chunk_size[1])), (0, 0))
        self.surface_dict[_index].blits(self.blit_list)

        # blit chests
        self.blit_list = [
            (item.texture[lod],
             (int((item.rect.x - TILE_SIZE * CHUNK_SIZE * _index[0]) / lod),
              int((item.rect.y - TILE_SIZE * CHUNK_SIZE * _index[1]) / lod))) for
            item
            in self._mat[_index][ObjectType.CHEST]]
        self.surface_dict[_index].blits(self.blit_list)

    def draw(self, lod, screen, scroll, index=(0, 0)):
        screen.blit(self.surface_dict[index],
                    (
                        (-scroll[0] + TILE_SIZE * CHUNK_SIZE * index[0]) // lod,
                        (-scroll[1] + TILE_SIZE * CHUNK_SIZE * index[1]) // lod)
                    )

    @staticmethod
    def get_position(index: Tuple[int, int], radius: int) -> List[Tuple[int, int]]:
        """
        gets the indexes to be rendered
        :param index: the current chunk index
        :param radius: the radius of the render area
        :return a list of all positions in a square of radius around index """
        output = []
        for y in range(index[1] - radius // 2, index[1] + radius // 2):
            for x in range(index[0] - radius, index[0] + radius):
                if MAP_SIZE // CHUNK_SIZE > x >= 0 and MAP_SIZE // CHUNK_SIZE > y >= 0:
                    output.append((x, y))
        return output

    def render_map(self, lod, radius, index, force=False):
        """
        :param lod: current level of detail
        :param radius: the radius of the render area
        :param index: the current chunk index
        :param force: boolean to force the re-rendering of the chunk
        """
        # print('size of surface dict',asizeof.asizeof(self.surface_dict))
        # print('size of map', asizeof.asizeof(self._mat))
        indexes = self.get_position(index, radius)
        for index_ in indexes:
            if not force:
                try:
                    self.surface_dict[index_]
                except KeyError:
                    self.update_drawing(lod, index_)

            else:
                self.update_drawing(lod, index_)

    def draw_map_chunks(self, lod, screen, draw_scroll, radius, index):
        # self.draw(lod, screen, draw_scroll, index)

        indexes = self.get_position(index, radius)
        for index_ in indexes:
            try:
                self.draw(lod, screen, draw_scroll, index_)
            except KeyError as e:
                print(e)


def generate_perlin_noise_2d(shape, res):
    """https://pvigier.github.io/2018/06/13/perlin-noise-numpy.html"""

    def f(_t):
        return 6 * _t ** 5 - 15 * _t ** 4 + 10 * _t ** 3

    delta = (res[0] / shape[0], res[1] / shape[1])
    d = (shape[0] // res[0], shape[1] // res[1])
    grid = np.mgrid[0:res[0]:delta[0], 0:res[1]:delta[1]].transpose(1, 2, 0) % 1
    # Gradients
    angles = 2 * np.pi * np.random.rand(res[0] + 1, res[1] + 1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    g00 = gradients[0:-1, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g10 = gradients[1:, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g01 = gradients[0:-1, 1:].repeat(d[0], 0).repeat(d[1], 1)
    g11 = gradients[1:, 1:].repeat(d[0], 0).repeat(d[1], 1)
    # Ramps
    n00 = np.sum(grid * g00, 2)
    n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
    n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
    n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)
    # Interpolation
    t = f(grid)
    n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
    n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11
    return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)


def is_thing(a, threshold):
    if -0.2 < a < threshold:
        return True


def generate_map_file():
    import matplotlib.pyplot as plt
    import pandas as pd
    max_threshold = -0.15
    min_threshold = -0.30

    x = generate_perlin_noise_2d((MAP_SIZE, MAP_SIZE), (MAP_SIZE // PERLIN_FACTOR, MAP_SIZE // PERLIN_FACTOR))

    x[np.logical_and(min_threshold < x, x < max_threshold)] = 0
    x[x < min_threshold] = 10
    print()
    list_arr = block_shaped(x, CHUNK_SIZE, CHUNK_SIZE)
    np.save('mapchunck3', list_arr)
    # for loop in list_arr:
    #     plt.imshow(loop, interpolation='nearest')
    #     plt.show()
    plt.imshow(x, interpolation='nearest')
    plt.show()
    np.savetxt('map2', x)

    # convert your array into a dataframe
    df = pd.DataFrame(x)

    # save to xlsx file

    filepath = 'my_excel_file.xlsx'

    df.to_excel(filepath, index=False)
    print()

# game_map = Map()
# game_map.load_chunks('mapchunck.npy')
# print(game_map._mat['size'])
# print(game_map)
# # print(game_map)

# # print(np.load('mapchunck.npy'))
# generate_map_file()

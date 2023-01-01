from typing import Tuple, List, Any

import pygame
import pygame_gui
import math
from loading import load, TILE_SIZE
from game_class import Game
from post_effects import CameraShake, Glitch, Circle
from base_bodies import StaticObject, textures, Element, ParticleSystem, Usable, PhysicalObject, Creature, START_HP, \
    DASH_ACCELERATION, WALKING_ACCELERATION, MAX_STAMINA, MAX_HP, MAX_MAGIC, STAMINA_GAIN, STAMINA_DASH_DRAIN, \
    WALL_BOUNCINESS, GAME_SIZE, BULLET_FIRE_RATE, MAX_BULLETS, BULLET_POWER, BULLET_MAX_SPEED, BULLET_ACCELERATION
from guns import Gun, FireGun, MiniGun, QuadriGun
import hud
from enums import *
import random
from input_dictionary import INPUT_HANDLING_DICT
from uimagicbar import UIScreenSpaceMagicBar

GAME_SIZE = GAME_SIZE
shit_pc = True
if shit_pc:
    Glitch = CameraShake


# from pygame.locals import BLEND_ALPHA_SDL2


# import loading


class Chest(StaticObject):
    def __init__(self, x, y, x_size, y_size, game_map, game):
        super().__init__(x, y, x_size, y_size, object_type=ObjectType.CHEST)
        self.game = game
        self.inventory = []
        self.current_health = 1
        self.health_capacity = 1
        self.index = game_map.get_index(self)

        self.texture = textures["enviroment_textures"]['chest'][0]
        self.game_map = game_map
        self.chest_list = game_map.get_current_chests(self.index)
        self.on_map_elements_list = game_map.current_on_map_elements
        # self.hp_bar = hud.CustomUiHealthBar(
        #     pygame.Rect((0, 0), (150 / self.game.lod_offset, 30 / self.game.lod_offset)),
        #     self.game.manager, self)
        # self.hp_bar.bar_filled_colour = pygame_gui.core.ColourGradient(0, pygame.Color(0, 0, 0),
        #                                                                pygame.Color(120, 200, 120))
        # self.hp_bar.bar_unfilled_colour = pygame_gui.core.ColourGradient(0, pygame.Color(255, 0, 0),
        #                                                                  pygame.Color(0, 20, 10))
        # self.hp_bar.rebuild()

    def apply_damage(self, amount, vector=None):
        self.current_health -= amount
        if self.current_health <= 0:
            self.open()

    def open(self):
        # print('opned')
        potion = self.game.get_random_potion(self.game.player.level, pos=(self.x, self.y))
        self.inventory.append(potion)
        self.inventory.append(self.game.get_random_gun(None, pos=(self.x, self.y)))

        for loop in range(int(random.randint(1, 5) * self.game.player.level)):
            self.inventory.append(Exp(self.game, pos=(self.x, self.y)))

        # if self in self.chest_list:
        #     self.chest_list.remove(self)
        self.game_map.rm(self)
        self.on_map_elements_list.extend(self.inventory)
        # self.game_map.update_current_physics_objects(self.index, 6)
        self.game.active_post_effects.append(
            Circle(self.game.base_display, 100, 100, self.game, self.rect.center, 500))

        del self

    # def update(self, player):
    #     pass

    def draw(self, screen, scroll, lod):
        screen.blit(pygame.transform.scale(self.texture, (TILE_SIZE // lod, TILE_SIZE // lod)),
                    ((self.x - scroll[0]) / lod, (self.y - scroll[1]) / lod))


class Exp(Element):
    def __init__(self, game, pos=(0, 0), value=10):
        super().__init__(f'exp {value}', pos=pos)
        self.name = """THIS IS EXP DON'T EAT IT"""
        self.image = textures['other_elements']['on_map_elements']['exp'][0]
        self.game = game
        self.xp_amount = value

    def draw(self, win, scroll, lod):

        if self.game.check_if_on_base_display(self.rect):
            win.blit(textures['other_elements']['on_map_elements']['exp'][0][lod],
                     ((self.rect.x - scroll[0]) * 1 / lod,
                      (self.rect.y - scroll[1]) * 1 / lod))
            if self.game.night_mode:
                light = self.game.bullet_light[self.game.lod]
                # light=pygame.transform.scale(light,(light_size[0]//2,light_size[0]//2))
                light_rect = light.get_rect()
                center = self.game.scale_to_screen(self.rect.center)
                light_rect.center = (center[0] // self.game.fog_resolution, center[1] // self.game.fog_resolution)
                self.game.fog.blit(light, light_rect)

    def update(self, player, var2=None):
        vector_between_player_and_object = pygame.math.Vector2(player.x - self.x, player.y - self.y)

        self.vx, self.vy = self.vx / 1.2, self.vy / 1.2
        self.x += self.vx * self.dt / (100 / TILE_SIZE)
        self.y += self.vy * self.dt / (100 / TILE_SIZE)

        self.rect.x, self.rect.y = self.x, self.y
        if vector_between_player_and_object.magnitude() < 1000:
            self.particle_system.add_particles(random.getrandbits(1), self.x, self.y, 2)

            self.vx, self.vy = self.vx + vector_between_player_and_object[0] / 100, self.vy + \
                               vector_between_player_and_object[1] / 100
        self.particle_system.update(self.dt)

        if self.rect.colliderect(player.rect):
            player.current_xp += self.xp_amount
            player.game.data['sounds']['pickup.wav'].set_volume(50)
            player.game.collect_sound_mixer.play(player.game.data['sounds']['pickup.wav'])
            player.game.on_map_elements_list.remove(self)
            return True
        else:
            return False


class Potion(Usable):
    def __init__(self,
                 hp_heal: int = 0,
                 dash_acceleration: int = 0,
                 walking_acceleration: int = 0,
                 max_stamina: int = 0,
                 stamina_gain: int = 0,
                 stamina_dash_drain: int = 0,
                 max_hp: int = 0,
                 health_regen: int = 0,
                 magic_regen: float = 0,
                 magic_capacity: float = 0,
                 pos: Tuple[int, int] = (0, 0),
                 abbreviation=''):
        super().__init__(
            f"""potion:
            hp heal: {round(hp_heal, 2)}
            dash accelaration: {round(dash_acceleration, 2)}
            walking acceleration: {round(walking_acceleration, 2)}
            stamina_capacity: {round(max_stamina, 2)}
            stamina gain: {round(stamina_gain, 2)}
            stamina dash drain: {round(stamina_dash_drain, 2)}
            max hp: {round(max_hp, 2)}
            health regen: {round(health_regen, 2)}
            magic regen: {round(magic_regen, 2)} 
            magic capacity: {round(magic_capacity, 2)}""",
            pos=pos, abbreviation=abbreviation)
        self.health_regen = health_regen
        self.max_hp = max_hp
        self.stamina_dash_drain = stamina_dash_drain
        self.stamina_gain = stamina_gain
        self.max_stamina = max_stamina
        self.walking_acceleration = walking_acceleration
        self.dash_acceleration = dash_acceleration
        self.hp_heal = hp_heal
        self.magic_regen = magic_regen
        self.magic_capacity = magic_capacity
        self.image = textures["enviroment_textures"]['potion'][0]

    def use(self, creature: Creature):
        creature.health_regen = creature.health_regen + self.health_regen
        creature.current_health = creature.current_health + self.hp_heal
        creature.stamina_dash_drain = creature.stamina_dash_drain + self.stamina_dash_drain
        creature.stamina_capacity = creature.stamina_capacity + self.max_stamina
        creature.stamina_gain += self.stamina_gain

        creature.health_capacity = creature.health_capacity + self.max_hp
        creature.magic_capacity += self.magic_capacity
        creature.magic_regen += self.magic_regen
        creature.walking_acceleration += self.walking_acceleration
        creature.dash_acceleration += self.dash_acceleration

    def draw(self, win, scroll, lod):
        win.blit(textures["enviroment_textures"]['potion'][0][lod],
                 ((self.rect.x - scroll[0]) * 1 / lod,
                  (self.rect.y - scroll[1]) * 1 / lod))


class Enemy(Creature):
    def __init__(self, name, x: int, y: int, x_size: int, y_size: int, object_type: ObjectType,
                 game: Game,
                 start_hp: int = START_HP,
                 dash_acceleration: int = DASH_ACCELERATION,
                 walking_acceleration: int = WALKING_ACCELERATION,
                 max_stamina: int = MAX_STAMINA,
                 stamina_gain: int = STAMINA_GAIN,
                 stamina_dash_drain: int = STAMINA_DASH_DRAIN,
                 max_hp: int = MAX_HP, level=1) -> None:
        super().__init__(name, x, y, x_size, y_size, game, object_type, game.manager,
                         start_hp=random.uniform(start_hp // 2, start_hp * level),
                         dash_acceleration=dash_acceleration,
                         walking_acceleration=random.uniform(1, walking_acceleration * level),
                         max_stamina=max_stamina, stamina_gain=stamina_gain, stamina_dash_drain=stamina_dash_drain,
                         max_hp=random.uniform(100, max_hp * level), level=level)
        self.current_health = self.health_capacity
        self.game = game
        self.game_map = self.game.game_map
        # self.gun = QuadriGun(500, 10, self, self.game, texture=textures['enemy_bullet'])
        # self.gun = FireGun(1000, 500, self, game=game)
        self.gun = self.game.get_random_gun(self, level=level)
        self.gun.use(self)

        self.angle_to_player = 0
        self.original_position = self.x, self.y
        self.old_index = self.game_map.get_index(self)
        self.status = EnemyStatus.IDLE
        # player textures
        self.textures = {
            EnemyStatus.IDLE: textures['enemy']['idle'],
            # EnemyStatus.WALKING: textures['player']['walking'],
            # EnemyStatus.DASH: textures['player']['dash']
        }
        self.animation_tick = 0
        self.angle = 0

    def ai(self, player, collisions):
        if self.game.player.visible:
            x1, y1 = player.rect.center
            x2, y2 = self.rect.center
            self.angle_to_player = 180 + math.degrees(math.atan2((y2 - y1), (x2 - x1)))
            self.angle = self.angle_to_player
            vector_between_player_and_object = pygame.math.Vector2(player.x - self.x, player.y - self.y)
            magnitude = vector_between_player_and_object.magnitude()
            normal = vector_between_player_and_object.normalize()
            if 700 < magnitude < 2000:
                if magnitude > 500:
                    self.apply_acceleration(
                        normal * self.walking_acceleration * self.dt)
                    if self.dt > 0.2:
                        self.gun.shoot(self.angle_to_player)

            elif magnitude < 700:
                self.apply_acceleration(
                    normal * -1 * self.walking_acceleration * self.dt)

    def update(self, player, platforms=None):
        self.hp_bar.show()
        new_index = self.game_map.get_index(self)
        if self.old_index != new_index:
            self.game_map.get_current_enemy(new_index).append(self.game_map.get_current_enemy(self.old_index).pop(
                self.game_map.get_current_enemy(self.old_index).index(self)))
            self.old_index = new_index
        platforms = self.game_map.get_chunks_border_objects(self.game_map.get_index(self), 4)
        Creature.update(self, None)

        self.speed /= 1.2
        collisions = self.update_position(platforms + [player])
        # if self.speed.magnitude() < 5:
        self.update_speed()
        self.gun.update([player], self.dt)
        self.ai(player, collisions)
        if collisions['right'] == collisions['left'] == collisions['top'] == collisions['bottom'] is True:
            self.delete()
        if self.current_health <= 0:
            self.delete()
            return

    def delete(self):
        for loop in range(int(random.randint(10, 40) * self.level)):
            self.game.on_map_elements_list.append(Exp(self.game, pos=(self.x, self.y), value=1))

        self.game.active_post_effects.append(
            Circle(self.game.base_display, 100, 100, self.game, self.rect.center, 500))
        # self.game.player.current_xp += random.randint(10, 40) * self.level
        self.game.game_map.rm(self, index=self.old_index)
        self.hp_bar.kill()
        del self

    def draw(self, win, scroll, lod):
        self.gun.draw(win, scroll, lod)
        Creature.draw(self, win, scroll, lod)
        # update animation tick
        self.animation_tick += self.dt
        if self.animation_tick >= len(self.textures[self.status]) - 1:
            self.animation_tick = 0

        if self.game.check_if_on_base_display(self.rect):
            pygame.draw.rect(win, (255, 255, 255),
                             ((self.rect.x - scroll[0]) / lod, (self.rect.y - scroll[1]) / lod, self.rect.width / lod,
                              self.rect.height / lod))
            win.blit(self.textures[self.status][int(self.animation_tick)][lod],
                     ((self.rect.x - scroll[0]) * 1 / lod,
                      (self.rect.y - scroll[1]) * 1 / lod))

    def apply_damage(self, power, vector):
        self.current_health -= power
        self.speed += vector.normalize() * power

    def hide_hp_bar(self):
        self.hp_bar.hide()


class Player(Creature):
    zoom = 2

    def __init__(self, x: int,
                 y: int,
                 x_size: int,
                 y_size: int,
                 game: Game,
                 start_hp: int = START_HP,
                 dash_acceleration: int = DASH_ACCELERATION,
                 walking_acceleration: int = WALKING_ACCELERATION,
                 max_stamina: int = MAX_STAMINA,
                 stamina_gain: int = STAMINA_GAIN,
                 stamina_dash_drain: int = STAMINA_DASH_DRAIN,
                 max_hp: int = MAX_HP,
                 ) -> None:
        """

        Player object
        :param x: x position of the player
        :param y: y position of the player
        :param x_size: x_size of the player
        :param y_size: y size of the player
        :param start_hp: Player start Hp
        :param dash_acceleration: Player's dash acceleration
        :param walking_acceleration: Player's walking acceleration
        :param max_stamina: Player's maximum stamina
        :param stamina_gain: Player's stamina gain
        :param stamina_dash_drain: Player's dash stamina drain
        :param max_hp: Player's Max hp
        """
        # super().__init__(x, y, x_size, y_size, ObjectType.PLAYER, 'Player')  # init the Physical object
        # Player stats
        super().__init__('Player', x, y, x_size, y_size, game, ObjectType.PLAYER, game.manager, start_hp,
                         dash_acceleration,
                         walking_acceleration,
                         max_stamina, stamina_gain, stamina_dash_drain, max_hp)

        self.angle = 0  # current player angle
        self.direction = (0, 0)  # player direction
        self.inputs = [0, 0, 0, 0, 0]  # player inputs format (left,right,up,down,shift)
        self.current_xp = 0
        self.level = 1
        self.xp_capacity = 50

        # player textures
        self.textures = {
            PlayerStatus.IDLE: textures['player']['idle'],
            PlayerStatus.WALKING: textures['player']['walking'],
            PlayerStatus.DASH: textures['player']['dash']
        }

        # player status used for animation
        self.status = None
        # player particle system
        self.particle_system = ParticleSystem((self.x, self.y))
        # player animation tick to chose the frames
        self.animation_tick = 0

        # player acceleration dict converts player inputs into pygame vectors #TODO make controller support
        self.acceleration_dict = {
            (0, 0, 0, 0): (pygame.math.Vector2(0, 0), PlayerStatus.IDLE),
            (0, 1, 0, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(-90), PlayerStatus.WALKING),
            (1, 0, 0, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(90), PlayerStatus.WALKING),
            (0, 0, 1, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(180), PlayerStatus.WALKING),
            (0, 0, 0, 1): (pygame.math.Vector2(0, self.walking_acceleration), PlayerStatus.WALKING),
            (0, 1, 1, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(225), PlayerStatus.WALKING),
            (1, 0, 1, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(135), PlayerStatus.WALKING),
            (1, 0, 0, 1): (pygame.math.Vector2(0, self.walking_acceleration).rotate(45), PlayerStatus.WALKING),
            (0, 1, 0, 1): (pygame.math.Vector2(0, self.walking_acceleration).rotate(-45), PlayerStatus.WALKING),

        }
        # self.gun = MiniGun(0, 5000, self, game=game)

        self.gun = self.game.get_random_gun(self, level=self.level)
        self.game = game
        self.hp_bar.show()
        self.inventory = hud.Inventory(game.manager, [5, 5], game.base_display.get_size()[1] // 1.4,
                                       game.on_map_elements_list,
                                       self)
        self.gun.use(self)
        self.inventory.remove_element(self.gun)
        self.inventory_shown = False
        self.inventory.add_element(Potion())
        self.player_ui = hud.PlayerBaseInfoUi(self.game, self)
        self.channel = pygame.mixer.Channel(4)
        self.visible = True

    def reset(self):
        pass
        # self.gun = MiniGun(0, 5000, self, game=self.game, )
        # self.inventory = hud.Inventory(self.game.manager, [5, 5], self.game.base_display.get_size()[1] // 1.4,
        #                                self.game.on_map_elements_list,
        #                                self)
        # self.gun.use(self)
        # self.inventory.remove_element(self.gun)
        # self.inventory_shown = False
        # self.inventory.add_element(Potion())
        # self.player_ui = hud.PlayerBaseInfoUi(self.game, self)

    def process_inputs(self, event):
        self.inventory.handle_inventory_inputs(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT or event.key == INPUT_HANDLING_DICT['right']:
                self.inputs[1] = True
            if event.key == pygame.K_LEFT or event.key == INPUT_HANDLING_DICT['left']:
                self.inputs[0] = True
            if event.key == pygame.K_UP or event.key == INPUT_HANDLING_DICT['up']:
                self.inputs[2] = True
            if event.key == pygame.K_DOWN or event.key == INPUT_HANDLING_DICT['down']:
                self.inputs[3] = True
            if event.key == pygame.K_SPACE:
                self.inputs[4] = True
            if event.key == pygame.K_i:
                if not self.inventory_shown:
                    self.inventory_shown = True
                    self.inventory.show()
                else:
                    self.inventory_shown = False
                    self.inventory.hide()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT or event.key == INPUT_HANDLING_DICT['right']:
                self.inputs[1] = False
            if event.key == pygame.K_LEFT or event.key == INPUT_HANDLING_DICT['left']:
                self.inputs[0] = False
            if event.key == pygame.K_UP or event.key == INPUT_HANDLING_DICT['up']:
                self.inputs[2] = False
            if event.key == pygame.K_DOWN or event.key == INPUT_HANDLING_DICT['down']:
                self.inputs[3] = False

    def draw(self, screen, scroll, lod):
        Creature.draw(self, screen, scroll, lod)
        # getting angle
        x1, y1 = pygame.mouse.get_pos()
        x1, y1 = x1 * self.zoom + scroll[0], y1 * self.zoom + scroll[1]
        x2, y2 = self.rect.center
        self.angle = 180 + math.degrees(math.atan2((y2 - y1), (x2 - x1)))
        self.animation_tick += 1 * self.dt
        # counting frames for animation
        if self.animation_tick >= len(self.textures[self.status]):
            self.animation_tick = 0
        # if self.animation_tick >= 23 and self.status == PlayerStatus.IDLE:
        #     self.animation_tick = 0
        # if self.animation_tick >= 4 and self.status == PlayerStatus.WALKING:
        #     self.animation_tick = 0
        # if self.animation_tick >= 23 and self.status == PlayerStatus.DASH:
        #     self.animation_tick = 0

        # drawing
        self.particle_system.draw(screen, scroll, lod)
        # draw Gun
        self.gun.draw(screen, scroll, lod)
        screen.blit(self.textures[self.status][int(self.animation_tick)][lod],
                    self.game.scale_rect_to_screen(self.rect))
        pygame.draw.rect(screen, (255, 255, 255), self.game.scale_rect_to_screen(self.rect),
                         width=int(5 / lod))
        # radar_len = 1000
        # x = self.rect.centerx - scroll[0] + math.cos(math.radians(self.angle)) * radar_len
        # y = self.rect.centery - scroll[1] + math.sin(math.radians(self.angle)) * radar_len
        # pygame.draw.aaline(screen, (255, 0, 255),
        #                    ((self.rect.centerx - scroll[0]) / lod, (self.rect.centery - scroll[1]) / lod),
        #                    (x / lod, y / lod), 10 // lod, )

    def update(self, arg1=None, arg2=None):
        # self.game.game_map.update_current_physics_objects(self.game.game_map.get_index(self), None)
        self.acceleration_dict = {
            (0, 0, 0, 0): (pygame.math.Vector2(0, 0), PlayerStatus.IDLE),
            (0, 1, 0, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(-90), PlayerStatus.WALKING),
            (1, 0, 0, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(90), PlayerStatus.WALKING),
            (0, 0, 1, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(180), PlayerStatus.WALKING),
            (0, 0, 0, 1): (pygame.math.Vector2(0, self.walking_acceleration), PlayerStatus.WALKING),
            (0, 1, 1, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(225), PlayerStatus.WALKING),
            (1, 0, 1, 0): (pygame.math.Vector2(0, self.walking_acceleration).rotate(135), PlayerStatus.WALKING),
            (1, 0, 0, 1): (pygame.math.Vector2(0, self.walking_acceleration).rotate(45), PlayerStatus.WALKING),
            (0, 1, 0, 1): (pygame.math.Vector2(0, self.walking_acceleration).rotate(-45), PlayerStatus.WALKING),

        }
        Creature.update(self, None)
        if self.current_xp >= self.xp_capacity:
            self.game.data['sounds']["levelup.wav"].play()
            self.level += 1
            self.xp_capacity *= 2
            self.current_xp = 0
        # update player particle system
        self.particle_system.update(self.dt)

        # update Gun
        physics_objects = self.game.game_map.get_chunks_border_objects(self.game.game_map.get_index(self), 4)
        gun_physical_objects = self.game.game_map.get_chunks_border_objects_no_environment(
            self.game.game_map.get_index(self), 6)

        mouse_buttons = pygame.mouse.get_pressed(num_buttons=3)
        if mouse_buttons[0] and not self.status == PlayerStatus.DASH:
            self.gun.shoot(self.angle)

        self.gun.update(gun_physical_objects, dt=self.dt * self.game.enemy_dt_factor)

        # physics
        self.status = PlayerStatus.IDLE
        self.player_movement = pygame.math.Vector2(0, 0)

        # inputs
        # noinspection PyTypeChecker
        x_y_inputs: Tuple[bool, bool, bool, bool] = tuple(self.inputs[:4])
        try:
            self.player_movement, self.status = self.acceleration_dict[x_y_inputs]
        except KeyError as e:
            print(e)

        self.direction = (
            self.player_movement[0] / self.walking_acceleration, self.player_movement[1] / self.walking_acceleration)

        # dash
        if self.inputs[4] and self.current_stamina > self.stamina_dash_drain:
            self.game.data['player']['sounds']['dash'].play()
            self.player_movement = pygame.math.Vector2(
                self.player_movement[0] * self.dash_acceleration / self.walking_acceleration,
                self.player_movement[1] * self.dash_acceleration / self.walking_acceleration)
            self.current_stamina -= self.stamina_dash_drain
            self.animation_tick = 0
        if self.speed.length() > self.walking_acceleration * self.dash_acceleration / 9:
            self.status = PlayerStatus.DASH
        if self.player_movement != [0, 0]:
            if self.status == PlayerStatus.DASH:
                self.particle_system.add_particles(4, self.rect.centerx, self.rect.centery, 4)
            self.particle_system.add_particles(1, self.rect.centerx, self.rect.centery)
            if not self.channel.get_busy():
                self.channel.play(self.game.data['player']['sounds']['walking'], loops=-1)
        else:
            self.game.data['player']['sounds']['walking'].stop()

        # updating acceleration and speed
        self.apply_acceleration(self.player_movement)
        self.update_speed()
        player_collisions = self.update_position(physics_objects)

        # bouncing with everything
        if player_collisions['left'] or player_collisions['right']:
            self.speed = pygame.math.Vector2(-self.speed[0], self.speed[1] * WALL_BOUNCINESS)
        if player_collisions['top'] or player_collisions['bottom']:
            self.speed = pygame.math.Vector2(self.speed[0], -self.speed[1] * WALL_BOUNCINESS)
        # reset shift toggle
        self.inputs[4] = False

        # add resistance to the ground
        self.speed = self.speed * (1 / 1.2)

    def apply_damage(self, power, vector):
        Creature.apply_damage(self, power, vector)
        if not self.is_alive:
            self.game.paused = True
            self.game.game_over.show()
            self.game.pause_window.hide()
        self.game.data['player']['sounds']['hit'].play()
        if len(self.game.active_post_effects) <= 1:
            self.game.active_post_effects.append(Glitch(self.game.base_display, 10, 10, self.game))


class NoGun(Gun):
    def shoot(self, angle):
        pass

    def draw(self, win, scroll, lod):
        pass

    def update(self, physics_objects, dt=1):
        pass


class SucideEnemy(Enemy):
    def __init__(self, name, x: int, y: int, x_size: int, y_size: int, object_type: ObjectType,
                 game: Game,
                 start_hp: int = START_HP,
                 dash_acceleration: int = DASH_ACCELERATION,
                 walking_acceleration: int = WALKING_ACCELERATION,
                 max_stamina: int = MAX_STAMINA,
                 stamina_gain: int = STAMINA_GAIN,
                 stamina_dash_drain: int = STAMINA_DASH_DRAIN,
                 max_hp: int = MAX_HP, level=1) -> None:
        walking_acceleration *= 2
        super().__init__(name, x, y, x_size, y_size, object_type, game, start_hp=start_hp,
                         dash_acceleration=dash_acceleration, walking_acceleration=walking_acceleration,
                         max_stamina=max_stamina, stamina_gain=stamina_gain, stamina_dash_drain=stamina_dash_drain,
                         max_hp=max_hp, level=level)

        self.gun = NoGun(100, 990, self, game, power=30)

        self.gun.use(self)
        self.textures = {
            EnemyStatus.IDLE: textures['suicide_enemy']['idle'],
            # EnemyStatus.WALKING: textures['player']['walking'],
            # EnemyStatus.DASH: textures['player']['dash']
        }

    def ai(self, player, collisions):
        if player.visible:
            x1, y1 = player.rect.center
            x2, y2 = self.rect.center
            self.angle_to_player = 180 + math.degrees(math.atan2((y2 - y1), (x2 - x1)))
            self.angle = self.angle_to_player
            vector_between_player_and_object = pygame.math.Vector2(player.x - self.x, player.y - self.y)
            magnitude = vector_between_player_and_object.magnitude()
            normal = vector_between_player_and_object.normalize()
            if magnitude < 2000:
                self.apply_acceleration(
                    normal * self.walking_acceleration * self.dt)
            if player in collisions['data']:
                player.apply_damage(self.current_health * self.level, vector=self.acceleration)
                self.delete()


class GoNextFloor(Usable):
    def __init__(self, game, pos=(0, 0)):
        super().__init__('goNextFloor', pos=pos)
        self.name = "You have defeated the boss<br>use this item to go to the next floor"
        self.image = textures['other_elements']['on_map_elements']['next_floor'][0]
        self.game = game

    def draw(self, win, scroll, lod):
        win.blit(textures['other_elements']['on_map_elements']['next_floor'][0][lod],
                 ((self.rect.x - scroll[0]) * 1 / lod,
                  (self.rect.y - scroll[1]) * 1 / lod))

    def use(self, creature):
        # print('used onced')
        self.game.rebuild_map()


class Boss(Enemy):
    def __init__(self, name, x: int, y: int, x_size: int, y_size: int, object_type: ObjectType, game: Game):
        super().__init__(name, x, y, x_size, y_size, object_type, game, max_hp=1000, level=game.game_map.map_level + 1)
        # self.current_health = 1000 * game.game_map.map_level
        self.gun = QuadriGun(100 / (game.game_map.map_level + 0.01), 990, self, game,
                             power=10 * game.game_map.map_level)

        self.gun.use(self)
        self.textures = {
            EnemyStatus.IDLE: textures['boss']['idle'],
            # EnemyStatus.WALKING: textures['player']['walking'],
            # EnemyStatus.DASH: textures['player']['dash']
        }

    def delete(self):
        for loop in range(int(random.randint(10, 40) * self.level * 10)):
            self.game.on_map_elements_list.append(Exp(self.game, pos=(self.x, self.y), value=1))
        self.game.on_map_elements_list.append(GoNextFloor(self.game, pos=(self.x, self.y)))
        self.game.active_post_effects.append(
            Circle(self.game.base_display, 100, 100, self.game, self.rect.center, 4000))

        self.game.active_post_effects.append(
            Circle(self.game.base_display, 140, 200, self.game, self.rect.center, 500))

        self.game.active_post_effects.append(
            Circle(self.game.base_display, 150, 300, self.game, self.rect.center, 1000))
        # self.game.player.current_xp += random.randint(10, 40) * self.level
        try:
            self.game.game_map.rm(self, index=self.old_index)
        except KeyError:
            print('enemy has FCKED UP')
        self.is_alive = False
        self.hp_bar.kill()
        del self

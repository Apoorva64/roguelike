import pygame
from post_effects import Glitch, CameraShake
from skills import ZaWarudo, InvisibleSkill, DoubleDmg, DoubleHealthRegen, DoubleFireRate
import random


class Game:
    def __init__(self, multiprocessing_manager):
        import pygame_gui
        import pygame
        import menu
        from load_settings import settings
        from minimap import MiniMap
        self.pygame = pygame
        self.pygame_gui = pygame_gui
        import os
        from pygame_gui.core import ColourGradient
        from hud import SkillsUi, PauseWindow, GameOverScreen, PayerInfoUi

        # change display to display on
        x = 0
        y = settings
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"

        # init multiprocessing manager
        self.multiprocessing_manager = multiprocessing_manager
        self.multiprocessing_dict = self.multiprocessing_manager.dict()
        self.pathfinding_map = self.multiprocessing_manager.list()
        self.pathfinding_map.append([])

        # init
        pygame.mixer.pre_init(frequency=44100)
        pygame.init()
        pygame.mixer.init(frequency=44100)
        self.font = pygame.font.SysFont('', 24)
        self.clock = pygame.time.Clock()
        self.SMOOTH_ZOOM = settings["game_class"]["SMOOTH_ZOOM"]
        self.ZOOM_SENSITIVITY = settings["game_class"]["ZOOM_SENSITIVITY"]

        # game resolution offset,the higher it is the lower the game resolution, 1 is minimum
        self.lod_offset = settings["game_class"]["lod_offset"]
        if not self.SMOOTH_ZOOM:
            self.ZOOM_SENSITIVITY = 1
        # Set up the drawing window
        self.fullscreen = settings["game_class"]["fullscreen"]

        if self.fullscreen:
            self.base_display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
            self.DISPLAY_SIZE = self.base_display.get_size()
        else:
            self.DISPLAY_SIZE = settings["game_class"]["WINDOWED_DISPLAY_SIZE"]
            self.base_display = pygame.display.set_mode(self.DISPLAY_SIZE)

        # importing modules
        import bodies
        import maps.map_generation as map_generation

        # menu
        skip_menu = settings["game_class"]["skip_menu"]
        if not skip_menu:
            menu.main(self.base_display)

        self.bodies = bodies
        self.data = bodies.textures
        self.map_generation = map_generation

        # self.guns = [bodies.Gun, bodies.FireGun, bodies.MiniGun, bodies.FireGun]
        self.enemies = [bodies.Enemy, bodies.SucideEnemy]
        self.skills = [ZaWarudo, InvisibleSkill, DoubleDmg, DoubleFireRate, DoubleHealthRegen]
        self.guns = [bodies.MiniGun, bodies.QuadriGun, bodies.FireGun]
        self.potions = [bodies.Potion]

        self.zoom = 1 * bodies.TILE_SIZE // 50
        bodies.BASE_DISPLAY_SIZE = self.DISPLAY_SIZE
        bodies.GAME_SIZE = (self.DISPLAY_SIZE[0] * self.zoom, self.DISPLAY_SIZE[1] * self.zoom)

        # screen where the game is rendered on
        self.screen = pygame.Surface(bodies.GAME_SIZE)

        # manager for all of the game ui elements
        self.manager = pygame_gui.UIManager(self.DISPLAY_SIZE)

        # change cursor
        pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)

        # Run until the user asks to quit
        self.running = True
        self.dt = 1
        self.level = 1

        # loading map
        self.game_map = map_generation.Map(self)
        # game_map.load_chunks('block_map.npy')
        # self.game_map.load_chunks(r'base_ver/block_map100.npy')
        self.game_map.load_chunks()
        self.on_map_elements_list = self.game_map.current_on_map_elements
        pos = self.get_player_position()
        self.player = bodies.Player(pos[0], pos[1], bodies.TILE_SIZE, bodies.TILE_SIZE,
                                    self)

        self.player.inventory.hide()

        self.base_scroll = [self.player.rect.x, self.player.rect.y]
        self.player.zoom = self.zoom
        self.fps_target = settings["game_class"]["fps_target"]
        self.index = 0, 0  # current chunk index
        self.radius = 2
        self.lod = self.lod_offset
        pygame.display.flip()
        self.game_map.render_map(self.lod, self.radius, self.index)

        # init game
        self.rect = self.base_display.get_rect()
        self.time_delta = 0
        self.level = 1
        self.enemy_dt_factor = 1
        self.clock.tick(self.fps_target)
        # init graphics
        self.draw_scroll = (0, 0)
        self.night_color = settings["game_class"]["night_color"]
        self.fog_resolution = settings["game_class"]["fog_resolution"]
        self.fog = self.pygame.Surface((self.screen.get_size()[0] // self.fog_resolution,
                                        self.screen.get_size()[1] // self.fog_resolution))

        self.light = bodies.textures['gradients']['light1'][1]
        self.bullet_light = bodies.textures['gradients']['light2'][0]
        self.light_size = (500, 500)
        self.night_mode = settings["game_class"]["night_mode_active"]
        # self.base_display.set_alpha(None)
        self.screen.set_alpha(None)

        # init effects
        self.active_skills = []
        self.active_post_effects = []
        self.debug = settings["game_class"]["debug"]

        self.paused = False
        # init ui
        self.debug_ui = pygame_gui.elements.UITextBox('', pygame.Rect((0, 0), (1000, 100)), manager=self.manager)
        self.debug_ui.bg_colour = ColourGradient(10, pygame.Color((100, 100, 100, 100)), pygame.Color((0, 0, 0, 100)))
        self.skills_ui = SkillsUi(self)
        self.pause_window = PauseWindow(self)
        rect = pygame.Rect(self.rect.centerx, self.rect.height // 50, -1, -1)
        self.message_display = pygame_gui.elements.UITextBox('', rect, self.manager)
        self.player_info = PayerInfoUi(self)
        self.message_display.background_colour = self.pygame_gui.core.ColourGradient(0, self.pygame.Color(0, 0, 0, 0),
                                                                                     self.pygame.Color(0, 0, 0, 0))
        self.messages = []
        self.mini_map = MiniMap(self)
        self.game_over = GameOverScreen(self)
        self.collect_sound_mixer = pygame.mixer.Channel(2)
        self.explosion_sound_mixer = pygame.mixer.Channel(3)

        self.check_position_pathfinding(rebuild=False)

    def rebuild_messages(self):
        """rebuilds the message ui"""
        self.message_display.kill()
        rect = pygame.Rect(self.rect.centerx, self.rect.height // 50, -1, -1)
        self.message_display = self.pygame_gui.elements.UITextBox('<br>'.join(self.messages), rect, self.manager)
        self.message_display.background_colour = self.pygame_gui.core.ColourGradient(0, self.pygame.Color(0, 0, 0, 0),
                                                                                     self.pygame.Color(0, 0, 0, 0))
        # print(self.message_display.text)
        self.message_display.rect.center = (self.rect.centerx, self.rect.height // 5)
        self.message_display.border_width = 0
        self.message_display.rebuild()

    def rebuild_map(self, reset=False):
        """rebuilds the map"""
        # self.manager.clear_and_reset()
        # self.player.reset()
        # self.manager=self.pygame_gui.UIManager(self.DISPLAY_SIZE)
        self.paused = False
        self.game_over.hide()
        self.pause_window.hide()
        self.pathfinding_map[0] = []
        # del self.pathfinding_map
        # self.pathfinding_map=[]

        if reset:
            self.game_map.rebuild_map(add_diff=False)
        else:
            self.game_map.rebuild_map()
        self.game_map.load_chunks()
        self.mini_map.rebuild()
        self.on_map_elements_list = self.game_map.current_on_map_elements
        self.game_map.render_map(self.lod, self.radius, self.index)
        pos = self.get_player_position()
        self.player.x = pos[0]
        self.player.y = pos[1]
        self.player.current_health = self.player.health_capacity
        self.time_delta = self.clock.tick(self.fps_target) / 1000.0
        self.time_delta = self.clock.tick(self.fps_target) / 1000.0
        # print(self.player.dt)
        self.player.dt = self.time_delta * 60
        self.player.is_alive = True
        self.check_position_pathfinding(rebuild=False)
        for _index in self.game_map.get_position(self.index, self.radius + 100):
            for enemy in self.game_map.get_current_enemy(_index):
                enemy.hide_hp_bar()

        self.set_scroll_to_player_pos()

    @staticmethod
    def get_random_elements(level, elements):
        """get a random element from a list"""
        # """Returns a clone of random element from a collection using exponential random law."""
        # x = random.expovariate(1 / (level**2))
        # l = None
        # for k in range(len(elements)):
        #     if k <= x:
        #         return elements[k]
        return random.choice(elements)

    def get_random_gun(self, parent_obj, pos=(0, 0), level=1):
        """get a random gun with level scaling"""
        gun = self.get_random_elements(level, self.guns)
        gun = gun(random.uniform(100 / self.level, self.bodies.BULLET_FIRE_RATE / level), self.bodies.MAX_BULLETS,
                  parent_obj,
                  self,
                  bullet_lifetime=500,
                  power=random.uniform(2, self.bodies.BULLET_POWER * level),
                  max_speed=random.uniform(10, self.bodies.BULLET_MAX_SPEED * level),
                  acceleration=random.uniform(1, self.bodies.BULLET_ACCELERATION * level), pos=pos)
        # print(gun.name)
        return gun

    def get_random_potion(self, level, pos=(0, 0)):
        potion = self.get_random_elements(self.level, self.potions)

        potion = potion(hp_heal=random.uniform(0, 50 * level),
                        dash_acceleration=random.uniform(0, 0.1 * level),
                        walking_acceleration=random.uniform(0, 0.1 * level),
                        max_stamina=random.uniform(0, 10 * level),
                        stamina_gain=random.uniform(0, 0.01 * level),
                        stamina_dash_drain=random.uniform(0.5 * level, 0),
                        max_hp=random.uniform(0, 10 * level),
                        health_regen=random.uniform(0, 0.01 * level),
                        magic_capacity=random.uniform(0, 10 * level),
                        magic_regen=random.uniform(0, 0.01 * level),
                        pos=pos)
        return potion

    def draw_night_mode(self):
        """draws night mode"""
        self.screen.blit(self.pygame.transform.scale(self.fog, self.screen.get_size()), (0, 0),
                         special_flags=pygame.BLEND_MULT)

    def get_player_position(self):
        """gets a valid player position"""
        pos = None
        while pos is None:
            pos = self.game_map.get_random_position()
            vector_to_player = self.pygame.math.Vector2(self.game_map.enemy_base_coordinates[0] - pos[0],
                                                        self.game_map.enemy_base_coordinates[1] - pos[1])
            if vector_to_player.magnitude() < self.game_map.MAP_SIZE * self.game_map.TILE_SIZE // 2:
                pos = None

        return pos

    def check_position_pathfinding(self, rebuild=False):
        """gets a valid player position and check with pathfinding"""
        rect = self.pygame.Rect((0, 0, 300, 100))
        rect.center = self.base_display.get_rect().center
        ui_pathfinding = self.pygame_gui.elements.UITextBox('verifing position with pathfinding', rect, self.manager)
        ui_pathfinding.background_colour = self.pygame_gui.core.ColourGradient(0, self.pygame.Color(0, 0, 0, 0),
                                                                               self.pygame.Color(0, 0, 0, 0))
        ui_pathfinding.border_colour = self.pygame_gui.core.ColourGradient(0, self.pygame.Color(0, 0, 0, 0),
                                                                           self.pygame.Color(0, 0, 0, 0))
        ui_pathfinding.rebuild()
        pos = (-1, -1)
        while len(self.game_map.multiprocessing_dict['path']) == 0:
            if rebuild:
                self.rebuild_map(reset=True)
                rebuild = not rebuild
            # print(self.game_map.multiprocessing_dict['path'])

            pos = (self.player.x, self.player.y)
            self.game_map.start_pathfinding(
                (pos[0] // 100, pos[1] // 100),
                (self.game_map.enemy_base_coordinates[0] // 100, self.game_map.enemy_base_coordinates[1] // 100))
            while self.game_map.processes[0].is_alive():
                self.game_map.processes[0].join(timeout=0)
                for event in self.pygame.event.get():
                    self.manager.process_events(event)
                self.manager.update(10)
                self.base_display.fill((0, 0, 0))
                self.manager.draw_ui(self.base_display)

                self.pygame.display.flip()
            rebuild = True

            self.game_map.processes[0].join()
        ui_pathfinding.kill()
        self.clock.tick(60)
        return pos

    def scale_to_base_display(self, vector):
        """scales a vector to the main base display"""
        return int(1 / self.zoom * (vector[0] - self.draw_scroll[0])), int(
            1 / self.zoom * (vector[1] - self.draw_scroll[1]))

    def scale_rect_to_base_display(self, rect: pygame.Rect):
        """Scales a rect to the main base display"""
        size = rect.width // self.zoom, rect.height // self.zoom
        center = self.scale_to_base_display(rect.center)
        new_rect = self.pygame.Rect((0, 0), size)
        new_rect.center = center
        return new_rect

    def scale_to_screen(self, vector):
        """Scales a vector to the game screen"""
        return (vector[0] - self.draw_scroll[0]) / self.lod, (vector[1] - self.draw_scroll[1]) / self.lod

    def scale_rect_to_screen(self, rect: pygame.Rect):
        """Scales a rect to the game screen"""
        return self.pygame.Rect(self.scale_to_screen(rect.topleft), (rect.width / self.lod, rect.height / self.lod))

    def check_if_on_base_display(self, rect: pygame.Rect):
        """checks if an element is on the base_display"""
        return self.base_display.get_rect().colliderect(self.scale_rect_to_base_display(rect))

    def process_inputs(self):
        """processes the inputs for the game"""
        # Did the user click the window close button?
        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                return False
                # break
                # TODO CLOSE THE FUCKING MULTIPROCESSING PIPE
            if event.type == self.pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.zoom += self.ZOOM_SENSITIVITY
                    # self.set_scroll_to_player_pos()

                if event.button == 5:
                    self.zoom -= self.ZOOM_SENSITIVITY
                    if self.zoom <= 0.4:
                        self.zoom += self.ZOOM_SENSITIVITY
                    # self.set_scroll_to_player_pos()

                self.player.zoom = self.zoom
                self.bodies.GAME_SIZE = (
                    self.DISPLAY_SIZE[0] * self.zoom * 1 / self.lod, self.DISPLAY_SIZE[1] * self.zoom * 1 / self.lod)
            if event.type == self.pygame.KEYDOWN:
                if event.key == self.pygame.K_p:
                    self.paused = not self.paused

                if event.key == self.pygame.K_m:
                    if self.player_info.get_visible():
                        self.player_info.hide()
                    else:
                        self.player_info.show()

                if event.key == self.pygame.K_b:
                    self.game_over.show()
                # skills inputs
                for skill in self.skills:
                    if event.key == skill.control:
                        x = skill(self)
                        if x.get_can_use():
                            self.active_skills.append(x)
                        else:
                            del x
                # debug inputs
                if self.debug:
                    if event.key == self.pygame.K_5:
                        self.zoom = 1
                        self.player.zoom = self.zoom
                        self.lod = 1
                        self.radius = 7
                        self.game_map.clear_surfaces()
                        self.game_map.render_map(self.lod, self.radius, self.index, force=True)
                        self.bodies.GAME_SIZE = (
                            self.DISPLAY_SIZE[0] * self.zoom * 1 / self.lod,
                            self.DISPLAY_SIZE[1] * self.zoom * 1 / self.lod)
                        # self.set_scroll_to_player_pos()

                    if event.key == self.pygame.K_l:
                        self.lod_offset += 1
                    if event.key == self.pygame.K_k:
                        self.lod_offset -= 1

                    if event.key == self.pygame.K_3:
                        self.fps_target -= 10
                    if event.key == self.pygame.K_4:
                        self.fps_target += 10
                    if event.key == self.pygame.K_n:
                        self.night_mode = not self.night_mode
                if event.key == self.pygame.K_x:
                    self.debug = not self.debug
            self.player.process_inputs(event)
            self.pause_window.process_inputs(event)
            if self.game_over.get_visible():
                self.game_over.process_inputs(event)

    def set_scroll_to_player_pos(self):
        self.base_scroll[0] += (self.player.rect.centerx - self.base_scroll[0] - (
                self.lod * self.bodies.GAME_SIZE[0] / 2))
        self.base_scroll[1] += (self.player.rect.centery - self.base_scroll[1] - (
                self.lod * self.bodies.GAME_SIZE[1] / 2))
        self.draw_scroll = (int(self.base_scroll[0]), int(self.base_scroll[1]))

    def update_lod(self):
        """updates games current lad"""
        old_lod = self.lod
        self.lod = int(self.zoom) + self.lod_offset
        if self.lod == 0:
            self.lod = 1
        if self.lod >= 20:
            self.lod = 19
        elif self.lod == 0:
            self.lod = 1
        elif self.lod == 9:
            self.lod = 10
        if old_lod != self.lod:
            self.bodies.GAME_SIZE = (
                self.DISPLAY_SIZE[0] * self.zoom * 1 / self.lod, self.DISPLAY_SIZE[1] * self.zoom * 1 / self.lod)
            self.radius = int(self.zoom) + 4
            self.game_map.clear_surfaces()
            # self.set_scroll_to_player_pos()
            self.game_map.render_map(self.lod, self.radius, self.index, force=True)

        self.game_map.current_index = self.index
        self.game_map.current_lod = self.lod
        self.game_map.current_scroll = self.draw_scroll

    def update_scroll(self):
        """updates game scroll in according to the player position"""
        self.base_scroll[0] += (self.player.rect.centerx - self.base_scroll[0] - (
                self.lod * self.bodies.GAME_SIZE[0] / 2)) * self.player.dt / 20
        self.base_scroll[1] += (self.player.rect.centery - self.base_scroll[1] - (
                self.lod * self.bodies.GAME_SIZE[1] / 2)) * self.player.dt / 20
        self.draw_scroll = (int(self.base_scroll[0]), int(self.base_scroll[1]))

    def draw_debug(self):
        """draws the debug"""
        if self.debug:
            self.debug_ui.wrap_to_height = True
            self.debug_ui.rebuild()
            self.debug_ui.show()
        else:
            self.debug_ui.hide()

    def update_index(self):
        """updates the index of the game to get the current chunk the player is in"""
        self.bodies.GAME_SIZE = [int(self.bodies.GAME_SIZE[0]), int(self.bodies.GAME_SIZE[1])]
        if self.index != (int(self.player.x // (self.bodies.TILE_SIZE * self.map_generation.CHUNK_SIZE)),
                          int(self.player.y // (self.bodies.TILE_SIZE * self.map_generation.CHUNK_SIZE))):
            self.index = (int(self.player.x // (self.bodies.TILE_SIZE * self.map_generation.CHUNK_SIZE)),
                          int(self.player.y // (self.bodies.TILE_SIZE * self.map_generation.CHUNK_SIZE)))
            self.game_map.render_map(self.lod, self.radius, self.index)

    def update(self):
        """main update function for the game"""
        self.debug_ui.html_text = f"""lod offset: {self.lod_offset}display size: {self.base_display.get_size()} game size:{self.bodies.GAME_SIZE} player_accel: {self.player.acceleration}stamina: {round(self.player.current_stamina, 2)}<br>fps: {round(self.clock.get_fps(), 2)}<br>zoom: {self.zoom}<br>lod: {self.lod}<br>player position: {self.player.x} {self.player.y} draw scroll:{self.draw_scroll} draw radius {self.radius} <br>bullets:{len(self.player.gun.bullets)} player magic: {self.player.current_magic}<br>level: {self.level}<br>is_inventory)full:{self.player.inventory.is_inventory_full()}<br>inventory:{self.player.inventory}"""

        if self.paused:
            self.pause_window.show()
        else:
            self.messages.clear()
            self.pause_window.hide()

        if self.night_mode:
            self.fog = self.pygame.Surface((self.screen.get_size()[0] // self.fog_resolution,
                                            self.screen.get_size()[1] // self.fog_resolution))
            self.fog.fill(self.night_color)

        self.game_map.start_pathfinding(
            (self.player.x // self.bodies.TILE_SIZE, self.player.y // self.bodies.TILE_SIZE),
            (self.game_map.enemy_base_coordinates[0] // 100, self.game_map.enemy_base_coordinates[1] // 100))

        self.level = self.player.level
        self.update_index()
        self.time_delta = self.clock.tick(self.fps_target) / 1000.0
        # print(self.player.dt)
        self.player.dt = self.time_delta * 60
        self.screen = self.pygame.Surface(self.bodies.GAME_SIZE)

        self.update_scroll()
        self.update_lod()
        if self.process_inputs() is not None:
            return False
        if not self.paused:
            self.player.update()

        # Fill the background with Black
        self.screen.fill((0, 0, 0))

        # Draw
        self.game_map.draw_map_chunks(self.lod, self.screen, self.draw_scroll, self.radius, self.index)
        self.game_map.draw_path(self.screen, self.draw_scroll, self.lod)
        self.player.draw(self.screen, self.draw_scroll, self.lod)

        if not self.paused:
            i = 0
            while i < len(self.on_map_elements_list):
                if not self.on_map_elements_list[i].update(self.player):
                    self.on_map_elements_list[i].draw(self.screen, self.draw_scroll, self.lod)
                    i += 1

            for _index in self.game_map.get_position(self.index, self.radius + 50):
                for enemy in self.game_map.get_current_enemy(_index):
                    enemy.hide_hp_bar()
            # [[enemy.hide_hp_bar() for enemy in game_map.get_current_enemy(_index)] for _index in
            #  game_map.get_position(index, 20)]

            # update enemies
            for _index in self.game_map.get_position(self.index, self.radius):
                for enemy in self.game_map.get_current_enemy(_index):
                    if self.debug:
                        self.debug_ui.html_text += enemy.name.replace('\n', '<br>')
                    enemy.dt = self.player.dt * self.enemy_dt_factor
                    enemy.update(self.player, None)
        # draw enemies
        for _index in self.game_map.get_position(self.index, self.radius):
            for enemy in self.game_map.get_current_enemy(_index):
                enemy.draw(self.screen, self.draw_scroll, self.lod)
        if self.night_mode:
            self.draw_night_mode()
        self.base_display.unlock()
        self.screen.unlock()
        if self.SMOOTH_ZOOM:
            self.base_display.blit(self.pygame.transform.scale(self.screen, self.DISPLAY_SIZE), (0, 0))
        else:
            self.base_display.blit(self.screen, (0, 0))

        if not self.paused:
            # update skills
            for skill in self.active_skills:
                skill.update(self.player.dt)
                self.messages.append(skill.render_string)
            # update post effects
            for post_effect in self.active_post_effects:
                post_effect.update(self.player.dt)
                post_effect.draw()
        # if self.messages != []:

        # ui rebuild update draw
        if self.game_over.get_visible():
            self.game_over.draw()
        self.rebuild_messages()
        self.draw_debug()
        self.mini_map.update()
        try:
            self.manager.update(self.time_delta)
        except pygame.error:
            print('manager has fucked up')
        if self.pause_window.get_visible():
            self.pause_window.draw()
        try:
            self.manager.draw_ui(self.base_display)
        except TypeError:
            pass

        # Flip the display
        self.pygame.display.flip()
        return True

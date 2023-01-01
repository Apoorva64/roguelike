import pygame
import numpy
import pygame_gui
import random

from load_settings import settings

CONVERTER_DICT = {
    10: settings["mini_map"]["background_color"],
    0: settings["mini_map"]["border_color"]

}


class MiniMap:
    def __init__(self, game):
        self.game = game
        self.map = game.game_map.base_map
        self.manager = game.manager
        self.player = game.player
        display_rect = game.base_display.get_rect()
        self.rect = pygame.Rect(0, 0, display_rect.width // settings["mini_map"]["size"],
                                display_rect.width // settings["mini_map"]["size"])
        self.rect.topright = display_rect.topright
        self.base_surface = pygame.Surface(self.map.shape)
        self.base_surface.fill(settings["mini_map"]["ground_color"])
        self.mask_surface = pygame.Surface(self.map.shape)
        self.draw_surface = pygame.Surface(self.map.shape)

        self.ui = pygame_gui.elements.UIImage(relative_rect=self.rect, image_surface=self.draw_surface,
                                              manager=self.manager)
        self.rebuild()
        if settings['mini_map']['render']:
            self.show()
        else:
            self.hide()

    def hide(self):
        self.ui.hide()

    def show(self):
        self.ui.show()

    def rebuild(self):
        self.map = self.game.game_map.base_map
        # self.base_surface.lock()
        self.base_surface = pygame.Surface(self.map.shape)
        self.base_surface.fill(settings["mini_map"]["ground_color"])
        self.draw_surface = pygame.Surface(self.map.shape)
        self.mask_surface = pygame.Surface(self.map.shape)
        array = pygame.surfarray.pixels3d(self.base_surface)
        for y, elem_y in enumerate(array):
            for x, elem_x in enumerate(elem_y):
                if self.map[x][y] in CONVERTER_DICT:
                    array[y][x] = CONVERTER_DICT[self.map[x][y]]
            # print(elem_y)
        pygame.surfarray.blit_array(self.base_surface, array)
        # self.base_surface.unlock()

    def update(self):
        if self.ui.visible:
            self.draw_surface.fill((0, 0, 0))
            self.draw_surface.blit(self.base_surface, (0, 0))
            pygame.draw.circle(self.draw_surface, settings["mini_map"]["player_color"],
                               (self.player.x // self.game.game_map.TILE_SIZE,
                                self.player.y // self.game.game_map.TILE_SIZE),
                               settings["mini_map"]["dot_size"])

            pygame.draw.circle(self.mask_surface, settings["mini_map"]["player_color"],
                               (self.player.x // self.game.game_map.TILE_SIZE,
                                self.player.y // self.game.game_map.TILE_SIZE),
                               settings["mini_map"]["dot_size"] * 20)

            self.draw_surface.blit(self.mask_surface, (0, 0), special_flags=pygame.BLEND_MULT)
            if self.game.game_map.get_boss().is_alive:
                # print(self.game.game_map.get_boss().is_alive)
                pygame.draw.circle(self.draw_surface, settings["mini_map"]["boss_color"],
                                   (self.game.game_map.get_boss().x // self.game.game_map.TILE_SIZE,
                                    self.game.game_map.get_boss().y // self.game.game_map.TILE_SIZE),
                                   settings["mini_map"]["dot_size"])
            self.ui.set_image(pygame.transform.scale(self.draw_surface, self.rect.size))

    # def draw(self, screen):
    #     pass

# pygame.init()
# window = pygame.display.set_mode((500, 500))
#
# RUNNING = True
#
# while RUNNING:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             RUNNING = False
#     array_resolution = 300
#     array = numpy.ndarray(shape=(array_resolution, array_resolution), dtype=(numpy.int32, 3))
#     for y, elem_y in enumerate(array):
#         for x, elem_x in enumerate(elem_y):
#             array[y][x] = (128, 128, 128)
#     surface = pygame.Surface((array_resolution, array_resolution))
#     x = numpy.array(array)
#     print(x)
#     pygame.surfarray.blit_array(surface, x)
#
#     window.blit(pygame.transform.scale(surface, window.get_size()), (0, 0))
#     pygame.display.update()
#
# pygame.quit()

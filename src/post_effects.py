import random
import numpy as np
import pygame
import time


def shift5(arr, num, fill_value=np.nan):
    result = np.empty_like(arr)
    if num > 0:
        result[:num] = fill_value
        result[num:] = arr[:-num]
    elif num < 0:
        result[num:] = fill_value
        result[:num] = arr[-num:]
    else:
        result[:] = arr
    return result


def glitch(arr, blue_shift, green_shift, red_shift):
    # slicing the array
    r = arr[..., 0]
    g = arr[..., 1]
    b = arr[..., 2]
    # shifting the different colors in the x axis
    r = shift5(r, red_shift[0], 0)
    g = shift5(g, green_shift[0], 0)
    b = shift5(b, blue_shift[0], 0)
    # recombine
    rgb = np.dstack((r, g, b))

    # y axis
    # rotate the array
    rgb = np.rot90(rgb)
    # slice the array
    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]
    # shift the array
    r = shift5(r, red_shift[1], 0)
    g = shift5(g, green_shift[1], 0)
    b = shift5(b, blue_shift[1], 0)
    # recombine
    rgb = np.dstack((r, g, b))
    # rotate back to normal
    rgb = np.rot90(rgb, -1)

    return rgb


class PostEffect:
    def __init__(self, surface, duration, amount, game, amount_fall_off=1.1, delay=0, on_end_execute=lambda: None,
                 on_start_execute=lambda: None):
        self.surface = surface
        self.duration = duration
        self.amount = amount
        self.amount_fall_off = amount_fall_off
        self.game = game
        self.delay = delay
        self.on_end_execute = on_end_execute
        self.on_start_execute = on_start_execute
        self.on_start_execute_done = False

    def update(self, dt):
        self.delay -= dt
        if self.delay < 0:
            if not self.on_start_execute_done:
                self.on_start_execute()
                self.on_start_execute_done = True

            self.duration -= dt
            self.amount = self.amount / self.amount_fall_off
            if self.duration < 0:
                self.on_end_execute()
                self.delete()

    def draw(self):
        pass

    def delete(self):
        self.game.active_post_effects.remove(self)
        del self


class Glitch(PostEffect):
    def draw(self):
        if self.delay < 0:
            if -0.1 < self.amount < 0.1:
                self.delete()
            pixel_arr = pygame.surfarray.pixels3d(self.surface)
            amount = int(self.amount)
            pixel_arr = glitch(pixel_arr,
                               (random.randint(-amount, amount), random.randint(-amount, amount)),
                               (random.randint(-amount, amount), random.randint(-amount, amount)),
                               (random.randint(-amount, amount), random.randint(-amount, amount)))
            pygame.surfarray.blit_array(self.surface, pixel_arr)


class CameraShake(PostEffect):
    def update(self, dt):
        base_scroll = self.game.base_scroll
        amount = int(self.amount)
        base_scroll[0] += random.randint(-amount, amount)
        base_scroll[1] += random.randint(-amount, amount)
        self.duration -= dt
        self.amount = self.amount / self.amount_fall_off
        if self.duration < 0:
            self.delete()


class Circle(PostEffect):
    def __init__(self, surface, duration, amount, game, pos, size, color=(255, 255, 255)):
        super().__init__(surface, duration, amount, game)
        self.pos = pos
        self.size = size
        self.color = color
        self.original_amount = amount
        self.original_duration = duration
        self.game.explosion_sound_mixer.play(self.game.data['other_elements']['explosions']['sounds']['kaboom'])

    def update(self, dt):
        self.amount = self.amount / self.amount_fall_off
        if int(self.amount) <= 0:
            self.delete()

    def draw(self):
        pos = (self.pos[0] - self.game.draw_scroll[0]) / self.game.zoom, (
                self.pos[1] - self.game.draw_scroll[1]) / self.game.zoom
        # self.pos=self.game.base_display.get_rect().center
        surface = pygame.Surface(self.surface.get_size())
        surface.set_colorkey((0, 0, 0))
        surface.set_alpha(np.interp(self.amount, (0, self.original_amount), (0, 255)))
        size = self.size - np.interp(self.amount, (0, self.original_amount), (0, self.size))
        pygame.draw.circle(surface, self.color, pos, int(size) / self.game.zoom, int(self.amount) + 1)
        self.surface.blit(surface, (0, 0))


class Game:
    def __init__(self, surface):
        self.post_effects = []
        self.surface = surface
        self.base_scroll = [0, 0]
        self.draw_scroll = [0, 0]
        self.zoom = 1

    def update(self, dt):
        self.draw_scroll = (int(self.base_scroll[0]), int(self.base_scroll[1]))

# if __name__ == '__main__':
#
#     pygame.init()
#     surface = pygame.display.set_mode((500, 500))
#     clock = pygame.time.Clock()
#     game = Game(surface)
#     running = True
#
#     while running:
#
#         # 1 Process input/events
#
#         for event in pygame.event.get():
#
#             if event.type == pygame.QUIT:
#                 running = False
#             if event.type == pygame.KEYDOWN:
#                 if event.key == pygame.K_g:
#                     # adding post effect
#                     game.post_effects.append(Glitch(game.surface, 200, 10, game))
#                 if event.key == pygame.K_c:
#                     # adding post effect
#                     game.post_effects.append(Circle(game.surface, 200, 50, game, (400, 400), 100))
#                 if event.key == pygame.K_d:
#                     # adding post effect
#                     game.post_effects.append(CameraShake(game.surface, 10, 10, game))
#
#         time_delta = clock.tick(60) / 1000.0
#         dt = time_delta * 60
#         game.update(dt)
#         # Draw/render
#         surface.fill((0, 0, 0))
#         val = 100
#         pygame.draw.rect(surface, (255, 255, 255), (val, val, val, val))
#
#         # updating effects
#         tic = time.perf_counter()
#         for post_effect in game.post_effects:
#             post_effect.update(dt)
#             post_effect.draw()
#         toc = time.perf_counter()
#         print(toc - tic)
#
#         pygame.display.flip()
#
#     pygame.quit()

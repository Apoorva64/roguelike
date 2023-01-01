import pygame
import pygame_gui
import os
from menu_text import text


def main(window_surface):
    font = pygame.font.SysFont('', 24)
    length = len(os.listdir('../data/background images'))
    images = []
    for i, img in enumerate(os.listdir('../data/background images')):
        print('loading img', i)
        img2 = font.render(f" loading background {100 * i / length}", True, (255, 255, 255))

        window_surface.fill((0, 0, 0))
        # if y % 10 == 0:
        #     pygame.event.get()
        img_rect = img2.get_rect()
        rect = window_surface.get_rect()
        img_rect.center = rect.center
        window_surface.blit(img2, img_rect)
        loading_bar_rect = pygame.Rect((0, 0), (300, 10))
        loading_bar_rect.midtop = img_rect.midbottom
        pygame.draw.rect(window_surface, (255, 255, 255), loading_bar_rect, width=1)
        pygame.draw.rect(window_surface, (255, 255, 255),
                         pygame.Rect(loading_bar_rect.left, loading_bar_rect.top, 300 * i // length,
                                     loading_bar_rect.height))
        pygame.display.update()
        images.append(pygame.image.load('../data/background images/' + img))
    background = pygame.Surface(window_surface.get_size())
    background.fill(pygame.Color('#000000'))

    manager = pygame_gui.UIManager(window_surface.get_size())
    rect = pygame.Rect((0, 0), (window_surface.get_rect().width // 4, window_surface.get_rect().height // 10))
    rect.center = window_surface.get_rect().center

    start_button = pygame_gui.elements.UIButton(relative_rect=rect,
                                                text='Start',
                                                manager=manager)

    skip_button = pygame_gui.elements.UIButton(relative_rect=rect,
                                               text='Skip',
                                               manager=manager)
    skip_button.hide()

    text_box_rect = pygame.Rect((0, 0),
                                (window_surface.get_rect().width // 1.2, window_surface.get_rect().height // 1.2))
    text_box_rect.center = window_surface.get_rect().center

    text_box = pygame_gui.elements.UITextBox(text, text_box_rect, manager)
    skip_button.rect.midbottom = text_box_rect.midtop
    skip_button.rebuild()
    text_box.hide()

    clock = pygame.time.Clock()
    is_running = True
    tick = 0
    text_box_finished = False
    while is_running:
        tick += 0.2
        if tick >= len(images) - 1:
            tick = 0
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == start_button:
                        start_button.hide()
                        text_box.show()
                        skip_button.show()
                        text_box.set_active_effect(pygame_gui.TEXT_EFFECT_TYPING_APPEAR)
                        # is_running = False
                    if event.ui_element == skip_button:
                        print('clicked')
                        if not text_box_finished:
                            text_box_finished = True
                            text_box.set_active_effect(None)
                            text_box.rebuild()
                            skip_button.set_text('Start')
                        else:
                            is_running = False

            manager.process_events(event)

        manager.update(time_delta)

        window_surface.blit(pygame.transform.scale(images[int(tick)], window_surface.get_size()), (0, 0))
        manager.draw_ui(window_surface)

        pygame.display.update()


if __name__ == '__main__':
    pygame.init()
    surface = pygame.display.set_mode()

    main(surface)

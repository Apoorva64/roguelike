# import pygame
from pygame_gui.core import ColourGradient
# import pygame_gui

# import pygame_gui
#
# """
#  Pygame base template for opening a window
#
#  Sample Python/Pygame Programs
#  Simpson College Computer Science
#  http://programarcadegames.com/
#  http://simpson.edu/computer-science/
#
#  Explanation video: http://youtu.be/vRB_983kUMc
# """
#
# # Define some colors
# BLACK = (0, 0, 0)
# WHITE = (255, 255, 255)
# GREEN = (0, 255, 0)
# RED = (255, 0, 0)
#
# pygame.init()
#
# # Set the width and height of the screen [width, height]
# size = (700, 500)
# screen = pygame.display.set_mode(size)
#
# pygame.display.set_caption("My Game")
#
# # Loop until the user clicks the close button.
# done = False
#
# # Used to manage how fast the screen updates
# clock = pygame.time.Clock()
#
# # -------- Main Program Loop -----------
# angle = 0
# manager = pygame_gui.UIManager(size)
# while not done:
#     angle += 1
#     if angle > 359:
#         angle = 0
#     surface = pygame.Surface((500, 500))
#     color = ColourGradient(angle, pygame.Color(255, 38, 146, 255), pygame.Color(255, 255, 0, 255))
#     color.apply_gradient_to_surface(surface)
#     # print(color)
#     # --- Main event loop
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             done = True
#     pygame.draw.rect(screen, WHITE, pygame.Rect((100, 100), (0, 0)))
#     # --- Drawing code should go here
#     screen.blit(surface, (0, 0))
#     # --- Go ahead and update the screen with what we've drawn.
#     pygame.display.update()
#
#     # --- Limit to 60 frames per second
#     clock.tick(60)
#     manager.update(6)
#     manager.draw_ui(screen)
#
# # Close the window and quit.
# pygame.quit()

"""
 Pygame base template for opening a window

 Sample Python/Pygame Programs
 Simpson College Computer Science
 http://programarcadegames.com/
 http://simpson.edu/computer-science/

 Explanation video: http://youtu.be/vRB_983kUMc
"""
import pygame
import pygame_gui

pygame.init()
pygame.display.set_caption('Quick Start')
window_surface = pygame.display.set_mode((800, 600))

background = pygame.Surface((800, 600))
background.fill(pygame.Color('#000000'))

manager = pygame_gui.UIManager((800, 600))

hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((350, 275), (100, 50)),
                                            text='Say Hello',
                                            manager=manager)
clock = pygame.time.Clock()
while True:
    # --- Main event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                print('hwerwfdc')
        manager.process_events(event)

    # --- Game logic should go here

    # --- Screen-clearing code goes here

    # Here, we clear the screen to white. Don't put other drawing commands
    # above this, or they will be erased with this command.

    # If you want a background image, replace this clear with blit'ing the
    manager.update(clock.tick(60) / 1000.0)
    # background image.
    # manager.update(time_delta)

    window_surface.blit(background, (0, 0))
    manager.draw_ui(window_surface)

    pygame.display.update()



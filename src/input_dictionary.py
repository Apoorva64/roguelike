import pygame
from get_keyboard_layout import get_keyboard_language

# inputs dictonary
BASE_KEYBOARD_INPUTS = {
    'right': pygame.K_RIGHT,
    'left': pygame.K_LEFT,
    'up': pygame.K_UP,
    'down': pygame.K_DOWN,
}
ENG_KEYBOARD_INPUTS = {
    'right': pygame.K_d,
    'left': pygame.K_a,
    'up': pygame.K_w,
    'down': pygame.K_s,
}
FR_KEYBOARD_INPUTS = {
    'right': pygame.K_d,
    'left': pygame.K_q,
    'up': pygame.K_z,
    'down': pygame.K_s,
}

INPUT_HANDLING_DICT = ENG_KEYBOARD_INPUTS
if 'French' in get_keyboard_language():
    INPUT_HANDLING_DICT = FR_KEYBOARD_INPUTS
elif 'English' in get_keyboard_language():
    INPUT_HANDLING_DICT = ENG_KEYBOARD_INPUTS
else:
    print('keyboard not recognised defaulting to english keyboard')

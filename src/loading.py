import os
import pygame
import math

DATA_FOLDER = r"../data"
TILE_SIZE = 100


def load_lod(screen, rect, font, animation_folder):
    """
    loads images from a folder data structure:
    

    :param screen: current screen
    :param rect: screen rect
    :param font: fonts
    :param animation_folder: folder containing the items to load 
    :return: animation_dict: dictionary of loaded images
    
    """
    animation_dict = {}
    # load player animations
    for animations in os.listdir(animation_folder):
        animation_dict[animations] = {}
        animation_dict[animations]['sounds'] = {}
        for animation_type in os.listdir(os.path.join(animation_folder, animations)):
            # draw progress bar
            img = font.render(f"loading: {animations}:{animation_type}", True, (255, 255, 255))
            screen.fill((0, 0, 0))
            img_rect = img.get_rect()
            img_rect.center = rect.center
            screen.blit(img, img_rect)
            pygame.event.get()
            pygame.display.flip()
            animation_type_name = animation_type
            # if animation needs scale
            if 'scale' in animation_type:
                scale = animation_type.split(',')
                custom_scale = (float(scale[-2]), float(scale[-1]))
                animation_type_name = scale[0]
            else:
                custom_scale = False
            # going though the animations
            animation_dict[animations][animation_type_name] = {}

            for i, img in enumerate(os.listdir(os.path.join(animation_folder, animations, animation_type))):
                if img.split('.')[-1] in ['png', 'gif']:
                    # loading a full resolution image
                    full_scale = pygame.image.load(os.path.join(animation_folder, animations, animation_type, img))
                    # generating lods(levels of detail) and putting them in the dictionary
                    animation_dict[animations][animation_type_name][i] = {}
                    # checking if needs scaling
                    if not custom_scale:
                        for loop in range(1, 20):
                            animation_dict[animations][animation_type_name][i][loop] = pygame.transform.scale(
                                full_scale,
                                (math.ceil(TILE_SIZE / loop), math.ceil(TILE_SIZE / loop)))
                    else:
                        # custom scaling
                        for loop in range(1, 20):
                            animation_dict[animations][animation_type_name][i][loop] = pygame.transform.scale(
                                full_scale,
                                (math.ceil(TILE_SIZE / (loop * custom_scale[0])),
                                 math.ceil(TILE_SIZE / (loop * custom_scale[1]))))
                else:
                    animation_dict[animations]['sounds'][img.split('.')[0]] = pygame.mixer.Sound(
                        os.path.join(animation_folder, animations, animation_type, img))
    return animation_dict


def load():
    """
    loads all the textures and sounds needed for the game
    :param basediplay: 
    :return: data: a dictionary containing all the data
    """
    # loading fonts
    try:
        screen = pygame.display.get_surface()
        rect = screen.get_rect()
        font = pygame.font.SysFont('', 24)
    except AttributeError:
        screen = pygame.display.set_mode((1, 1))
        rect = screen.get_rect()
        pygame.font.init()
        font = pygame.font.SysFont('', 24)
    # loading base textures    
    data = load_lod(screen, rect, font, f"{DATA_FOLDER}/animations")

    # loading gun textures
    data['guns'] = {}
    for item in os.listdir(f"{DATA_FOLDER}/guns"):
        data['guns'][item] = load_lod(screen, rect, font, f"{DATA_FOLDER}/guns/{item}")

    # loading other items
    data['other_elements'] = load_lod(screen, rect, font, f'{DATA_FOLDER}/other_elements')

    # loading sounds
    data['sounds'] = {}
    for item in os.listdir(f"{DATA_FOLDER}/sounds"):
        if item == 'music.mp3':
            pygame.mixer.music.load(f"{DATA_FOLDER}/sounds/{item}")
            pygame.mixer.music.play(-1)

        else:
            data["sounds"][item] = pygame.mixer.Sound(f"{DATA_FOLDER}/sounds/{item}")

    return data

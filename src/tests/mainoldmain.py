from multiprocessing import Manager, freeze_support

if __name__ == '__main__':
    from subprocess import call

    # auto installer
    call(["python", "-m", "pip", "install", "-r", "requirements.txt"])

    import platform

    if platform.system() == 'Windows':
        freeze_support()
    import pygame
    from pygame.locals import *
    from post_effects import camera_shake
    import random
    from pygame_gui.core import ColourGradient
    import numpy as np

    multiprocessing_manager = Manager()
    multiprocessing_dict = multiprocessing_manager.dict()
    pathfinding_map = multiprocessing_manager.list()
    # init
    pygame.init()
    font = pygame.font.SysFont('', 24)
    clock = pygame.time.Clock()
    GRAVITY = 0
    SMOOTH_ZOOM = True
    ZOOM_SENSITIVITY = 0.2
    if not SMOOTH_ZOOM:
        ZOOM_SENSITIVITY = 1
    # Set up the drawing window
    fullscreen = True

    if fullscreen:
        base_display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE)
        DISPLAY_SIZE = base_display.get_size()
    else:
        DISPLAY_SIZE = (1920 // 2, 1080 // 2)
        base_display = pygame.display.set_mode(DISPLAY_SIZE)
    # importing modules
    import bodies
    import map_generation
    import pygame_gui

    # import math
    # import random
    mask_img = pygame.image.load('Mask.png')
    mask_img.set_colorkey((255, 255, 255))
    mask_img = pygame.transform.scale(mask_img, (DISPLAY_SIZE[0] * 2, DISPLAY_SIZE[1] * 2))

    zoom = 1 * bodies.TILE_SIZE // 50
    bodies.BASE_DISPLAY_SIZE = DISPLAY_SIZE
    bodies.GAME_SIZE = (DISPLAY_SIZE[0] * zoom, DISPLAY_SIZE[1] * zoom)
    screen = pygame.Surface(bodies.GAME_SIZE)
    # manager for out of the game lelements
    manager = pygame_gui.UIManager(DISPLAY_SIZE)
    # manager for health bars in game
    screen_manager = pygame_gui.UIManager(screen.get_size())

    # pygame.key.set_repeat(0)
    pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
    # Run until the user asks to quit
    running = True
    # moving_left = moving_right = False
    dt = 1

    # loading map

    game_map = map_generation.Map(screen, multiprocessing_dict, pathfinding_map)
    # game_map.load_chunks('block_map.npy')
    game_map.load_chunks('mapchunck2.npy')
    on_map_elements_list = game_map.current_on_map_elements
    player = bodies.Player(200 * bodies.TILE_SIZE, 300 * bodies.TILE_SIZE, bodies.TILE_SIZE, bodies.TILE_SIZE, manager,
                           screen_manager,
                           on_map_elements_list)
    enemy1 = bodies.Enemy('simik', 190 * bodies.TILE_SIZE, 300 * bodies.TILE_SIZE, 200, 200, bodies.ObjectType.ENEMY,
                          screen_manager, game_map)
    game_map.put(enemy1)
    player.jump = False
    base_scroll = [player.rect.x, player.rect.y]
    player.zoom = zoom
    fps_target = 60
    index = 0, 0
    radius = 2
    max_physics_radius = 6
    lod = 1
    pygame.display.flip()
    game_map.render_map(lod, radius, index)

    background_img = pygame.transform.scale(pygame.image.load('ezgif-frame-001.jpg'), (100, 100))
    game_map.update_current_physics_objects(index, radius)
    player.inventory.hide()
    debug_ui = pygame_gui.elements.UITextBox('', pygame.Rect((0, 0), (1000, 100)), manager=manager)
    debug_ui.bg_colour = ColourGradient(10, pygame.Color((100, 100, 100, 100)), pygame.Color((0, 0, 0, 100)))
    rect = base_display.get_rect()
    # camera_shake(base_scroll, 10)
    # mask_img.set_colorkey()
    # mask = pygame.Surface(DISPLAY_SIZE)
    # mask_img = mask
    rect2 = mask_img.get_rect()

    rect2.center = rect.center

    while running:

        game_map.start_pathfinding((player.x // bodies.TILE_SIZE, player.y // bodies.TILE_SIZE), (20, 46))
        physics_objects, player_collision = game_map.get_current_physics_objects()
        physics_objects = physics_objects.copy()
        player_collision = player_collision.copy()
        # for enemy in game_map.get_current_enemy(index):
        #     player_collision.append(enemy)
        #     physics_objects.append(enemy)

        bodies.GAME_SIZE = [int(bodies.GAME_SIZE[0]), int(bodies.GAME_SIZE[1])]
        if index != (int(player.x // (bodies.TILE_SIZE * map_generation.CHUNK_SIZE)),
                     int(player.y // (bodies.TILE_SIZE * map_generation.CHUNK_SIZE))):
            index = (int(player.x // (bodies.TILE_SIZE * map_generation.CHUNK_SIZE)),
                     int(player.y // (bodies.TILE_SIZE * map_generation.CHUNK_SIZE)))
            game_map.render_map(lod, radius, index)
            game_map.update_current_physics_objects(index, radius)
            # physics_objects, player_collision = update_physics_lists()

        time_delta = clock.tick(fps_target) / 1000.0
        player.dt = time_delta * 60
        screen = pygame.Surface(bodies.GAME_SIZE)
        base_scroll[0] += (player.rect.centerx - base_scroll[0] - (
                lod * bodies.GAME_SIZE[0] / 2)) * player.dt / 20
        base_scroll[1] += (player.rect.centery - base_scroll[1] - (
                lod * bodies.GAME_SIZE[1] / 2)) * player.dt / 20
        draw_scroll = (int(base_scroll[0]), int(base_scroll[1]))
        old_lod = lod
        lod = int(zoom)
        if old_lod != lod:
            if lod >= 20:
                lod = 19
            elif lod == 0:
                lod = 1
            elif lod == 9:
                lod = 10

            else:
                radius = int(zoom) + 6
            game_map.clear_surfaces()
            game_map.render_map(lod, radius, index, force=True)
            bodies.GAME_SIZE = (DISPLAY_SIZE[0] * zoom * 1 / lod, DISPLAY_SIZE[1] * zoom * 1 / lod)

        game_map.current_index = index
        game_map.current_lod = lod
        game_map.current_scroll = draw_scroll

        # Did the user click the window close button?
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # break
                running = False
                # TODO CLOSE THE FUCKING MULTIPROCESSING PIPE FOR FUCK SAKE
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    zoom += ZOOM_SENSITIVITY

                if event.button == 5:
                    zoom -= ZOOM_SENSITIVITY

                player.zoom = zoom
                bodies.GAME_SIZE = (DISPLAY_SIZE[0] * zoom * 1 / lod, DISPLAY_SIZE[1] * zoom * 1 / lod)
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_3:
                    fps_target -= 10
                if event.key == pygame.K_4:
                    fps_target += 10
                if event.key == pygame.K_5:
                    zoom = 1
                    player.zoom = zoom
                    lod = 1
                    radius = 7
                    game_map.clear_surfaces()
                    game_map.render_map(lod, radius, index, force=True)
                    bodies.GAME_SIZE = (DISPLAY_SIZE[0] * zoom * 1 / lod, DISPLAY_SIZE[1] * zoom * 1 / lod)
            player.process_inputs(event)

        player.update(player_collision, physics_objects)

        # Fill the background with white
        screen.fill((0, 0, 0))

        # Draw
        game_map.draw_map_chunks(lod, screen, draw_scroll, radius, index)
        game_map.draw_path(screen, draw_scroll, lod)
        player.draw(screen, draw_scroll, lod)
        debug_ui.wrap_to_height = True
        debug_ui.html_text = f"""stamina: {round(player.current_stamina, 2)}<br>fps: {round(clock.get_fps(), 2)}<br>zoom: {zoom}<br>lod: {lod}<br>player position: {player.x} {player.y}<br>draw scroll:{draw_scroll} <br>draw radius {radius}<br> enemy{enemy1.speed} <br>"""
        debug_ui.rebuild()

        manager.update(time_delta)
        screen_manager.update(time_delta)
        i = 0
        while i < len(on_map_elements_list):
            if not on_map_elements_list[i].update(player):
                on_map_elements_list[i].draw(screen, draw_scroll, lod)
                i += 1
        for _index in game_map.get_position(index, 20):
            for enemy in game_map.get_current_enemy(_index):
                enemy.hide_hp_bar()
        # [[enemy.hide_hp_bar() for enemy in game_map.get_current_enemy(_index)] for _index in
        #  game_map.get_position(index, 20)]
        for _index in game_map.get_position(index, 10):
            for enemy in game_map.get_current_enemy(_index):
                enemy.update(player, None)
                enemy.draw(screen, draw_scroll, lod)

        screen_manager.draw_ui(screen)
        if SMOOTH_ZOOM:
            base_display.blit(pygame.transform.scale(screen, DISPLAY_SIZE), (0, 0))
        else:
            base_display.blit(screen, (0, 0))

        base_display.blit(mask_img, rect2 )
        base_display.lock()
        # arr = pygame.surfarray.pixels2d(base_display)
        # for loop in range(6):
        #     blur2(arr)

        base_display.unlock()
        manager.draw_ui(base_display)

        # Flip the display
        pygame.display.flip()

    # Done! Time to quit..
    pygame.quit()

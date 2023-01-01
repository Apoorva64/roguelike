import pygame
import pygame_gui
from enums import PlayerStatus
from pygame_gui.elements.text.text_effects import TypingAppearEffect
from pygame_gui.core.drawable_shapes import RectDrawableShape, RoundedRectangleShape
from uimagicbar import UIScreenSpaceMagicBar
from uistaminabar import UIScreenSpaceStaminaBar
from uixpbar import UIScreenSpaceXpBar


class FasterTypingAppearEffect(TypingAppearEffect):
    def __init__(self, all_characters: str):
        super().__init__(all_characters)
        self.time_per_letter = 0.001

    def update(self, time_delta: float):
        """
               Updates the effect with amount of time passed since the last call to update. Adds a new
               letter to the progress every self.time_per_letter seconds.

               :param time_delta: time in seconds since last frame.
               """
        if self.text_progress < len(self.all_characters):

            if self.time_per_letter_acc < self.time_per_letter:
                self.time_per_letter_acc += time_delta
            else:
                self.time_per_letter_acc = 0.0
                self.text_progress += 10
                self.time_to_redraw = True


class Player1:
    def __init__(self):
        self.health_capacity = 100
        self.current_health = 20


image = pygame.image.load('../data/inventory_img_background/download.png')
image.set_colorkey((255, 255, 255))


class Cell:
    """Cell of the inventory"""

    def __init__(self, relative_rect: pygame.Rect, text: str, _manager, _container, usable_element=None):
        self.manager = _manager
        self.element = usable_element
        self.count = 0
        self.elements = []
        self.container = pygame_gui.core.UIContainer(manager=_manager, relative_rect=relative_rect,
                                                     container=_container)
        self.elements.append(self.container)
        rect = pygame.Rect((0, 0), (relative_rect.height, relative_rect.width))
        self.button = pygame_gui.elements.UIButton(rect, text, _manager, self.container)
        self.button.parent_elem = self
        self.elements.append(self.button)
        rect2 = pygame.Rect((0, 0), (relative_rect.height - 10, relative_rect.width - 10))
        rect2.center = rect.center
        text_rect = pygame.Rect((25, 25), (40, 40))
        text_rect.bottomright = (self.container.rect.width, self.container.rect.height)

        self.image = pygame_gui.elements.UIImage(relative_rect=rect2, image_surface=image, manager=_manager,
                                                 container=self.container, anchors={'left': 'left',
                                                                                    'right': 'right',
                                                                                    'top': 'top',
                                                                                    'bottom': 'bottom'})
        self.text = pygame_gui.elements.UILabel(text_rect,
                                                f"<font face=’verdana’ color=’#000000’ size=3.5>{self.count}</font>",
                                                manager=self.manager, container=self.container)
        self.item_image = None
        if self.element is not None:
            self.item_image = pygame_gui.elements.UIImage(relative_rect=rect2, image_surface=self.element.image,
                                                          manager=_manager,
                                                          container=self.container, anchors={'left': 'left',
                                                                                             'right': 'right',
                                                                                             'top': 'top',
                                                                                             'bottom': 'bottom'})
            self.elements.append(self.item_image)
        self.elements.append(self.image)
        self.elements.append(self.text)
        self.center_rect = rect2
        self.update()

    def __repr__(self):
        return str(self.element)

    def add_image(self):
        self.item_image = pygame_gui.elements.UIImage(relative_rect=self.center_rect,
                                                      image_surface=self.element.image[1],
                                                      manager=self.manager,
                                                      container=self.container, anchors={'left': 'left',
                                                                                         'right': 'right',
                                                                                         'top': 'top',
                                                                                         'bottom': 'bottom'})

        self.elements.append(self.item_image)
        self.text.kill()
        text_rect = pygame.Rect((25, 25), (40, 40))
        text_rect.bottomright = (self.container.rect.width, self.container.rect.height)

        self.text = pygame_gui.elements.UILabel(text_rect,
                                                f"<font face=’verdana’ color=’#000000’ size=3.5>{self.count}</font>",
                                                manager=self.manager, container=self.container)

        self.elements.append(self.text)

    def hide(self):
        for _element in self.elements:
            _element.visible = 0

    def show(self):
        for _element in self.elements:
            _element.visible = 1

    def update(self):
        self.text.set_text(str(self.count))
        # text_rect = pygame.Rect((25, 25), (40, 40))
        # text_rect.bottomright = (self.container.rect.width, self.container.rect.height)
        #
        # self.text = pygame_gui.elements.UILabel(text_rect,f"<font face=’verdana’ color=’#000000’ size=3.5>{self.count}</font>",_manager=self._manager,container=self.container)

    def use(self, creature):
        print('used')
        if self.count != 0:
            if not self.element.use(creature):
                self.count -= 1
            self.update()
        if self.count == 0:
            if self.item_image:
                self.item_image.kill()
            self.element = None


class Inventory:
    """inventory of the player"""

    def __init__(self, _manager, size, pixel_size, on_map_elements_list, parent_object):
        self.manager = _manager
        self.parent_object = parent_object

        # rect of the inventory cells
        self.rect = pygame.Rect((0, 0), (pixel_size, pixel_size))
        cell_size = pixel_size // size[0]

        # self.rect.midbottom = _manager.window_resolution[0] / 2, _manager.window_resolution[1]
        #
        # place the rect
        self.rect.center = _manager.window_resolution[0] // 2, _manager.window_resolution[1] / 2
        self.rect.centerx -= self.rect.width // 6
        # create a container for the cells
        self.container = pygame_gui.core.UIContainer(manager=_manager, relative_rect=self.rect)
        self.cells = []
        self.elements = [self.cells]
        self.on_map_elements_list = on_map_elements_list
        # create cells
        for y in range(size[0]):
            for x in range(size[1]):
                self.cells.append(
                    Cell(relative_rect=pygame.Rect((x * cell_size, y * cell_size), (cell_size, cell_size)),
                         text=f"{x}{y}",
                         _manager=_manager, _container=self.container, usable_element=None))

        # text box for info on objects
        text_box_rect = pygame.Rect((0, 0), (self.container.rect.width // 2, self.container.rect.height // 2))
        text_box_rect.bottomleft = self.container.rect.bottomright
        self.text_box = pygame_gui.elements.UITextBox(' ', text_box_rect, self.manager, layer_starting_height=1000)
        self.elements.append([self.text_box])

        # player info box
        self.player_info_rect = pygame.Rect((0, 0), (self.container.rect.width // 2, self.container.rect.height // 2))
        self.player_info_rect.bottomleft = self.container.rect.midright
        self.player_info = pygame_gui.core.UIContainer(manager=_manager, relative_rect=self.player_info_rect)
        self.elements.append([self.player_info])

        # player image
        image_rect = pygame.Rect((0, 0), (self.player_info.get_size()[0] // 2, self.player_info.get_size()[1] // 2))
        image_rect.midtop = self.player_info_rect.midtop
        image_rect.y += 10

        rect = pygame.Rect((0, 0), (self.player_info.get_size()[0] - 9, self.player_info.get_size()[1] - 9))
        rect.center = self.player_info.get_rect().center
        # background image
        self.player_info.add_element(
            pygame_gui.elements.UIImage(relative_rect=rect, image_surface=pygame.Surface((100, 100)), manager=_manager))

        self.player_info.add_element(
            pygame_gui.elements.UIImage(relative_rect=image_rect,
                                        image_surface=self.parent_object.textures[PlayerStatus.IDLE][0][1],
                                        manager=_manager))

        # equipped gun
        equipped_gun_rect = pygame.Rect((0, 0),
                                        (self.player_info.get_size()[0] // 4, self.player_info.get_size()[1] // 4))
        equipped_gun_rect.bottomleft = (
            self.player_info.rect.bottomleft[0] + 20, self.player_info.rect.bottomleft[1] - 20)
        self.equipped_gun_image = pygame_gui.elements.UIImage(relative_rect=equipped_gun_rect,
                                                              image_surface=pygame.Surface((100, 100)),
                                                              manager=_manager)

        self.equipped_gun_image.set_image(
            pygame.transform.scale(self.parent_object.gun.image[1], self.equipped_gun_image.rect.size))
        self.player_info.add_element(self.equipped_gun_image)

    def __repr__(self):
        return str(self.cells)

    def update_player_info(self):
        self.equipped_gun_image.set_image(
            pygame.transform.scale(self.parent_object.gun.image[1], self.equipped_gun_image.rect.size))

    def add_element(self, _element):
        try:
            self.on_map_elements_list.remove(_element)
        except ValueError:
            print('element not in map')
        for item in self.cells:
            if item.element is not None:
                if item.element.name == _element.name:
                    item.count += 1
                    item.update()
                    return True
        for item in self.cells:
            if item.element is None:
                item.element = _element
                item.add_image()
                item.count += 1
                item.update()
                return True
        return False

    def is_inventory_full(self):
        for item in self.cells:
            if item.element is None:
                return False
        return True

    def remove_element(self, _element):
        for item in self.cells:
            if item.element is not None:
                if item.element.name == _element.name:
                    if item.count != 0:
                        item.count -= 1
                        item.update()
                    if item.count == 0:
                        if item.item_image:
                            item.item_image.kill()
                        item.element = None

    def hide(self):
        for item_list in self.elements:
            for item in item_list:
                item.hide()

    def show(self):
        for item_list in self.elements:
            for item in item_list:
                item.show()

    @staticmethod
    def get_parent_element(event):
        element = event.ui_element
        if isinstance(element, pygame_gui.elements.UIButton):
            if hasattr(element, 'parent_elem'):
                parent_elem = element.parent_elem
                if isinstance(parent_elem, Cell):
                    return parent_elem
        return False

    def handle_inventory_inputs(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                parent_element = self.get_parent_element(event)
                if parent_element and parent_element != self.equipped_gun_image:
                    parent_element.use(self.parent_object)
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED and pygame.key.get_mods() & pygame.KMOD_CTRL:
                parent_element = self.get_parent_element(event)
                if parent_element and parent_element != self.equipped_gun_image:
                    self.parent_object.inventory.remove_element(parent_element.element)
                # if isinstance(event.ui_element, pygame_gui.elements.UIButton):
                #     parent_elem = event.ui_element.parent_elem
                #     if isinstance(parent_elem, Cell):
                #         parent_elem.use(self.parent_object)
            if event.user_type == pygame_gui.UI_BUTTON_ON_HOVERED:
                parent_element = self.get_parent_element(event)
                if parent_element:
                    self.text_box.html_text = 'my Gun:<br>' + self.parent_object.gun.name.replace("\n", "<br>")
                    self.text_box.set_active_effect(None)
                    self.text_box.rebuild()
                if parent_element and parent_element.element is not None:
                    self.text_box.html_text = parent_element.element.name.replace("\n", "<br>")
                    self.text_box.rebuild()
                    # self.text_box.set_active_effect(pygame_gui.TEXT_EFFECT_TYPING_APPEAR)

                    self.text_box.active_text_effect = FasterTypingAppearEffect(
                        self.text_box.formatted_text_block.characters)
                    # self.text_box.active_text_effect.time_per_letter = 0.01
                    self.text_box.full_redraw()
                    # self.text_box.redraw_from_chunks()

        self.manager.process_events(event)


class SkillsUi:
    """Ui for the skills"""

    def __init__(self, game):
        self.manager = game.manager
        self.game = game
        self.player = game.player
        game_size = self.game.base_display.get_size()
        self.rect = pygame.Rect((0, 0), (game_size[0] / 15, game_size[1] / 2))
        self.rect.midleft = self.game.base_display.get_rect().midleft
        self.container = pygame_gui.core.UIContainer(manager=self.manager, relative_rect=self.rect)
        surf = pygame.Surface(self.rect.size)
        surf.fill((128, 128, 128))
        self.buttons = []
        # self.background_image = pygame_gui.elements.UIImage(pygame.Rect((0, 0), self.rect.size), image_surface=surf,
        #                                                     manager=self.manager, container=self.container)
        self.rebuild()

    def rebuild(self):
        if not self.buttons == []:
            for button in self.buttons:
                button.kill()
        self.buttons = []

        button_size = min(self.rect.size[1] / len(self.game.skills), self.rect.size[0])
        rect = pygame.Rect((0, 0), (button_size, button_size))
        for i, skill in enumerate(self.game.skills):
            skill_cell = SkillCell(relative_rect=rect, manager=self.manager, tool_tip_text=skill.info,
                                   text=skill.name,
                                   container=self.container)
            self.buttons.append(skill_cell)
            rect.y += button_size


class SkillCell(pygame_gui.elements.UIButton):
    def __init__(self, relative_rect: pygame.Rect, text: str, manager, tool_tip_text='buttoasdwqn',
                 container=None):
        super().__init__(relative_rect, text, manager, tool_tip_text=tool_tip_text,
                         container=container)
        self.tool_tip_delay = 0.0
        self.font = pygame.font.SysFont('', self.rect.size[0] // 5)
        self.rebuild()


class PlayerBaseInfoUi:
    def __init__(self, game, player):
        self.manager = game.manager
        self.game = game
        self.player = player

        # container rect
        game_size = self.game.base_display.get_size()
        self.rect = pygame.Rect((0, 0), (game_size[0] / 1.3, game_size[1] / 10))
        self.rect.midbottom = self.game.base_display.get_rect().midbottom
        self.container = pygame_gui.core.UIContainer(manager=self.manager, relative_rect=self.rect)

        # magic points bar
        rect = pygame.Rect((0, 0), (self.container.rect.width, self.container.rect.height / 2))
        self.magic_points_bar = UIScreenSpaceMagicBar(rect, self.game.manager, player, container=self.container)
        self.magic_points_bar.bar_unfilled_colour = pygame.Color(128, 128, 128, 200)
        self.magic_points_bar.bar_filled_colour = pygame.Color(0, 255, 255)
        self.magic_points_bar.text_colour = pygame.Color(0, 0, 0)

        # stamina bar
        rect.width /= 1.2
        rect.midtop = rect.midbottom
        rect.centerx = self.container.rect.width / 2
        self.stamina_points_bar = UIScreenSpaceStaminaBar(rect, self.game.manager, player, container=self.container)
        self.stamina_points_bar.bar_unfilled_colour = pygame.Color(128, 128, 128, 200)
        self.stamina_points_bar.bar_filled_colour = pygame.Color(150, 0, 0)
        self.stamina_points_bar.text_colour = pygame.Color(0, 0, 0)

        # xp bar
        rect.width /= 1.2
        rect.midtop = self.game.base_display.get_rect().midtop
        self.xp_bar = UIScreenSpaceXpBar(rect, self.game.manager, player)
        self.xp_bar.bar_unfilled_colour = pygame.Color(208, 228, 128, 200)
        self.xp_bar.bar_filled_colour = pygame.Color(10, 0, 0)
        self.xp_bar.text_colour = pygame.Color(255, 255, 0)


class CustomUiHealthBar(pygame_gui.elements.UIScreenSpaceHealthBar):
    """Custom Ui health bar with int numbers"""

    def redraw(self):
        """
        Redraws the health bar rectangles and text onto the underlying sprite's image surface.
        Takes a little while so we only do it when the health has changed.
        """
        health_display_string = str(int(self.current_health)) + "/" + str(int(self.health_capacity))

        theming_parameters = {'normal_bg': self.bar_unfilled_colour,
                              'normal_border': self.border_colour,
                              'border_width': self.border_width,
                              'shadow_width': self.shadow_width,
                              'shape_corner_radius': self.shape_corner_radius,
                              'filled_bar': self.bar_filled_colour,
                              'filled_bar_width_percentage': self.health_percentage,
                              'font': self.font,
                              'text': health_display_string,
                              'normal_text': self.text_colour,
                              'text_shadow': self.text_shadow_colour,
                              'text_horiz_alignment': self.text_horiz_alignment,
                              'text_vert_alignment': self.text_vert_alignment,
                              'text_horiz_alignment_padding': self.text_horiz_alignment_padding,
                              'text_vert_alignment_padding': self.text_vert_alignment_padding,
                              }

        if self.shape == 'rectangle':
            self.drawable_shape = RectDrawableShape(self.rect, theming_parameters,
                                                    ['normal'], self.ui_manager)
        elif self.shape == 'rounded_rectangle':
            self.drawable_shape = RoundedRectangleShape(self.rect, theming_parameters,
                                                        ['normal'], self.ui_manager)

        self.set_image(self.drawable_shape.get_fresh_surface())


class PauseWindow:
    def __init__(self, game):
        self.game = game
        self.container = pygame_gui.core.UIContainer(self.game.rect, self.game.manager, starting_height=1000)
        self.gradient = pygame.Color(10, 10, 10)
        self.background = pygame.Surface(self.container.rect.size)
        self.background.fill(self.gradient)
        self.background.set_alpha(200)
        # self.container.set_image(self.background)
        # self.container.add_element(
        #     pygame_gui.elements.UIImage(self.container.rect, image_surface=self.background,
        #                                 manager=self.game.manager))
        rect = pygame.Rect((0, 0), (self.container.rect.size[0] // 4, self.container.rect.size[1] // 20))
        rect.center = self.container.rect.center
        self.quit_button = pygame_gui.elements.UIButton(rect, 'quit', self.game.manager, container=self.container)
        self.hide()

    def process_inputs(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.quit_button:
                    quit()

    def get_visible(self):
        return self.container.visible

    def draw(self):
        self.game.base_display.blit(self.background, (0, 0))

    def hide(self):
        self.container.hide()

    def show(self):
        self.container.show()


class GameOverScreen(PauseWindow):
    def __init__(self, game):
        super().__init__(game)
        self.container = pygame_gui.core.UIContainer(self.game.rect, self.game.manager, starting_height=1001)
        self.gradient = pygame.Color(10, 10, 10)
        self.background = pygame.Surface(self.container.rect.size)
        self.background.fill(self.gradient)
        self.background.set_alpha(200)
        # self.container.set_image(self.background)
        # self.container.add_element(
        #     pygame_gui.elements.UIImage(self.container.rect, image_surface=self.background,
        #                                 manager=self.game.manager))
        rect = pygame.Rect((0, 0), (self.container.rect.size[0] // 4, self.container.rect.size[1] // 20))
        rect.center = self.container.rect.center
        self.quit_button = pygame_gui.elements.UIButton(rect, 'quit', self.game.manager, container=self.container)
        space_between = rect.height
        rect.y -= space_between
        self.restart_button = pygame_gui.elements.UIButton(rect, 'restart', self.game.manager, container=self.container)
        self.hide()

        # rect.y -= space_between
        # rect.y -= rect.height
        # self.difficulty_container = pygame_gui.core.UIContainer(rect, self.game.manager, container=self.container)
        # text_box_rect = rect.copy()
        # text_box_rect.width //= 1.2
        # text_box_rect.height //= 1.2
        # text_box_rect.midright=self.difficulty_container.get_rect().midright
        # self.text_box = pygame_gui.elements.UITextEntryLine(text_box_rect, self.game.manager)
        # self.difficulty_container.add_element(self.text_box)

    def process_inputs(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.quit_button:
                    quit()
                if event.ui_element == self.restart_button:
                    self.game.rebuild_map(reset=True)


class PayerInfoUi:
    def __init__(self, game):
        self.game = game
        self.container = pygame_gui.core.UIContainer(self.game.rect, self.game.manager, starting_height=1010)
        self.gradient = pygame.Color(10, 10, 10)
        self.background = pygame.Surface(self.container.rect.size)
        self.background.fill(self.gradient)
        self.background.set_alpha(200)
        # self.container.set_image(self.background)
        # self.container.add_element(
        #     pygame_gui.elements.UIImage(self.container.rect, image_surface=self.background,
        #                                 manager=self.game.manager))
        rect = pygame.Rect((0, 0), (self.container.rect.size[0] // 3, self.container.rect.size[1] // 3))
        rect.midright = self.container.rect.midright
        self.text_box = pygame_gui.elements.UITextBox('', rect, self.game.manager, wrap_to_height=True)
        self.container.add_element(self.text_box)
        self.hide()

    def process_inputs(self, event):
        pass

    def get_visible(self):
        return self.container.visible

    def draw(self):
        self.game.base_display.blit(self.background, (0, 0))

    def hide(self):
        self.container.hide()

    def rebuild(self):
        self.text_box.html_text = self.game.player.name.replace('\n', '<br>') + \
                                  self.game.player.gun.name.replace('\n', "<br>")
        self.text_box.rebuild()

    def show(self):
        self.rebuild()
        self.container.show()

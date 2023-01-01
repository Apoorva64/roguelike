import pygame
from post_effects import Glitch, CameraShake

NUMBER_KEY_DICT = {
    0: pygame.K_0,
    1: pygame.K_1,
    2: pygame.K_2,
    3: pygame.K_3,
    4: pygame.K_4,
    5: pygame.K_5,
    6: pygame.K_6,
    7: pygame.K_7,
    8: pygame.K_8,
    9: pygame.K_9,

}


class SimpleTimer:
    def __init__(self, duration, amount, game, amount_fall_off=1.1, delay=0, on_end_execute=lambda: None,
                 on_start_execute=lambda: None, on_first_update_start=lambda: None):
        """
        Simple timer with delay and other things
        :param duration: duration of the timer
        :param amount: Value to be decremented with amount_fall_off
        :param game: game class
        :param amount_fall_off: amount to decrement amount variable
        :param delay: delay
        :param on_end_execute:  function to run on the end of the timer
        :param on_start_execute: function to run on the start of the timer acounting the delay
        :param on_first_update_start: function to run on on the instanciation of the timer
        """
        self.duration = duration
        self.amount = amount
        self.amount_fall_off = amount_fall_off
        self.game = game
        self.delay = delay
        self.on_end_execute = on_end_execute
        self.on_start_execute = on_start_execute
        self.on_start_execute_done = False
        self.exec_on_first_update = on_first_update_start
        self.exec_on_first_update_done = False

    def update(self, dt):
        """
        Update the timer
        :param dt: time delta per frame
        """
        if not self.exec_on_first_update_done:
            self.exec_on_first_update()
            self.exec_on_first_update_done = True

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
        self.game.simple_timers.remove(self)
        del self


class Skill(SimpleTimer):
    name = 'ZA WARDOO'
    duration = 1000
    magic_consumption = 100
    control = pygame.K_0
    control_str = '0'
    info = f"{name}: Stops the time when activated <br>requirements: {magic_consumption} MP <br>duration: {duration} second <br>press {control_str} to use "

    def __init__(self, game, duration=duration, amount=10, amount_fall_off=1.1, delay=0):
        """
        Base class for skills
        :param game:
        :param duration:
        :param amount:
        :param amount_fall_off:
        :param delay:
        """
        super().__init__(duration, amount, game, amount_fall_off=amount_fall_off, delay=delay)
        self.can_use = True
        self.on_start_execute = self.activate
        self.on_end_execute = self.deactivate
        self.exec_on_first_update = self.play
        self.render_string = ''
        self.sound = game.data['sounds']['ZA WARUDO.mp3']
        self.end_sound = game.data['sounds']['end_Zawardo.mp3']
        self.sound.set_volume(1)
        self.string = ''

    def activate(self):
        self.string = f'<b>{self.name} SKILL ACTIVE</b>'
        # self.game.messages.append(self.string)
        # self.game.rebuild_messages()

    def deactivate(self):
        self.end_sound.play()
        pass
        # self.game.messages.remove(self.string)
        # self.game.rebuild_messages()

    def get_can_use(self):
        if self.game.player.current_magic - self.magic_consumption > 0:
            for skill in self.game.active_skills:
                if skill.name == self.name:
                    self.can_use = False
        else:
            self.can_use = False
        if self.can_use:
            self.game.player.current_magic -= self.magic_consumption
        return self.can_use

    def update(self, dt):
        SimpleTimer.update(self, dt)
        if self.delay < 0:
            self.render_string = f'<font size=5>{self.string} left:{int(self.duration)}</font>'
        else:
            self.render_string = f'<font size=5>{self.name} starts in {int(self.delay)}</font>'

    def play(self):
        self.sound.play()

    def delete(self):
        self.game.active_skills.remove(self)
        del self


class ZaWarudo(Skill):
    name = 'ZaWarudo'
    duration = 400
    magic_consumption = 500
    control = pygame.K_1
    control_str = '1'

    # info = f"Za Wardo skill: Stops the time when activated <br>requirements: {magic_consumption} MP <br>duration: {duration} second <br>press control to use "

    def __init__(self, game):
        super().__init__(game, duration=ZaWarudo.duration, amount_fall_off=10, delay=150)
        self.can_use = True
        self.sound = game.data['sounds']['ZA WARUDO.mp3']
        # self.magic_consumption = 500
        ZaWarudo.info = f"{self.name} skill: Stops the time when activated <br>requirements: {self.magic_consumption} MP <br>duration: {self.duration} second <br>press control to use "
        self.game.skills_ui.rebuild()
        self.original_night_color = self.game.night_color

    def activate(self):
        Skill.activate(self)
        # self.game.night_mode = True
        self.game.active_post_effects.append(Glitch(self.game.base_display, 50, 200, self.game))
        self.game.enemy_dt_factor = 0
        self.game.night_color = (255, 0, 0)

    def deactivate(self):
        Skill.deactivate(self)
        self.game.enemy_dt_factor = 1
        self.game.active_post_effects.append(Glitch(self.game.base_display, 50, 200, self.game))
        self.game.night_color = self.original_night_color
        # self.game.night_mode = False

    def update(self, dt):
        Skill.update(self, dt)


class InvisibleSkill(Skill):
    name = 'Invisible'
    duration = 500
    magic_consumption = 100
    control = pygame.K_2
    control_str = '2'
    info = f"{name} skill: Makes player Invisible <br>requirements: {magic_consumption} MP <br>duration: {duration} second <br>press {control_str} to use "

    def __init__(self, game):
        super().__init__(game, duration=InvisibleSkill.duration, amount_fall_off=10, delay=10)
        self.sound = game.data['sounds']['activate.wav']
        self.end_sound = game.data['sounds']['deactivate.wav']
        self.magic_consumption = 500
        InvisibleSkill.info = f"{self.name} skill: Makes player Invisible <br>requirements: {self.magic_consumption} MP <br>duration: {self.duration} second <br>press {self.control_str} to use "
        self.game.skills_ui.rebuild()
        self.original_night_color = self.game.night_color

    def activate(self):
        Skill.activate(self)
        self.game.player.visible = False
        # self.game.night_mode = True

    def deactivate(self):
        Skill.deactivate(self)
        self.game.player.visible = True
        # self.game.night_mode = False

    def update(self, dt):
        Skill.update(self, dt)


class DoubleDmg(Skill):
    name = 'DoubleDmg'
    duration = 1000
    magic_consumption = 300
    control = pygame.K_3
    control_str = '3'
    info = f"{name} skill: Doubles gun dmg <br>requirements: {magic_consumption} MP <br>duration: {duration} second <br>press {control_str} to use "

    def __init__(self, game, ):
        super().__init__(game, duration=DoubleDmg.duration)
        self.sound = game.data['sounds']['activate.wav']
        self.end_sound = game.data['sounds']['deactivate.wav']
        self.magic_consumption = 500
        DoubleDmg.info = f"{self.name} skill: Doubles gun dmg <br>requirements: {self.magic_consumption} MP <br>duration: {self.duration} second <br>press {self.control_str} to use "
        self.game.skills_ui.rebuild()
        self.original_night_color = self.game.night_color
        self.gun = self.game.player.gun

    def activate(self):
        Skill.activate(self)
        self.gun.power *= 2

    def deactivate(self):
        Skill.deactivate(self)
        self.gun.power /= 2


class DoubleFireRate(Skill):
    name = 'DoubleFireRate'
    duration = 200
    magic_consumption = 300
    control = pygame.K_4
    control_str = '4'
    info = f"{name} skill: Doubles the firerate duh <br>requirements: {magic_consumption} MP <br>duration: {duration} second <br>press {control_str} to use "

    def __init__(self, game, ):
        super().__init__(game, duration=DoubleDmg.duration)
        self.sound = game.data['sounds']['activate.wav']
        self.end_sound = game.data['sounds']['deactivate.wav']
        self.magic_consumption = 500
        DoubleDmg.info = f"{self.name} skill: Doubles the firerate duh <br>requirements: {self.magic_consumption} MP <br>duration: {self.duration} second <br>press {self.control_str} to use "
        self.game.skills_ui.rebuild()
        self.original_night_color = self.game.night_color
        self.gun = self.game.player.gun

    def activate(self):
        Skill.activate(self)
        self.gun.fire_rate /= 2

    def deactivate(self):
        Skill.deactivate(self)
        self.gun.fire_rate *= 2


class DoubleHealthRegen(Skill):
    name = 'DoubleRegen'
    duration = 600
    magic_consumption = 200
    control = pygame.K_5
    control_str = '5'
    info = f"{name} skill: Doubles the health regeneration <br>requirements: {magic_consumption} MP <br>duration: {duration} second <br>press {control_str} to use "

    def __init__(self, game):
        super().__init__(game, duration=DoubleHealthRegen.duration)
        self.sound = game.data['sounds']['activate.wav']
        self.end_sound = game.data['sounds']['deactivate.wav']
        self.magic_consumption = 500
        DoubleDmg.info = f"{self.name} skill: Doubles the health regeneration <br>requirements: {self.magic_consumption} MP <br>duration: {self.duration} second <br>press {self.control_str} to use "
        self.game.skills_ui.rebuild()
        self.original_night_color = self.game.night_color

    def activate(self):
        Skill.activate(self)
        self.game.player.health_regen *= 2

    def deactivate(self):
        Skill.deactivate(self)
        self.game.player.health_regen /= 2

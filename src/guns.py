import pygame
from enums import ObjectType
from base_bodies import Usable, textures, ParticleSystem, Element, Creature, blit_rotate, random, \
    PhysicalObject, WALL_BOUNCINESS
import math
from loading import TILE_SIZE


class Gun(Usable):
    def __init__(self, fire_rate, max_bullets, parent_obj, game, texture=textures['guns']['normal_gun'],
                 bullet_lifetime=500,
                 power=10, max_speed=20,
                 acceleration=0.5, pos=(0, 0), name='BaseGun'):

        super().__init__(f"""{name}:
        fire rate:{int(fire_rate)}
        max bullets:{max_bullets}
        power: {int(power)}
        max speed: {round(max_speed, 2)}
        acceleration: {int(round(acceleration, 2))}""", parent_obj, pos=pos)
        self.fire_rate = fire_rate
        self.max_bullets = max_bullets
        self.max_speed = max_speed
        self.acceleration = acceleration
        self.bullets = []
        self.parent_obj = parent_obj
        self.dt = 1
        self.bullet_delay_timer = 0
        self.bullet_lifetime = bullet_lifetime
        self.textures = texture
        self.base_texture = None

        self.barrel_texture = self.textures['barrel']["idle"][0]
        self.barrel_texture_size = self.barrel_texture[1].get_size()[1] // 2
        # self.barrel_texture.fill((200,0,0))

        self.bullet_texture = texture
        self.equipped = False
        self.image = self.textures['misc']["icon"][0]
        self.power = power
        self.game = game
        self.mixer = pygame.mixer.Channel(1)

    def shoot(self, angle):
        Bullet.dt = self.dt
        current_time = pygame.time.get_ticks()

        if current_time - self.bullet_delay_timer > self.fire_rate:
            y_adding = self.barrel_texture_size * math.cos(math.radians(angle))
            x_adding = self.barrel_texture_size * math.sin(math.radians(angle))

            bullet = Bullet(self.parent_obj.rect.centerx + y_adding, self.parent_obj.rect.centery + x_adding, TILE_SIZE,
                            TILE_SIZE // 2,
                            angle, self, self.bullet_lifetime, self.game, power=self.power,
                            acceleration=self.acceleration,
                            max_speed=self.max_speed,
                            texture=self.bullet_texture)
            self.mixer.play(self.textures['misc']['sounds']['shoot'])
            bullet.speed += self.parent_obj.speed
            self.bullets.append(bullet)
            self.bullet_delay_timer = current_time

    def update(self, physics_objects, dt=1):
        if self.equipped:
            Bullet.dt = dt
            # update bullets
            [bullet.update(physics_objects) for bullet in self.bullets]
            if len(self.bullets) > self.max_bullets:
                del self.bullets[0]
        else:
            return Usable.update(self, physics_objects)

    def use(self, creature):
        if creature.object_type == ObjectType.PLAYER:
            self.bullet_texture = self.textures['bullet_normal']
        else:
            self.bullet_texture = self.textures['bullet_enemy']
        creature.gun.bullets.clear()
        if isinstance(creature, Creature) and creature.object_type == ObjectType.PLAYER:
            creature.inventory.add_element(creature.gun)

        creature.gun = self
        self.parent_obj = creature
        self.equipped = True
        if isinstance(creature, Creature) and creature.object_type == ObjectType.PLAYER:
            creature.inventory.update_player_info()
        return False

    def draw(self, screen, scroll, lod):

        if self.equipped:
            for bullet in self.bullets:
                bullet.draw(screen, scroll, lod)

            blit_rotate(screen, self.barrel_texture[lod], self.game.scale_to_screen(self.parent_obj.rect.center),
                        -self.parent_obj.angle - 90)
        else:
            screen.blit(self.image[lod],
                        self.game.scale_to_screen(self.rect.topleft))


class QuadriGun(Gun):
    def __init__(self, fire_rate, max_bullets, parent_obj, game, bullet_lifetime=500,
                 power=10, max_speed=20,
                 acceleration=0.5, pos=(0, 0)):
        # power //= 2
        super().__init__(fire_rate, max_bullets, parent_obj, game, bullet_lifetime=bullet_lifetime,
                         power=power, max_speed=max_speed,
                         acceleration=acceleration, pos=pos, name='QuadriGun')

    def shoot(self, angle):

        Bullet.dt = self.dt
        current_time = pygame.time.get_ticks()
        if current_time - self.bullet_delay_timer > self.fire_rate:
            self.mixer.play(self.textures['misc']['sounds']['shoot'])
            for loop in range(4):
                bullet = Bullet(self.parent_obj.rect.centerx, self.parent_obj.rect.centery, TILE_SIZE, TILE_SIZE // 2,
                                angle + 90 * loop, self, self.bullet_lifetime, self.game, power=self.power,
                                acceleration=self.acceleration,
                                max_speed=self.max_speed,
                                texture=self.bullet_texture)
                bullet.speed += self.parent_obj.speed
                self.bullets.append(bullet)
                self.bullet_delay_timer = current_time

    def draw(self, screen, scroll, lod):

        if self.equipped:
            for bullet in self.bullets:
                bullet.draw(screen, scroll, lod)
            for loop in range(4):
                blit_rotate(screen, self.barrel_texture[lod], self.game.scale_to_screen(self.parent_obj.rect.center),
                            -self.parent_obj.angle - 90 + loop * 90)
        else:
            screen.blit(self.image[lod],
                        self.game.scale_to_screen(self.rect.topleft))


class FireGun(Gun):
    def __init__(self, fire_rate, max_bullets, parent_obj, game, bullet_lifetime=500,
                 power=10, max_speed=20,
                 acceleration=0.5, pos=(0, 0)):
        power *= 4
        fire_rate *= 4
        if fire_rate < 500:
            fire_rate = 500
        if fire_rate > 2000:
            fire_rate = 2000
        # self.animation_counter = 0
        super().__init__(fire_rate, max_bullets, parent_obj, game, texture=textures['guns']['firegun'],
                         bullet_lifetime=bullet_lifetime, power=power, max_speed=max_speed, acceleration=acceleration,
                         pos=pos, name='Fire Gun')

        # self.fire_rate = fire_rate

    def shoot(self, angle):
        Bullet.dt = self.dt
        current_time = pygame.time.get_ticks()
        if current_time - self.bullet_delay_timer > self.fire_rate:
            bullet = FireBullet(self.parent_obj.rect.centerx, self.parent_obj.rect.centery, TILE_SIZE * 2, TILE_SIZE,
                                angle, self, self.bullet_lifetime, self.game, power=self.power,
                                acceleration=self.acceleration,
                                max_speed=self.max_speed,
                                texture=self.bullet_texture)
            self.mixer.play(self.textures['misc']['sounds']['shoot'])
            bullet.speed += self.parent_obj.speed
            self.bullets.append(bullet)
            self.bullet_delay_timer = current_time


class MiniGun(Gun):
    def __init__(self, fire_rate, max_bullets, parent_obj, game, bullet_lifetime=500,
                 power=10, max_speed=20,
                 acceleration=0.5, pos=(0, 0), spread=10):
        self.spread = spread
        max_speed /= 2
        fire_rate /= 4
        power /= 2
        super().__init__(fire_rate, max_bullets, parent_obj, game, texture=textures['guns']['minigun'],
                         bullet_lifetime=bullet_lifetime, power=power, max_speed=max_speed, acceleration=acceleration,
                         pos=pos, name='Mini Gun')

        self.barrel_texture_size /= 1.2
        self.mixer = pygame.mixer.Channel(2)
        self.textures['misc']['sounds']['shoot'].set_volume(0.4)

    def shoot(self, angle):
        Bullet.dt = self.dt
        current_time = pygame.time.get_ticks()
        if current_time - self.bullet_delay_timer > self.fire_rate:
            y_adding = self.barrel_texture_size * math.cos(math.radians(angle))
            x_adding = self.barrel_texture_size * math.sin(math.radians(angle))

            bullet = Bullet(self.parent_obj.rect.centerx + y_adding, self.parent_obj.rect.centery + x_adding, TILE_SIZE,
                            TILE_SIZE // 2,
                            angle + random.randint(-self.spread, self.spread), self, self.bullet_lifetime, self.game,
                            power=self.power,
                            acceleration=self.acceleration,
                            max_speed=self.max_speed,
                            texture=self.bullet_texture)
            self.mixer.play(self.textures['misc']['sounds']['shoot'])
            bullet.angle_difference = 0
            bullet.speed += self.parent_obj.speed
            self.bullets.append(bullet)
            self.bullet_delay_timer = current_time


class Bullet(PhysicalObject):
    dt = 1

    def __init__(self, x, y, x_size, y_size, angle, parent_obj, lifetime, game, texture, power=10,
                 acceleration=2.0, max_speed=20):
        super().__init__(x, y, x_size, y_size, game, ObjectType.BULLET, 'bullet')
        self.rect.center = (x, y)
        self.x = self.rect.x
        self.y = self.rect.y
        self.texture = texture
        self.power = power
        self.angle = angle
        self.acceleration = pygame.math.Vector2(acceleration, 0)
        self.acceleration = self.acceleration.rotate_rad(math.radians(self.angle))
        self.max_bullet_speed = max_speed

        self.lifetime = 0
        self.max_lifetime = lifetime

        self.particle_system = ParticleSystem(self.rect.center, color=(255, 0, 128))
        self.parent_obj = parent_obj
        self.game = game
        self.animation_tick = 0
        self.angle_difference = 90

    def update_speed(self):
        if not (self.speed.magnitude() > self.max_bullet_speed):
            self.speed = self.speed + self.acceleration

    def draw(self, screen, scroll, lod):
        if self.game.check_if_on_base_display(self.rect):
            if int(self.animation_tick) > len(self.texture['in_flight']) - 1:
                self.animation_tick = 0
            surface = self.texture['in_flight'][int(self.animation_tick)][lod]

            # self.particle_system.draw(screen, scroll,lod)

            # x, y = self.rect.center

            # # show hitbox
            # pygame.draw.rect(screen, (255, 255, 255),
            #                  ((self.rect.x - scroll[0]) / lod, (self.rect.y - scroll[1]) / lod, self.rect.width / lod,
            #                   self.rect.height / lod),
            #                  width=int(5 / lod))

            blit_rotate(screen, surface, self.game.scale_to_screen(self.rect.center),
                        self.angle_difference - self.angle)
            # if self.game.night_mode:
            #     light = self.parent_obj.textures["misc"]["gradient"][1][self.game.lod]
            #     light_rect = light.get_rect()
            #     light_rect.center = self.game.scale_to_base_display(self.rect.center)
            #     self.game.fog.blit(light, light_rect)
            if self.game.night_mode:
                light = self.parent_obj.textures["misc"]["gradient"][1][self.game.lod]
                light_size = light.get_size()
                # light=pygame.transform.scale(light,(light_size[0]//2,light_size[0]//2))
                light_rect = light.get_rect()
                center = self.game.scale_to_screen(self.rect.center)
                light_rect.center = (center[0] // self.game.fog_resolution, center[1] // self.game.fog_resolution)
                self.game.fog.blit(light, light_rect)
            # image = pygame.Surface((self.width, self.height))
            # rotated_image = pygame.transform.rotate(image, self.angle)
            # rect = rotated_image.get_rect(center=image.get_rect(center=self.rect.center).center)
            # rect.center = self.rect.center
            # self.rect = rect
            # self.x = self.rect.x
            # self.y = self.rect.y

    def update(self, platforms, var2=None):
        """
        updates the bullets each frame

        :param platforms: object list
        :param var2: None
        :return:
        """
        self.animation_tick += self.dt
        self.dt = Bullet.dt
        self.lifetime += Bullet.dt

        self.update_speed()
        self.angle = pygame.math.Vector2(1, 0).angle_to(self.speed)
        collisions = self.update_position(platforms)
        delete = False
        # applying damage
        for key, value in collisions['data'].items():
            # print(collisions)
            if key.object_type == ObjectType.ENEMY or key.object_type == ObjectType.PLAYER or key.object_type == ObjectType.CHEST and self.parent_obj.parent_obj.object_type != key.object_type:
                key.apply_damage(self.power, vector=self.speed.normalize())
                self.game.data['other_elements']['hitmarker']['sounds']['hitmarker'].play()
                # print('applying dmg')
                delete = True

        if collisions['left'] or collisions['right']:
            self.speed = pygame.math.Vector2(-self.speed[0], self.speed[1] * WALL_BOUNCINESS)
            self.acceleration[0] *= -1
        if collisions['top'] or collisions['bottom']:
            self.speed = pygame.math.Vector2(self.speed[0], -self.speed[1] * WALL_BOUNCINESS)
            self.acceleration[1] *= -1
        if collisions['right'] == collisions['left'] == collisions['top'] == collisions['bottom'] == True:
            self.delete()

        if self.lifetime > self.max_lifetime or delete:
            self.delete()
        return collisions

        # self.particle_system.add_particles(2, self.rect.centerx, self.rect.centery)
        # self.particle_system.update(self.dt)

    def delete(self):
        try:
            self.parent_obj.bullets.remove(self)
        except ValueError:
            print('low fps wried things happends bullet not found in' + str(self.parent_obj))
        del self
        return 0


class FireBullet(Bullet):
    def __init__(self, x, y, x_size, y_size, angle, parent_obj, lifetime, game,
                 texture=textures['guns']['firegun']['bullet_normal'], power=10,
                 acceleration=2.0, max_speed=20):
        self.max_bullet_speed = 2
        super().__init__(x, y, x_size, y_size, angle, parent_obj, lifetime, game, texture=texture, power=power,
                         acceleration=acceleration, max_speed=max_speed)
        self.angle_difference = 0

    def update(self, platforms, var2=None):
        collisions = Bullet.update(self, platforms)
        if collisions:
            if collisions['left'] or collisions['right'] or collisions['top'] or collisions['bottom']:
                try:
                    self.parent_obj.bullets.remove(self)
                except ValueError:
                    pass
                    # print(f'bullets not found in {self.parent_obj.parent_obj}')
                del self
                return 0

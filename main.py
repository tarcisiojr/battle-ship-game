import abc
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import Tuple

import pygame
import pygame.locals as locals
from pygame.event import Event
from pygame.mixer import Sound
from pygame.rect import Rect
from pygame.sprite import Group
from pygame.sprite import Sprite
from pygame.surface import Surface


BLACK = pygame.Color(0, 0, 0)
WHITE = pygame.Color(255, 255, 255)
RED = pygame.Color(255, 0, 0)
BLUE = pygame.Color(0, 0, 255)

pygame.init()
pygame.mixer.pre_init(44100, 16, 2, 4096)

# pygame.mixer.music.load('assets/rocket.wav')
# pygame.mixer.music.play(-1)
# Sound('/home/tarcisio/dados/Projetos/tarsa-game/assets/rocket.mp3').play()

SCREEN_WITH = int(pygame.display.Info().current_w * 0.90)
SCREEN_HEIGHT = int(pygame.display.Info().current_h * 0.90)

screen = pygame.display.set_mode((SCREEN_WITH, SCREEN_HEIGHT))
pygame.display.set_caption('Spaceship')
pygame.event.set_blocked(pygame.MOUSEMOTION)

running = True


class InterrupGameException(Exception):
    pass


class Drawable(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def draw(self, surface: pygame.Surface):
        pass


class DrawableMixin(Drawable):
    def __init__(self):
        self.rect = None
        self.surf = None

    def draw(self, surface: pygame.Surface):
        if self.rect and self.surf:
            surface.blit(self.surf, self.rect)


class EventHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def handle(self, event: pygame.event.Event):
        pass


class Directon(Enum):
    UP = -1
    DOWN = 1


class CustomEvent:
    CLOCK_EVENT = pygame.USEREVENT + 1
    TRIGGER_DELAYED_EVENT = pygame.USEREVENT + 2


@dataclass
class CreateElementEvent(CustomEvent):
    element: Sprite


@dataclass
class ChangeDirectionEvent(CustomEvent):
    pass


@dataclass
class ShootEvent(CustomEvent):
    pass


@dataclass
class CreateEnemyEvent(CustomEvent):
    pass


@dataclass
class AnimateEvent(CustomEvent):
    pass


@dataclass
class RestartPlayerEvent(CustomEvent):
    pass


class CreateDelayedEvent(CustomEvent, Sprite):
    def __init__(self, delay: int, event: CustomEvent, element=None):
        super().__init__()
        self.delay = delay
        self.timeout = delay
        self.event = event
        self.element = element


class Text(pygame.sprite.Sprite):
    def __init__(self, text, color=WHITE, size=50):
        super().__init__()
        self.font = pygame.font.SysFont('Comic Sans MS', size)
        self.image = self.font.render(text, True, color)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WITH // 2 - self.rect.width // 2
        self.rect.y = SCREEN_HEIGHT // 2 - self.rect.height // 2


class Scoreboard(pygame.sprite.Sprite):
    def __init__(self, score=0):
        super().__init__()
        self.score = score
        self.font = pygame.font.SysFont('Comic Sans MS', 20)
        self.image = None
        self.rect = None
        self.update_score(0)

    def update_score(self, increment):
        self.score += increment
        self.image = self.font.render(f'SCORE: {self.score}', True, WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WITH - self.rect.width - 10
        self.rect.y = 5


class LifePanel(pygame.sprite.Sprite):
    def __init__(self, total_lives=3):
        super().__init__()
        self.total_lives = total_lives
        self.lives_count = total_lives

        self.image0 = pygame.image.load(f'assets/life_0.png').convert_alpha()
        rect = self.image0.get_rect()
        self.image0 = pygame.transform.scale(self.image0, (rect.width // 2, rect.height // 2))

        self.image1 = pygame.image.load(f'assets/life_1.png').convert_alpha()
        rect = self.image1.get_rect()
        self.image1 = pygame.transform.scale(self.image1, (rect.width // 2, rect.height // 2))

        self._load_image()

    def _load_image(self):
        rect = self.image0.get_rect()
        surf = Surface((rect.width * self.total_lives + 2 * (self.total_lives - 1), rect.height), pygame.SRCALPHA)

        for i in range(0, self.total_lives):
            image = self.image1 if i < self.lives_count else self.image0
            surf.blit(image, (i * rect.width + 2 * i, 0))

        self.image = surf
        self.rect = surf.get_rect()
        self.rect.x = 10
        self.rect.y = 10

    def update_life(self, increment=1):
        self.lives_count += increment
        self._load_image()


class Explosion(pygame.sprite.Sprite, EventHandler):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.count = 1
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.sound = Sound('assets/explosion.wav')
        self.sound.play()
        self._load_image()
        self._next_animation()

    def _load_image(self):
        self.image = pygame.image.load(f'assets/explosion_{self.count}.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def _next_animation(self):
        event = Event(pygame.USEREVENT, dict(value=CreateDelayedEvent(
            delay=200,
            element=self,
            event=AnimateEvent()
        )))
        pygame.event.post(event)

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.USEREVENT and isinstance(event.value, AnimateEvent):
            if self.count >= 3:
                self.kill()
            else:
                self.count += 1
                self._load_image()
                self._next_animation()


class Star(pygame.sprite.Sprite, Drawable):
    height = 1
    width = 1
    move_step = 2

    def __init__(self, direction: Directon = Directon.DOWN):
        super().__init__()
        self.direction = direction
        self.rect = Rect(random.randint(0, SCREEN_WITH), random.randint(0, SCREEN_HEIGHT), self.width, self.height)
        self.image = Surface((self.width, self.height))
        self.image.fill(WHITE)

    def handle(self, event: pygame.event.Event):
        pass

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, WHITE, self.rect)

    def update(self, *args, **kwargs):
        self.rect.move_ip(0, self.move_step)

        if self.rect.y < 0 or self.rect.y > SCREEN_HEIGHT:
            self.rect.y = 0
            self.rect.x = random.randint(0, SCREEN_WITH)


class Bullet(pygame.sprite.Sprite, Drawable, EventHandler):
    height = 5
    width = 5

    def __init__(self, x, y, direction: Directon = Directon.UP, velocity=5):
        super().__init__()
        self.velocity = velocity
        self.direction = direction
        self.rect = Rect(int(x - self.width / 2), y - self.height, self.width, self.height)
        self.image = Surface((self.width, self.height))
        self.image.fill(WHITE)

    def handle(self, event: pygame.event.Event):
        pass

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, WHITE, self.rect)

    def update(self, *args, **kwargs):
        # noinspection PyTypeChecker
        self.rect.move_ip(0, self.velocity * self.direction.value)

        if self.rect.y < 0 or self.rect.y > SCREEN_HEIGHT:
            self.kill()


class Spaceship(pygame.sprite.Sprite):
    MOVE_STEP = 5
    MOVE_Y_STEP = 2

    def __init__(self, image_path):
        super().__init__()
        self.image = None
        self.rect = None
        self.move_x = 0
        self.move_y = 0
        self.load_image(image_path)

    def load_image(self, image_path):
        self.image = pygame.image.load(image_path).convert_alpha()
        rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (rect.width // 3, rect.height // 3))

        if not self.rect:
            self.rect = self.image.get_rect()
            self.rect.x = SCREEN_WITH // 2 - self.rect.width // 2
            self.rect.y = SCREEN_HEIGHT - self.rect.height

    def create_bullet(self, direction=Directon.UP):
        return Bullet(self.rect.x + self.rect.width // 2, self.rect.y, direction)

    def shoot(self):
        event = Event(pygame.USEREVENT, dict(value=CreateElementEvent(element=self.create_bullet())))
        pygame.event.post(event)

    def update(self, *args, **kwargs):
        if 0 < (self.rect.x + self.move_x) < (SCREEN_WITH - self.rect.width):
            self.rect.move_ip(self.move_x, 0)

        if 0 < (self.rect.y + self.move_y) < (SCREEN_HEIGHT - self.rect.height):
            self.rect.move_ip(0, self.move_y)


class Player(Spaceship, EventHandler):
    def __init__(self):
        super().__init__(image_path='assets/spaceship_1_normal.png')
        self.rocket_sound = Sound('assets/rocket.wav')
        self.shoot_sound = Sound('assets/player_shoot.wav')

    def handle(self, event: pygame.event.Event):
        if event.type == locals.KEYDOWN:
            if event.key == locals.K_RIGHT:
                self.move_x = self.MOVE_STEP
            elif event.key == locals.K_LEFT:
                self.move_x = -self.MOVE_STEP
            elif event.key == locals.K_UP:
                self.move_y = -self.MOVE_Y_STEP
                self.load_image('assets/spaceship_1_rocket.png')
                self.rocket_sound.play(-1)
            elif event.key == locals.K_DOWN:
                self.move_y = self.MOVE_STEP

        if event.type == locals.KEYUP:
            if event.key in (locals.K_LEFT, locals.K_RIGHT):
                self.move_x = 0
            elif event.key == locals.K_SPACE:
                self.shoot()
                self.shoot_sound.play()
            elif event.key in (locals.K_UP, locals.K_DOWN):
                self.move_y = 0
                self.load_image('assets/spaceship_1_normal.png')
                self.rocket_sound.stop()


@dataclass
class EnenyConfig:
    image_id: str = '1'
    movement_freq: Tuple[int, int] = (100, 1000)
    shoot_freq: Tuple[int, int] = (200, 1000)
    bullet_velocity: int = 5


class Enemy(Spaceship, EventHandler):
    def __init__(self, config: EnenyConfig):
        super().__init__(image_path=f'assets/enemy_{config.image_id}.png')
        self.shoot_sound = Sound('assets/player_shoot.wav')
        self.shoot_sound.set_volume(0.5)
        self.config = config
        self.rect.y = 0
        self.rect.x = SCREEN_WITH // 2 - self.rect.width // 2
        self._random_move()
        self._random_shoot()

    def _random_move(self):
        event = Event(pygame.USEREVENT, dict(value=CreateDelayedEvent(
            delay=random.randint(*self.config.movement_freq),
            element=self,
            event=ChangeDirectionEvent()
        )))
        pygame.event.post(event)

    def _random_shoot(self):
        event = Event(pygame.USEREVENT, dict(value=CreateDelayedEvent(
            delay=random.randint(*self.config.shoot_freq),
            element=self,
            event=ShootEvent())
        ))

        pygame.event.post(event)

    def create_bullet(self, direction=Directon.UP):
        return Bullet(self.rect.x + self.rect.width // 2, self.rect.y + self.rect.height, Directon.DOWN)

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.USEREVENT:
            if isinstance(event.value, ChangeDirectionEvent):
                self.move_x = random.randint(-1, 1) * self.MOVE_STEP
                self._random_move()
            elif isinstance(event.value, ShootEvent):
                self.shoot()
                self.shoot_sound.play()
                self._random_shoot()


class EventHolder:
    # Em milisegundos
    DELAY_CONSTANT = 100

    def __init__(self):
        self._events = Group()

    def add(self, event: CreateDelayedEvent):
        self._events.add(event)

    def update(self):
        events_to_trigger = []

        for event in self._events:
            event.timeout -= self.DELAY_CONSTANT

            if event.timeout <= 0:
                event.kill()
                events_to_trigger.append(event)

        return events_to_trigger


def _post_enemy_creation_event(delay_in_secs=10):
    event = Event(
        pygame.USEREVENT,
        dict(value=CreateDelayedEvent(delay=1000 * delay_in_secs, event=CreateEnemyEvent()))
    )
    pygame.event.post(event)


ENEMIES = [
    EnenyConfig(image_id='1', movement_freq=(100, 1000), shoot_freq=(200, 1000), bullet_velocity=5),
    EnenyConfig(image_id='2', movement_freq=(100, 700),  shoot_freq=(200, 700), bullet_velocity=5),
    EnenyConfig(image_id='3', movement_freq=(100, 1000), shoot_freq=(200, 1000), bullet_velocity=6),
    EnenyConfig(image_id='4', movement_freq=(100, 700), shoot_freq=(200, 600), bullet_velocity=6),
    EnenyConfig(image_id='5', movement_freq=(100, 500), shoot_freq=(300, 500), bullet_velocity=5),
    EnenyConfig(image_id='6', movement_freq=(100, 200), shoot_freq=(200, 400), bullet_velocity=6),
    EnenyConfig(image_id='7', movement_freq=(100, 500), shoot_freq=(200, 500), bullet_velocity=7),
    EnenyConfig(image_id='8', movement_freq=(100, 400), shoot_freq=(200, 400), bullet_velocity=7),
]


def _can_stop(event):
    return (event.type == locals.KEYDOWN and event.key == locals.K_ESCAPE) or (event.type == locals.QUIT)


def _create_animation(sprite: Sprite):
    return Explosion(
        sprite.rect.x,
        sprite.rect.y,
        sprite.rect.width,
        sprite.rect.height
    )


class Game:
    def __init__(self):
        self.running = True
        self.all_sprites = Group()
        self.enemies_group = Group()
        self.bullets_group = Group()
        self.handlable_group = Group()
        self.clock = pygame.time.Clock()
        self.events = EventHolder()
        self.player = Player()
        self.life_panel = LifePanel()
        self.score_panel = Scoreboard()
        self._create_elements()

        pygame.time.set_timer(CustomEvent.CLOCK_EVENT, EventHolder.DELAY_CONSTANT)

    def _create_elements(self):
        for i in range(100):
            self._create_element(Star())

        self._create_element(self.life_panel)
        self._create_element(self.score_panel)
        self._create_element(self.player)
        _post_enemy_creation_event(0)

    def _create_element(self, element: Sprite):
        self.all_sprites.add(element)

        if isinstance(element, Enemy):
            self.enemies_group.add(element)
        elif isinstance(element, Bullet):
            self.bullets_group.add(element)

        if isinstance(element, EventHandler) and isinstance(element, Sprite):
            self.handlable_group.add(element)

    def _handle_event(self, event: CustomEvent):
        if isinstance(event, CreateElementEvent):
            self._create_element(event.element)
        elif isinstance(event, CreateDelayedEvent):
            self.events.add(event)
        elif isinstance(event, CreateEnemyEvent):
            self._create_element(Enemy(ENEMIES[random.randint(0, min(7, self.score_panel.score // 150))]))
            _post_enemy_creation_event(max(10, 10 - self.score_panel.score // 150))
        elif isinstance(event, RestartPlayerEvent):
            self.player = Player()
            self._create_element(self.player)

    def _process_event_holder(self):
        for event in self.events.update():
            event = Event(CustomEvent.TRIGGER_DELAYED_EVENT, dict(value=event.event, element=event.element))
            pygame.event.post(event)

    def _collisions_detec(self):
        if self.player and (
                pygame.sprite.spritecollideany(self.player, self.bullets_group) or
                pygame.sprite.spritecollideany(self.player, self.enemies_group)):
            event = Event(pygame.USEREVENT, dict(value=CreateElementEvent(element=_create_animation(self.player))))
            pygame.event.post(event)
            self.player.kill()
            self.player = None
            self.life_panel.update_life(-1)

            if self.life_panel.lives_count <= 0:
                self._create_element(Text('GAME OVER'))
            else:
                event = Event(pygame.USEREVENT, dict(value=CreateDelayedEvent(
                    delay=700,
                    element=self,
                    event=RestartPlayerEvent()
                )))
                pygame.event.post(event)

        items = pygame.sprite.groupcollide(self.enemies_group, self.bullets_group, True, True)

        for enemy in items.keys():
            event = Event(pygame.USEREVENT, dict(value=CreateElementEvent(element=_create_animation(enemy))))
            pygame.event.post(event)
            self.score_panel.update_score(100)

    def _restart(self):
        self.life_panel.lives_count = 3
        self.score_panel.update_score(-self.score_panel.score)
        self.life_panel.update_life(self.life_panel.lives_count)

        for sprite in self.enemies_group:
            sprite.kill()

        for sprite in self.bullets_group:
            sprite.kill()

    def start(self):
        global screen

        while self.running:
            self._collisions_detec()

            try:
                for event in pygame.event.get():
                    self.running = not _can_stop(event)

                    if event.type == pygame.KEYUP and event.key == locals.K_r:
                        self._restart()

                    if event.type == pygame.KEYUP and event.key == locals.K_f:
                        screen = pygame.display.set_mode((SCREEN_WITH, SCREEN_HEIGHT), pygame.FULLSCREEN)

                    for handler in self.handlable_group:
                        handler.handle(event)

                    if event.type == pygame.USEREVENT:
                        self._handle_event(event.value)

                    if event.type == CustomEvent.CLOCK_EVENT:
                        self._process_event_holder()

                    if event.type == CustomEvent.TRIGGER_DELAYED_EVENT:
                        if event.element and isinstance(event.element, EventHandler) and event.element.alive():
                            event.element.handle(Event(pygame.USEREVENT, dict(value=event.value)))
                        else:
                            self._handle_event(event.value)

            except InterrupGameException:
                self.running = False

            screen.fill(BLACK)

            self.all_sprites.update()
            self.all_sprites.draw(screen)
            pygame.display.update()
            self.clock.tick(30)


Game().start()

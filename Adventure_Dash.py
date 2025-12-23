import pygame
import sys
import random
import math

pygame.init()

# --- Window (resizable) ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Hero Adventure - University Project")

# --- Colors & fonts ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
SKY_BLUE = (135, 206, 235)
PURPLE = (128, 0, 128)
DOOR_BROWN = (101, 67, 33)
DOOR_YELLOW = (255, 204, 0)
GREY = (80, 80, 80)
ORANGE = (255, 165, 0)
GRASS_GREEN = (34, 139, 34)
PLATFORM_BROWN = (101, 67, 33)
PLATFORM_DARK = (81, 47, 13)

font = pygame.font.SysFont("arial", 24)
title_font = pygame.font.SysFont("arial", 36, bold=True)

# --- Sound ---
try:
    pygame.mixer.init()
    monster_sound = pygame.mixer.Sound("monster.wav")
    monster_sound.set_volume(0.4)
    coin_sound = pygame.mixer.Sound("coin.wav")
    coin_sound.set_volume(0.3)
    jump_sound = pygame.mixer.Sound("jump.wav")
    jump_sound.set_volume(0.3)
    door_sound = pygame.mixer.Sound("door.wav")
    door_sound.set_volume(0.5)
except Exception:
    monster_sound = None
    coin_sound = None
    jump_sound = None
    door_sound = None


# --- Button Class ---
class Button:
    def __init__(self, text, rect, color, hover_color, action):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.color = color
        self.hover_color = hover_color
        self.action = action

    def draw(self):
        mx, my = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint((mx, my))
        pygame.draw.rect(screen, self.hover_color if hovered else self.color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)
        txt = font.render(self.text, True, WHITE)
        screen.blit(txt, (self.rect.centerx - txt.get_width() // 2, self.rect.centery - txt.get_height() // 2))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


# --- Platform Class ---
class Platform:
    def __init__(self, x, y, width, height=20, is_ground=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_ground = is_ground
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self):
        if self.is_ground:
            # Draw ground platform
            pygame.draw.rect(screen, BROWN, (self.x, self.y, self.width, self.height))
            # Grass on top
            pygame.draw.rect(screen, GRASS_GREEN, (self.x, self.y, self.width, 8))
            # Ground details
            for i in range(0, self.width, 20):
                pygame.draw.line(screen, PLATFORM_DARK, (self.x + i, self.y + 8), 
                               (self.x + i, self.y + self.height), 1)
        else:
            # Draw floating platform
            # Platform shadow
            pygame.draw.rect(screen, PLATFORM_DARK, (self.x + 3, self.y + 3, self.width, self.height))
            # Platform body
            pygame.draw.rect(screen, PLATFORM_BROWN, (self.x, self.y, self.width, self.height), border_radius=4)
            # Grass on top
            pygame.draw.rect(screen, GRASS_GREEN, (self.x, self.y, self.width, 6), border_radius=4)
            # Platform sides
            pygame.draw.rect(screen, PLATFORM_DARK, (self.x, self.y, 4, self.height))
            pygame.draw.rect(screen, PLATFORM_DARK, (self.x + self.width - 4, self.y, 4, self.height))
            
    def update_rect(self):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)


# --- Entities ---
class Player:
    def __init__(self):
        self.size = 40
        self.x = 50
        self.y = HEIGHT - 100
        self.speed = 5
        self.health = 100
        self.coins = 0
        self.facing_right = True
        self.vel_y = 0
        self.on_ground = False
        self.jump_power = 12
        self.can_double_jump = True
        self.double_jumped = False
        self.invincible = 0
        self.animation_frame = 0

    def draw(self):
        # Flashing when invincible
        if self.invincible > 0 and self.invincible % 10 < 5:
            return
            
        self.animation_frame += 1
        # Body with walking animation
        body_offset = math.sin(self.animation_frame * 0.2) * 2 if not self.on_ground else 0
        pygame.draw.rect(screen, GREEN, (self.x, self.y + body_offset, self.size, self.size), border_radius=5)
        # Eyes
        eye_x = self.x + 10 if self.facing_right else self.x + 25
        eye_y = self.y + 15 + body_offset
        pygame.draw.circle(screen, WHITE, (eye_x, int(eye_y)), 5)
        pygame.draw.circle(screen, BLACK, (eye_x, int(eye_y)), 2)
        # Smile
        smile_y = self.y + 30 + body_offset
        if self.facing_right:
            pygame.draw.arc(screen, WHITE, (self.x + 10, smile_y - 5, 20, 15), 0, math.pi, 2)
        else:
            pygame.draw.arc(screen, WHITE, (self.x + 10, smile_y - 5, 20, 15), 0, math.pi, 2)

    def jump(self):
        if self.on_ground:
            self.vel_y = -self.jump_power
            self.on_ground = False
            if jump_sound:
                jump_sound.play()
        elif not self.double_jumped and self.can_double_jump:
            self.vel_y = -self.jump_power * 0.8
            self.double_jumped = True
            if jump_sound:
                jump_sound.play()

    def update(self, platforms):
        # Update invincibility
        if self.invincible > 0:
            self.invincible -= 1
            
        # Apply gravity
        self.vel_y += 0.5
        self.vel_y = min(self.vel_y, 15)
        
        # Move vertically
        self.y += self.vel_y
        self.on_ground = False
        
        # Update player rect
        player_rect = pygame.Rect(self.x, self.y, self.size, self.size)
        
        # Platform collision
        for platform in platforms:
            if player_rect.colliderect(platform.rect):
                # Bottom collision (landing on platform)
                if self.vel_y > 0 and player_rect.bottom > platform.rect.top and player_rect.top < platform.rect.top:
                    self.y = platform.rect.top - self.size
                    self.vel_y = 0
                    self.on_ground = True
                    self.double_jumped = False
                # Top collision (hitting head)
                elif self.vel_y < 0 and player_rect.top < platform.rect.bottom and player_rect.bottom > platform.rect.bottom:
                    self.y = platform.rect.bottom
                    self.vel_y = 0
                # Side collision
                elif self.vel_y == 0:
                    if player_rect.right > platform.rect.left and player_rect.left < platform.rect.left:
                        self.x = platform.rect.left - self.size
                    elif player_rect.left < platform.rect.right and player_rect.right > platform.rect.right:
                        self.x = platform.rect.right

        # Ground collision
        if self.y > HEIGHT - 50 - self.size:
            self.y = HEIGHT - 50 - self.size
            self.vel_y = 0
            self.on_ground = True
            self.double_jumped = False

        # Screen boundaries
        self.x = max(0, min(WIDTH - self.size, self.x))
        
    def take_damage(self, amount):
        if self.invincible <= 0:
            self.health -= amount
            self.invincible = 30  # 0.5 seconds of invincibility
            return True
        return False


class Enemy:
    def __init__(self, x, y, speed=2):
        self.size = 35
        self.x = x
        self.y = y
        self.speed = speed
        self.direction = -1
        self.animation_frame = 0
        self.platform = None

    def draw(self):
        self.animation_frame += 1
        # Body with idle animation
        body_offset = math.sin(self.animation_frame * 0.1) * 2
        pygame.draw.rect(screen, RED, (self.x, self.y + body_offset, self.size, self.size), border_radius=3)
        # Eyes
        eye_y = self.y + 10 + body_offset
        pygame.draw.circle(screen, WHITE, (int(self.x + 10), int(eye_y)), 6)
        pygame.draw.circle(screen, WHITE, (int(self.x + 25), int(eye_y)), 6)
        pygame.draw.circle(screen, BLACK, (int(self.x + 10), int(eye_y)), 3)
        pygame.draw.circle(screen, BLACK, (int(self.x + 25), int(eye_y)), 3)
        # Angry eyebrows
        pygame.draw.line(screen, BLACK, (self.x + 8, self.y + 5 + body_offset), 
                        (self.x + 12, self.y + 8 + body_offset), 2)
        pygame.draw.line(screen, BLACK, (self.x + 23, self.y + 5 + body_offset), 
                        (self.x + 27, self.y + 8 + body_offset), 2)

    def update(self, platforms):
        self.x += self.speed * self.direction
        
        # Find current platform
        self.platform = None
        enemy_rect = pygame.Rect(self.x, self.y + 1, self.size, self.size)
        for platform in platforms:
            if enemy_rect.colliderect(platform.rect):
                self.platform = platform
                break
        
        # Turn around at platform edges or screen edges
        if self.platform:
            at_left_edge = self.x <= self.platform.x + 5
            at_right_edge = self.x + self.size >= self.platform.x + self.platform.width - 5
            if at_left_edge or at_right_edge:
                self.direction *= -1
        else:
            # If not on a platform, reverse direction
            self.direction *= -1
            # Try to find a platform to land on
            for platform in platforms:
                if (self.x + self.size//2 >= platform.x and 
                    self.x + self.size//2 <= platform.x + platform.width):
                    self.y = platform.y - self.size
                    break
        
        # Screen boundaries
        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x >= WIDTH - self.size:
            self.x = WIDTH - self.size
            self.direction = -1


class Coin:
    def __init__(self, x, y):
        self.size = 20
        self.x = x
        self.y = y
        self.animation_time = 0
        self.collected = False

    def draw(self):
        if self.collected:
            return
            
        self.animation_time += 1
        bounce = math.sin(self.animation_time * 0.1) * 3
        rotation = self.animation_time * 5
        
        # Draw coin with rotation effect
        coin_center = (int(self.x + self.size // 2), int(self.y + self.size // 2 + bounce))
        
        # Coin shadow
        pygame.draw.circle(screen, (100, 100, 0), coin_center, self.size // 2 + 1)
        
        # Main coin
        pygame.draw.circle(screen, YELLOW, coin_center, self.size // 2)
        pygame.draw.circle(screen, ORANGE, coin_center, self.size // 2 - 3)
        
        # Rotating shine effect
        shine_angle = math.radians(rotation)
        shine_x = self.x + self.size // 2 + math.cos(shine_angle) * (self.size // 4)
        shine_y = self.y + self.size // 2 + bounce + math.sin(shine_angle) * (self.size // 4)
        pygame.draw.circle(screen, WHITE, (int(shine_x), int(shine_y)), 5)


class Door:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 60
        self.animation_frame = 0
        self.platform = None
        
    def draw(self):
        self.animation_frame += 1
        glow = math.sin(self.animation_frame * 0.1) * 5
        
        # Door glow effect
        pygame.draw.circle(screen, (255, 255, 200, 100), 
                          (self.x + self.width//2, self.y + self.height//2), 
                          40 + glow)
        
        # Door frame with shadow
        pygame.draw.rect(screen, DOOR_BROWN, (self.x + 2, self.y + 2, self.width, self.height))
        pygame.draw.rect(screen, (150, 100, 50), (self.x, self.y, self.width, self.height))
        
        # Door panel
        pygame.draw.rect(screen, (120, 80, 40), (self.x + 3, self.y + 3, self.width - 6, self.height - 6))
        
        # Door details
        pygame.draw.rect(screen, (100, 60, 20), (self.x + self.width//2 - 5, self.y + 10, 10, self.height - 20))
        
        # Door handle
        handle_y = self.y + self.height//2
        pygame.draw.circle(screen, DOOR_YELLOW, (self.x + self.width - 8, handle_y), 4)
        pygame.draw.circle(screen, (200, 150, 0), (self.x + self.width - 8, handle_y), 2)
        
        # Magic sparkles
        for i in range(3):
            sparkle_x = self.x + random.randint(5, self.width - 5)
            sparkle_y = self.y + random.randint(5, self.height - 5)
            if random.random() < 0.3:
                pygame.draw.circle(screen, (255, 255, 200), (sparkle_x, sparkle_y), 2)
                
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# --- Game Manager ---
class Game:
    def __init__(self):
        self.reset_full()
        self.state = "main_menu"
        self.from_pause = False
        self.camera_x = 0
        self.max_levels = 5

    def reset_full(self):
        self.player = Player()
        self.enemies = []
        self.coins = []
        self.platforms = []
        self.door = None
        self.level = 1
        self.enemy_timer = 0
        self.coin_timer = 0
        self.generate_level()
        if monster_sound:
            monster_sound.stop()

    def generate_level(self):
        self.platforms = []
        self.coins = []
        
        # Create ground platform
        ground = Platform(0, HEIGHT - 50, WIDTH, 50, is_ground=True)
        self.platforms.append(ground)
        
        if self.level == 1:
            # Simple beginner level
            platforms_data = [
                (150, HEIGHT - 150, 100),
                (350, HEIGHT - 200, 100),
                (550, HEIGHT - 150, 100),
                (700, HEIGHT - 200, 100)  # Door platform
            ]
            
            for x, y, width in platforms_data:
                platform = Platform(x, y, width)
                self.platforms.append(platform)
                
            # Coins on platforms
            self.coins = [
                Coin(180, HEIGHT - 170),
                Coin(380, HEIGHT - 220),
                Coin(580, HEIGHT - 170),
                Coin(730, HEIGHT - 220)
            ]
            
            # Door on last platform
            door_platform = self.platforms[-1]
            self.door = Door(door_platform.x + door_platform.width//2 - 15, 
                           door_platform.y - 60)
            
        elif self.level == 2:
            # Medium difficulty
            platforms_data = [
                (100, HEIGHT - 180, 120),
                (300, HEIGHT - 250, 120),
                (500, HEIGHT - 180, 120),
                (650, HEIGHT - 300, 150)  # Door platform
            ]
            
            for x, y, width in platforms_data:
                platform = Platform(x, y, width)
                self.platforms.append(platform)
                
            # More coins
            for i in range(6):
                platform = random.choice(self.platforms[1:])
                coin_x = platform.x + random.randint(20, platform.width - 40)
                coin_y = platform.y - 30
                self.coins.append(Coin(coin_x, coin_y))
                
            # Door on highest platform
            highest_platform = min(self.platforms[1:], key=lambda p: p.y)
            self.door = Door(highest_platform.x + highest_platform.width//2 - 15,
                           highest_platform.y - 60)
            
        elif self.level <= self.max_levels:
            # Progressive difficulty
            num_platforms = min(4 + self.level, 8)
            min_y = HEIGHT - 300
            max_y = HEIGHT - 150
            
            # Create connected platforms
            prev_x = 100
            prev_y = HEIGHT - 150
            
            for i in range(num_platforms):
                if i == num_platforms - 1:
                    # Last platform for door
                    x = WIDTH - 150
                    y = random.randint(min_y, max_y - 50)
                    width = 150
                else:
                    x = prev_x + random.randint(100, 200)
                    y = random.randint(min_y, max_y)
                    # Ensure platforms are reachable
                    if abs(y - prev_y) > 100:
                        y = prev_y + random.choice([-80, -60, -40, 40, 60, 80])
                    width = random.randint(80, 140)
                
                platform = Platform(x, y, width)
                self.platforms.append(platform)
                
                prev_x = x + width
                prev_y = y
            
            # Add coins
            for i in range(4 + self.level):
                platform = random.choice(self.platforms[1:])
                coin_x = platform.x + random.randint(20, platform.width - 40)
                coin_y = platform.y - 30
                self.coins.append(Coin(coin_x, coin_y))
            
            # Door on last platform
            door_platform = self.platforms[-1]
            self.door = Door(door_platform.x + door_platform.width//2 - 15,
                           door_platform.y - 60)
        else:
            # Final level
            self.generate_final_level()
        
        if monster_sound:
            monster_sound.stop()
        self.enemies.clear()
        
    def generate_final_level(self):
        # Boss level
        platforms_data = [
            (100, HEIGHT - 200, 100),
            (250, HEIGHT - 300, 100),
            (400, HEIGHT - 250, 100),
            (550, HEIGHT - 350, 100),
            (700, HEIGHT - 200, 100)  # Door platform
        ]
        
        for x, y, width in platforms_data:
            platform = Platform(x, y, width)
            self.platforms.append(platform)
            
        # Lots of coins
        for i in range(10):
            platform = random.choice(self.platforms[1:])
            coin_x = platform.x + random.randint(20, platform.width - 40)
            coin_y = platform.y - 30
            self.coins.append(Coin(coin_x, coin_y))
            
        # Door
        door_platform = self.platforms[-1]
        self.door = Door(door_platform.x + door_platform.width//2 - 15,
                       door_platform.y - 60)

    def draw_background(self):
        # Sky gradient
        for i in range(HEIGHT):
            color_factor = i / HEIGHT
            color = (
                int(SKY_BLUE[0] * (1 - color_factor) + 100 * color_factor),
                int(SKY_BLUE[1] * (1 - color_factor) + 150 * color_factor),
                int(SKY_BLUE[2] * (1 - color_factor) + 200 * color_factor)
            )
            pygame.draw.line(screen, color, (0, i), (WIDTH, i))
        
        # Distant mountains
        for i in range(3):
            mountain_x = (i * WIDTH // 3) - (pygame.time.get_ticks() // 100) % (WIDTH // 3)
            points = [
                (mountain_x, HEIGHT - 100),
                (mountain_x + 100, HEIGHT - 250),
                (mountain_x + 200, HEIGHT - 100)
            ]
            color = (100 - i*20, 120 - i*20, 140 - i*20)
            pygame.draw.polygon(screen, color, points)
        
        # Clouds
        for i in range(4):
            cloud_x = (pygame.time.get_ticks() // 80 + i * 250) % (WIDTH + 400) - 200
            cloud_y = 60 + i * 40
            cloud_size = 25 + i * 5
            pygame.draw.circle(screen, (240, 240, 240), (int(cloud_x), cloud_y), cloud_size)
            pygame.draw.circle(screen, (240, 240, 240), (int(cloud_x + cloud_size*0.8), cloud_y - 10), cloud_size*0.8)
            pygame.draw.circle(screen, (240, 240, 240), (int(cloud_x + cloud_size*0.8), cloud_y + 10), cloud_size*0.8)

    def draw_platforms(self):
        for platform in self.platforms:
            platform.draw()

    def draw_ui(self):
        # Health bar
        health_width = 200
        health_height = 24
        health_x = 10
        health_y = 10
        
        # Background
        pygame.draw.rect(screen, (40, 40, 40), (health_x, health_y, health_width, health_height), border_radius=4)
        # Health fill
        health_percent = self.player.health / 100
        fill_width = max(0, int(health_width * health_percent))
        if health_percent > 0.6:
            health_color = GREEN
        elif health_percent > 0.3:
            health_color = YELLOW
        else:
            health_color = RED
        pygame.draw.rect(screen, health_color, (health_x, health_y, fill_width, health_height), border_radius=4)
        # Border
        pygame.draw.rect(screen, BLACK, (health_x, health_y, health_width, health_height), 2, border_radius=4)
        # Health text
        health_text = font.render(f"{self.player.health}/100", True, WHITE)
        screen.blit(health_text, (health_x + health_width + 10, health_y))
        
        # Coins display with icon
        coin_icon = font.render("🪙", True, YELLOW)
        screen.blit(coin_icon, (WIDTH - 180, 12))
        coin_text = font.render(f"{self.player.coins}", True, WHITE)
        screen.blit(coin_text, (WIDTH - 150, 10))
        
        # Level display
        level_text = font.render(f"Level {self.level}/{self.max_levels}", True, WHITE)
        screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 10))
        
        # Controls hint
        if self.state == "playing":
            controls = [
                "← →: Move",
                "SPACE: Jump",
                "ESC: Menu"
            ]
            for i, control in enumerate(controls):
                control_text = font.render(control, True, (200, 200, 200))
                screen.blit(control_text, (10, HEIGHT - 80 + i * 25))

    def update(self):
        if self.state != "playing":
            return
        
        self.player.update(self.platforms)
        
        # Spawn enemies with increasing difficulty
        self.enemy_timer += 1
        spawn_rate = max(50, 200 - (self.level * 20))
        if self.enemy_timer >= spawn_rate and len(self.enemies) < 3 + self.level // 2:
            self.spawn_enemy()
            self.enemy_timer = 0
        
        # Spawn coins
        self.coin_timer += 1
        if self.coin_timer >= 400 and len(self.coins) < 8 + self.level:
            self.spawn_coin()
            self.coin_timer = 0
        
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.update(self.platforms)
            
            # Remove off-screen enemies
            if enemy.x < -100 or enemy.x > WIDTH + 100:
                self.enemies.remove(enemy)
                continue
            
            # Enemy collision with player
            player_rect = pygame.Rect(self.player.x, self.player.y, self.player.size, self.player.size)
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.size, enemy.size)
            if player_rect.colliderect(enemy_rect):
                if self.player.take_damage(10):
                    # Knockback effect
                    if self.player.x < enemy.x:
                        self.player.x -= 30
                    else:
                        self.player.x += 30
                    
                    if self.player.health <= 0:
                        self.state = "game_over"
        
        # Coin collection
        for coin in self.coins[:]:
            if coin.collected:
                self.coins.remove(coin)
                continue
                
            player_rect = pygame.Rect(self.player.x, self.player.y, self.player.size, self.player.size)
            coin_rect = pygame.Rect(coin.x, coin.y, coin.size, coin.size)
            if player_rect.colliderect(coin_rect):
                coin.collected = True
                self.player.coins += 1
                if coin_sound:
                    coin_sound.play()
        
        # Door collision (level completion)
        if self.door:
            player_rect = pygame.Rect(self.player.x, self.player.y, self.player.size, self.player.size)
            door_rect = self.door.get_rect()
            if player_rect.colliderect(door_rect):
                self.complete_level()
    
    def spawn_enemy(self):
        if len(self.platforms) > 1:
            platform = random.choice(self.platforms[1:])
            spawn_x = platform.x + random.randint(20, max(20, platform.width - 55))
            spawn_y = platform.y - 35
            speed = 1.5 + (self.level * 0.3)
            self.enemies.append(Enemy(spawn_x, spawn_y, speed))
            if monster_sound:
                monster_sound.play()
    
    def spawn_coin(self):
        if len(self.platforms) > 1:
            platform = random.choice(self.platforms[1:])
            coin_x = platform.x + random.randint(20, max(20, platform.width - 40))
            coin_y = platform.y - 30
            self.coins.append(Coin(coin_x, coin_y))
    
    def complete_level(self):
        if door_sound:
            door_sound.play()
            
        if monster_sound:
            monster_sound.stop()
            
        if self.level >= self.max_levels:
            self.state = "victory"
        else:
            self.level += 1
            self.player.x, self.player.y = 50, HEIGHT - 100
            self.player.health = min(100, self.player.health + 25)  # Heal on level completion
            self.player.coins += 5  # Bonus coins for completing level
            self.enemy_timer = 0
            self.coin_timer = 0
            self.generate_level()


# --- Instantiate game ---
game = Game()


# --- Menu Actions ---
def start_game():
    game.reset_full()
    game.state = "playing"


def resume_game():
    game.state = "playing"
    game.from_pause = False


def open_instructions():
    game.state = "instructions"


def quit_game():
    pygame.quit()
    sys.exit()


def back_to_menu():
    if monster_sound:
        monster_sound.stop()
    game.from_pause = True
    game.state = "main_menu"


# --- Buttons ---
def create_main_menu_buttons():
    w, h = 240, 54
    cx = WIDTH // 2 - w // 2
    start_y = HEIGHT // 2 - 100
    buttons = []

    if game.from_pause:
        buttons.append(Button("Resume", (cx, start_y, w, h), GREY, GREEN, resume_game))
        start_y += 70

    buttons += [
        Button("Start Game", (cx, start_y, w, h), GREY, GREEN, start_game),
        Button("Instructions", (cx, start_y + 70, w, h), GREY, BLUE, open_instructions),
        Button("Quit", (cx, start_y + 140, w, h), GREY, RED, quit_game),
    ]
    return buttons


def create_in_game_menu_button():
    return Button("Menu", (20, HEIGHT - 60, 120, 36), GREY, GREEN, back_to_menu)


# --- Main Loop ---
clock = pygame.time.Clock()

while True:
    clicked = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_game()
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            game.generate_level()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game.state == "playing":
                    back_to_menu()
                elif game.state in ["game_over", "victory"]:
                    back_to_menu()
            if event.key == pygame.K_SPACE and game.state == "playing":
                game.player.jump()
            if event.key == pygame.K_r and game.state == "game_over":
                start_game()
            if event.key == pygame.K_RETURN and game.state == "victory":
                back_to_menu()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = event.pos

    # Movement
    keys = pygame.key.get_pressed()
    if game.state == "playing":
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            game.player.x -= game.player.speed
            game.player.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            game.player.x += game.player.speed
            game.player.facing_right = True

    game.update()

    # --- Draw ---
    if game.state == "main_menu":
        game.draw_background()
        
        # Title with glow effect
        for offset in range(3, 0, -1):
            title = title_font.render("Hero Adventure", True, (255//offset, 255//offset, 0))
            screen.blit(title, (WIDTH//2 - title.get_width()//2 + offset, 
                              HEIGHT//2 - 200 + offset))
        title = title_font.render("Hero Adventure", True, YELLOW)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 200))
        
        subtitle = font.render("University Project", True, WHITE)
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2 - 150))
        
        # Draw sample gameplay in background
        if len(game.platforms) > 0:
            sample_platform = Platform(WIDTH//2 - 100, HEIGHT//2 - 300, 200)
            sample_platform.draw()
            sample_door = Door(WIDTH//2 - 15, HEIGHT//2 - 360)
            sample_door.draw()
        
        buttons = create_main_menu_buttons()
        for b in buttons:
            b.draw()
        if clicked:
            for b in buttons:
                if b.clicked(clicked):
                    b.action()

    elif game.state == "instructions":
        screen.fill((20, 20, 40))
        
        # Decorative border
        pygame.draw.rect(screen, (50, 50, 80), (50, 50, WIDTH-100, HEIGHT-100), border_radius=10)
        pygame.draw.rect(screen, (80, 80, 120), (50, 50, WIDTH-100, HEIGHT-100), 3, border_radius=10)
        
        title = title_font.render("How to Play", True, YELLOW)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
        
        sections = [
            ("CONTROLS", [
                "← → or A D : Move Left/Right",
                "SPACE : Jump (Press again for double jump!)",
                "ESC : Pause Game / Return to Menu"
            ]),
            ("OBJECTIVE", [
                "• Collect golden coins for points",
                "• Avoid red enemies (they damage you!)",
                "• Reach the magical door to advance",
                f"• Complete all {game.max_levels} levels to win!"
            ]),
            ("FEATURES", [
                "• Double jump in mid-air",
                "• Health regenerates between levels",
                "• Enemies get faster each level",
                "• Bonus coins for completing levels"
            ])
        ]
        
        y_offset = 150
        for section_title, lines in sections:
            section_title_text = font.render(section_title, True, (100, 200, 255))
            screen.blit(section_title_text, (WIDTH//2 - section_title_text.get_width()//2, y_offset))
            y_offset += 40
            
            for line in lines:
                line_text = font.render(line, True, WHITE)
                screen.blit(line_text, (100, y_offset))
                y_offset += 30
            y_offset += 20
        
        back_btn = Button("Back to Menu", (WIDTH//2 - 110, HEIGHT - 100, 220, 50), 
                         (80, 80, 120), (100, 150, 255), back_to_menu)
        back_btn.draw()
        if clicked and back_btn.clicked(clicked):
            game.state = "main_menu"

    elif game.state == "playing":
        game.draw_background()
        game.draw_platforms()
        if game.door:
            game.door.draw()
        for coin in game.coins:
            coin.draw()
        for enemy in game.enemies:
            enemy.draw()
        game.player.draw()
        game.draw_ui()
        btn = create_in_game_menu_button()
        btn.draw()
        if clicked and btn.clicked(clicked):
            btn.action()

    elif game.state == "game_over":
        screen.fill((20, 0, 0))
        
        # Game over text with effect
        game_over_text = title_font.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
        
        # Glow effect
        for i in range(10, 0, -1):
            glow_text = title_font.render("GAME OVER", True, (255//i, 0, 0))
            glow_rect = glow_text.get_rect(center=(WIDTH//2 + random.randint(-3, 3), 
                                                  HEIGHT//2 - 60 + random.randint(-3, 3)))
            screen.blit(glow_text, glow_rect)
        
        screen.blit(game_over_text, text_rect)
        
        stats = [
            f"Final Score: {game.player.coins} coins",
            f"Level Reached: {game.level}",
            f"Enemies Defeated: {game.player.coins // 10}"
        ]
        
        for i, stat in enumerate(stats):
            stat_text = font.render(stat, True, YELLOW)
            screen.blit(stat_text, (WIDTH//2 - stat_text.get_width()//2, HEIGHT//2 + i * 30))
        
        instructions = font.render("Press R to Restart or ESC for Menu", True, WHITE)
        screen.blit(instructions, (WIDTH//2 - instructions.get_width()//2, HEIGHT//2 + 120))

    elif game.state == "victory":
        screen.fill((0, 20, 0))
        
        # Victory text with sparkle effect
        victory_text = title_font.render("VICTORY!", True, YELLOW)
        screen.blit(victory_text, (WIDTH//2 - victory_text.get_width()//2, HEIGHT//2 - 80))
        
        congrats = font.render(f"Congratulations! You completed all {game.max_levels} levels!", True, WHITE)
        screen.blit(congrats, (WIDTH//2 - congrats.get_width()//2, HEIGHT//2))
        
        final_score = font.render(f"Final Score: {game.player.coins} coins", True, (255, 215, 0))
        screen.blit(final_score, (WIDTH//2 - final_score.get_width()//2, HEIGHT//2 + 40))
        
        # Sparkle effect
        for _ in range(10):
            sparkle_x = random.randint(WIDTH//2 - 200, WIDTH//2 + 200)
            sparkle_y = random.randint(HEIGHT//2 - 100, HEIGHT//2 + 100)
            pygame.draw.circle(screen, (255, 255, 200), (sparkle_x, sparkle_y), random.randint(2, 5))
        
        instructions = font.render("Press ENTER to return to Menu", True, (200, 255, 200))
        screen.blit(instructions, (WIDTH//2 - instructions.get_width()//2, HEIGHT//2 + 100))

    pygame.display.flip()
    clock.tick(60)
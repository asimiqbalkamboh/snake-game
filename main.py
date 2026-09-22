import pygame
import random
import sys
import math
import asyncio
import os

# 1. Sound Buffer & Low Latency Initialization
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

# 2. Screen Setup
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Z. Games - Snake Adventure")

# 3. Signature Image Loader
sig_image = None
if os.path.exists("signature.jpg"):
    try:
        sig_image = pygame.image.load("signature.jpg")
        sig_image = pygame.transform.scale(sig_image, (180, 100)) # Resize for clean UI
    except Exception:
        sig_image = None
elif os.path.exists("signature.png"):
    try:
        sig_image = pygame.image.load("signature.png")
        sig_image = pygame.transform.scale(sig_image, (180, 100))
    except Exception:
        sig_image = None

# 4. Save / Load System (Local Progress)
SAVE_FILE = "save_data.txt"

def load_unlocked_level():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                val = int(f.read().strip())
                return max(1, min(50, val))
        except Exception:
            return 1
    return 1

def save_unlocked_level(level):
    try:
        current_saved = load_unlocked_level()
        if level > current_saved:
            with open(SAVE_FILE, "w") as f:
                f.write(str(level))
    except Exception:
        pass

# 5. Optimized Dynamic Sound Generator
def play_sound(freq, duration=60):
    try:
        sample_rate = 22050
        n_samples = int(sample_rate * (duration / 1000.0))
        buf = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            val = int(127 + 127 * math.sin(2 * math.pi * freq * t))
            buf.append(val)
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        sound.set_volume(0.15)
        sound.play()
    except Exception:
        pass

# 6. Color Palette
DARK_BG = (12, 16, 28)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
NEON_GREEN = (0, 255, 128)
NEON_BLUE = (0, 191, 255)
RED = (255, 50, 80)
PURPLE = (160, 32, 240)
ORANGE = (255, 140, 0)
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)
GRAY = (70, 70, 80)

# 7. Fonts Setup
font_logo = pygame.font.SysFont('impact', 55)
font_title = pygame.font.SysFont('arial black', 30)
font_large = pygame.font.SysFont('arial', 24, bold=True)
font_medium = pygame.font.SysFont('arial', 18, bold=True)
font_small = pygame.font.SysFont('arial', 13, bold=True)
font_sig = pygame.font.SysFont('cursive', 22, bold=True)

# 8. Game States
STATE_SPLASH = 0
STATE_NAME_INPUT = 1
STATE_RULES = 2
STATE_CHAR_SELECT = 3
STATE_LEVEL_SELECT = 4
STATE_PLAYING = 5
STATE_LEVEL_CLEAR = 6
STATE_GAME_OVER = 7

class SnakeCharacter:
    def __init__(self, char_id, name, color, category):
        self.id = char_id
        self.name = name
        self.color = color
        self.category = category

# 50 Character Roster Generation
CHARACTERS = []
for i in range(1, 51):
    if i <= 10: cat, col = "Water World", (0, 180 + (i*7)%75, 255)
    elif i <= 20: cat, col = "Fire World", (255, 60 + (i*15)%150, 0)
    elif i <= 30: cat, col = "Soil World", (160, 82 + (i*5)%50, 45)
    elif i <= 40: cat, col = "Monster World", (148, 0, 211)
    else: cat, col = "Cosmic World", (255, 215, (i*20)%255)
    CHARACTERS.append(SnakeCharacter(i, f"Snake Mark-{i}", col, cat))

class SnakeEntity:
    def __init__(self, x, y, color, is_user=False, name="AI Snake"):
        self.start_pos = (x, y)
        self.color = color
        self.is_user = is_user
        self.name = name
        self.reset()

    def reset(self):
        x, y = self.start_pos
        self.body = [[x, y], [x-10, y], [x-20, y]]
        self.dir = [6, 0]  # Balanced controlled speed
        self.coins = 0
        self.alive = True
        self.respawn_timer = 0

    def move(self, bounds_w, bounds_h):
        if not self.alive:
            return

        new_head = [self.body[0][0] + self.dir[0], self.body[0][1] + self.dir[1]]
        new_head[0] %= bounds_w
        new_head[1] %= bounds_h

        self.body.insert(0, new_head)
        self.body.pop()

    def grow(self, count=1):
        for _ in range(count):
            self.body.append(list(self.body[-1]))

class SnakeAdventureGame:
    def __init__(self):
        self.state = STATE_SPLASH
        self.player_name = "Player 1"
        self.current_level = 1
        self.unlocked_level = load_unlocked_level()
        self.selected_char_idx = 0

        self.timer = 60
        self.start_ticks = 0
        self.coins_list = []
        self.gift_boxes = []
        self.snakes = []
        self.user_snake = None
        self.status_msg = ""
        self.level_buttons = []

        self.clock = pygame.time.Clock()

    def setup_level(self):
        self.start_ticks = pygame.time.get_ticks()
        self.coins_list = []
        self.gift_boxes = []
        self.snakes = []

        is_boss_level = (self.current_level % 10 == 0)
        self.timer = 120 if is_boss_level else 60

        user_col = CHARACTERS[self.selected_char_idx].color
        self.user_snake = SnakeEntity(300, 400, user_col, is_user=True, name=self.player_name)
        self.snakes.append(self.user_snake)

        if is_boss_level:
            boss_col = GOLD if self.current_level == 50 else RED
            boss_name = "THE CELESTIAL KING" if self.current_level == 50 else f"KING BOSS L-{self.current_level}"
            boss = SnakeEntity(800, 400, boss_col, is_user=False, name=boss_name)
            self.snakes.append(boss)
            self.status_msg = f"BOSS LEVEL {self.current_level}! Collect max coins in 2 Minutes!"
        else:
            num_ai = min(6, 3 + (self.current_level // 10))
            for i in range(num_ai):
                rx = random.randint(100, 900)
                ry = random.randint(100, 600)
                col = (random.randint(80, 240), random.randint(80, 240), random.randint(80, 240))
                self.snakes.append(SnakeEntity(rx, ry, col, is_user=False, name=f"Bot-{i+1}"))
            self.status_msg = f"Level {self.current_level}: Equal Coins Combat Rule active!"

        for _ in range(18):
            self.spawn_coin()

    def spawn_coin(self):
        cx = random.randint(40, SCREEN_WIDTH - 40)
        cy = random.randint(80, SCREEN_HEIGHT - 40)
        self.coins_list.append([cx, cy])

    def spawn_gift_box(self):
        gx = random.randint(60, SCREEN_WIDTH - 60)
        gy = random.randint(90, SCREEN_HEIGHT - 60)
        self.gift_boxes.append({"pos": [gx, gy], "value": 5})

    def get_bg_color(self):
        if self.current_level <= 10: return (10, 35, 60)
        elif self.current_level <= 20: return (55, 15, 10)
        elif self.current_level <= 30: return (35, 25, 15)
        elif self.current_level <= 40: return (25, 10, 35)
        else: return (8, 8, 22)

    async def run(self):
        running = True
        coin_timer = 0
        gift_timer = 0
        move_tick_counter = 0

        while running:
            dt = self.clock.tick(60)
            coin_timer += dt
            gift_timer += dt
            move_tick_counter += 1

            pygame.event.pump()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if self.state == STATE_SPLASH and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.state = STATE_NAME_INPUT

                elif self.state == STATE_NAME_INPUT and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(self.player_name.strip()) > 0:
                        self.state = STATE_RULES
                    elif event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    else:
                        if len(self.player_name) < 12 and event.unicode.isalnum():
                            self.player_name += event.unicode

                elif self.state == STATE_RULES and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.state = STATE_CHAR_SELECT

                elif self.state == STATE_CHAR_SELECT and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.selected_char_idx = max(0, self.selected_char_idx - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.selected_char_idx = min(self.unlocked_level - 1, self.selected_char_idx + 1)
                    elif event.key == pygame.K_RETURN:
                        self.state = STATE_LEVEL_SELECT

                elif self.state == STATE_LEVEL_SELECT and event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for lvl, rect in self.level_buttons:
                        if rect.collidepoint(mx, my) and lvl <= self.unlocked_level:
                            self.current_level = lvl
                            self.setup_level()
                            self.state = STATE_PLAYING
                            break

                elif self.state == STATE_PLAYING and event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_LEFT, pygame.K_a] and self.user_snake.dir[0] == 0:
                        self.user_snake.dir = [-6, 0]
                    elif event.key in [pygame.K_RIGHT, pygame.K_d] and self.user_snake.dir[0] == 0:
                        self.user_snake.dir = [6, 0]
                    elif event.key in [pygame.K_UP, pygame.K_w] and self.user_snake.dir[1] == 0:
                        self.user_snake.dir = [0, -6]
                    elif event.key in [pygame.K_DOWN, pygame.K_s] and self.user_snake.dir[1] == 0:
                        self.user_snake.dir = [0, 6]

                elif self.state in [STATE_LEVEL_CLEAR, STATE_GAME_OVER] and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.state == STATE_LEVEL_CLEAR:
                            self.current_level += 1
                            self.unlocked_level = max(self.unlocked_level, self.current_level)
                            save_unlocked_level(self.unlocked_level)
                            self.state = STATE_LEVEL_SELECT
                        else:
                            self.setup_level()
                            self.state = STATE_PLAYING
                    elif event.key == pygame.K_m:
                        self.state = STATE_LEVEL_SELECT

            if self.state == STATE_PLAYING:
                elapsed_sec = (pygame.time.get_ticks() - self.start_ticks) // 1000
                remaining_time = max(0, self.timer - elapsed_sec)

                if coin_timer >= 2500:
                    self.spawn_coin()
                    coin_timer = 0

                if (self.current_level % 10 == 0) and gift_timer >= 8000:
                    self.spawn_gift_box()
                    gift_timer = 0

                if move_tick_counter % 2 == 0:
                    for s in self.snakes:
                        if not s.alive:
                            s.respawn_timer += 1
                            if s.respawn_timer >= 30:
                                s.start_pos = (random.randint(100, 900), random.randint(100, 600))
                                s.reset()
                                play_sound(700, 30)
                            continue

                        if not s.is_user and self.coins_list and (move_tick_counter % 5 == 0):
                            nearest = min(self.coins_list, key=lambda c: math.hypot(c[0]-s.body[0][0], c[1]-s.body[0][1]))
                            if nearest[0] > s.body[0][0] and s.dir[0] == 0: s.dir = [6, 0]
                            elif nearest[0] < s.body[0][0] and s.dir[0] == 0: s.dir = [-6, 0]
                            elif nearest[1] > s.body[0][1] and s.dir[1] == 0: s.dir = [0, 6]
                            elif nearest[1] < s.body[0][1] and s.dir[1] == 0: s.dir = [0, -6]

                        s.move(SCREEN_WIDTH, SCREEN_HEIGHT)

                is_boss = (self.current_level % 10 == 0)
                for s in self.snakes:
                    if not s.alive: continue
                    head = s.body[0]

                    for c in self.coins_list[:]:
                        if math.hypot(head[0] - c[0], head[1] - c[1]) < 16:
                            self.coins_list.remove(c)
                            s.coins += 1
                            s.grow(1)
                            play_sound(880, 25)

                    for g in self.gift_boxes[:]:
                        if math.hypot(head[0] - g["pos"][0], head[1] - g["pos"][1]) < 20:
                            self.gift_boxes.remove(g)
                            s.coins += g["value"]
                            s.grow(3)
                            play_sound(1100, 80)

                    if not is_boss:
                        for defender in self.snakes:
                            if defender != s and defender.alive:
                                for seg in defender.body[1:]:
                                    if math.hypot(head[0] - seg[0], head[1] - seg[1]) < 10:
                                        if s.coins == defender.coins:
                                            s.coins += defender.coins
                                            s.grow(max(2, defender.coins // 2))
                                            defender.alive = False
                                            defender.respawn_timer = 0
                                            play_sound(250, 150)
                                            self.status_msg = f"{s.name} ATE {defender.name}!"
                                        else:
                                            self.status_msg = f"CANNOT EAT! Coins must be EQUAL ({s.coins} vs {defender.coins})"

                if remaining_time <= 0:
                    winner = max(self.snakes, key=lambda x: x.coins)
                    if winner == self.user_snake:
                        self.state = STATE_LEVEL_CLEAR
                        play_sound(1200, 300)
                    else:
                        self.state = STATE_GAME_OVER
                        play_sound(200, 300)

            # Rendering
            if self.state == STATE_SPLASH: self.draw_splash()
            elif self.state == STATE_NAME_INPUT: self.draw_name_input()
            elif self.state == STATE_RULES: self.draw_rules()
            elif self.state == STATE_CHAR_SELECT: self.draw_char_select()
            elif self.state == STATE_LEVEL_SELECT: self.draw_level_select()
            elif self.state == STATE_PLAYING: self.draw_playing(remaining_time)
            elif self.state == STATE_LEVEL_CLEAR: self.draw_level_clear()
            elif self.state == STATE_GAME_OVER: self.draw_game_over()

            pygame.display.flip()
            await asyncio.sleep(0)

        pygame.quit()
        sys.exit()

    def draw_splash(self):
        screen.fill(DARK_BG)
        pygame.draw.rect(screen, GOLD, (SCREEN_WIDTH//2 - 160, 90, 320, 70), border_radius=12)
        pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//2 - 155, 95, 310, 60), border_radius=10)
        t0 = font_logo.render("Z. GAMES", True, GOLD)
        screen.blit(t0, (SCREEN_WIDTH//2 - t0.get_width()//2, 95))

        # Signature Display (Top Side or Image Display)
        if sig_image:
            screen.blit(sig_image, (SCREEN_WIDTH - 210, 20))
        else:
            sig_txt = font_sig.render("Created By: Zohaib", True, CYAN)
            screen.blit(sig_txt, (SCREEN_WIDTH - 210, 30))

        t1 = font_title.render("SNAKE ADVENTURE", True, NEON_GREEN)
        t2 = font_large.render("50 Worlds • Equal Combat • Progress Save", True, WHITE)
        t3 = font_medium.render("Press [SPACE] to Begin", True, ORANGE)

        screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 220))
        screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, 300))
        screen.blit(t3, (SCREEN_WIDTH//2 - t3.get_width()//2, 450))

    def draw_name_input(self):
        screen.fill(DARK_BG)
        t1 = font_title.render("ENTER YOUR PLAYER NAME", True, GOLD)
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2 - 150, 260, 300, 50), border_radius=8)
        pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//2 - 146, 264, 292, 42), border_radius=6)

        t_name = font_large.render(self.player_name, True, CYAN)
        t_hint = font_medium.render("Press [ENTER] when ready", True, ORANGE)

        screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 160))
        screen.blit(t_name, (SCREEN_WIDTH//2 - t_name.get_width()//2, 272))
        screen.blit(t_hint, (SCREEN_WIDTH//2 - t_hint.get_width()//2, 360))

    def draw_rules(self):
        screen.fill(DARK_BG)
        pygame.draw.rect(screen, BLACK, (100, 60, 800, 560), border_radius=15)
        pygame.draw.rect(screen, GOLD, (100, 60, 800, 560), 3, border_radius=15)

        t_title = font_title.render("GAME RULES & CONTROLS", True, GOLD)
        screen.blit(t_title, (SCREEN_WIDTH//2 - t_title.get_width()//2, 90))

        rules = [
            "1. Normal Levels: 1 Minute. Boss Levels: 2 Minutes.",
            "2. Collect Coins on the field to gain score.",
            "3. EQUAL COINS COMBAT: Eat snakes ONLY if coins match!",
            "4. Progress is saved automatically! Unlocked levels stay unlocked.",
            "5. Retry anytime from Level Menu if you fail.",
            "6. Select unlocked levels anytime from 1 to 50 Grid."
        ]

        for idx, line in enumerate(rules):
            r_txt = font_medium.render(line, True, CYAN if "EQUAL COINS" in line else WHITE)
            screen.blit(r_txt, (130, 180 + (idx * 45)))

        t_start = font_large.render("Press [SPACE] to Select Snake", True, ORANGE)
        screen.blit(t_start, (SCREEN_WIDTH//2 - t_start.get_width()//2, 540))

    def draw_char_select(self):
        screen.fill(DARK_BG)
        curr = CHARACTERS[self.selected_char_idx]

        t1 = font_title.render("SELECT YOUR SNAKE", True, GOLD)
        t2 = font_large.render(f"Character {curr.id}/50: {curr.name}", True, WHITE)
        t3 = font_medium.render(f"World: {curr.category}", True, NEON_BLUE)
        t4 = font_small.render("Press [LEFT / RIGHT] to Switch • Press [ENTER] to Continue", True, ORANGE)

        cx = SCREEN_WIDTH // 2
        for idx in range(6):
            pygame.draw.circle(screen, curr.color, (cx - (idx * 20), 360), 12)
            pygame.draw.circle(screen, WHITE, (cx - (idx * 20), 360), 12, 2)

        screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 60))
        screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, 180))
        screen.blit(t3, (SCREEN_WIDTH//2 - t3.get_width()//2, 230))
        screen.blit(t4, (SCREEN_WIDTH//2 - t4.get_width()//2, 480))

    def draw_level_select(self):
        screen.fill(DARK_BG)
        t1 = font_title.render("SELECT LEVEL (1 to 50)", True, GOLD)
        screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 30))

        self.level_buttons = []
        cols = 10
        start_x, start_y = 80, 100
        btn_w, btn_h = 75, 45
        gap_x, gap_y = 12, 12

        for i in range(1, 51):
            row = (i - 1) // cols
            col = (i - 1) % cols
            x = start_x + col * (btn_w + gap_x)
            y = start_y + row * (btn_h + gap_y)

            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.level_buttons.append((i, rect))

            is_unlocked = i <= self.unlocked_level
            bg_col = NEON_GREEN if i == self.unlocked_level else (GOLD if is_unlocked else GRAY)
            txt_col = BLACK if is_unlocked else WHITE

            pygame.draw.rect(screen, bg_col, rect, border_radius=6)
            pygame.draw.rect(screen, WHITE if is_unlocked else BLACK, rect, 2, border_radius=6)

            lbl = font_medium.render(str(i), True, txt_col)
            screen.blit(lbl, (x + btn_w//2 - lbl.get_width()//2, y + btn_h//2 - lbl.get_height()//2))

        t_hint = font_small.render("Click any UNLOCKED level to play", True, CYAN)
        screen.blit(t_hint, (SCREEN_WIDTH//2 - t_hint.get_width()//2, 650))

    def draw_playing(self, time_left):
        screen.fill(self.get_bg_color())

        for c in self.coins_list:
            pygame.draw.circle(screen, GOLD, c, 7)
            pygame.draw.circle(screen, WHITE, c, 2)

        for g in self.gift_boxes:
            pygame.draw.rect(screen, PURPLE, (g["pos"][0]-12, g["pos"][1]-12, 24, 24), border_radius=4)
            pygame.draw.rect(screen, GOLD, (g["pos"][0]-12, g["pos"][1]-12, 24, 24), 2, border_radius=4)

        for s in self.snakes:
            if not s.alive: continue
            for i, seg in enumerate(s.body):
                rad = 9 if i == 0 else 7
                pygame.draw.circle(screen, s.color, (int(seg[0]), int(seg[1])), rad)
                pygame.draw.circle(screen, BLACK, (int(seg[0]), int(seg[1])), rad, 1)

                # Head Render + Black Eyes
                if i == 0:
                    hx, hy = int(seg[0]), int(seg[1])
                    dx, dy = s.dir[0], s.dir[1]
                    if dx > 0:
                        e1, e2 = (hx + 4, hy - 3), (hx + 4, hy + 3)
                    elif dx < 0:
                        e1, e2 = (hx - 4, hy - 3), (hx - 4, hy + 3)
                    elif dy > 0:
                        e1, e2 = (hx - 3, hy + 4), (hx + 3, hy + 4)
                    else:
                        e1, e2 = (hx - 3, hy - 4), (hx + 3, hy - 4)

                    pygame.draw.circle(screen, WHITE, e1, 3)
                    pygame.draw.circle(screen, WHITE, e2, 3)
                    pygame.draw.circle(screen, BLACK, e1, 1.5)
                    pygame.draw.circle(screen, BLACK, e2, 1.5)

        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, 65))
        pygame.draw.line(screen, GOLD, (0, 65), (SCREEN_WIDTH, 65), 2)

        hud1 = font_medium.render(f"LEVEL: {self.current_level}/50", True, GOLD)
        hud2 = font_medium.render(f"TIME: {time_left}s", True, RED if time_left < 15 else WHITE)
        hud3 = font_medium.render(f"{self.player_name.upper()}: {self.user_snake.coins} COINS", True, NEON_GREEN)
        msg_t = font_small.render(self.status_msg, True, ORANGE)

        screen.blit(hud1, (20, 10))
        screen.blit(hud2, (200, 10))
        screen.blit(hud3, (380, 10))
        screen.blit(msg_t, (20, 38))

    def draw_level_clear(self):
        screen.fill(DARK_BG)
        if self.current_level == 50:
            t1 = font_title.render("🎉 CHAMPION OF SNAKE ADVENTURE! 🎉", True, GOLD)
            t2 = font_large.render(f"CONGRATULATIONS {self.player_name.upper()}!", True, NEON_GREEN)
            t3 = font_medium.render("Z. Games Trophy Unlocked!", True, WHITE)
        else:
            t1 = font_title.render(f"LEVEL {self.current_level} CLEAR!", True, NEON_GREEN)
            t2 = font_large.render(f"{self.player_name}'s Score: {self.user_snake.coins} Coins", True, WHITE)
            t3 = font_medium.render(f"Next Unlocked Level: {self.current_level + 1}", True, GOLD)

        t4 = font_large.render("Press [SPACE] to Level Menu", True, ORANGE)

        screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 180))
        screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, 270))
        screen.blit(t3, (SCREEN_WIDTH//2 - t3.get_width()//2, 340))
        screen.blit(t4, (SCREEN_WIDTH//2 - t4.get_width()//2, 470))

    def draw_game_over(self):
        screen.fill(DARK_BG)
        t1 = font_title.render(f"LEVEL {self.current_level} FAILED!", True, RED)
        t2 = font_large.render("Another snake collected more coins!", True, WHITE)
        t3 = font_medium.render("Press [SPACE] to RETRY Level • Press [M] for Level Menu", True, ORANGE)

        screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 200))
        screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, 280))
        screen.blit(t3, (SCREEN_WIDTH//2 - t3.get_width()//2, 400))

if __name__ == "__main__":
    game = SnakeAdventureGame()
    asyncio.run(game.run())
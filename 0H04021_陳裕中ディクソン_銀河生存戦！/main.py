import pygame 
import random
import os

rock_scores = [7, 10, 13, 15, 20, 25, 30]

FPS = 60
WIDTH = 500
HEIGHT =600

BLACK  = (0, 0, 0)
WHITE  = (255,255,255)
GREEN  = (0, 255, 0)
RED    = (255, 0, 0)
YELLOW = (255, 255, 0)

#遊戯初期化　and ウィンドウズの作成
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("銀河生存戦！")
clock = pygame.time.Clock()

#写真導入
background_img = pygame.image.load(os.path.join("img","background.png")).convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
player_img = pygame.image.load(os.path.join("img","player.png")).convert_alpha()
player_mini_img = pygame.transform.scale(player_img, (25,19)).convert_alpha()
pygame.display.set_icon(player_mini_img)
bullet_img = pygame.image.load(os.path.join("img","bullet.png")).convert()
rock_imgs = []
for i in range(7):
    try:
        # 画像をロード (アルファチャンネル対応)
        img = pygame.image.load(os.path.join("img", f"rock{i}.png")).convert()
        img.set_colorkey(WHITE)  # 白色を透明に設定
        img = pygame.transform.scale(img, (60, 60))  # 画像を50x50に縮小
        rock_imgs.append(img)
    except pygame.error as e:
        print(f"Error loading rock image {i}: {e}")
expl_anim = {}
expl_anim['lg'] = []
expl_anim['sm'] = []
expl_anim['player'] = []
for i in range(6):
    expl_img = pygame.image.load(os.path.join("img", f"expl{i}.png")).convert_alpha()
    expl_anim['lg'].append(pygame.transform.scale(expl_img, (60, 60)))
    expl_anim['sm'].append(pygame.transform.scale(expl_img, (30, 30)))
    player_expl_img = pygame.image.load(os.path.join("img", f"player_expl{i}.png")).convert_alpha()
    expl_anim['player'].append(player_expl_img)
power_imgs = {}
power_imgs['shield'] = pygame.image.load(os.path.join("img", "shield.png")).convert_alpha()
power_imgs['gun'] = pygame.image.load(os.path.join("img", "gun.png")).convert_alpha()

#音を立てて
shoot_sound = pygame.mixer.Sound(os.path.join("sound","shoot.mp3"))
gun_sound = pygame.mixer.Sound(os.path.join("sound","pow1.mp3"))
shield_sound = pygame.mixer.Sound(os.path.join("sound","pow0.mp3"))
die_sound = pygame.mixer.Sound(os.path.join("sound","death.mp3"))
expl_sounds = [
    pygame.mixer.Sound(os.path.join("sound","expl0.mp3")),
    pygame.mixer.Sound(os.path.join("sound","expl1.mp3"))
]
pygame.mixer.music.load(os.path.join("sound","background.mp3"))
expl_sounds[0].set_volume(0.3)
expl_sounds[1].set_volume(0.3) 


font_name = os.path.join("MPLUSRounded1c-Black.ttf")


cached_text_surface = None

text_cache = {}

def get_text_surface(text, size):
    # キャッシュにテキストが存在しない場合、新しく作成
    if (text, size) not in text_cache:
        font = pygame.font.Font(font_name, size)
        text_surface = font.render(text, True, WHITE)
        text_cache[(text, size)] = text_surface
    return text_cache[(text, size)]

def draw_text(surf, text, size, x, y):
    text_surface = get_text_surface(text, size)
    text_rect = text_surface.get_rect()
    text_rect.centerx = x
    text_rect.top = y
    surf.blit(text_surface, text_rect)

def new_rock():
        r = Rock()
        all_sprites.add(r)
        rocks.add(r)
  
def draw_health(surf, hp, x, y):

    if hp < 0:
        hp = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (hp/100)*BAR_LENGTH
    outline_rect = pygame.Rect(x, y, BAR_LENGTH,BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, GREEN, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)

def draw_lives(surf, lives, img, x, y):
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + 32*i
        img_rect.y = y
        surf.blit(img,img_rect)

def draw_init():
    screen.blit(background_img, (0,0))
    draw_text(screen, '銀河生存戦！', 64, WIDTH/2, HEIGHT/4)
    draw_text(screen, '← →移動 、空白鍵は射撃する', 22, WIDTH/2, HEIGHT/2)
    draw_text(screen, '任意のキーを押してゲームスタート', 18, WIDTH/2, HEIGHT*3/4)
    pygame.display.update()
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return True
            elif event.type == pygame.KEYUP:
                waiting = False
                return False
            
def draw_fps(surf, clock, x, y):
    fps = str(int(clock.get_fps()))
    draw_text(surf, fps + " FPS", 18, x, y)

# ゲームループ内
draw_fps(screen, clock, WIDTH - 100, 10)



class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(player_img, (50, 38))
        self.image.set_colorkey(WHITE)  
        self.rect = self.image.get_rect()
        self.radius = 20
        #pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 10
        self.speedx = 0
        self.acceleration = 0.5  # 加速度
        self.max_speed = 8  # 最大速度
        self.friction = 0.9  # 摩擦による減速
        self.health = 100
        self.lives = 3
        self.hidden = False
        self.hide_time = 0
        self.gun = 1
        self.gun_time = 0
        self.last_shot_time = 0

    def update(self):
        now = pygame.time.get_ticks()
        if self.gun > 1 and now - self.gun_time > 5000:
            self.gun -= 1
            self.gun_time = now

        if self.hidden and now - self.hide_time > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH / 2
            self.rect.bottom = HEIGHT - 10

        key_pressed = pygame.key.get_pressed()
        self.speedx = 0  # 初期速度を0に設定して移動を制御
        if key_pressed[pygame.K_RIGHT]:
                self.speedx = 8  # 右に移動
        elif key_pressed[pygame.K_LEFT]:
                self.speedx = -8  # 左に移動

        # プレイヤーの位置を更新
        self.rect.x += self.speedx

        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        if not(self.hidden):
          if self.gun == 1:
               bullet = Bullet(self.rect.centerx, self.rect.top)
               all_sprites.add(bullet)
               bullets.add(bullet)
               shoot_sound.play()
          elif self.gun >= 2:
               bullet1 = Bullet(self.rect.left, self.rect.centery)
               bullet2 = Bullet(self.rect.right, self.rect.centery)
               all_sprites.add(bullet1)
               all_sprites.add(bullet2)
               bullets.add(bullet1)
               bullets.add(bullet2)
               shoot_sound.play()

    def hide(self):
        self.hidden = True
        self.hide_time = pygame.time.get_ticks()
        self.rect.center = (WIDTH/2, HEIGHT+500)

    def gunup(self):
        self.gun += 1
        self.gun_time = pygame.time.get_ticks()

class Rock(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image_ori = random.choice(rock_imgs)
        self.image_ori.set_colorkey(WHITE)
        self.image = self.image_ori.copy()
        self.rect = self.image.get_rect()
        self.radius = int(self.rect.width * 0.8 / 2)
        #pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-180, -100)
        self.speedy = random.randrange(2, 5)
        self.speedx = random.randrange(-3, 3)
        self.total_degree = 0
        self.rot_degree = random.randrange(-3, 3)
        rock_index = rock_imgs.index(self.image_ori)
        self.score = rock_scores[rock_index] 

    def rotate(self):
        self.total_degree += self.rot_degree
        self.total_degree = self.total_degree % 360
        if self.total_degree % 30 == 0:  # 30度ごとに回転処理を実行（例）
            self.image = pygame.transform.rotate(self.image_ori, self.total_degree)
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

    def update(self):
        self.rotate()
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if self.rect.top > HEIGHT or self.rect.left > WIDTH or self.rect.right < 0:
           self.rect.x = random.randrange(0, WIDTH - self.rect.width)
           self.rect.y = random.randrange(-180, -100)
           self.speedy = random.randrange(2, 10)
           self.speedx = random.randrange(-3, 3)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        self.image = pygame.transform.scale(bullet_img, (30, 38))
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = -10
        self.spawn_time = pygame.time.get_ticks()  # 生成時間を記録

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0 or pygame.time.get_ticks() - self.spawn_time > 5000:  # 5秒で削除
            self.kill()

class Explosion(pygame.sprite.Sprite):

    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = expl_anim[self.size][0]
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 60

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(expl_anim[self.size]):
                self.kill()
            else:
                self.image = expl_anim[self.size][self.frame]
                center = self.rect.center
                self.rect = self.image.get_rect()
                self.rect.center = center
    
       
class Power(pygame.sprite.Sprite):
    def __init__(self, center):
        pygame.sprite.Sprite.__init__(self)
        self.type = random.choice(['shield', 'gun'])
        self.image = power_imgs[self.type]
        self.image = pygame.transform.scale(self.image, (30, 38))
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 3

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

pygame.mixer.music.play(-1)

#遊戯ループ
show_init = True
running = True
while running:
    if show_init:
        close = draw_init()
        if close:
            break
        show_init = False
        all_sprites = pygame.sprite.Group()
        rocks = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        powers = pygame.sprite.Group()
        player = Player()
        all_sprites.add(player)
        for i in range(8):
         new_rock()
        score = 0

    clock.tick(FPS)
    #取得輸入
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()
        

    #判断と更新
    all_sprites.update()
    hits = pygame.sprite.groupcollide(rocks, bullets, True, True)
    for hit in hits:
        random.choice(expl_sounds).play()
        score += hit.radius 
        expl = Explosion(hit.rect.center, 'lg')
        all_sprites.add(expl)
        if random.random() > 0.95:
            pow = Power(hit.rect.center)
            all_sprites.add(pow)
            powers.add(pow)
        new_rock()

    hits = pygame.sprite.spritecollide(player, rocks, True, pygame.sprite.collide_circle)
    for hit in hits:
        new_rock()
        player.health -= hit.radius
        expl = Explosion(hit.rect.center, 'sm')
        all_sprites.add(expl)
        if player.health <= 0:
            death_expl = Explosion(player.rect.center,'player')
            all_sprites.add(death_expl)
            die_sound.play()
            player.lives -= 1
            player.health = 100
            player.hide()

#宝くじとぶつかり合う
    hits = pygame.sprite.spritecollide(player, powers, True)
    for hit in hits:
        if hit.type == 'shield':
            player.health += 20
            if player.health > 100:
                player.health = 100
            shield_sound.play()
        elif hit.type == 'gun':
            player.gunup()
            gun_sound.play()

    if player.lives == 0 and not any(isinstance(sprite, Explosion) for sprite in all_sprites):
        show_init = True

    #画面
    screen.fill((BLACK))
    screen.blit(background_img, (0,0))
    all_sprites.draw(screen)
    draw_text(screen, str(score), 18, WIDTH/2, 10)
    draw_health(screen, player.health, 5, 15)
    draw_lives(screen,player.lives,player_mini_img, WIDTH -100, 15)
    pygame.display.update()

pygame.quit()
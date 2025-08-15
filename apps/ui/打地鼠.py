import pygame
import random

# 游戏初始化
score = 0
pygame.init()

# 设置窗口大小
screen = pygame.display.set_mode((800, 600))

# 加载地鼠图片
mole_image = pygame.image.load('C:\\Users\\george\\source\\repos\\MyFunds\\ui\\OIG100.jpg')

# 地鼠的初始位置
mole_position = [random.randint(0, 700), random.randint(0, 500)]

# 定义一个自定义的事件ID
MOLE_DISAPPEAR = pygame.USEREVENT + 1
MOLE_REAPPEAR = pygame.USEREVENT + 2

# 游戏主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 检查鼠标点击位置是否在地鼠图片上
            x, y = event.pos
            if mole_position[0] <= x <= mole_position[0] + 100 and mole_position[1] <= y <= mole_position[1] + 100:
                # 更新地鼠位置
                mole_position = [random.randint(0, 700), random.randint(0, 500)]
                # 设置定时器，地鼠在0-1秒后消失
                pygame.time.set_timer(MOLE_DISAPPEAR, random.randint(500, 1500))
                # 增加分数
                score += 100
                print("Score:", score)                
        elif event.type == MOLE_DISAPPEAR:
            # 地鼠消失，将其移动到屏幕外
            mole_position = [-100, -100]
            # 设置定时器，地鼠在1-2秒后重新出现
            pygame.time.set_timer(MOLE_REAPPEAR, random.randint(1000, 2000))
        elif event.type == MOLE_REAPPEAR:
            # 地鼠重新出现，将其移动回屏幕内
            mole_position = [random.randint(0, 700), random.randint(0, 500)]


    # 清屏
    screen.fill((255, 255, 255))

    # 绘制地鼠
    screen.blit(mole_image, mole_position)

    # 更新屏幕
    pygame.display.flip()

print("Final Score:", score)
# 退出游戏
pygame.quit()
import pygame
import sys

# 初始化 Pygame
pygame.init()

# 创建游戏窗口
screen = pygame.display.set_mode((800, 600))

# 加载角色和怪物的图像
player_image = pygame.image.load('.\\ui\\player.jpg')
monster_image = pygame.image.load('.\\ui\\monster.jpg')

# 设置角色和怪物的位置
player_pos = [400, 300]
monster_pos = [200, 150]

# 创建角色和怪物的 Rect 对象
player_rect = player_image.get_rect(topleft=player_pos)
monster_rect = monster_image.get_rect(topleft=monster_pos)

# 设置移动速度
speed = 5

# 游戏循环
while True:
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:  # 按键被按下
            if event.key == pygame.K_LEFT:  # 左箭头键被按下
                player_pos[0] -= speed
            elif event.key == pygame.K_RIGHT:  # 右箭头键被按下
                player_pos[0] += speed
            elif event.key == pygame.K_UP:  # 上箭头键被按下
                player_pos[1] -= speed
            elif event.key == pygame.K_DOWN:  # 下箭头键被按下
                player_pos[1] += speed
    # 更新角色的 Rect 对象
    player_rect.topleft = player_pos
    # 更新游戏状态
    # 这里可以添加你的游戏逻辑

    # 检测碰撞
    if player_rect.colliderect(monster_rect):
        print("Collision detected!")

    # 绘制游戏窗口
    screen.fill((0, 0, 0))  # 使用黑色填充窗口
    screen.blit(player_image, player_pos)  # 绘制角色
    screen.blit(monster_image, monster_pos)  # 绘制怪物
    pygame.display.flip()  # 更新游戏窗口
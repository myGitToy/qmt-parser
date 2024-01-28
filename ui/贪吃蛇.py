import pygame
import sys
import random

# 初始化 Pygame
pygame.init()

# 设置窗口大小
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))


# 设置游戏速度
clock = pygame.time.Clock()

# 设置蛇的初始位置
snake_pos = [[100, 50], [90, 50], [80, 50]]

# 设置初始食物位置
food_pos = [random.randrange(1, 80)*10, random.randrange(1, 60)*10]
food_spawn = True

# 设置初始方向
direction = 'RIGHT'

# 设置初始分数
score = 0

# 创建字体对象
font = pygame.font.Font(None, 36)

#自动算法AI
def auto_play(snake, food , current_direction):
    snake_head = snake[0]
    new_direction = current_direction
    if food[0] > snake_head[0] and current_direction != 'LEFT':  # 食物在右边
        new_direction = 'RIGHT'
    elif food[0] < snake_head[0] and current_direction != 'RIGHT':  # 食物在左边
        new_direction = 'LEFT'
    elif food[1] > snake_head[1] and current_direction != 'UP':  # 食物在下面
        new_direction = 'DOWN'
    elif food[1] < snake_head[1] and current_direction != 'DOWN':  # 食物在上面
        new_direction = 'UP'

    return new_direction

def auto_play_v2(snake, current_direction, width, height):
    snake_head = snake[0]
    new_direction = current_direction

    # 游戏一开始，去右上角
    if snake_head == (0, 0):
        new_direction = 'RIGHT'
    # 从右上角向下
    elif snake_head[0] == width - 1 and snake_head[1] == 0:
        new_direction = 'DOWN'
    # 到底部倒数第三格向右走一格
    elif snake_head[0] == width - 1 and snake_head[1] == height - 3:
        new_direction = 'RIGHT'
    # 随后向上，直到最顶部
    elif snake_head[0] == width and snake_head[1] > 0:
        new_direction = 'UP'
    # 到达顶部后向右走一个，然后向下，直到底部倒数第三格
    elif snake_head[0] == width and snake_head[1] == 0:
        new_direction = 'RIGHT'
    elif snake_head[0] == width + 1 and snake_head[1] < height - 3:
        new_direction = 'DOWN'
    # 到达右侧边界后延底部向左，由此往复
    elif snake_head[0] == width + 1 and snake_head[1] == height - 3:
        new_direction = 'LEFT'
    elif snake_head[0] > 0 and snake_head[1] == height - 3:
        new_direction = 'LEFT'
    elif snake_head[0] == 0 and snake_head[1] == height - 3:
        new_direction = 'UP'

    return new_direction

# 游戏循环
while True:
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                direction = 'UP'
            if event.key == pygame.K_DOWN:
                direction = 'DOWN'
            if event.key == pygame.K_LEFT:
                direction = 'LEFT'
            if event.key == pygame.K_RIGHT:
                direction = 'RIGHT'
    # 自动算法AI
    direction = auto_play(snake_pos, food_pos , direction)
    # 自动算法AI
    #direction = auto_play_v2(snake_pos,direction, 800, 600)

    # 更新蛇的位置
    if direction == 'UP':
        snake_pos.insert(0, [snake_pos[0][0], snake_pos[0][1]-10])
    if direction == 'DOWN':
        snake_pos.insert(0, [snake_pos[0][0], snake_pos[0][1]+10])
    if direction == 'LEFT':
        snake_pos.insert(0, [snake_pos[0][0]-10, snake_pos[0][1]])
    if direction == 'RIGHT':
        snake_pos.insert(0, [snake_pos[0][0]+10, snake_pos[0][1]])

    # 蛇吃食物
    if snake_pos[0] == food_pos:
        score += 1
        food_spawn = False
    else:
        snake_pos.pop()

    # 生成新的食物
    if not food_spawn:
        food_pos = [random.randrange(1, 80)*10, random.randrange(1, 60)*10]
    food_spawn = True

    # 检测蛇头与蛇身的碰撞
    for body_part in snake_pos[1:]:
        if snake_pos[0] == body_part:
            print("Game Over!")
            pygame.quit()
            sys.exit()

    # 检测蛇头与窗口边界的碰撞
    if snake_pos[0][0] >= screen_width or snake_pos[0][0] < 0 or snake_pos[0][1] >= screen_height or snake_pos[0][1] < 0:
        print("Game Over!")
        pygame.quit()
        sys.exit()

    # 绘制游戏窗口
    screen.fill((0, 0, 0))
    for pos in snake_pos:
        pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(pos[0], pos[1], 10, 10))
    pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(food_pos[0], food_pos[1], 10, 10))

    # 绘制分数
    score_text = font.render("Score: " + str(score), True, (255, 255, 255))
    screen.blit(score_text, (0, 0))
    
    # 更新游戏窗口
    pygame.display.update()
    # 控制游戏速度                                         
    clock.tick(100)
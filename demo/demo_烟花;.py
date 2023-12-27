import pygame
import random

# Initialize Pygame
pygame.init()

# Set the width and height of the screen
width = 800
height = 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Fireworks Demo")

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Define firework class
class Firework:
    def __init__(self, x, y):
        self.x = x
        self.y = height
        self.target_y = y
        self.color = random.choice([RED, GREEN, BLUE])
        self.radius = 2
        self.speed = random.randint(5, 10)

    def move(self):
        if self.y > self.target_y:
            self.y -= self.speed

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

    def explode(self):
        for _ in range(100):
            x = random.randint(self.x - 50, self.x + 50)
            y = random.randint(self.y - 50, self.y + 50)
            color = random.choice([RED, GREEN, BLUE])
            radius = random.randint(1, 5)
            pygame.draw.circle(screen, color, (x, y), radius)

# Create a list to store fireworks
fireworks = []

# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the screen
    screen.fill(BLACK)

    # Create new fireworks
    if random.random() < 0.05:
        x = random.randint(0, width)
        y = random.randint(height // 2, height)
        fireworks.append(Firework(x, y))

    # Move and draw fireworks
    for firework in fireworks:
        firework.move()
        firework.draw()
        if firework.y <= firework.target_y:
            firework.explode()

    # Remove fireworks that have exploded
    fireworks = [firework for firework in fireworks if firework.y > firework.target_y]

    # Update the display
    pygame.display.flip()

    # Delay for smoother animation
    pygame.time.delay(100)

# Quit Pygame
pygame.quit()

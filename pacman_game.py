import math
import random
import sys

import pygame


TILE_SIZE = 32
FPS = 60

MAZE = [
    "####################",
    "#........##........#",
    "#.####.#.##.#.####.#",
    "#.#....#....#....#.#",
    "#.#.##.######.##.#.#",
    "#....#...##...#....#",
    "####.#.#.##.#.#.####",
    "#......#....#......#",
    "#.####.######.####.#",
    "#.#..............#.#",
    "#.#.####.##.####.#.#",
    "#...#....##....#...#",
    "#.###.##.##.##.###.#",
    "#........##........#",
    "####################",
]

WIDTH = len(MAZE[0]) * TILE_SIZE
HEIGHT = len(MAZE) * TILE_SIZE

BG_COLOR = (10, 10, 35)
WALL_COLOR = (20, 70, 180)
PELLET_COLOR = (250, 220, 120)
PLAYER_COLOR = (255, 215, 0)
GHOST_COLORS = [(230, 70, 70), (255, 120, 200), (80, 200, 255)]
TEXT_COLOR = (255, 255, 255)

PLAYER_RADIUS = TILE_SIZE // 2 - 4
GHOST_RADIUS = TILE_SIZE // 2 - 5
PELLET_RADIUS = 4
PLAYER_SPEED = 2.5
GHOST_SPEED = 2.0

PLAYING = "playing"
GAME_OVER = "game_over"

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


class Entity:
    def __init__(self, x, y, color, radius, speed):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.radius = radius
        self.speed = speed
        self.dx = 0
        self.dy = 0

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)


def tile_center(col, row):
    return col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2


def build_world():
    walls = []
    pellets = set()

    for row, line in enumerate(MAZE):
        for col, ch in enumerate(line):
            if ch == "#":
                walls.append(pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            elif ch == ".":
                pellets.add(tile_center(col, row))

    player = Entity(*tile_center(1, 1), PLAYER_COLOR, PLAYER_RADIUS, PLAYER_SPEED)
    ghosts = [
        Entity(*tile_center(18, 1), GHOST_COLORS[0], GHOST_RADIUS, GHOST_SPEED),
        Entity(*tile_center(10, 7), GHOST_COLORS[1], GHOST_RADIUS, GHOST_SPEED),
        Entity(*tile_center(18, 13), GHOST_COLORS[2], GHOST_RADIUS, GHOST_SPEED),
    ]

    for ghost in ghosts:
        ghost.dx, ghost.dy = random.choice(DIRECTIONS)

    return walls, pellets, player, ghosts


def collides_with_walls(x, y, radius, walls):
    test_rect = pygame.Rect(int(x - radius), int(y - radius), radius * 2, radius * 2)
    return any(test_rect.colliderect(wall) for wall in walls)


def move_entity(entity, walls):
    if entity.dx != 0:
        next_x = entity.x + entity.dx * entity.speed
        if not collides_with_walls(next_x, entity.y, entity.radius, walls):
            entity.x = next_x
    if entity.dy != 0:
        next_y = entity.y + entity.dy * entity.speed
        if not collides_with_walls(entity.x, next_y, entity.radius, walls):
            entity.y = next_y


def choose_new_ghost_direction(ghost, walls):
    options = []
    reverse = (-ghost.dx, -ghost.dy)

    for dx, dy in DIRECTIONS:
        if (dx, dy) == reverse:
            continue
        test_x = ghost.x + dx * ghost.speed * 2
        test_y = ghost.y + dy * ghost.speed * 2
        if not collides_with_walls(test_x, test_y, ghost.radius, walls):
            options.append((dx, dy))

    if not options:
        options = [reverse]

    ghost.dx, ghost.dy = random.choice(options)


def update_ghost(ghost, walls):
    next_x = ghost.x + ghost.dx * ghost.speed
    next_y = ghost.y + ghost.dy * ghost.speed
    if collides_with_walls(next_x, next_y, ghost.radius, walls):
        choose_new_ghost_direction(ghost, walls)
    move_entity(ghost, walls)

    # random turns at tile centers keep patrol movement dynamic
    if abs((ghost.x % TILE_SIZE) - TILE_SIZE / 2) < 2 and abs((ghost.y % TILE_SIZE) - TILE_SIZE / 2) < 2:
        if random.random() < 0.08:
            choose_new_ghost_direction(ghost, walls)


def collect_pellets(player, pellets):
    removed = []
    for pellet in pellets:
        if math.dist((player.x, player.y), pellet) <= player.radius:
            removed.append(pellet)
    for pellet in removed:
        pellets.remove(pellet)
    return len(removed)


def touches(a, b):
    return math.dist((a.x, a.y), (b.x, b.y)) <= a.radius + b.radius - 2


def draw_board(screen, walls, pellets):
    screen.fill(BG_COLOR)

    for wall in walls:
        pygame.draw.rect(screen, WALL_COLOR, wall)

    for px, py in pellets:
        pygame.draw.circle(screen, PELLET_COLOR, (int(px), int(py)), PELLET_RADIUS)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simple Pac-Man")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 28)
    small_font = pygame.font.SysFont("arial", 22)

    walls, pellets, player, ghosts = build_world()
    score = 0
    state = PLAYING

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and state == GAME_OVER and event.key == pygame.K_r:
                walls, pellets, player, ghosts = build_world()
                score = 0
                state = PLAYING

        if state == PLAYING:
            keys = pygame.key.get_pressed()
            player.dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            player.dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]

            # prevent diagonal movement
            if player.dx != 0:
                player.dy = 0
            move_entity(player, walls)

            score += collect_pellets(player, pellets)

            for ghost in ghosts:
                update_ghost(ghost, walls)
                if touches(player, ghost):
                    state = GAME_OVER

        draw_board(screen, walls, pellets)
        player.draw(screen)
        for ghost in ghosts:
            ghost.draw(screen)

        score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(score_text, (10, 8))

        if state == GAME_OVER:
            over_text = font.render("Game Over", True, (255, 100, 100))
            restart_text = small_font.render("Press R to restart", True, TEXT_COLOR)
            screen.blit(over_text, over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 18)))
            screen.blit(restart_text, restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 16)))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()

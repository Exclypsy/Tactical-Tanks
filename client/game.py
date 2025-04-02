import sys

import pygame
from pygame import Vector2

from tanky.Tank import Tank
from tanky.structure import SCREEN_WIDTH, BLUE, GREEN, RED, WHITE, SCREEN_HEIGHT, screen, BLACK, FPS, clock


class TankGame:
    def __init__(self, num_players=2):
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.tanks = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()

        # Create players
        self.players = []
        colors = [BLUE, GREEN, RED, WHITE]  # Colors for different players
        start_positions = [
            (SCREEN_WIDTH * 0.25, SCREEN_HEIGHT * 0.5),
            (SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.5),
            (SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.25),
            (SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.75)
        ]

        # Create tanks for each player
        for i in range(min(num_players, 4)):  # Maximum 4 players
            tank = Tank(start_positions[i][0], start_positions[i][1], colors[i], i)
            self.tanks.add(tank)
            self.all_sprites.add(tank)
            self.players.append({
                'tank': tank,
                'score': 0,
                'spacebar_pressed_last_frame': False
            })

    def handle_input(self):
        keys = pygame.key.get_pressed()

        # Player 1 input (SPACE)
        player1_spacebar = keys[pygame.K_SPACE]
        if player1_spacebar and not self.players[0]['spacebar_pressed_last_frame']:
            self.players[0]['tank'].handle_spacebar()
            # Handle bullet creation
            if not self.players[0]['tank'].spinning and self.players[0]['tank'].bullet:
                self.bullets.add(self.players[0]['tank'].bullet)
                self.all_sprites.add(self.players[0]['tank'].bullet)
                self.players[0]['tank'].bullet = None
        self.players[0]['spacebar_pressed_last_frame'] = player1_spacebar

        # Player 2 input (RETURN/ENTER key)
        if len(self.players) > 1:
            player2_spacebar = keys[pygame.K_RETURN]
            if player2_spacebar and not self.players[1]['spacebar_pressed_last_frame']:
                self.players[1]['tank'].handle_spacebar()
                # Handle bullet creation
                if not self.players[1]['tank'].spinning and self.players[1]['tank'].bullet:
                    self.bullets.add(self.players[1]['tank'].bullet)
                    self.all_sprites.add(self.players[1]['tank'].bullet)
                    self.players[1]['tank'].bullet = None
            self.players[1]['spacebar_pressed_last_frame'] = player2_spacebar

    def update(self):
        # Update all game objects
        self.all_sprites.update()

        # Check for bullet collisions with tanks
        for bullet in self.bullets:
            hits = pygame.sprite.spritecollide(bullet, self.tanks, False)
            for tank in hits:
                # Don't allow tanks to hit themselves
                if tank.player_id != bullet.owner_id:
                    # Handle hit
                    self.players[bullet.owner_id]['score'] += 1
                    tank.position = Vector2(tank.rect.centerx, tank.rect.centery)
                    tank.spinning = True
                    bullet.kill()

    def draw(self):
        # Clear the screen
        screen.fill(BLACK)

        # Draw all sprites
        self.all_sprites.draw(screen)

        # Draw scores
        font = pygame.font.Font(None, 36)
        for i, player in enumerate(self.players):
            score_text = font.render(f"Player {i + 1}: {player['score']}", True, WHITE)
            screen.blit(score_text, (10, 10 + i * 40))

        # Update the display
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            # Keep the game running at the right speed
            clock.tick(FPS)

            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Handle user input
            self.handle_input()

            # Update game state
            self.update()

            # Draw everything
            self.draw()

        pygame.quit()
        sys.exit()

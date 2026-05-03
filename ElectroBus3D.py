# Electrobus3D is a GNU licensed game.
# This game is about electrons escaping from a parasite living inside a processor bus.
import pygame
import pygame
import math
import os
import io
import sys
import random

class ElectronBus3D:
    def __init__(self):
        pygame.init()
        self.width, self.height = 1280, 720
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("ELECTRON BUS 3D - HARDWARE CORRUPTION")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24)
        self.big_font = pygame.font.SysFont("monospace", 72, bold=True)
        self.reset_button_rect = pygame.Rect(self.width // 2 - 100, self.height // 2 + 80, 200, 60)
        self.reset_game()

    def reset_game(self):
        self.fov = 400
        self.camera_z = 0
        self.speed = 18
        self.player_pos = [0, 0]
        self.target_pos = [0, 0]
        self.path_segments = [self.generate_segment(i * 100) for i in range(50)]
        self.obstacles = []
        self.score = 0
        self.glitch_timer = 0
        self.is_dead = False
        self.running = True

    def generate_segment(self, z):
        return {
            'points': [
                [-200, -200, z], [200, -200, z],
                [200, 200, z], [-200, 200, z]
            ]
        }

    def project(self, x, y, z):
        factor = self.fov / (max(0.1, z - self.camera_z))
        px = x * factor + self.width // 2
        py = y * factor + self.height // 2
        return px, py

    def spawn_obstacle(self):
        if random.random() < 0.15:
            z_pos = self.camera_z + 2500
            self.obstacles.append({
                'pos': [random.randint(-150, 150), random.randint(-150, 150), z_pos],
                'size': 25,
                'color': (255, 0, 0)
            })

    def apply_glitch(self, surface):
        if self.glitch_timer <= 0:
            return
        
        for _ in range(int(self.glitch_timer)):
            h = random.randint(1, 20)
            y = random.randint(0, self.height - h)
            shift = random.randint(-30, 30)
            rect = pygame.Rect(0, y, self.width, h)
            try:
                sub = surface.subsurface(rect).copy()
                surface.blit(sub, (shift, y))
            except:
                pass
            
            if random.random() > 0.7:
                pygame.draw.rect(surface, (random.randint(50, 255), 0, 0), rect, 1)

        if not self.is_dead:
            self.glitch_timer -= 1

    def update(self):
        if self.is_dead:
            if self.glitch_timer < 100: self.glitch_timer += 1
            return

        self.camera_z += self.speed
        self.speed += 0.002
        
        self.player_pos[0] += (self.target_pos[0] - self.player_pos[0]) * 0.12
        self.player_pos[1] += (self.target_pos[1] - self.player_pos[1]) * 0.12
        
        if self.path_segments[0]['points'][0][2] < self.camera_z:
            last_z = self.path_segments[-1]['points'][0][2]
            self.path_segments.pop(0)
            self.path_segments.append(self.generate_segment(last_z + 100))
            self.score += 1

        self.spawn_obstacle()
        
        for obs in self.obstacles[:]:
            if obs['pos'][2] < self.camera_z:
                self.obstacles.remove(obs)
            else:
                dx = abs(obs['pos'][0] - self.player_pos[0])
                dy = abs(obs['pos'][1] - self.player_pos[1])
                dz = abs(obs['pos'][2] - self.camera_z)
                
                if dx < 40 and dy < 40 and dz < 25:
                    self.is_dead = True
                    self.glitch_timer = 40

    def draw(self):
        temp_surface = pygame.Surface((self.width, self.height))
        temp_surface.fill((2, 4, 8))
        
        for i in range(len(self.path_segments) - 1):
            s1, s2 = self.path_segments[i], self.path_segments[i+1]
            p1_proj = [self.project(p[0], p[1], p[2]) for p in s1['points']]
            p2_proj = [self.project(p[0], p[1], p[2]) for p in s2['points']]
            
            z_dist = s1['points'][0][2] - self.camera_z
            lum = max(0, min(255, 255 - z_dist // 10))
            color = (0, lum // 2, lum)
            
            for j in range(4):
                pygame.draw.line(temp_surface, color, p1_proj[j], p1_proj[(j+1)%4], 1)
                pygame.draw.line(temp_surface, color, p1_proj[j], p2_proj[j], 1)

        for obs in self.obstacles:
            if obs['pos'][2] > self.camera_z:
                px, py = self.project(obs['pos'][0], obs['pos'][1], obs['pos'][2])
                dist = obs['pos'][2] - self.camera_z
                size = max(1, int(self.fov * obs['size'] / dist))
                alpha = max(0, min(255, 255 - dist // 15))
                pygame.draw.rect(temp_surface, (alpha, 0, 0), (px - size//2, py - size//2, size, size))

        player_x = self.width // 2 + int(self.player_pos[0])
        player_y = self.height // 2 + int(self.player_pos[1])
        pygame.draw.circle(temp_surface, (255, 255, 255), (player_x, player_y), 6)
        pygame.draw.circle(temp_surface, (0, 200, 255), (player_x, player_y), 10, 2)

        self.apply_glitch(temp_surface)
        self.screen.blit(temp_surface, (0, 0))
        
        info = f"FREQ: {self.score} MHz | SPEED: {int(self.speed)}nm/s"
        txt = self.font.render(info, True, (0, 255, 0))
        self.screen.blit(txt, (20, 20))
        
        if self.is_dead:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            go_txt = self.big_font.render("GAME OVER", True, (255, 0, 0))
            go_rect = go_txt.get_rect(center=(self.width//2, self.height//2 - 60))
            self.screen.blit(go_txt, go_rect)
            
            # Restart Button
            mouse_pos = pygame.mouse.get_pos()
            btn_color = (180, 0, 0) if self.reset_button_rect.collidepoint(mouse_pos) else (100, 0, 0)
            pygame.draw.rect(self.screen, btn_color, self.reset_button_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 0, 0), self.reset_button_rect, 2, border_radius=10)
            
            res_txt = self.font.render("RESTART", True, (255, 255, 255))
            res_rect = res_txt.get_rect(center=self.reset_button_rect.center)
            self.screen.blit(res_txt, res_rect)

        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.is_dead and self.reset_button_rect.collidepoint(event.pos):
                        self.reset_game()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.is_dead:
                        self.reset_game()
                
                if event.type == pygame.MOUSEMOTION and not self.is_dead:
                    mx, my = event.pos
                    self.target_pos[0] = (mx - self.width // 2) * 0.7
                    self.target_pos[1] = (my - self.height // 2) * 0.7

            self.update()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    ElectronBus3D().run()

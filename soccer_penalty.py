import pygame
import sys
import random
import math
from pygame.locals import *

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (100, 100, 255)
LIGHT_GREEN = (100, 255, 100)

# Game settings
MAX_ROUNDS = 5  # Best of 5 shots
GOAL_WIDTH = 400
GOAL_HEIGHT = 200
BALL_RADIUS = 15
GOALKEEPER_WIDTH = 80
GOALKEEPER_HEIGHT = 120

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Soccer Penalty Shootout Game')

# Clock for controlling game speed
clock = pygame.time.Clock()

# Fonts
title_font = pygame.font.SysFont(None, 72)
menu_font = pygame.font.SysFont(None, 48)
font = pygame.font.SysFont(None, 36)

# Game states
STATE_TITLE = 0
STATE_GAME = 1
STATE_GAME_OVER = 2

# Difficulty levels
DIFFICULTY_EASY = 0
DIFFICULTY_NORMAL = 1
DIFFICULTY_HARD = 2

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)  # Border
        
        text_surf = menu_font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click
class Game:
    def __init__(self, difficulty=DIFFICULTY_NORMAL):
        self.difficulty = difficulty
        self.player_score = 0
        self.cpu_score = 0
        self.current_round = 1
        self.player_turn = True
        self.game_over = False
        self.result_message = ""
        self.ball_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100]
        self.target_pos = None
        self.ball_moving = False
        self.sudden_death = False  # Flag for sudden death mode
        
        # Set goalkeeper sizes based on difficulty
        if self.difficulty == DIFFICULTY_EASY:
            # Easy: CPU goalkeeper is smaller, player goalkeeper is larger
            self.cpu_goalkeeper_width = GOALKEEPER_WIDTH * 0.7  # 70% of normal size
            self.cpu_goalkeeper_height = GOALKEEPER_HEIGHT * 0.7
            self.player_goalkeeper_width = GOALKEEPER_WIDTH * 1.3  # 130% of normal size
            self.player_goalkeeper_height = GOALKEEPER_HEIGHT * 1.3
        elif self.difficulty == DIFFICULTY_NORMAL:
            # Normal: Both goalkeepers are normal size
            self.cpu_goalkeeper_width = GOALKEEPER_WIDTH
            self.cpu_goalkeeper_height = GOALKEEPER_HEIGHT
            self.player_goalkeeper_width = GOALKEEPER_WIDTH
            self.player_goalkeeper_height = GOALKEEPER_HEIGHT
        else:
            # Hard: CPU goalkeeper is larger, player goalkeeper is smaller
            self.cpu_goalkeeper_width = GOALKEEPER_WIDTH * 1.3  # 130% of normal size
            self.cpu_goalkeeper_height = GOALKEEPER_HEIGHT * 1.3
            self.player_goalkeeper_width = GOALKEEPER_WIDTH * 0.7  # 70% of normal size
            self.player_goalkeeper_height = GOALKEEPER_HEIGHT * 0.7
        
        # Position goalkeeper in the center of the goal
        goal_x = SCREEN_WIDTH // 2 - GOAL_WIDTH // 2
        goal_y = SCREEN_HEIGHT // 4 - GOAL_HEIGHT // 2
        self.goalkeeper_pos = [
            goal_x + (GOAL_WIDTH - self.get_current_goalkeeper_width()) // 2,
            goal_y + (GOAL_HEIGHT - self.get_current_goalkeeper_height()) // 2
        ]
        
        self.goalkeeper_target = None
        self.goal_scored = None
        self.waiting_time = 0
        self.cpu_preparation_time = 0  # Time before CPU kicks
        self.preparing_for_cpu_kick = False
        self.check_win_after_waiting = False  # Flag to check for win after showing result
        
        # Track individual kick results (1 for goal, 0 for miss, -1 for not yet taken)
        self.player_results = [-1] * MAX_ROUNDS
        self.cpu_results = [-1] * MAX_ROUNDS
        
        # For sudden death rounds
        self.sd_player_results = []
        self.sd_cpu_results = []
        self.sd_round = 0
        
    def get_current_goalkeeper_width(self):
        # Return the appropriate goalkeeper width based on whose turn it is
        if self.player_turn:
            return self.cpu_goalkeeper_width  # CPU is the goalkeeper when player kicks
        else:
            return self.player_goalkeeper_width  # Player is the goalkeeper when CPU kicks
            
    def get_current_goalkeeper_height(self):
        # Return the appropriate goalkeeper height based on whose turn it is
        if self.player_turn:
            return self.cpu_goalkeeper_height  # CPU is the goalkeeper when player kicks
        else:
            return self.player_goalkeeper_height  # Player is the goalkeeper when CPU kicks
    def draw_field(self):
        # Draw grass
        screen.fill(GREEN)
        
        # Draw a black background for the results table area
        table_x = SCREEN_WIDTH - 220
        table_y = SCREEN_HEIGHT - 170
        table_width = 200
        table_height = 150
        pygame.draw.rect(screen, (0, 0, 0), (table_x, table_y, table_width, table_height))
        
        # Draw goal
        goal_x = SCREEN_WIDTH // 2 - GOAL_WIDTH // 2
        goal_y = SCREEN_HEIGHT // 4 - GOAL_HEIGHT // 2
        pygame.draw.rect(screen, WHITE, (goal_x, goal_y, GOAL_WIDTH, GOAL_HEIGHT), 5)
        
        # Draw goal net
        for i in range(0, GOAL_WIDTH, 20):
            pygame.draw.line(screen, WHITE, (goal_x + i, goal_y), 
                            (goal_x + i, goal_y + GOAL_HEIGHT), 1)
        for i in range(0, GOAL_HEIGHT, 20):
            pygame.draw.line(screen, WHITE, (goal_x, goal_y + i), 
                            (goal_x + GOAL_WIDTH, goal_y + i), 1)
        
        # Draw penalty spot
        pygame.draw.circle(screen, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100), 5)
        
    def draw_goalkeeper(self):
        # Use different colors for player and CPU goalkeeper
        if self.player_turn:
            # When it's player's turn, the goalkeeper is CPU's (blue)
            color = BLUE
            width = self.cpu_goalkeeper_width
            height = self.cpu_goalkeeper_height
        else:
            # When it's CPU's turn, the goalkeeper is player's (red)
            color = RED
            width = self.player_goalkeeper_width
            height = self.player_goalkeeper_height
            
        pygame.draw.rect(screen, color, 
                        (self.goalkeeper_pos[0], self.goalkeeper_pos[1], 
                         width, height))
        
    def draw_ball(self):
        pygame.draw.circle(screen, WHITE, (int(self.ball_pos[0]), int(self.ball_pos[1])), BALL_RADIUS)
    def draw_scoreboard(self):
        player_text = font.render(f"Player: {self.player_score}", True, WHITE)
        cpu_text = font.render(f"CPU: {self.cpu_score}", True, WHITE)
        
        # Show round information based on whether we're in sudden death or not
        if self.sudden_death:
            round_text = font.render(f"Sudden Death: Round {self.sd_round}", True, RED)
        else:
            round_text = font.render(f"Round: {self.current_round}/{MAX_ROUNDS}", True, WHITE)
        
        screen.blit(player_text, (20, 20))
        screen.blit(cpu_text, (20, 60))
        screen.blit(round_text, (SCREEN_WIDTH - 300, 20))
        
        # Draw difficulty indicator
        if self.difficulty == DIFFICULTY_EASY:
            diff_text = font.render("Difficulty: Easy", True, LIGHT_GREEN)
        elif self.difficulty == DIFFICULTY_NORMAL:
            diff_text = font.render("Difficulty: Normal", True, YELLOW)
        else:
            diff_text = font.render("Difficulty: Hard", True, RED)
        screen.blit(diff_text, (SCREEN_WIDTH - 300, 60))
        
        # Draw penalty kick results table in the bottom right
        self.draw_results_table()
        
        if self.preparing_for_cpu_kick:
            # Show countdown timer
            seconds_left = self.cpu_preparation_time // 60 + 1
            turn_text = font.render(f"Get ready! CPU kicks in {seconds_left}...", True, WHITE)
        elif self.player_turn:
            turn_text = font.render("Player's Kick", True, WHITE)
        else:
            turn_text = font.render("CPU's Kick", True, WHITE)
        screen.blit(turn_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 50))
        
        if self.result_message:
            # Split multi-line messages
            messages = self.result_message.split('\n')
            y_offset = SCREEN_HEIGHT // 2
            for msg in messages:
                result_text = font.render(msg, True, WHITE)
                text_rect = result_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                screen.blit(result_text, text_rect)
                y_offset += 40
    def draw_results_table(self):
        # Draw table header
        header_font = pygame.font.SysFont(None, 28)
        
        # Position the table in the bottom right corner
        table_x = SCREEN_WIDTH - 200
        table_y = SCREEN_HEIGHT - 150
        
        # Draw different tables based on game mode
        if self.sudden_death:
            # In sudden death mode, only show sudden death results
            header_text = header_font.render("Sudden Death Results", True, RED)
            screen.blit(header_text, (table_x, table_y - 30))
            
            cell_width = 30
            cell_height = 30
            
            # Draw column headers (round numbers)
            for i in range(len(self.sd_player_results)):
                round_num = header_font.render(f"{i+1}", True, RED)
                screen.blit(round_num, (table_x + i * cell_width + 10, table_y))
            
            # Draw row headers
            player_label = header_font.render("P", True, RED)
            cpu_label = header_font.render("C", True, RED)
            screen.blit(player_label, (table_x - 20, table_y + cell_height))
            screen.blit(cpu_label, (table_x - 20, table_y + 2 * cell_height))
            
            # Draw grid
            sd_width = len(self.sd_player_results) * cell_width
            
            # Vertical lines
            for i in range(len(self.sd_player_results) + 1):
                pygame.draw.line(screen, RED, 
                                (table_x + i * cell_width, table_y), 
                                (table_x + i * cell_width, table_y + 3 * cell_height))
            
            # Horizontal lines
            for i in range(4):
                pygame.draw.line(screen, RED, 
                                (table_x, table_y + i * cell_height), 
                                (table_x + sd_width, table_y + i * cell_height))
            
            # Draw results using text - centered in cells
            result_font = pygame.font.SysFont("Arial", 32, bold=True)
            for i in range(len(self.sd_player_results)):
                # Calculate cell center positions
                cell_center_x = table_x + i * cell_width + cell_width // 2
                player_center_y = table_y + cell_height + cell_height // 2
                cpu_center_y = table_y + 2 * cell_height + cell_height // 2
                
                # Player results
                if self.sd_player_results[i] == 1:  # Goal
                    result = result_font.render("O", True, (255, 255, 0))
                    text_rect = result.get_rect(center=(cell_center_x, player_center_y))
                    screen.blit(result, text_rect)
                elif self.sd_player_results[i] == 0:  # Miss
                    result = result_font.render("X", True, RED)
                    text_rect = result.get_rect(center=(cell_center_x, player_center_y))
                    screen.blit(result, text_rect)
                
                # CPU results
                if self.sd_cpu_results[i] == 1:  # Goal
                    result = result_font.render("O", True, (255, 255, 0))
                    text_rect = result.get_rect(center=(cell_center_x, cpu_center_y))
                    screen.blit(result, text_rect)
                elif self.sd_cpu_results[i] == 0:  # Miss
                    result = result_font.render("X", True, RED)
                    text_rect = result.get_rect(center=(cell_center_x, cpu_center_y))
                    screen.blit(result, text_rect)
        else:
            # In regular mode, show normal rounds
            header_text = header_font.render("Penalty Kick Results", True, WHITE)
            screen.blit(header_text, (table_x, table_y - 30))
            
            cell_width = 30
            cell_height = 30
            
            # Draw column headers (round numbers)
            for i in range(MAX_ROUNDS):
                round_num = header_font.render(f"{i+1}", True, WHITE)
                screen.blit(round_num, (table_x + i * cell_width + 10, table_y))
            
            # Draw row headers
            player_label = header_font.render("P", True, WHITE)
            cpu_label = header_font.render("C", True, WHITE)
            screen.blit(player_label, (table_x - 20, table_y + cell_height))
            screen.blit(cpu_label, (table_x - 20, table_y + 2 * cell_height))
            
            # Draw grid
            for i in range(MAX_ROUNDS + 1):
                pygame.draw.line(screen, WHITE, 
                                (table_x + i * cell_width, table_y), 
                                (table_x + i * cell_width, table_y + 3 * cell_height))
            
            for i in range(4):
                pygame.draw.line(screen, WHITE, 
                                (table_x, table_y + i * cell_height), 
                                (table_x + MAX_ROUNDS * cell_width, table_y + i * cell_height))
            
            # Draw results using text - centered in cells
            result_font = pygame.font.SysFont("Arial", 32, bold=True)
            for i in range(MAX_ROUNDS):
                # Calculate cell center positions
                cell_center_x = table_x + i * cell_width + cell_width // 2
                player_center_y = table_y + cell_height + cell_height // 2
                cpu_center_y = table_y + 2 * cell_height + cell_height // 2
                
                # Player results
                if self.player_results[i] == 1:  # Goal
                    # Draw bright yellow O for goal (more visible against any background)
                    result = result_font.render("O", True, (255, 255, 0))  # Bright Yellow
                    # Center the text in the cell
                    text_rect = result.get_rect(center=(cell_center_x, player_center_y))
                    screen.blit(result, text_rect)
                elif self.player_results[i] == 0:  # Miss
                    result = result_font.render("X", True, RED)
                    # Center the text in the cell
                    text_rect = result.get_rect(center=(cell_center_x, player_center_y))
                    screen.blit(result, text_rect)
                
                # CPU results
                if self.cpu_results[i] == 1:  # Goal
                    # Draw bright yellow O for goal (more visible against any background)
                    result = result_font.render("O", True, (255, 255, 0))  # Bright Yellow
                    # Center the text in the cell
                    text_rect = result.get_rect(center=(cell_center_x, cpu_center_y))
                    screen.blit(result, text_rect)
                elif self.cpu_results[i] == 0:  # Miss
                    result = result_font.render("X", True, RED)
                    # Center the text in the cell
                    text_rect = result.get_rect(center=(cell_center_x, cpu_center_y))
                    screen.blit(result, text_rect)
    def move_ball(self):
        if self.ball_moving and self.target_pos:
            # Calculate direction vector
            dx = self.target_pos[0] - self.ball_pos[0]
            dy = self.target_pos[1] - self.ball_pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 10:  # Ball reached target
                self.ball_moving = False
                self.check_goal()
                return
                
            # Normalize and scale
            speed = 15
            dx = dx / distance * speed
            dy = dy / distance * speed
            
            # Update position
            self.ball_pos[0] += dx
            self.ball_pos[1] += dy
            
    def move_goalkeeper(self):
        if self.goalkeeper_target:
            # Calculate direction vector for both x and y
            dx = self.goalkeeper_target[0] - self.goalkeeper_pos[0]
            dy = self.goalkeeper_target[1] - self.goalkeeper_pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 10:  # Goalkeeper reached target
                self.goalkeeper_target = None
                return
                
            # Normalize and scale
            speed = 10
            dx = dx / distance * speed if distance > 0 else 0
            dy = dy / distance * speed if distance > 0 else 0
            
            # Update both x and y positions
            self.goalkeeper_pos[0] += dx
            self.goalkeeper_pos[1] += dy
    def check_goal(self):
        goal_x = SCREEN_WIDTH // 2 - GOAL_WIDTH // 2
        goal_y = SCREEN_HEIGHT // 4 - GOAL_HEIGHT // 2
        
        # Check if ball is in goal area
        in_goal_x = goal_x < self.ball_pos[0] < goal_x + GOAL_WIDTH
        in_goal_y = goal_y < self.ball_pos[1] < goal_y + GOAL_HEIGHT
        
        # Check if goalkeeper blocked
        gk_left = self.goalkeeper_pos[0]
        gk_right = self.goalkeeper_pos[0] + int(self.get_current_goalkeeper_width())
        gk_top = self.goalkeeper_pos[1]
        gk_bottom = self.goalkeeper_pos[1] + int(self.get_current_goalkeeper_height())
        
        blocked = (gk_left < self.ball_pos[0] < gk_right and 
                  gk_top < self.ball_pos[1] < gk_bottom)
        
        if in_goal_x and in_goal_y and not blocked:
            self.goal_scored = True
            self.result_message = "GOAL!"
            if self.player_turn:
                self.player_score += 1
                if self.sudden_death:
                    self.sd_player_results[self.sd_round - 1] = 1  # 1 for goal
                else:
                    self.player_results[self.current_round - 1] = 1  # 1 for goal
            else:
                self.cpu_score += 1
                if self.sudden_death:
                    self.sd_cpu_results[self.sd_round - 1] = 1  # 1 for goal
                else:
                    self.cpu_results[self.current_round - 1] = 1  # 1 for goal
        else:
            self.goal_scored = False
            self.result_message = "SAVED!"
            if self.player_turn:
                if self.sudden_death:
                    self.sd_player_results[self.sd_round - 1] = 0  # 0 for miss
                else:
                    self.player_results[self.current_round - 1] = 0  # 0 for miss
            else:
                if self.sudden_death:
                    self.sd_cpu_results[self.sd_round - 1] = 0  # 0 for miss
                else:
                    self.cpu_results[self.current_round - 1] = 0  # 0 for miss
        
        # Always set waiting time to show the result before checking for win
        self.waiting_time = 60  # Wait 1 second (60 frames)
        
        # Flag to check for win after waiting time
        self.check_win_after_waiting = True
    def next_turn(self):
        # If we're waiting after a goal/save, just count down
        if self.waiting_time > 0:
            self.waiting_time -= 1
            return
            
        # Special case: End of round 5, check if we need to go to sudden death
        if not self.sudden_death and self.current_round == 5 and not self.player_turn and not self.preparing_for_cpu_kick and self.goal_scored is not None:
            if self.player_score == self.cpu_score:
                # Scores are tied after 5 rounds, go to sudden death
                self.start_sudden_death()
                return
            else:
                # Game is over, determine winner
                self.end_game()
                return
            
        # Check if we need to check for win after showing the result
        if self.check_win_after_waiting:
            self.check_win_after_waiting = False
            
            # Handle sudden death mode differently
            if self.sudden_death:
                # In sudden death, we check for a winner after both players have kicked
                if not self.player_turn:  # After CPU's turn
                    # Check if one player scored and the other missed
                    player_result = self.sd_player_results[self.sd_round - 1]
                    cpu_result = self.sd_cpu_results[self.sd_round - 1]
                    
                    if player_result == 1 and cpu_result == 0:
                        # Player scored, CPU missed - Player wins
                        self.end_game()
                        return
                    elif player_result == 0 and cpu_result == 1:
                        # Player missed, CPU scored - CPU wins
                        self.end_game()
                        return
                    # If both scored or both missed, continue to next sudden death round
            else:
                # Regular rounds logic
                # Now check for mathematical win conditions
                remaining_kicks = MAX_ROUNDS - self.current_round
                
                # If player just kicked
                if self.player_turn:
                    # Calculate maximum possible score for CPU including current round
                    max_possible_cpu_score = self.cpu_score + remaining_kicks + 1  # +1 for current round
                    
                    # Critical case: Round 5, player scores making it 5-3 or better
                    if self.current_round == 5:
                        # Only end if CPU can't catch up even with their last kick
                        if self.player_score > self.cpu_score + 1:
                            self.end_game()
                            return
                        # If CPU is already ahead after player's kick in round 5, CPU wins
                        if self.cpu_score > self.player_score:
                            self.end_game()
                            return
                    # Check if player just scored and now has an insurmountable lead
                    elif self.player_score > max_possible_cpu_score:
                        self.end_game()
                        return
                # If CPU just kicked
                else:
                    # Calculate maximum possible score for player including next round
                    max_possible_player_score = self.player_score + remaining_kicks
                    
                    # Critical case: Round 5, CPU scores making it 3-5 or better
                    if self.current_round == 5:
                        # Only end if player can't catch up even with their last kick
                        if self.cpu_score > self.player_score + 1:
                            self.end_game()
                            return
                        # If player is already ahead after CPU's kick in round 5, player wins
                        if self.player_score > self.cpu_score:
                            self.end_game()
                            return
                    # Check if CPU just scored and now has an insurmountable lead
                    elif self.cpu_score > max_possible_player_score:
                        self.end_game()
                        return
                    
                    # Check if player just missed and now cannot catch up to CPU
                    if not self.player_turn and not self.goal_scored:
                        max_possible_player_score = self.player_score + remaining_kicks
                        if max_possible_player_score < self.cpu_score:
                            self.end_game()
                            return
                    
                    # Check if CPU just missed and now cannot catch up to player
                    if self.player_turn and not self.goal_scored:
                        max_possible_cpu_score = self.cpu_score + remaining_kicks
                        if max_possible_cpu_score < self.player_score:
                            self.end_game()
                            return
                            
                    # Special case: After round 4, check if game is mathematically decided
                    if self.current_round == 4 and not self.player_turn:
                        # If player has 4 points and CPU has 2 or less, player wins
                        if self.player_score >= 4 and self.cpu_score <= 2:
                            self.end_game()
                            return
                        # If CPU has 4 points and player has 2 or less, CPU wins
                        if self.cpu_score >= 4 and self.player_score <= 2:
                            self.end_game()
                            return
                        # If player has 3 points and CPU has 1 or less, player wins
                        if self.player_score >= 3 and self.cpu_score <= 1:
                            self.end_game()
                            return
                        # If CPU has 3 points and player has 1 or less, CPU wins
                        if self.cpu_score >= 3 and self.player_score <= 1:
                            self.end_game()
                            return
                        # If player has 2 points and CPU has 0, player wins
                        if self.player_score >= 2 and self.cpu_score == 0:
                            self.end_game()
                            return
                        # If CPU has 2 points and player has 0, CPU wins
                        if self.cpu_score >= 2 and self.player_score == 0:
                            self.end_game()
                            return
        
        # If game is already marked as over, end it now
        if self.game_over:
            self.end_game()
            return
        
        self.result_message = ""
        self.ball_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100]
        
        # Reset goalkeeper to center position
        goal_x = SCREEN_WIDTH // 2 - GOAL_WIDTH // 2
        goal_y = SCREEN_HEIGHT // 4 - GOAL_HEIGHT // 2
        
        # Use integer values for goalkeeper position calculation
        current_gk_width = int(self.get_current_goalkeeper_width())
        current_gk_height = int(self.get_current_goalkeeper_height())
        
        self.goalkeeper_pos = [
            goal_x + (GOAL_WIDTH - current_gk_width) // 2,
            goal_y + (GOAL_HEIGHT - current_gk_height) // 2
        ]
        
        self.target_pos = None
        self.ball_moving = False
        self.goalkeeper_target = None
        self.goal_scored = None
        
        if self.sudden_death:
            # In sudden death, we alternate kicks within the same round
            if not self.player_turn:  # After CPU's turn
                self.sd_round += 1  # Increment sudden death round
                
                # Check if we need to reset the table (every 5 rounds)
                if self.sd_round % 5 == 1 and self.sd_round > 1:
                    # Clear the results and start a new table
                    self.sd_player_results = []
                    self.sd_cpu_results = []
                
                self.sd_player_results.append(-1)  # Add placeholder for new round
                self.sd_cpu_results.append(-1)
                self.player_turn = True  # Switch to player's turn
            else:
                # After player's turn, prepare for CPU's turn with a delay
                self.player_turn = False
                self.preparing_for_cpu_kick = True
                self.cpu_preparation_time = 180  # 3 seconds (60 frames per second)
        else:
            # Regular rounds
            if not self.player_turn:  # After CPU's turn
                self.current_round += 1
                if self.current_round > MAX_ROUNDS:
                    self.end_game()
                    return
                self.player_turn = True  # Switch to player's turn
            else:
                # After player's turn, prepare for CPU's turn with a delay
                self.player_turn = False
                self.preparing_for_cpu_kick = True
                self.cpu_preparation_time = 180  # 3 seconds (60 frames per second)
    def update_cpu_preparation(self):
        if self.preparing_for_cpu_kick:
            if self.cpu_preparation_time > 0:
                self.cpu_preparation_time -= 1
            else:
                self.preparing_for_cpu_kick = False
                
                # If game is already marked as over, end it now
                if self.game_over:
                    self.end_game()
                    return
                
                # Before CPU shoots, check if it's mathematically impossible for CPU to win
                if not self.sudden_death:  # Only check in regular mode
                    remaining_kicks = MAX_ROUNDS - self.current_round
                    max_possible_cpu_score = self.cpu_score + remaining_kicks
                    
                    # Only check for early win in round 5, let all round 4 kicks complete
                    if self.current_round == 5 and max_possible_cpu_score + 1 < self.player_score:
                        # Player has already won mathematically by more than 1 point
                        self.end_game()
                        return
                
                # Proceed with CPU's kick if the game isn't over
                self.cpu_shoot()
                
    def cpu_shoot(self):
        # CPU randomly selects target
        goal_x = SCREEN_WIDTH // 2 - GOAL_WIDTH // 2
        goal_y = SCREEN_HEIGHT // 4 - GOAL_HEIGHT // 2
        
        target_x = random.randint(goal_x + 20, goal_x + GOAL_WIDTH - 20)
        target_y = random.randint(goal_y + 20, goal_y + GOAL_HEIGHT - 20)
        self.target_pos = [target_x, target_y]
        
        # Player controls goalkeeper
        self.ball_moving = True
    def player_shoot(self, pos):
        if not self.ball_moving and self.player_turn:
            goal_x = SCREEN_WIDTH // 2 - GOAL_WIDTH // 2
            goal_y = SCREEN_HEIGHT // 4 - GOAL_HEIGHT // 2
            
            # Check if click is in goal area
            if (goal_x < pos[0] < goal_x + GOAL_WIDTH and 
                goal_y < pos[1] < goal_y + GOAL_HEIGHT):
                self.target_pos = pos
                self.ball_moving = True
                
                # CPU goalkeeper moves randomly within the goal area
                # Convert float values to integers for random.randint
                random_x = random.randint(goal_x, int(goal_x + GOAL_WIDTH - self.cpu_goalkeeper_width))
                random_y = random.randint(goal_y, int(goal_y + GOAL_HEIGHT - self.cpu_goalkeeper_height))
                self.goalkeeper_target = [random_x, random_y]
                
    def cpu_goalkeeper_move(self, pos):
        # Allow goalkeeper movement during CPU preparation time or when it's CPU's turn
        if self.player_turn or self.ball_moving:
            return
            
        goal_x = SCREEN_WIDTH // 2 - GOAL_WIDTH // 2
        goal_y = SCREEN_HEIGHT // 4 - GOAL_HEIGHT // 2
        max_x = goal_x + GOAL_WIDTH - int(self.player_goalkeeper_width)
        max_y = goal_y + GOAL_HEIGHT - int(self.player_goalkeeper_height)
        
        # Limit goalkeeper movement to goal area
        if pos[0] < goal_x:
            pos = (goal_x, pos[1])
        elif pos[0] > max_x:
            pos = (max_x, pos[1])
            
        # Also allow vertical movement
        if pos[1] < goal_y:
            pos = (pos[0], goal_y)
        elif pos[1] > max_y:
            pos = (pos[0], max_y)
            
        # Update both x and y positions
        self.goalkeeper_pos[0] = pos[0]
        self.goalkeeper_pos[1] = pos[1]
    def start_sudden_death(self):
        """Start sudden death mode after a tie in regular rounds"""
        self.sudden_death = True
        self.sd_round = 1
        self.sd_player_results.append(-1)  # Add placeholder for first sudden death round
        self.sd_cpu_results.append(-1)
        self.player_turn = True  # Player always kicks first in sudden death
        self.result_message = "SUDDEN DEATH!"
        self.waiting_time = 120  # Show message for 2 seconds
        self.preparing_for_cpu_kick = False  # Make sure this is False so player kicks first
        
        # Reset ball position to the penalty spot
        self.ball_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100]
        
        # Reset goalkeeper to center position
        goal_x = SCREEN_WIDTH // 2 - GOAL_WIDTH // 2
        goal_y = SCREEN_HEIGHT // 4 - GOAL_HEIGHT // 2
        
        # Use integer values for goalkeeper position calculation
        current_gk_width = int(self.cpu_goalkeeper_width)  # Use CPU goalkeeper width since player kicks first
        current_gk_height = int(self.cpu_goalkeeper_height)
        
        self.goalkeeper_pos = [
            goal_x + (GOAL_WIDTH - current_gk_width) // 2,
            goal_y + (GOAL_HEIGHT - current_gk_height) // 2
        ]
        
        # Reset other game state variables
        self.target_pos = None
        self.ball_moving = False
        self.goalkeeper_target = None
        self.goal_scored = None
        
    def end_game(self):
        # If game is already over, just update the message
        if not self.game_over:
            self.game_over = True
            if self.player_score > self.cpu_score:
                self.result_message = "PLAYER WINS!"
            elif self.cpu_score > self.player_score:
                self.result_message = "CPU WINS!"
            else:
                self.result_message = "IT'S A DRAW!"
                
            # Display additional message if game ended early
            if not self.sudden_death and self.current_round <= MAX_ROUNDS:
                remaining = MAX_ROUNDS - self.current_round
                if self.current_round == MAX_ROUNDS:
                    # Final round, show appropriate message
                    if self.player_score > self.cpu_score:
                        self.result_message += "\nPlayer wins in the final round!"
                    elif self.cpu_score > self.player_score:
                        self.result_message += "\nCPU wins in the final round!"
                elif remaining > 0:
                    # Earlier rounds, show remaining kicks
                    if self.player_score > self.cpu_score:
                        self.result_message += f"\nPlayer wins with {remaining} kicks remaining!"
                    else:
                        self.result_message += f"\nCPU wins with {remaining} kicks remaining!"
            elif self.sudden_death:
                # Sudden death message
                if self.player_score > self.cpu_score:
                    self.result_message += f"\nPlayer wins in sudden death round {self.sd_round}!"
                else:
                    self.result_message += f"\nCPU wins in sudden death round {self.sd_round}!"
            
    def restart_game(self, difficulty=None):
        if difficulty is not None:
            self.difficulty = difficulty
        self.__init__(self.difficulty)
class TitleScreen:
    def __init__(self):
        self.buttons = [
            Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 60, 200, 50, "Easy", LIGHT_GREEN, (150, 255, 150)),
            Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50, "Normal", YELLOW, (255, 255, 150)),
            Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 60, 200, 50, "Hard", RED, (255, 150, 150))
        ]
        
    def draw(self):
        # Draw background
        screen.fill(GREEN)
        
        # Draw title
        title_text = title_font.render("Soccer Penalty Shootout", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = menu_font.render("Select Difficulty", True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4 + 60))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw()
            
    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            for button in self.buttons:
                button.check_hover(event.pos)
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.buttons):
                if button.is_clicked(event.pos, True):
                    return i  # Return the difficulty level
        return None

# Create game instance and title screen
title_screen = TitleScreen()
game = None
current_state = STATE_TITLE

# Main game loop
running = True
while running:
    # Process events
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
            
        if current_state == STATE_TITLE:
            difficulty = title_screen.handle_event(event)
            if difficulty is not None:
                game = Game(difficulty)
                current_state = STATE_GAME
                
        elif current_state == STATE_GAME:
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                if game.game_over:
                    current_state = STATE_TITLE
                elif game.player_turn and not game.ball_moving:
                    game.player_shoot(event.pos)
            elif event.type == MOUSEMOTION:
                # Always pass mouse motion to goalkeeper move function
                # The function itself will determine if movement is allowed
                if game:
                    game.cpu_goalkeeper_move(event.pos)
    
    # Update game state
    if current_state == STATE_TITLE:
        title_screen.draw()
    elif current_state == STATE_GAME:
        game.move_ball()
        game.move_goalkeeper()
        game.update_cpu_preparation()  # Handle CPU preparation time
        
        # If ball stopped moving, prepare for next turn
        if not game.ball_moving and game.goal_scored is not None:
            game.next_turn()
        
        # Draw everything
        game.draw_field()
        game.draw_goalkeeper()
        game.draw_ball()
        game.draw_scoreboard()
    
    # Update display
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(60)

# Quit pygame
pygame.quit()
sys.exit()

import pygame
import uuid
import numpy as np
import pandas as pd
import os
from ConfigUtil import load_experiment_config

# Constants
WIDTH, HEIGHT = 600, 600
MARGINS = 10, 50
SPACING = 10
CAKE_W, CAKE_H = 6, 6
CELL_SIZE = 70
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CANDLE_COLOR = (0, 0, 255)
CAKES_TO_DECORATE = 1



class CakeDecorator:
    def __init__(self, session_id=None, num_candles=3, candle_color=CANDLE_COLOR, cakes_to_decorate=CAKES_TO_DECORATE):
        # Initialize Pygame
        pygame.init()

        # Create the window
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Grid of Rectangles")

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Cake Decorator")

        if session_id is None:
            session_id = uuid.uuid4()
        self.session_id = session_id
        self.candle_color = candle_color
        self.past_cakes = []
        self.num_candles = num_candles
        self.cakes_to_decorate = cakes_to_decorate

        self.set_up_cake()

        font = pygame.font.Font(None, 30)
        self.submit_text = font.render("Done", True, BLACK)
        self.submit_button_size = (100, 50)
        self.submit_button_coords = (WIDTH // 2 - (self.submit_button_size[0] // 2), MARGINS[1] * 2 + CAKE_H * CELL_SIZE)

    
    def set_up_cake(self):
        self.candles = self.init_candles(self.num_candles)
        font = pygame.font.Font(None, 36)
        self.title = font.render(f'Cake Number: {len(self.past_cakes) + 1}', True, WHITE)
        self.candles_placed = 0
    
    def write_to_csv(self, fp):
    
        cols = ['ssid']
        data = [self.session_id.hex]

        for i in range(self.cakes_to_decorate):
            for j in range(self.num_candles):
                cols.append(f'cake{i}_candle{j}_x')
                cols.append(f'cake{i}_candle{j}_y')

                data.append(self.past_cakes[i][j][0])
                data.append(self.past_cakes[i][j][1])
        
        avg = self.average_candles()
        
        for i in range(self.num_candles):
            cols.append(f'avg_x{i}')
            cols.append(f'avg_y{i}')
            data.append(avg[i][0])
            data.append(avg[i][1])
            print(i, avg[i][1], data[-1])
        
        
        df = pd.DataFrame([data], columns=cols)
        df.to_csv(fp, mode='a', header=not os.path.exists(fp))
    
    def average_candles(self):
        candles = np.array(self.past_cakes)
        avg = np.round(np.average(candles, axis=0))

        # getting rid of duplicates
        vals, indices, counts = np.unique(avg, return_inverse=True, return_counts=True, axis=0)
        num_offsets = np.max(counts)

        offsets = [np.array((0, 0))]
        angles = np.array([0, np.pi / 2, np.pi, 3 * np.pi / 2])
        np.random.shuffle(angles)

        for r in range(1, int(np.ceil((num_offsets - 1) / 4)) + 1):
            for angle in angles:
                offsets.append(r * np.array((np.cos(angle), np.sin(angle))))

        res = []
        inserted_counts = np.zeros(counts.shape, dtype=int)
        for i in indices:
            val = vals[i]
    
            res.append(np.round((val + offsets[inserted_counts[i]])).tolist())
            inserted_counts[i] += 1

        return res
    
    # initializes candle list, where each candle is represented as an x 
    #   coordinate, y coordinate, and integer mode
    # mode should be -1 for unplaced, 0 for in the process of being placed, and 
    #   otherwise denote order in which placement occured
    def init_candles(self, num_candles):
        candles = []
        x = CAKE_W * CELL_SIZE + MARGINS[0] + SPACING

        for i in range(num_candles):
            candles.append([x, i * (CELL_SIZE + SPACING) + MARGINS[1], -1])

        return candles

    def draw(self, mouse_x, mouse_y):
        # title
        text_rect = self.title.get_rect(center=(WIDTH // 2, MARGINS[1] // 2))
        self.screen.blit(self.title, text_rect)

        # cake
        pygame.draw.rect(self.screen, WHITE, (MARGINS[0], MARGINS[1], CAKE_W * CELL_SIZE, CAKE_H * CELL_SIZE))

        # candles
        for [x, y, candle_mode] in self.candles:
            if candle_mode != 0:
                pygame.draw.rect(self.screen, self.candle_color, (x, y, CELL_SIZE, CELL_SIZE))
            else:
                pygame.draw.rect(self.screen, self.candle_color, (*self.normalize_to_corner(mouse_x, mouse_y), CELL_SIZE, CELL_SIZE))
        
        # done button
        pygame.draw.rect(self.screen, WHITE, (*self.submit_button_coords, *self.submit_button_size))
        text_rect = self.submit_text.get_rect(center=(WIDTH // 2, MARGINS[1] * 2 + CAKE_H * CELL_SIZE + (self.submit_button_size[1] // 2)))
        self.screen.blit(self.submit_text, text_rect)
    
    # discretize coordinates inside a cake grid cell to the corner of that cell
    def normalize_to_corner(self, x, y):
        return ((x - MARGINS[0]) // CELL_SIZE) * CELL_SIZE + MARGINS[0], ((y - MARGINS[1]) // CELL_SIZE) * CELL_SIZE + MARGINS[1]
    
    # check if a click is on a candle
    def on_candle(self, x, y, unplaced=True):
        for i, [cx, cy, mode] in enumerate(self.candles):
            if (unplaced and mode == -1) or (not unplaced and mode > 0):
                if cx <= x < cx + CELL_SIZE and cy <= y < cy + CELL_SIZE:
                    return i
        
        return -1

    # check if a click is on the 'Done' button
    def on_submit_button(self, x, y):
        return self.submit_button_coords[0] <= x < self.submit_button_coords[0] + self.submit_button_size[0] and self.submit_button_coords[1] <= y < self.submit_button_coords[1] + self.submit_button_size[1]
    
    # save candle positions for current cake
    def save_current_cake(self):
        sorted_candles = sorted(self.candles, key=lambda x: x[2])
        self.past_cakes.append([])

        for [x, y, mode] in sorted_candles:
            if mode > 0:
                self.past_cakes[-1].append([(x - MARGINS[0]) // CELL_SIZE, CAKE_H - 1 - ((y - MARGINS[1]) // CELL_SIZE)])
    
    # place a candle on the cake in current mouse position
    def place_candle(self, mouse_x, mouse_y, candle_i):
        if MARGINS[0] <= mouse_x < CAKE_W * CELL_SIZE + MARGINS[0] and MARGINS[1] <= mouse_y < CAKE_H * CELL_SIZE + MARGINS[1] and self.on_candle(mouse_x, mouse_y, False) == -1:
            self.candles_placed += 1
            self.candles[candle_i][2] = self.candles_placed
            self.candles[candle_i][0], self.candles[candle_i][1] = self.normalize_to_corner(mouse_x, mouse_y)

    def run(self):
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    candle = self.on_candle(*mouse_pos)
                    if candle >= 0:
                        self.candles[candle][2] = 0
                    elif self.on_submit_button(*mouse_pos):
                        self.save_current_cake()

                        if len(self.past_cakes) < self.cakes_to_decorate:
                            self.set_up_cake()
                        else:
                            running = False
                elif event.type == pygame.MOUSEBUTTONUP:
                    for i, (_, _, candle_mode) in enumerate(self.candles):
                        if candle_mode == 0:
                            self.place_candle(*mouse_pos, i)

            self.screen.fill(BLACK)
            self.draw(*mouse_pos)

            pygame.display.flip()

        pygame.quit()

        return self.past_cakes


if __name__ == '__main__':
    gui = CakeDecorator()
    cakes = gui.run()
    exp_config = load_experiment_config('experiment_config.yaml')
    user_name = exp_config['user_name']
    gui.write_to_csv(fp=f'user_interface_results/{user_name}.csv')
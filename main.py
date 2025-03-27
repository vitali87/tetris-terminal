# -*- coding: utf-8 -*-
import curses # The main library for terminal handling
import random
import time

# --- Game Configuration (Simplified - Colors handled by curses later) ---
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
EMPTY_CELL = "."
BLOCK_CELL = "■" # Or "█"
BORDER_CELL = "#"

TETROMINOES = { # ... (same as before) ...
    'I': [[(0, -1), (0, 0), (0, 1), (0, 2)], [( -1, 0), (0, 0), (1, 0), (2, 0)]],
    'O': [[(0, 0), (0, 1), (1, 0), (1, 1)]],
    'T': [[(0, -1), (0, 0), (0, 1), (-1, 0)], [(-1, 0), (0, 0), (1, 0), (0, 1)],
          [(0, -1), (0, 0), (0, 1), (1, 0)], [(-1, 0), (0, 0), (1, 0), (0, -1)]],
    'S': [[(0, 0), (0, 1), (-1, 1), (-1, 2)], [(0, 1), (1, 1), (1, 0), (2, 0)]],
    'Z': [[(0, -1), (0, 0), (-1, 0), (-1, 1)], [(0, 0), (1, 0), (1, 1), (2, 1)]],
    'J': [[(0, -1), (0, 0), (0, 1), (-1, 1)], [(-1, 0), (0, 0), (1, 0), (1, 1)],
          [(0, -1), (0, 0), (0, 1), (1, -1)], [(-1, -1), (-1, 0), (0, 0), (1, 0)]],
    'L': [[(0, -1), (0, 0), (0, 1), (-1, -1)], [(-1, 0), (0, 0), (1, 0), (-1, 1)],
          [(0, -1), (0, 0), (0, 1), (1, 1)], [(1, -1), (-1, 0), (0, 0), (1, 0)]]
}

# Map piece types to curses color pair indices (we'll define pairs later)
# Indices 1-7 for pieces, 8 for border, 9 for info text
# Index 0 is reserved for default background/foreground
COLOR_MAP = {
    'I': 1, 'O': 2, 'T': 3, 'S': 4,
    'Z': 5, 'J': 6, 'L': 7,
    'BORDER': 8, 'INFO': 9,
}
# Define the actual curses colors for the indices
# (curses.COLOR_CYAN, curses.COLOR_YELLOW, etc.)
CURSES_COLOR_PAIRS = {
    1: (curses.COLOR_CYAN, curses.COLOR_BLACK),
    2: (curses.COLOR_YELLOW, curses.COLOR_BLACK),
    3: (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
    4: (curses.COLOR_GREEN, curses.COLOR_BLACK),
    5: (curses.COLOR_RED, curses.COLOR_BLACK),
    6: (curses.COLOR_BLUE, curses.COLOR_BLACK),
    7: (curses.COLOR_WHITE, curses.COLOR_BLACK), # Using White for Orange fallback
    8: (curses.COLOR_WHITE, curses.COLOR_BLACK), # Grey/White for Border
    9: (curses.COLOR_WHITE, curses.COLOR_BLACK), # White for Info text
}

# --- Game Class (Modified draw method) ---
class TetrisGame:
    def __init__(self, width=BOARD_WIDTH, height=BOARD_HEIGHT):
        self.width = width
        self.height = height
        self.board = [[0 for _ in range(width)] for _ in range(height)] # Store color index, 0 = empty
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.current_piece_type = None
        self.current_rotation = 0
        self.current_pos = {'row': 0, 'col': 0}
        self.next_piece_type = random.choice(list(TETROMINOES.keys()))
        self.fall_time = time.time()
        self.fall_speed = 0.8
        self._spawn_new_piece()

    # --- Core Logic (Mostly Unchanged, but board uses 0/color index) ---

    def _get_piece_coords(self, piece_type=None, rotation=None, position=None):
        p_type = piece_type if piece_type is not None else self.current_piece_type
        rot = rotation if rotation is not None else self.current_rotation
        pos = position if position is not None else self.current_pos
        if not p_type: return [] # No piece
        shape = TETROMINOES[p_type][rot % len(TETROMINOES[p_type])]
        coords = [(pos['row'] + r, pos['col'] + c) for r, c in shape]
        return coords

    def _is_valid_position(self, piece_type=None, rotation=None, position=None):
        coords = self._get_piece_coords(piece_type, rotation, position)
        if not coords: return False # No piece to validate

        for r, c in coords:
            # Check bounds
            if not (0 <= c < self.width): return False # Check width first
            if r >= self.height : return False # Check bottom boundary only
            if r < 0: continue # Allow parts above screen initially

            # Check collision with existing blocks on the board (where value > 0)
            if self.board[r][c] != 0:
                return False
        return True

    def _spawn_new_piece(self):
        self.current_piece_type = self.next_piece_type
        self.next_piece_type = random.choice(list(TETROMINOES.keys()))
        self.current_rotation = 0
        self.current_pos = {'row': 0, 'col': self.width // 2}
        min_row_offset = min(r for r, c in TETROMINOES[self.current_piece_type][0])
        self.current_pos['row'] -= min_row_offset
        if not self._is_valid_position():
            self.game_over = True
            self.current_piece_type = None

    def _lock_piece(self):
        coords = self._get_piece_coords()
        color_index = COLOR_MAP.get(self.current_piece_type, 0)
        piece_fully_on_board = True

        for r, c in coords:
            if 0 <= r < self.height and 0 <= c < self.width:
                self.board[r][c] = color_index
            elif r < 0 and 0 <= c < self.width: # Part locked above screen
                 piece_fully_on_board = False

        # Game over if piece locked partially/fully above visible area
        if not piece_fully_on_board:
             self.game_over = True

        if not self.game_over:
            lines_cleared_now = self._clear_lines()
            self._update_score(lines_cleared_now)
            self._spawn_new_piece() # Spawns only if not game over
        else:
             self.current_piece_type = None # Ensure no piece drawn if game over

        self.fall_time = time.time() # Reset timer

    def _clear_lines(self):
        lines_to_clear = [r for r, row in enumerate(self.board) if all(cell != 0 for cell in row)]
        if not lines_to_clear: return 0
        num_cleared = len(lines_to_clear)
        new_rows = [[0 for _ in range(self.width)] for _ in range(num_cleared)]
        new_board = [row for r, row in enumerate(self.board) if r not in lines_to_clear]
        self.board = new_rows + new_board
        return num_cleared

    def _update_score(self, lines_cleared_now):
        score_map = {1: 40, 2: 100, 3: 300, 4: 1200}
        self.score += score_map.get(lines_cleared_now, 0) * self.level
        self.lines_cleared += lines_cleared_now
        new_level = (self.lines_cleared // 10) + 1
        if new_level > self.level:
            self.level = new_level
            self.fall_speed = max(0.1, 0.8 - (self.level - 1) * 0.05)

    def move(self, dr, dc):
        if self.game_over or not self.current_piece_type: return False
        new_pos = {'row': self.current_pos['row'] + dr, 'col': self.current_pos['col'] + dc}
        if self._is_valid_position(position=new_pos):
            self.current_pos = new_pos
            return True
        return False

    def rotate(self):
        if self.game_over or not self.current_piece_type: return False
        current_rot = self.current_rotation
        num_rotations = len(TETROMINOES[self.current_piece_type])
        next_rotation = (current_rot + 1) % num_rotations
        kick_offsets = [(0, 0), (0, -1), (0, 1), (0, -2), (0, 2)]
        for dr_kick, dc_kick in kick_offsets:
             kick_pos = {'row': self.current_pos['row'] + dr_kick, 'col': self.current_pos['col'] + dc_kick}
             if self._is_valid_position(rotation=next_rotation, position=kick_pos):
                 self.current_rotation = next_rotation
                 self.current_pos = kick_pos
                 return True
        return False

    def drop(self):
         if not self.move(1, 0):
             coords = self._get_piece_coords()
             if not coords: # No piece, should imply game over state or just before spawn
                 if not self.game_over: # If somehow no piece but not game over, trigger check
                     self.game_over = True # Safety
                 return

             # Check if piece is entirely above board when lock happens
             if all(r < 0 for r, c in coords):
                 self.game_over = True
                 self.current_piece_type = None
             # Check if *any* part is on board (row >= 0) before locking
             elif any(r >= 0 for r, c in coords):
                 self._lock_piece()
             else: # Should be covered by all(r<0), but as fallback
                  self.game_over = True
                  self.current_piece_type = None

    def hard_drop(self):
        if self.game_over or not self.current_piece_type: return
        rows_to_drop = 0
        while self._is_valid_position(position={'row': self.current_pos['row'] + rows_to_drop + 1, 'col': self.current_pos['col']}):
            rows_to_drop += 1
        if rows_to_drop > 0:
            self.current_pos['row'] += rows_to_drop
        self._lock_piece() # Lock after dropping

    def step(self):
        if self.game_over: return
        now = time.time()
        if now - self.fall_time > self.fall_speed:
            self.drop()
            # Timer reset is handled within _lock_piece or here if drop didn't lock
            if not self.game_over and self.current_piece_type:
                 self.fall_time = now # Use 'now' to prevent drift

    # --- Drawing using curses ---
    def draw(self, stdscr):
        """Draws the game state using the provided curses window."""
        stdscr.clear() # Clear the screen managed by curses

        # --- Draw Board and Locked Pieces ---
        board_start_row, board_start_col = 1, 2 # Offset for info line and border
        for r in range(self.height):
            for c in range(self.width):
                cell_color_index = self.board[r][c]
                char_to_draw = BLOCK_CELL if cell_color_index != 0 else EMPTY_CELL
                color_pair = curses.color_pair(cell_color_index) if cell_color_index != 0 else curses.A_NORMAL
                try:
                    stdscr.addch(board_start_row + r, board_start_col + c, char_to_draw, color_pair)
                except curses.error: pass # Ignore errors writing to bottom-right corner

        # --- Draw Current Falling Piece ---
        if not self.game_over and self.current_piece_type:
            piece_coords = self._get_piece_coords()
            color_index = COLOR_MAP.get(self.current_piece_type, 0)
            color_pair = curses.color_pair(color_index)
            for r, c in piece_coords:
                if 0 <= r < self.height and 0 <= c < self.width: # Only draw visible parts
                    try:
                         stdscr.addch(board_start_row + r, board_start_col + c, BLOCK_CELL, color_pair)
                    except curses.error: pass

        # --- Draw Borders ---
        border_color_pair = curses.color_pair(COLOR_MAP['BORDER']) | curses.A_BOLD
        # Top/Bottom borders
        for c in range(self.width + 2):
            try:
                stdscr.addch(board_start_row - 1, board_start_col - 1 + c, BORDER_CELL, border_color_pair)
                stdscr.addch(board_start_row + self.height, board_start_col - 1 + c, BORDER_CELL, border_color_pair)
            except curses.error: pass
        # Left/Right borders
        for r in range(self.height):
             try:
                 stdscr.addch(board_start_row + r, board_start_col - 1, BORDER_CELL, border_color_pair)
                 stdscr.addch(board_start_row + r, board_start_col + self.width, BORDER_CELL, border_color_pair)
             except curses.error: pass

        # --- Draw Info Text ---
        info_color_pair = curses.color_pair(COLOR_MAP['INFO']) | curses.A_BOLD
        info_text = f"Score: {self.score:<8} Level: {self.level:<5} Lines: {self.lines_cleared}"
        try:
             stdscr.addstr(0, 0, info_text, info_color_pair)
        except curses.error: pass

        # --- Draw Next Piece Preview ---
        preview_start_row = board_start_row
        preview_start_col = board_start_col + self.width + 3 # Position it to the right
        try:
            stdscr.addstr(preview_start_row -1, preview_start_col, "Next:", info_color_pair)
        except curses.error: pass

        if self.next_piece_type:
            next_shape = TETROMINOES[self.next_piece_type][0]
            next_color_index = COLOR_MAP.get(self.next_piece_type, 0)
            next_color_pair = curses.color_pair(next_color_index)
            # Calculate offsets to draw preview centered
            min_r = min(r for r, c in next_shape)
            min_c = min(c for r, c in next_shape)
            for r_p, c_p in next_shape:
                 draw_r = preview_start_row + (r_p - min_r)
                 draw_c = preview_start_col + (c_p - min_c)
                 try:
                     stdscr.addch(draw_r, draw_c, BLOCK_CELL, next_color_pair)
                 except curses.error: pass # Ignore if preview goes off screen limits


        # --- Draw Game Over Message ---
        if self.game_over:
            game_over_text1 = "=" * 10 + " GAME OVER " + "=" * 10
            game_over_text2 = f"Final Score: {self.score}"
            game_over_text3 = "Press 'q' to exit."
            # Center the text
            center_row = board_start_row + self.height // 2 - 1
            center_col1 = board_start_col + (self.width // 2) - (len(game_over_text1) // 2)
            center_col2 = board_start_col + (self.width // 2) - (len(game_over_text2) // 2)
            center_col3 = board_start_col + (self.width // 2) - (len(game_over_text3) // 2)
            try:
                stdscr.addstr(center_row, center_col1, game_over_text1, curses.A_BOLD | curses.color_pair(COLOR_MAP.get('Z', 0))) # Red color
                stdscr.addstr(center_row + 1, center_col2, game_over_text2, curses.A_BOLD)
                stdscr.addstr(center_row + 2, center_col3, game_over_text3, curses.A_BOLD)
            except curses.error: pass


        # --- Refresh Screen ---
        stdscr.refresh()


# --- Main Game Function (using curses) ---
def run_game(stdscr):
    """Main function called by curses.wrapper."""
    # --- Curses Initialization ---
    curses.curs_set(0) # Hide cursor
    stdscr.nodelay(1) # Make getch non-blocking
    stdscr.timeout(100) # Set a timeout for getch (milliseconds), e.g., 100ms

    # Initialize colors (if terminal supports it)
    if curses.has_colors():
        curses.start_color()
        # Optional: Use terminal's default background
        # curses.use_default_colors()
        # background = -1 if curses.has_colors() and curses.can_change_color() else curses.COLOR_BLACK

        # Define color pairs used by the game
        for index, (fg, bg) in CURSES_COLOR_PAIRS.items():
             if 0 < fg < curses.COLORS and 0 <= bg < curses.COLORS: # Check valid color range
                  curses.init_pair(index, fg, bg)
             else: # Fallback if colors are out of range for the terminal
                  curses.init_pair(index, curses.COLOR_WHITE, curses.COLOR_BLACK)


    # --- Game Setup ---
    game = TetrisGame()

    # --- Game Loop ---
    while True:
        # --- Input Handling ---
        key = stdscr.getch() # Get input (-1 if no input within timeout)

        quit_game = False
        if not game.game_over:
            action_taken = False
            if key == curses.KEY_LEFT or key == ord('a') or key == ord('A'):
                action_taken = game.move(0, -1)
            elif key == curses.KEY_RIGHT or key == ord('d') or key == ord('D'):
                action_taken = game.move(0, 1)
            elif key == curses.KEY_DOWN or key == ord('s') or key == ord('S'):
                action_taken = game.move(1, 0)
                if action_taken: game.fall_time = time.time() # Reset fall on successful soft drop
            elif key == curses.KEY_UP or key == ord('w') or key == ord('W'):
                action_taken = game.rotate()
            elif key == ord(' '): # Space for hard drop
                game.hard_drop()
                action_taken = True # Hard drop is always an action
            elif key == ord('q') or key == ord('Q') or key == 27: # Quit on 'q' or ESC (key code 27)
                quit_game = True

            # Potential optimization: Add small delay if action taken?
            # if action_taken: time.sleep(0.01)

            # --- Game Logic Step ---
            game.step()

        elif key == ord('q') or key == ord('Q') or key == 27: # Allow quit from game over screen
             quit_game = True

        if quit_game:
            break # Exit the main loop

        # --- Drawing ---
        try:
            game.draw(stdscr)
        except curses.error as e:
             # Handle potential drawing errors, maybe terminal resized?
             # For now, just break the loop gracefully.
             # A more robust solution might try to re-initialize curses.
             break

        # Loop speed is implicitly controlled by stdscr.timeout and game logic speed


# --- Entry Point ---
if __name__ == "__main__":
    try:
        # curses.wrapper handles initialization and cleanup automatically
        curses.wrapper(run_game)
        print("Game exited normally.")
    except curses.error as e:
         print(f"A curses error occurred: {e}")
         print("Your terminal might not fully support curses features required by the game.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
         # curses.wrapper should handle cleanup, but an extra print helps
         print("Cleanup finished.")
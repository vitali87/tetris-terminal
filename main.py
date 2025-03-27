# -*- coding: utf-8 -*-
import curses
import random
import time
import math # Needed for ceiling function

# --- Constants (Defaults/Minimums) ---
# These are now minimums, actual size will be dynamic
MIN_BOARD_WIDTH = 10
MIN_BOARD_HEIGHT = 20
DEFAULT_ASPECT_RATIO = 0.5 # Width / Height

EMPTY_CELL = "."
BLOCK_CELL = "■"
BORDER_CELL = "#"

# UI Element Dimensions (approximate)
INFO_HEIGHT = 1
BORDER_HEIGHT = 2 # Top + Bottom
BORDER_WIDTH = 2  # Left + Right
PREVIEW_WIDTH = 6 # Width needed for "Next:" + 4-wide piece + spacing
PREVIEW_HEIGHT = 6 # Height for "Next:" + 4-tall piece
MIN_PREVIEW_SPACING = 2 # Space between board and preview

TETROMINOES = { # (Shapes remain the same)
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

# Color setup remains the same
COLOR_MAP = {
    'I': 1, 'O': 2, 'T': 3, 'S': 4,
    'Z': 5, 'J': 6, 'L': 7, # L might be overridden by orange
    'BORDER': 8, 'INFO': 9, 'ERROR': 5 # Use Red for errors
}
CURSES_COLOR_PAIRS = {
    1: (curses.COLOR_CYAN, curses.COLOR_BLACK), 2: (curses.COLOR_YELLOW, curses.COLOR_BLACK),
    3: (curses.COLOR_MAGENTA, curses.COLOR_BLACK), 4: (curses.COLOR_GREEN, curses.COLOR_BLACK),
    5: (curses.COLOR_RED, curses.COLOR_BLACK), 6: (curses.COLOR_BLUE, curses.COLOR_BLACK),
    7: (curses.COLOR_WHITE, curses.COLOR_BLACK), # Fallback for L (Orange)
    8: (curses.COLOR_WHITE, curses.COLOR_BLACK), # Border
    9: (curses.COLOR_WHITE, curses.COLOR_BLACK), # Info
}
ORANGE_COLOR_INDEX = 10 # Use a higher index for custom color
ORANGE_PAIR_INDEX = 7   # Use pair 7 for the L piece, will be redefined if orange works
ORANGE_DEFINED = False

# --- Game Class (Accepts dynamic width/height) ---
class TetrisGame:
    # __init__ and core logic methods remain the same, using self.width/height
    def __init__(self, width, height): # Accepts calculated dimensions
        self.width = width
        self.height = height
        self.board = [[0 for _ in range(width)] for _ in range(height)]
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
        self._spawn_new_piece() # Uses self.width for centering

    def _get_piece_coords(self, piece_type=None, rotation=None, position=None):
        p_type = piece_type if piece_type is not None else self.current_piece_type
        rot = rotation if rotation is not None else self.current_rotation
        pos = position if position is not None else self.current_pos
        if not p_type: return []
        shape = TETROMINOES[p_type][rot % len(TETROMINOES[p_type])]
        coords = [(pos['row'] + r, pos['col'] + c) for r, c in shape]
        return coords

    def _is_valid_position(self, piece_type=None, rotation=None, position=None):
        coords = self._get_piece_coords(piece_type, rotation, position)
        if not coords: return False
        for r, c in coords:
            if not (0 <= c < self.width): return False
            if r >= self.height : return False
            if r < 0: continue
            # Check board collision using potentially non-existent index if r is negative
            # Need to ensure r is valid for board access *after* bounds check
            if r >= 0 and self.board[r][c] != 0: return False
        return True

    def _spawn_new_piece(self):
        self.current_piece_type = self.next_piece_type
        self.next_piece_type = random.choice(list(TETROMINOES.keys()))
        self.current_rotation = 0
        self.current_pos = {'row': 0, 'col': self.width // 2} # Center based on current width
        min_row_offset = min(r for r, c in TETROMINOES[self.current_piece_type][0])
        self.current_pos['row'] -= min_row_offset
        if not self._is_valid_position():
            self.game_over = True
            self.current_piece_type = None

    def _lock_piece(self):
        coords = self._get_piece_coords()
        color_index = COLOR_MAP.get(self.current_piece_type, 0)
        # Override for L piece if orange is defined and working
        if ORANGE_DEFINED and self.current_piece_type == 'L':
            color_index = ORANGE_PAIR_INDEX # Use the pair index assigned to L/Orange

        piece_fully_on_board = True
        for r, c in coords:
            if 0 <= r < self.height and 0 <= c < self.width:
                self.board[r][c] = color_index
            elif r < 0 and 0 <= c < self.width:
                 piece_fully_on_board = False

        if not piece_fully_on_board: self.game_over = True

        if not self.game_over:
            lines_cleared_now = self._clear_lines()
            self._update_score(lines_cleared_now)
            self._spawn_new_piece()
        else:
             self.current_piece_type = None
        self.fall_time = time.time()

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
        # ... rotate logic unchanged ...
        if self.game_over or not self.current_piece_type: return False
        current_rot = self.current_rotation
        num_rotations = len(TETROMINOES[self.current_piece_type])
        next_rotation = (current_rot + 1) % num_rotations
        kick_offsets = [(0, 0), (0, -1), (0, 1), (0, -2), (0, 2)] # Basic wall kicks
        # More complex SRS kicks could be implemented here if needed
        for dr_kick, dc_kick in kick_offsets:
             kick_pos = {'row': self.current_pos['row'] + dr_kick,
                         'col': self.current_pos['col'] + dc_kick}
             if self._is_valid_position(rotation=next_rotation, position=kick_pos):
                 self.current_rotation = next_rotation
                 self.current_pos = kick_pos
                 return True
        return False # Rotation failed

    def drop(self):
        # ... drop logic unchanged ...
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
        # ... hard_drop logic unchanged ...
        if self.game_over or not self.current_piece_type: return
        rows_to_drop = 0
        while self._is_valid_position(position={'row': self.current_pos['row'] + rows_to_drop + 1, 'col': self.current_pos['col']}):
            rows_to_drop += 1
        if rows_to_drop > 0:
            self.current_pos['row'] += rows_to_drop
        self._lock_piece() # Lock after dropping


    def step(self):
        # ... step logic unchanged ...
        if self.game_over: return
        now = time.time()
        if now - self.fall_time > self.fall_speed:
            self.drop()
            # Timer reset is handled within _lock_piece or here if drop didn't lock
            if not self.game_over and self.current_piece_type:
                 # Use 'now' to prevent drift if step takes time
                 self.fall_time = now

    # --- Drawing (Now accepts offsets) ---
    def draw(self, stdscr, top_offset, left_offset):
        """Draws the game state using the provided curses window and offsets."""
        # Calculate absolute positions based on offsets
        info_row = top_offset
        board_start_row = top_offset + INFO_HEIGHT # Row where top border starts
        board_start_col = left_offset             # Col where left border starts

        # Clear only the area we intend to draw in? Might be complex.
        # stdscr.clear() is simpler for now.
        stdscr.clear()

        # --- Draw Info Text (At top, relative to left offset) ---
        info_color_pair = curses.color_pair(COLOR_MAP['INFO']) | curses.A_BOLD
        info_text = f"Score: {self.score:<8} Level: {self.level:<5} Lines: {self.lines_cleared}"
        try:
            # Draw info line spanning roughly the board width area
             stdscr.addstr(info_row, board_start_col, info_text.ljust(self.width + BORDER_WIDTH), info_color_pair)
        except curses.error: pass # Ignore errors drawing near edges

        # --- Draw Borders ---
        border_color_pair = curses.color_pair(COLOR_MAP['BORDER']) | curses.A_BOLD
        # Top/Bottom borders
        for c in range(self.width + BORDER_WIDTH):
            try:
                stdscr.addch(board_start_row, board_start_col + c, BORDER_CELL, border_color_pair)
                stdscr.addch(board_start_row + self.height + 1, board_start_col + c, BORDER_CELL, border_color_pair)
            except curses.error: pass
        # Left/Right borders
        for r in range(self.height):
             try:
                 # Border is drawn at board_start_col and board_start_col + width + 1
                 stdscr.addch(board_start_row + 1 + r, board_start_col, BORDER_CELL, border_color_pair)
                 stdscr.addch(board_start_row + 1 + r, board_start_col + self.width + 1, BORDER_CELL, border_color_pair)
             except curses.error: pass

        # --- Draw Board and Locked Pieces (Relative to board_start_row/col) ---
        draw_origin_r = board_start_row + 1
        draw_origin_c = board_start_col + 1
        for r in range(self.height):
            for c in range(self.width):
                cell_color_index = self.board[r][c]
                char_to_draw = BLOCK_CELL if cell_color_index != 0 else EMPTY_CELL
                color_pair = curses.color_pair(cell_color_index) if cell_color_index != 0 else curses.A_NORMAL
                try:
                    stdscr.addch(draw_origin_r + r, draw_origin_c + c, char_to_draw, color_pair)
                except curses.error: pass

        # --- Draw Current Falling Piece ---
        if not self.game_over and self.current_piece_type:
            piece_coords = self._get_piece_coords()
            color_index = COLOR_MAP.get(self.current_piece_type, 0)
            # Override for L piece if orange is defined
            if ORANGE_DEFINED and self.current_piece_type == 'L':
                color_index = ORANGE_PAIR_INDEX
            color_pair = curses.color_pair(color_index)

            for r, c in piece_coords:
                # Only draw visible parts within the board boundaries
                if 0 <= r < self.height and 0 <= c < self.width:
                    try:
                         stdscr.addch(draw_origin_r + r, draw_origin_c + c, BLOCK_CELL, color_pair)
                    except curses.error: pass

        # --- Draw Next Piece Preview ---
        preview_start_row = board_start_row + 1 # Align top with board content
        preview_start_col = board_start_col + self.width + BORDER_WIDTH + MIN_PREVIEW_SPACING
        try:
            stdscr.addstr(preview_start_row -1, preview_start_col, "Next:", info_color_pair) # Place "Next:" above
        except curses.error: pass

        if self.next_piece_type:
            next_shape = TETROMINOES[self.next_piece_type][0]
            next_color_index = COLOR_MAP.get(self.next_piece_type, 0)
            # Override for L piece if orange is defined
            if ORANGE_DEFINED and self.next_piece_type == 'L':
                next_color_index = ORANGE_PAIR_INDEX
            next_color_pair = curses.color_pair(next_color_index)

            min_r = min(r for r, c in next_shape); min_c = min(c for r, c in next_shape)
            for r_p, c_p in next_shape:
                 # Position relative to preview_start_row/col
                 draw_r = preview_start_row + (r_p - min_r)
                 draw_c = preview_start_col + (c_p - min_c)
                 try:
                     stdscr.addch(draw_r, draw_c, BLOCK_CELL, next_color_pair)
                 except curses.error: pass

        # --- Draw Game Over Message (Centered within the board area) ---
        if self.game_over:
            game_over_text1 = "=" * 10 + " GAME OVER " + "=" * 10
            game_over_text2 = f"Final Score: {self.score}"
            game_over_text3 = "Press 'q' to exit."
            # Center relative to the board drawing area
            center_row = draw_origin_r + self.height // 2 - 1
            center_col1 = draw_origin_c + (self.width // 2) - (len(game_over_text1) // 2)
            center_col2 = draw_origin_c + (self.width // 2) - (len(game_over_text2) // 2)
            center_col3 = draw_origin_c + (self.width // 2) - (len(game_over_text3) // 2)
            try:
                red_pair = curses.color_pair(COLOR_MAP['ERROR']) | curses.A_BOLD
                stdscr.addstr(center_row, center_col1, game_over_text1, red_pair)
                stdscr.addstr(center_row + 1, center_col2, game_over_text2, curses.A_BOLD)
                stdscr.addstr(center_row + 2, center_col3, game_over_text3, curses.A_BOLD)
            except curses.error: pass

        # Refresh Screen (done once after all drawing)
        stdscr.refresh()

# --- Main Game Function (Handles sizing and centering) ---
def run_game(stdscr):
    global ORANGE_DEFINED, ORANGE_PAIR_INDEX

    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    # --- Initialize Colors (including trying orange) ---
    if curses.has_colors():
        curses.start_color()
        try:
            if curses.COLORS >= 256 and curses.can_change_color():
                 curses.init_color(ORANGE_COLOR_INDEX, 1000, 650, 0) # Define RGB for orange
                 curses.init_pair(ORANGE_PAIR_INDEX, ORANGE_COLOR_INDEX, curses.COLOR_BLACK)
                 ORANGE_DEFINED = True
                 # No need to update COLOR_MAP, we just use ORANGE_PAIR_INDEX directly for 'L'
            else: # Fallback if 256 colors or color change not supported
                 curses.init_pair(ORANGE_PAIR_INDEX, curses.COLOR_WHITE, curses.COLOR_BLACK) # Use white for L
        except Exception: # Catch potential errors during color init
            ORANGE_DEFINED = False
            try: # Try setting fallback pair again just in case
                 curses.init_pair(ORANGE_PAIR_INDEX, curses.COLOR_WHITE, curses.COLOR_BLACK)
            except: pass # Ignore errors if fallback also fails

        # Define the standard color pairs (excluding the L/Orange pair index if orange worked)
        for index, (fg, bg) in CURSES_COLOR_PAIRS.items():
             if index != ORANGE_PAIR_INDEX: # Don't redefine the L/Orange pair
                  try:
                      curses.init_pair(index, fg, bg)
                  except: pass # Ignore errors for other pairs

    # --- Calculate Dimensions and Centering ---
    max_y, max_x = stdscr.getmaxyx()

    # Calculate available space for the board itself
    available_h = max_y - INFO_HEIGHT - BORDER_HEIGHT
    available_w = max_x - BORDER_WIDTH - MIN_PREVIEW_SPACING - PREVIEW_WIDTH

    # Check if terminal is too small
    min_total_h = MIN_BOARD_HEIGHT + INFO_HEIGHT + BORDER_HEIGHT
    min_total_w = MIN_BOARD_WIDTH + BORDER_WIDTH + MIN_PREVIEW_SPACING + PREVIEW_WIDTH
    if max_y < min_total_h or max_x < min_total_w:
        stdscr.clear()
        error_msg = "Terminal too small!"
        err_y = max_y // 2
        err_x = max(0, (max_x - len(error_msg)) // 2)
        try:
             stdscr.addstr(err_y, err_x, error_msg, curses.color_pair(COLOR_MAP['ERROR']) | curses.A_BOLD)
        except curses.error:
             stdscr.addstr(0, 0, error_msg) # Fallback position
        stdscr.refresh()
        stdscr.timeout(-1) # Wait indefinitely for input
        stdscr.getch()     # Wait for a key press before exiting
        return             # Exit run_game

    # Determine final board size (prioritize height, maintain aspect ratio)
    final_board_h = available_h
    # Calculate width based on height and aspect ratio, limited by available width
    final_board_w = min(available_w, math.ceil(final_board_h * DEFAULT_ASPECT_RATIO))

    # Ensure minimum size is met (this might slightly break aspect ratio if space is tight)
    final_board_h = max(MIN_BOARD_HEIGHT, final_board_h)
    final_board_w = max(MIN_BOARD_WIDTH, final_board_w)

    # Calculate total content size based on final board dimensions
    content_h = final_board_h + BORDER_HEIGHT + INFO_HEIGHT
    content_w = final_board_w + BORDER_WIDTH + MIN_PREVIEW_SPACING + PREVIEW_WIDTH

    # Calculate top-left corner offsets for centering
    top_offset = max(0, (max_y - content_h) // 2)
    left_offset = max(0, (max_x - content_w) // 2)


    # --- Game Setup ---
    game = TetrisGame(width=final_board_w, height=final_board_h)

    # --- Game Loop ---
    while True:
        key = stdscr.getch()
        quit_game = False

        # Handle resize event (curses.KEY_RESIZE) - redraw required
        if key == curses.KEY_RESIZE:
            # Recalculate dimensions and offsets on resize
            max_y, max_x = stdscr.getmaxyx()
            if max_y < min_total_h or max_x < min_total_w:
                 # Handle terminal becoming too small during gameplay (e.g., show message, pause)
                 # For simplicity, we'll just break for now
                 break # Or implement a proper "too small" screen

            available_h = max_y - INFO_HEIGHT - BORDER_HEIGHT
            available_w = max_x - BORDER_WIDTH - MIN_PREVIEW_SPACING - PREVIEW_WIDTH
            # Re-calculate board size based on new dimensions
            # Note: This doesn't resize the *existing* game state/board, just the drawing area.
            # A full resize would require more complex game state adaptation.
            final_board_h = available_h
            final_board_w = min(available_w, math.ceil(final_board_h * DEFAULT_ASPECT_RATIO))
            final_board_h = max(MIN_BOARD_HEIGHT, final_board_h)
            final_board_w = max(MIN_BOARD_WIDTH, final_board_w)

            # Update game dimensions IF it's feasible (might require game logic changes)
            # For now, just update offsets for drawing
            content_h = final_board_h + BORDER_HEIGHT + INFO_HEIGHT
            content_w = final_board_w + BORDER_WIDTH + MIN_PREVIEW_SPACING + PREVIEW_WIDTH
            top_offset = max(0, (max_y - content_h) // 2)
            left_offset = max(0, (max_x - content_w) // 2)

            stdscr.clear() # Clear before redraw after resize

        # --- Input Handling (remains the same) ---
        elif not game.game_over:
            if key == curses.KEY_LEFT or key == ord('a') or key == ord('A'): game.move(0, -1)
            elif key == curses.KEY_RIGHT or key == ord('d') or key == ord('D'): game.move(0, 1)
            elif key == curses.KEY_DOWN or key == ord('s') or key == ord('S'):
                if game.move(1, 0): game.fall_time = time.time()
            elif key == curses.KEY_UP or key == ord('w') or key == ord('W'): game.rotate()
            elif key == ord(' '): game.hard_drop()
            elif key == ord('q') or key == ord('Q') or key == 27: quit_game = True
            game.step() # Game logic step
        elif key == ord('q') or key == ord('Q') or key == 27: quit_game = True # Quit from game over

        if quit_game: break

        # --- Drawing ---
        try:
            # Pass calculated offsets to draw method
            game.draw(stdscr, top_offset, left_offset)
        except curses.error as e:
             # If drawing fails (e.g., terminal resized smaller than expected between check and draw)
             # Log error maybe, then break
             # print(f"Draw error: {e}") # Avoid printing directly in curses
             break


# --- Entry Point ---
if __name__ == "__main__":
    try:
        curses.wrapper(run_game)
        print("Game exited normally.")
    except curses.error as e:
         print(f"\nA curses error occurred: {e}")
         print("Terminal might not fully support curses or was resized unexpectedly.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    # No finally needed, curses.wrapper handles cleanup
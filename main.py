# -*- coding: utf-8 -*-
import curses
import random
import time
import math

# --- Constants (Defaults/Minimums) ---
MIN_BOARD_WIDTH = 10
MIN_BOARD_HEIGHT = 20
TARGET_WIDTH_FRACTION = 0.4 # Use 40% of terminal width for the game area

EMPTY_CELL = "."
BLOCK_CELL = "■"
BORDER_CELL = "#"
INFO_HEIGHT = 1; BORDER_HEIGHT = 2; BORDER_WIDTH = 2
PREVIEW_WIDTH = 6; PREVIEW_HEIGHT = 6; MIN_PREVIEW_SPACING = 2

# --- Tetrominoes and Colors ---
TETROMINOES = { 'I': [[(0,-1),(0,0),(0,1),(0,2)],[(-1,0),(0,0),(1,0),(2,0)]], 'O': [[(0,0),(0,1),(1,0),(1,1)]], 'T': [[(0,-1),(0,0),(0,1),(-1,0)],[(-1,0),(0,0),(1,0),(0,1)],[(0,-1),(0,0),(0,1),(1,0)],[(-1,0),(0,0),(1,0),(0,-1)]], 'S': [[(0,0),(0,1),(-1,1),(-1,2)],[(0,1),(1,1),(1,0),(2,0)]], 'Z': [[(0,-1),(0,0),(-1,0),(-1,1)],[(0,0),(1,0),(1,1),(2,1)]], 'J': [[(0,-1),(0,0),(0,1),(-1,1)],[(-1,0),(0,0),(1,0),(1,1)],[(0,-1),(0,0),(0,1),(1,-1)],[(-1,-1),(-1,0),(0,0),(1,0)]], 'L': [[(0,-1),(0,0),(0,1),(-1,-1)],[(-1,0),(0,0),(1,0),(-1,1)],[(0,-1),(0,0),(0,1),(1,1)],[(1,-1),(-1,0),(0,0),(1,0)]] }
COLOR_MAP = { 'I': 1, 'O': 2, 'T': 3, 'S': 4, 'Z': 5, 'J': 6, 'L': 7, 'BORDER': 8, 'INFO': 9, 'ERROR': 5 }
CURSES_COLOR_PAIRS = { 1: (curses.COLOR_CYAN, curses.COLOR_BLACK), 2: (curses.COLOR_YELLOW, curses.COLOR_BLACK), 3: (curses.COLOR_MAGENTA, curses.COLOR_BLACK), 4: (curses.COLOR_GREEN, curses.COLOR_BLACK), 5: (curses.COLOR_RED, curses.COLOR_BLACK), 6: (curses.COLOR_BLUE, curses.COLOR_BLACK), 7: (curses.COLOR_WHITE, curses.COLOR_BLACK), 8: (curses.COLOR_WHITE, curses.COLOR_BLACK), 9: (curses.COLOR_WHITE, curses.COLOR_BLACK), }
ORANGE_COLOR_INDEX = 10; ORANGE_PAIR_INDEX = 7; ORANGE_DEFINED = False

# --- Game Class ---
class TetrisGame:
    def __init__(self, width, height):
        self.width = width; self.height = height
        self.board = [[0 for _ in range(width)] for _ in range(height)]
        self.score = 0; self.level = 1; self.lines_cleared = 0
        self.game_over = False
        self.current_piece_type = None; self.current_rotation = 0
        self.current_pos = {'row': 0, 'col': 0}
        self.next_piece_type = random.choice(list(TETROMINOES.keys()))
        self.fall_time = time.time(); self.fall_speed = 0.8
        self._spawn_new_piece()

    def _get_piece_coords(self, pt=None, rot=None, pos=None):
        p_type=pt if pt is not None else self.current_piece_type
        rt=rot if rot is not None else self.current_rotation
        p=pos if pos is not None else self.current_pos
        if not p_type: return []
        shape=TETROMINOES[p_type][rt % len(TETROMINOES[p_type])]
        return [(p['row']+r, p['col']+c) for r,c in shape]

    def _is_valid_position(self, pt=None, rot=None, pos=None): # Expects pt, rot, pos
        coords=self._get_piece_coords(pt, rot, pos);
        if not coords: return False
        for r,c in coords:
            if not (0<=c<self.width): return False
            if r>=self.height: return False
            if r<0: continue
            if self.board[r][c]!=0: return False
        return True

    def _spawn_new_piece(self):
        self.current_piece_type=self.next_piece_type
        self.next_piece_type=random.choice(list(TETROMINOES.keys()))
        self.current_rotation=0
        self.current_pos={'row':0, 'col':self.width//2}
        min_r=min(r for r,c in TETROMINOES[self.current_piece_type][0])
        self.current_pos['row']-=min_r
        if not self._is_valid_position(): self.game_over=True; self.current_piece_type=None

    def _lock_piece(self):
        coords=self._get_piece_coords()
        idx=COLOR_MAP.get(self.current_piece_type, 0)
        if ORANGE_DEFINED and self.current_piece_type=='L': idx=ORANGE_PAIR_INDEX
        on_board=True
        for r,c in coords:
            if 0<=r<self.height and 0<=c<self.width: self.board[r][c]=idx
            elif r<0 and 0<=c<self.width: on_board=False
        if not on_board: self.game_over=True
        if not self.game_over:
            lines=self._clear_lines(); self._update_score(lines); self._spawn_new_piece()
        else: self.current_piece_type=None
        self.fall_time=time.time()

    def _clear_lines(self):
        clear=[r for r, row in enumerate(self.board) if all(c!=0 for c in row)]
        if not clear: return 0
        cnt=len(clear); new_rows=[[0]*self.width for _ in range(cnt)]
        new_board=[row for r, row in enumerate(self.board) if r not in clear]
        self.board=new_rows+new_board; return cnt

    def _update_score(self, lines):
        scores={1:40, 2:100, 3:300, 4:1200}; self.score+=scores.get(lines,0)*self.level
        self.lines_cleared+=lines; new_level=(self.lines_cleared//10)+1
        if new_level>self.level: self.level=new_level; self.fall_speed=max(0.1, 0.8-(self.level-1)*0.05)

    def move(self, dr, dc):
        if self.game_over or not self.current_piece_type: return False
        new_pos={'row':self.current_pos['row']+dr, 'col':self.current_pos['col']+dc}
        if self._is_valid_position(pos=new_pos): # Use 'pos='
            self.current_pos = new_pos; return True
        return False

    # ****** THIS METHOD IS CORRECTED ******
    def rotate(self):
        if self.game_over or not self.current_piece_type: return False
        cr=self.current_rotation; num_rots=len(TETROMINOES[self.current_piece_type])
        nr=(cr+1)%num_rots; kicks=[(0,0),(0,-1),(0,1),(0,-2),(0,2)]
        for dr_k, dc_k in kicks:
             kp={'row':self.current_pos['row']+dr_k, 'col':self.current_pos['col']+dc_k}
             # Use 'rot=' and 'pos=' here
             if self._is_valid_position(rot=nr, pos=kp):
                 self.current_rotation=nr; self.current_pos=kp; return True
        return False
    # **************************************

    def drop(self):
         if not self.move(1,0):
             coords=self._get_piece_coords()
             if not coords:
                 if not self.game_over: self.game_over=True
                 return
             if all(r<0 for r,c in coords): self.game_over=True; self.current_piece_type=None
             elif any(r>=0 for r,c in coords): self._lock_piece()
             else: self.game_over=True; self.current_piece_type=None

    def hard_drop(self):
        if self.game_over or not self.current_piece_type: return
        rows=0
        while self._is_valid_position(pos={'row':self.current_pos['row']+rows+1, 'col':self.current_pos['col']}): rows+=1 # Use 'pos='
        if rows>0: self.current_pos['row']+=rows
        self._lock_piece()

    def step(self):
        if self.game_over: return
        now=time.time()
        if now-self.fall_time > self.fall_speed:
            self.drop()
            if not self.game_over and self.current_piece_type: self.fall_time=now

    def draw(self, stdscr, top_offset, left_offset):
        # ... (draw method unchanged) ...
        info_row = top_offset; board_start_row = top_offset + INFO_HEIGHT; board_start_col = left_offset
        stdscr.clear()
        info_pair = curses.color_pair(COLOR_MAP['INFO']) | curses.A_BOLD
        info_text = f"Score:{self.score:<6} Lvl:{self.level:<3} Lines:{self.lines_cleared}"
        try: stdscr.addstr(info_row, board_start_col, info_text.ljust(self.width + BORDER_WIDTH), info_pair)
        except: pass
        border_pair = curses.color_pair(COLOR_MAP['BORDER']) | curses.A_BOLD
        for c in range(self.width + BORDER_WIDTH): # Draw Top/Bottom borders
            try: stdscr.addch(board_start_row, board_start_col + c, BORDER_CELL, border_pair)
            except: pass
            try: stdscr.addch(board_start_row + self.height + 1, board_start_col + c, BORDER_CELL, border_pair)
            except: pass
        for r in range(self.height): # Draw Left/Right borders
             try: stdscr.addch(board_start_row + 1 + r, board_start_col, BORDER_CELL, border_pair)
             except: pass
             try: stdscr.addch(board_start_row + 1 + r, board_start_col + self.width + 1, BORDER_CELL, border_pair)
             except: pass
        draw_origin_r, draw_origin_c = board_start_row + 1, board_start_col + 1
        for r in range(self.height): # Draw board content
            for c in range(self.width):
                idx = self.board[r][c]; char = BLOCK_CELL if idx != 0 else EMPTY_CELL
                pair = curses.color_pair(idx) if idx != 0 else curses.A_NORMAL
                try: stdscr.addch(draw_origin_r + r, draw_origin_c + c, char, pair)
                except: pass
        if not self.game_over and self.current_piece_type: # Draw current piece
            coords = self._get_piece_coords(); idx = COLOR_MAP.get(self.current_piece_type, 0)
            if ORANGE_DEFINED and self.current_piece_type == 'L': idx = ORANGE_PAIR_INDEX
            pair = curses.color_pair(idx)
            for r, c in coords:
                if 0 <= r < self.height and 0 <= c < self.width:
                    try: stdscr.addch(draw_origin_r + r, draw_origin_c + c, BLOCK_CELL, pair)
                    except: pass
        preview_start_row = board_start_row + 1 # Draw preview
        preview_start_col = board_start_col + self.width + BORDER_WIDTH + MIN_PREVIEW_SPACING
        try: stdscr.addstr(preview_start_row -1, preview_start_col, "Next:", info_pair)
        except: pass
        if self.next_piece_type:
            shape = TETROMINOES[self.next_piece_type][0]; idx = COLOR_MAP.get(self.next_piece_type, 0)
            if ORANGE_DEFINED and self.next_piece_type == 'L': idx = ORANGE_PAIR_INDEX
            pair = curses.color_pair(idx); min_r, min_c = min(r for r,c in shape), min(c for r,c in shape)
            for r_p, c_p in shape:
                 dr, dc = preview_start_row+(r_p-min_r), preview_start_col+(c_p-min_c)
                 try: stdscr.addch(dr, dc, BLOCK_CELL, pair)
                 except: pass
        if self.game_over: # Draw Game Over
            t1="GAME OVER"; t2=f"Score: {self.score}"; t3="Exit: q"
            r = draw_origin_r + self.height // 2 - 1
            c1 = draw_origin_c + (self.width - len(t1)) // 2; c2 = draw_origin_c + (self.width - len(t2)) // 2; c3 = draw_origin_c + (self.width - len(t3)) // 2
            red = curses.color_pair(COLOR_MAP['ERROR']) | curses.A_BOLD
            try: stdscr.addstr(r, c1, t1, red); stdscr.addstr(r + 1, c2, t2, curses.A_BOLD); stdscr.addstr(r + 2, c3, t3, curses.A_BOLD)
            except: pass
        stdscr.refresh()

# --- Sizing Calculation Helper (Unchanged) ---
def calculate_layout(max_y, max_x):
    target_total_w = math.floor(max_x * TARGET_WIDTH_FRACTION)
    target_board_w = target_total_w - BORDER_WIDTH - MIN_PREVIEW_SPACING - PREVIEW_WIDTH
    available_h = max_y - INFO_HEIGHT - BORDER_HEIGHT
    final_board_w = max(MIN_BOARD_WIDTH, target_board_w)
    final_board_h = max(MIN_BOARD_HEIGHT, available_h)
    required_total_h = final_board_h + INFO_HEIGHT + BORDER_HEIGHT
    required_total_w = final_board_w + BORDER_WIDTH + MIN_PREVIEW_SPACING + PREVIEW_WIDTH
    if required_total_h > max_y or required_total_w > max_x:
        fallback_h = max_y - INFO_HEIGHT - BORDER_HEIGHT
        fallback_w = max_x - BORDER_WIDTH - MIN_PREVIEW_SPACING - PREVIEW_WIDTH
        if fallback_h < MIN_BOARD_HEIGHT or fallback_w < MIN_BOARD_WIDTH: return None
        final_board_w = max(MIN_BOARD_WIDTH, fallback_w)
        final_board_h = max(MIN_BOARD_HEIGHT, fallback_h)
        required_total_h = final_board_h + INFO_HEIGHT + BORDER_HEIGHT
        required_total_w = final_board_w + BORDER_WIDTH + MIN_PREVIEW_SPACING + PREVIEW_WIDTH
    content_h = required_total_h; content_w = required_total_w
    top_offset = max(0, (max_y - content_h) // 2)
    left_offset = max(0, (max_x - content_w) // 2)
    return final_board_w, final_board_h, top_offset, left_offset

# --- Main Game Function (Unchanged) ---
def run_game(stdscr):
    global ORANGE_DEFINED, ORANGE_PAIR_INDEX
    curses.curs_set(0); stdscr.nodelay(1); stdscr.timeout(100)
    if curses.has_colors(): # Color Setup
        curses.start_color()
        try:
            if curses.COLORS>=256 and curses.can_change_color():
                 curses.init_color(ORANGE_COLOR_INDEX,1000,650,0); curses.init_pair(ORANGE_PAIR_INDEX,ORANGE_COLOR_INDEX,curses.COLOR_BLACK); ORANGE_DEFINED=True
            else: raise Exception()
        except: ORANGE_DEFINED=False; curses.init_pair(ORANGE_PAIR_INDEX,curses.COLOR_WHITE,curses.COLOR_BLACK)
        for i,(fg,bg) in CURSES_COLOR_PAIRS.items():
             if i!=ORANGE_PAIR_INDEX:
                 try: curses.init_pair(i,fg,bg)
                 except: pass

    layout = calculate_layout(*stdscr.getmaxyx()) # Initial Layout
    if layout is None:
        stdscr.clear(); msg="Terminal too small!"; y,x=stdscr.getmaxyx(); cy,cx=y//2,max(0,(x-len(msg))//2)
        try: stdscr.addstr(cy, cx, msg, curses.color_pair(COLOR_MAP['ERROR'])|curses.A_BOLD)
        except: stdscr.addstr(0,0,msg)
        stdscr.refresh(); stdscr.timeout(-1); stdscr.getch(); return
    board_w, board_h, top_offset, left_offset = layout
    game = TetrisGame(width=board_w, height=board_h)

    while True: # Game Loop
        key = stdscr.getch(); quit_game = False
        if key == curses.KEY_RESIZE: # Handle Resize
            new_layout = calculate_layout(*stdscr.getmaxyx())
            if new_layout is None: quit_game = True
            else:
                board_w, board_h, top_offset, left_offset = new_layout
                stdscr.clear()
        elif not game.game_over: # Input Handling
            if key in (curses.KEY_LEFT, ord('a'), ord('A')): game.move(0, -1)
            elif key in (curses.KEY_RIGHT, ord('d'), ord('D')): game.move(0, 1)
            elif key in (curses.KEY_DOWN, ord('s'), ord('S')):
                if game.move(1, 0): game.fall_time = time.time()
            elif key in (curses.KEY_UP, ord('w'), ord('W')): game.rotate() # Calls corrected rotate
            elif key == ord(' '): game.hard_drop()
            elif key in (ord('q'), ord('Q'), 27): quit_game = True
            game.step() # Game Step
        elif key in (ord('q'), ord('Q'), 27): quit_game = True

        if quit_game: break
        try: game.draw(stdscr, top_offset, left_offset) # Draw
        except curses.error: break

# --- Entry Point (Unchanged) ---
if __name__ == "__main__":
    try: curses.wrapper(run_game); print("Game exited normally.")
    except curses.error as e: print(f"\nCurses error: {e}")
    except Exception as e: print(f"\nUnexpected error: {e}"); import traceback; traceback.print_exc()
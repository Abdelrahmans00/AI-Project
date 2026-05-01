"""
Hnefatafl (Viking Chess) - Tkinter GUI
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from game_state import *
from game_logic import get_piece_moves, get_all_moves, make_move, is_valid_move
from ai import get_computer_move

CELL = 58
MARGIN = 40
BOARD_PX = CELL * BOARD_SIZE + MARGIN * 2
PIECE_R = 22

# Colors
BG_DARK = "#1a1a2e"
BOARD_LIGHT = "#d4a76a"
BOARD_DARK = "#c49555"
THRONE_CLR = "#8b4513"
CORNER_CLR = "#6b3410"
GRID_CLR = "#8b6914"
SEL_CLR = "#ffe066"
MOVE_CLR = "#66ff99"
ATK_CLR = "#2c2c2c"
ATK_OUT = "#111111"
DEF_CLR = "#f0e6d3"
DEF_OUT = "#b8a88a"
KING_CLR = "#ffd700"
KING_OUT = "#b8860b"
LAST_SRC = "#ff6b6b"
LAST_DST = "#69db7c"
CAPTURE_CLR = "#ff4444"

class HnefataflGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hnefatafl - Viking Chess")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)

        self.state = GameState()
        self.selected = None
        self.valid_moves = []
        self.human_player = ATTACKER_PLAYER
        self.computer_player = DEFENDER_PLAYER
        self.difficulty = "Medium"
        self.thinking = False
        self.last_move = None
        self.last_captured = []
        self.move_history = []

        self._build_ui()
        self.draw_board()

    def _build_ui(self):
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(padx=10, pady=10)

        # Board canvas
        self.canvas = tk.Canvas(main, width=BOARD_PX, height=BOARD_PX,
                                bg=BOARD_LIGHT, highlightthickness=2,
                                highlightbackground="#8b6914")
        self.canvas.pack(side=tk.LEFT, padx=(0, 15))
        self.canvas.bind("<Button-1>", self.on_click)

        # Side panel
        panel = tk.Frame(main, bg=BG_DARK, width=220)
        panel.pack(side=tk.RIGHT, fill=tk.Y)

        # Title
        tk.Label(panel, text="⚔ HNEFATAFL ⚔", font=("Segoe UI", 18, "bold"),
                 fg="#ffd700", bg=BG_DARK).pack(pady=(0, 5))
        tk.Label(panel, text="Viking Chess", font=("Segoe UI", 11),
                 fg="#aaa", bg=BG_DARK).pack(pady=(0, 15))

        sep = tk.Frame(panel, bg="#444", height=1)
        sep.pack(fill=tk.X, pady=5)

        # Play as
        tk.Label(panel, text="Play as:", font=("Segoe UI", 11, "bold"),
                 fg="#ddd", bg=BG_DARK).pack(anchor=tk.W, pady=(10, 3))
        self.side_var = tk.StringVar(value="Attacker")
        sf = tk.Frame(panel, bg=BG_DARK)
        sf.pack(anchor=tk.W)
        for txt in ("Attacker", "Defender"):
            tk.Radiobutton(sf, text=txt, variable=self.side_var, value=txt,
                           font=("Segoe UI", 10), fg="#ddd", bg=BG_DARK,
                           selectcolor=BG_DARK, activebackground=BG_DARK,
                           activeforeground="#ffd700",
                           command=self.on_side_change).pack(anchor=tk.W)

        # Difficulty
        tk.Label(panel, text="Difficulty:", font=("Segoe UI", 11, "bold"),
                 fg="#ddd", bg=BG_DARK).pack(anchor=tk.W, pady=(15, 3))
        self.diff_var = tk.StringVar(value="Medium")
        df = tk.Frame(panel, bg=BG_DARK)
        df.pack(anchor=tk.W)
        depth_map = {'Easy': 1, 'Medium': 3, 'Hard': 5}
        for txt in ("Easy", "Medium", "Hard"):
            label = f"{txt} (depth {depth_map[txt]})"
            tk.Radiobutton(df, text=label,
                           variable=self.diff_var, value=txt,
                           font=("Segoe UI", 10), fg="#ddd", bg=BG_DARK,
                           selectcolor=BG_DARK, activebackground=BG_DARK,
                           activeforeground="#ffd700").pack(anchor=tk.W)

        sep2 = tk.Frame(panel, bg="#444", height=1)
        sep2.pack(fill=tk.X, pady=10)

        # Status
        self.status_var = tk.StringVar(value="Attacker's turn (You)")
        tk.Label(panel, textvariable=self.status_var,
                 font=("Segoe UI", 12, "bold"), fg="#66ff99", bg=BG_DARK,
                 wraplength=200).pack(pady=5)

        # Piece counts
        self.count_var = tk.StringVar()
        tk.Label(panel, textvariable=self.count_var,
                 font=("Segoe UI", 10), fg="#ccc", bg=BG_DARK,
                 wraplength=200, justify=tk.LEFT).pack(pady=5)
        self._update_counts()

        # Turn counter
        self.turn_var = tk.StringVar(value="Turn: 1")
        tk.Label(panel, textvariable=self.turn_var,
                 font=("Segoe UI", 10), fg="#aaa", bg=BG_DARK).pack(pady=3)

        sep3 = tk.Frame(panel, bg="#444", height=1)
        sep3.pack(fill=tk.X, pady=10)

        # Buttons
        btn_style = {"font": ("Segoe UI", 11, "bold"), "width": 18,
                     "cursor": "hand2", "relief": tk.FLAT, "bd": 0}
        tk.Button(panel, text="🔄 New Game", bg="#2d6a4f", fg="white",
                  activebackground="#40916c", command=self.new_game,
                  **btn_style).pack(pady=4)
        tk.Button(panel, text="↩ Undo Move", bg="#e76f51", fg="white",
                  activebackground="#f4845f", command=self.undo_move,
                  **btn_style).pack(pady=4)

        # Legend
        sep4 = tk.Frame(panel, bg="#444", height=1)
        sep4.pack(fill=tk.X, pady=10)
        tk.Label(panel, text="Legend", font=("Segoe UI", 10, "bold"),
                 fg="#aaa", bg=BG_DARK).pack(anchor=tk.W)
        legend = tk.Canvas(panel, width=200, height=80, bg=BG_DARK,
                           highlightthickness=0)
        legend.pack(anchor=tk.W, pady=5)
        legend.create_oval(10, 5, 28, 23, fill=ATK_CLR, outline=ATK_OUT, width=2)
        legend.create_text(40, 14, text="Attacker (24)", fill="#ccc",
                           font=("Segoe UI", 9), anchor=tk.W)
        legend.create_oval(10, 30, 28, 48, fill=DEF_CLR, outline=DEF_OUT, width=2)
        legend.create_text(40, 39, text="Defender (12)", fill="#ccc",
                           font=("Segoe UI", 9), anchor=tk.W)
        legend.create_oval(10, 55, 28, 73, fill=KING_CLR, outline=KING_OUT, width=2)
        legend.create_text(40, 64, text="King (1)", fill="#ccc",
                           font=("Segoe UI", 9), anchor=tk.W)

    def _rc_to_px(self, row, col):
        x = MARGIN + col * CELL + CELL // 2
        y = MARGIN + row * CELL + CELL // 2
        return x, y

    def _px_to_rc(self, x, y):
        col = (x - MARGIN) // CELL
        row = (y - MARGIN) // CELL
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return row, col
        return None

    def draw_board(self):
        c = self.canvas
        c.delete("all")

        # Draw cells
        for r in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x1 = MARGIN + col * CELL
                y1 = MARGIN + r * CELL
                x2 = x1 + CELL
                y2 = y1 + CELL

                # Cell color
                if (r, col) in CORNERS:
                    clr = CORNER_CLR
                elif (r, col) == THRONE:
                    clr = THRONE_CLR
                elif (r + col) % 2 == 0:
                    clr = BOARD_LIGHT
                else:
                    clr = BOARD_DARK

                c.create_rectangle(x1, y1, x2, y2, fill=clr, outline=GRID_CLR,
                                   width=1)

        # Draw corner markers (X pattern)
        for cr, cc in CORNERS:
            x, y = self._rc_to_px(cr, cc)
            off = CELL // 3
            c.create_line(x-off, y-off, x+off, y+off, fill="#ffd700", width=2)
            c.create_line(x-off, y+off, x+off, y-off, fill="#ffd700", width=2)

        # Throne marker
        tx, ty = self._rc_to_px(5, 5)
        c.create_line(tx-12, ty-12, tx+12, ty+12, fill="#ffd700", width=2)
        c.create_line(tx-12, ty+12, tx+12, ty-12, fill="#ffd700", width=2)

        # Highlight last move
        if self.last_move:
            src, dst = self.last_move
            sx, sy = self._rc_to_px(*src)
            c.create_rectangle(sx-CELL//2+2, sy-CELL//2+2,
                               sx+CELL//2-2, sy+CELL//2-2,
                               outline=LAST_SRC, width=2, dash=(4, 2))
            dx, dy = self._rc_to_px(*dst)
            c.create_rectangle(dx-CELL//2+2, dy-CELL//2+2,
                               dx+CELL//2-2, dy+CELL//2-2,
                               outline=LAST_DST, width=2, dash=(4, 2))

        # Highlight captured pieces
        for cr, cc in self.last_captured:
            cx, cy = self._rc_to_px(cr, cc)
            c.create_rectangle(cx-CELL//2+2, cy-CELL//2+2,
                               cx+CELL//2-2, cy+CELL//2-2,
                               outline=CAPTURE_CLR, width=2, dash=(3, 2))

        # Highlight selected piece
        if self.selected:
            sx, sy = self._rc_to_px(*self.selected)
            c.create_rectangle(sx-CELL//2+1, sy-CELL//2+1,
                               sx+CELL//2-1, sy+CELL//2-1,
                               outline=SEL_CLR, width=3)

        # Highlight valid moves
        for mr, mc in self.valid_moves:
            mx, my = self._rc_to_px(mr, mc)
            c.create_oval(mx-8, my-8, mx+8, my+8, fill=MOVE_CLR,
                          outline="", stipple="gray50")

        # Draw pieces
        for r in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.state.get_piece(r, col)
                if piece == EMPTY:
                    continue
                x, y = self._rc_to_px(r, col)
                if piece == ATTACKER:
                    fill, outline = ATK_CLR, ATK_OUT
                elif piece == DEFENDER:
                    fill, outline = DEF_CLR, DEF_OUT
                else:
                    fill, outline = KING_CLR, KING_OUT

                c.create_oval(x-PIECE_R, y-PIECE_R, x+PIECE_R, y+PIECE_R,
                              fill=fill, outline=outline, width=2)

                # King crown symbol
                if piece == KING:
                    c.create_text(x, y, text="♚", font=("Segoe UI", 16),
                                  fill="#8b4513")

        # Row/col labels
        for i in range(BOARD_SIZE):
            lx = MARGIN + i * CELL + CELL // 2
            c.create_text(lx, MARGIN - 15, text=str(i),
                          font=("Segoe UI", 9), fill=GRID_CLR)
            c.create_text(lx, BOARD_PX - MARGIN + 15, text=str(i),
                          font=("Segoe UI", 9), fill=GRID_CLR)
            ly = MARGIN + i * CELL + CELL // 2
            c.create_text(MARGIN - 15, ly, text=str(i),
                          font=("Segoe UI", 9), fill=GRID_CLR)

    def on_click(self, event):
        if self.thinking or self.state.game_over:
            return
        if self.state.current_player != self.human_player:
            return

        pos = self._px_to_rc(event.x, event.y)
        if pos is None:
            return
        r, c = pos

        # If a piece is selected and click on valid move → execute
        if self.selected and (r, c) in self.valid_moves:
            self._execute_human_move(self.selected, (r, c))
            return

        # Select a piece
        piece = self.state.get_piece(r, c)
        can_select = False
        if self.human_player == ATTACKER_PLAYER and piece == ATTACKER:
            can_select = True
        elif self.human_player == DEFENDER_PLAYER and piece in (DEFENDER, KING):
            can_select = True

        if can_select:
            self.selected = (r, c)
            self.valid_moves = get_piece_moves(self.state, r, c)
        else:
            self.selected = None
            self.valid_moves = []

        self.draw_board()

    def _execute_human_move(self, src, dst):
        self.move_history.append(self.state.copy())
        self.state, captured = make_move(self.state, src, dst)
        self.last_move = (src, dst)
        self.last_captured = captured
        self.selected = None
        self.valid_moves = []
        self._update_status()
        self.draw_board()

        if not self.state.game_over:
            self.root.after(400, self._computer_turn)

    def _computer_turn(self):
        if self.state.game_over or self.state.current_player != self.computer_player:
            return
        self.thinking = True
        self.status_var.set("🤔 Computer thinking...")
        self.root.update()

        def think():
            diff = self.diff_var.get()
            move = get_computer_move(self.state, diff, self.computer_player)
            self.root.after(0, lambda: self._apply_computer_move(move))

        threading.Thread(target=think, daemon=True).start()

    def _apply_computer_move(self, move):
        if move is None:
            self.thinking = False
            return
        src, dst = move
        self.move_history.append(self.state.copy())
        self.state, captured = make_move(self.state, src, dst)
        self.last_move = (src, dst)
        self.last_captured = captured
        self.thinking = False
        self._update_status()
        self.draw_board()

    def _update_status(self):
        na, nd = self.state.count_pieces()
        self.count_var.set(f"Attackers: {na}  |  Defenders: {nd}")
        turn_num = len(self.move_history) // 2 + 1
        self.turn_var.set(f"Turn: {turn_num}")

        if self.state.game_over:
            if self.state.winner == ATTACKER_PLAYER:
                msg = "⚔ Attackers WIN! King captured!"
            else:
                msg = "👑 Defenders WIN! King escaped!"
            self.status_var.set(msg)
            who = "You win!" if self.state.winner == self.human_player else "Computer wins!"
            messagebox.showinfo("Game Over", f"{msg}\n{who}")
        else:
            if self.state.current_player == self.human_player:
                self.status_var.set(f"Your turn ({self.human_player.title()})")
            else:
                self.status_var.set(f"Computer's turn ({self.computer_player.title()})")

    def _update_counts(self):
        na, nd = self.state.count_pieces()
        self.count_var.set(f"Attackers: {na}  |  Defenders: {nd}")

    def new_game(self):
        self.state = GameState()
        self.selected = None
        self.valid_moves = []
        self.last_move = None
        self.last_captured = []
        self.move_history = []
        self.thinking = False
        self.on_side_change()

    def on_side_change(self):
        side = self.side_var.get()
        if side == "Attacker":
            self.human_player = ATTACKER_PLAYER
            self.computer_player = DEFENDER_PLAYER
        else:
            self.human_player = DEFENDER_PLAYER
            self.computer_player = ATTACKER_PLAYER

        if not self.state.game_over:
            self._update_status()
            self._update_counts()
            self.draw_board()
            if self.state.current_player == self.computer_player:
                self.root.after(500, self._computer_turn)

    def undo_move(self):
        if self.thinking or len(self.move_history) < 2:
            return
        # Undo both computer and human move
        self.move_history.pop()
        self.state = self.move_history.pop()
        self.selected = None
        self.valid_moves = []
        self.last_move = None
        self.last_captured = []
        self._update_status()
        self.draw_board()


def main():
    root = tk.Tk()
    root.configure(bg=BG_DARK)
    app = HnefataflGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

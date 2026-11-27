from dataclasses import dataclass, field
from typing import ClassVar
import random
from itertools import product
import tkinter as tk

@dataclass
class GameState:
    PLAYER_NONE: ClassVar[int] = 0
    PLAYER_BLUE: ClassVar[int] = 1
    PLAYER_RED:  ClassVar[int] = 2
    
    CARD_SUIT: ClassVar[tuple[tuple[str, list]]] = (
        # --- BLUE (0..7) ---
        ("Tiger",  [(-2, 0), (1, 0)]),
        ("Crab",   [(-1, 0), (0, -2), (0, 2)]),
        ("Monkey", [(-1, -1), (-1, 1), (1, -1), (1, 1)]),
        ("Crane",  [(-1, 0), (1, -1), (1, 1)]),
        ("Rabbit", [(0, 2), (-1, 1), (1, -1)]),    # Frogの鏡像
        ("Goose",  [(-1, -1), (0, -1), (0, 1), (1, 1)]), # Roosterの鏡像
        ("Ox",     [(-1, 0), (0, 1), (1, 0)]),     # Horseの鏡像
        ("Eel",    [(-1, -1), (0, 1), (1, -1)]),   # Cobraの鏡像
    
        # --- RED (8..15) ---
        ("Dragon",   [(-1, -2), (-1, 2), (1, -1), (1, 1)]),
        ("Elephant", [(-1, -1), (-1, 1), (0, -1), (0, 1)]),
        ("Mantis",   [(-1, -1), (-1, 1), (1, 0)]),
        ("Boar",     [(-1, 0), (0, -1), (0, 1)]),
        ("Frog",     [(0, -2), (-1, -1), (1, 1)]),   # Rabbitの鏡像
        ("Rooster",  [(-1, 1), (0, -1), (0, 1), (1, -1)]), # Gooseの鏡像
        ("Horse",    [(-1, 0), (0, -1), (1, 0)]),    # Oxの鏡像
        ("Cobra",    [(-1, 1), (0, -1), (1, 1)]),    # Eelの鏡像
    )
    
    # maps card ID (starts with 1) to card name
    CARD_NAMES: ClassVar[tuple[str]] = tuple(card[0] for card in CARD_SUIT)
    # maps card name to card ID
    CARD_ID: ClassVar[dict] = {name: i for i, name in enumerate(CARD_NAMES[:len(set(CARD_NAMES))])}
    CARD_MOVES: ClassVar[dict] = {card[0]: card[1] for card in CARD_SUIT }
    
    PIECE_ID: ClassVar[dict] = {"empty": 0, "master": 1, "student": 2}
    PIECE_NAMES = (
        " ", 
        #"onmyoji", "shikigami",
        "master", "student",
        #"seirei", "sylph",
    )
    
    board: bytearray = field(default_factory=lambda: bytearray(25))
    # cards[0:2]: BLUEの手札, cards[2]: 交換用, cards[3:5]: REDの手札
    cards: bytearray = field(default_factory=lambda: bytearray(5))
    turn: int = PLAYER_BLUE

    @staticmethod
    def piece(cellval):
        # player id, piece type
        return ((cellval >> 2) & 3, cellval & 3)
    
    @staticmethod
    def card_stamp(card_id):
        if 15 < card_id :
            raise ValueError(f"card ID out of range: {card_id}")
        return ("blue", "red")[card_id>>3]
    
    @staticmethod
    def card_stamp_byname(card_name):
        if card_name not in GameState.CARD_NAMES :
            raise ValueError(f"unknown card name: {card_name}")
        return GameState.card_stamp(GameState.CARD_ID[card_name])

    def __post_init__(self):
        if any(self.board):
            return
        # self.cards (blue[2], deck, red[2]
        chosen = random.sample(self.CARD_NAMES, 5)
        for i, name in enumerate(chosen):
            self.cards[i] = self.CARD_ID[name]
        # 5枚目(交換用)のスタンプ色で先手決定
        self.turn = self.PLAYER_BLUE if self.card_stamp(self.cards[2]) == "blue" else self.PLAYER_RED

        # BLUEは下(row 4)、REDは上(row 0)に固定
        for col in range(5):
            pctype = self.PIECE_ID["master"] if col == 2 else self.PIECE_ID["student"]
            self.board[4 * 5 + col] = (self.PLAYER_BLUE << 2) | pctype
            self.board[0 * 5 + col] = (self.PLAYER_RED << 2) | pctype

    # bytearray(25) -> 100bit int（リトルエンディアン的なパック）
    # 各バイトの上位4bitは0なので、16進文字列経由で一発変換できる
    def board_int(self):
        return int.from_bytes(bytes((((self.board[i+1] if i < 25 - 1 else 0)<<4) | self.board[i]) for i in range(0, 25, 2)), "little") # ※あるいは単純なシフト合算

    def cards_int(self):
        return int.from_bytes(bytes( 
            ( (self.cards[1]<<4) | (self.cards[0] & 0x0f), 
              (self.cards[2] & 0x0f),
              (self.cards[4] <<4) | (self.cards[3] & 0x0f) )
            ), "little") # ※あるいは単純なシフト合算

    def to_int(self):
        return (self.turn << 120) | (self.cards_int() << 100) | self.board_int()
    
    def set_int(self, bitval):
        for i in range(25):
            self.board[i] = bitval & 0x0f
            bitval >>= 4
        for i in (0, 1, 2, 3, 4):
            self.cards[i] = bitval & 0x0f
            bitval >>=4
            if i == 2 :
                bitval >>= 4
        self.turn = bitval & 0x03
    
    @classmethod
    def from_int(cls, val: int) -> "GameState":
        obj = cls.__new__(cls)
        obj.set_int(val)
        return obj

    def piece_at(self, row, col):
        cellval = self.board[row * 5 + col]
        # player id, piece type
        return ((cellval >> 2) & 3, cellval & 3)
    
    def legal_destinations(self, r, c, card_id):
        """(r, c)の駒に card_id を使ったときの合法な移動先リストを返す"""
        player, _ = self.piece_at(r, c)
        if player != self.turn:
            return []
        card_name = self.CARD_NAMES[card_id]
        sign = 1 if player == self.PLAYER_BLUE else -1
        dests = []
        for dr, dc in self.CARD_MOVES[card_name]:
            nr, nc = r + sign * dr, c + sign * dc
            if 0 <= nr < 5 and 0 <= nc < 5:
                target_player, _ = self.piece_at(nr, nc)
                if target_player != player:  # 自駒の上には移動不可
                    dests.append((nr, nc))
        print(hex(self.to_int()))
        return dests

    def apply_move(self, r, c, nr, nc, card_slot):
        """駒を移動し、使用したカード(card_slot: 0,1 or 3,4)を中央(2)と交換"""
        self.board[nr * 5 + nc] = self.board[r * 5 + c]
        self.board[r * 5 + c] = 0
        self.cards[card_slot], self.cards[2] = self.cards[2], self.cards[card_slot]
        self.turn = self.PLAYER_RED if self.turn == self.PLAYER_BLUE else self.PLAYER_BLUE

    def board_square(self, row, col):
        return self.board[row*5 + col]

    def __str__(self):
        resstr = ""
        resstr += self.CARD_NAMES[self.cards[3]] + ", " + self.CARD_NAMES[self.cards[4]]
        resstr += "\nRed\n+-+-+-+-+-+\n"
        for r, c in product(range(5), range(5)) :
            player_id, pc_type = self.piece_at(r,c)
            resstr += '|'
            if player_id == self.PLAYER_NONE:
                resstr += ' '
            elif player_id == self.PLAYER_RED :
                resstr += 'R' if self.PIECE_NAMES[pc_type] == 'master' else 'r'
            elif player_id == self.PLAYER_BLUE :
                resstr += 'B' if self.PIECE_NAMES[pc_type] == 'master' else 'b'
            if (c % 5) == 4 :
                resstr += '|'
                if r == 2 :
                    resstr += ' ' + self.CARD_NAMES[self.cards[2]]
                resstr += '\n+-+-+-+-+-+\n'
        resstr += 'Blue\n'
        resstr += self.CARD_NAMES[self.cards[0]] + ", " + self.CARD_NAMES[self.cards[1]]
        return resstr

class OnitamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Onitama Prototype")
        self.state = GameState()
        self.selected_sq = None    # (r, c)
        self.selected_slot = None  # 0, 1 (BLUE) or 3, 4 (RED)

        self.info_label = tk.Label(root, font=("Helvetica", 14, "bold"))
        self.info_label.pack(pady=5)

        # RED (上側) のカード表示エリア
        self.red_frame = tk.Frame(root)
        self.red_frame.pack(pady=5)

        # 中央エリア（盤面 + 交換用カード）
        mid_frame = tk.Frame(root)
        mid_frame.pack(pady=5)

        self.board_canvas = tk.Canvas(mid_frame, width=300, height=300, bg="#e8d0a9")
        self.board_canvas.pack(side=tk.LEFT, padx=10)
        self.board_canvas.bind("<Button-1>", self.on_board_click)

        self.side_frame = tk.Frame(mid_frame)
        self.side_frame.pack(side=tk.LEFT, padx=10)

        # BLUE (下側) のカード表示エリア
        self.blue_frame = tk.Frame(root)
        self.blue_frame.pack(pady=5)

        self.draw_all()


    def draw_card(self, parent, card_id, slot=None, rotate=False):
        name = self.state.CARD_NAMES[card_id]
        is_selected = (slot is not None and slot == self.selected_slot)
        bg = "#fff2cc" if is_selected else "#f0f0f0"
        relief = tk.SUNKEN if is_selected else tk.RAISED

        frame = tk.Frame(parent, bd=2, relief=relief, bg=bg, padx=4, pady=4)

        # ラベル(高さ22px) + 5x5グリッド(75px) を1つのCanvasにまとめる
        cv = tk.Canvas(frame, width=75, height=97, bg=bg, highlightthickness=0)
        cv.pack()

        if rotate:
            # 180度回転時: グリッドを上(y=0..75)、逆さまのカード名を下(y=86)に配置
            grid_y0 = 0
            cv.create_text(37, 86, text=name, font=("Helvetica", 10, "bold"), angle=180)
        else:
            # 通常時: カード名を上(y=11)、グリッドを下(y=22..97)に配置
            grid_y0 = 22
            cv.create_text(37, 11, text=name, font=("Helvetica", 10, "bold"))

        sign = -1 if rotate else 1
        moves = {(2 + sign * dr, 2 + sign * dc) for dr, dc in self.state.CARD_MOVES[name]}
        stamp_color = "#4a90e2" if self.state.card_stamp_byname(name) == "blue" else "#e24a4a"

        for r in range(5):
            for c in range(5):
                color = "white"
                if (r, c) == (2, 2):
                    color = "#444444"
                elif (r, c) in moves:
                    color = stamp_color
                y1 = grid_y0 + r * 15
                cv.create_rectangle(c * 15, y1, (c + 1) * 15, y1 + 15, fill=color, outline="#cccccc")

        if slot is not None:
            for w in (frame, cv):
                w.bind("<Button-1>", lambda e, s=slot: self.on_card_click(s))
        return frame

    def draw_all(self):
        turn_str = "BLUE (下)" if self.state.turn == GameState.PLAYER_BLUE else "RED (上)"
        self.info_label.config(text=f"Turn: {turn_str}")

        # カード領域クリア＆再描画
        for f in (self.red_frame, self.side_frame, self.blue_frame):
            for w in f.winfo_children():
                w.destroy()

        for slot in (3, 4):
            self.draw_card(self.red_frame, self.state.cards[slot], slot, rotate=True).pack(side=tk.LEFT, padx=5)

        tk.Label(self.side_frame, text="Next Card").pack()
        self.draw_card(self.side_frame, self.state.cards[2], slot=None).pack()

        for slot in (0, 1):
            self.draw_card(self.blue_frame, self.state.cards[slot], slot, rotate=False).pack(side=tk.LEFT, padx=5)

        # 盤面描画
        self.board_canvas.delete("all")
        dests = []
        if self.selected_sq and self.selected_slot is not None:
            dests = self.state.legal_destinations(*self.selected_sq, self.state.cards[self.selected_slot])

        for r in range(5):
            for c in range(5):
                x1, y1, x2, y2 = c * 60, r * 60, (c + 1) * 60, (r + 1) * 60
                fill = "#e8d0a9"
                if (r, c) in ((0, 2), (4, 2)):  # 玉座（Temple Arch）
                    fill = "#d4b483"
                if self.selected_sq == (r, c):
                    fill = "#ffe066"
                elif (r, c) in dests:
                    fill = "#a8e6cf"

                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#5c4033")

                player, ptype = self.state.piece(self.state.board[r * 5 + c])
                if player != 0:
                    pcolor = "#1f6feb" if player == GameState.PLAYER_BLUE else "#d73a49"
                    pad = 10 if ptype == 1 else 18
                    self.board_canvas.create_oval(x1+pad, y1+pad, x2-pad, y2-pad, fill=pcolor, outline="white", width=2)
                    if ptype == 1:
                        self.board_canvas.create_text(x1+30, y1+30, text="王", fill="white", font=("Helvetica", 12, "bold"))

    def on_card_click(self, slot):
        is_blue_slot = slot in (0, 1)
        if (self.state.turn == GameState.PLAYER_BLUE and is_blue_slot) or \
           (self.state.turn == GameState.PLAYER_RED and not is_blue_slot):
            self.selected_slot = slot
            self.draw_all()

    def on_board_click(self, event):
        c, r = event.x // 60, event.y // 60
        if not (0 <= r < 5 and 0 <= c < 5):
            return

        # 移動先をクリックした場合
        if self.selected_sq and self.selected_slot is not None:
            dests = self.state.legal_destinations(*self.selected_sq, self.state.cards[self.selected_slot])
            if (r, c) in dests:
                self.state.apply_move(*self.selected_sq, r, c, self.selected_slot)
                self.selected_sq = None
                self.selected_slot = None
                self.draw_all()
                return

        # 自分の駒を選択した場合
        player, _ = self.state.piece(self.state.board[r * 5 + c])
        if player == self.state.turn:
            self.selected_sq = (r, c)
            # 手札をまだ選んでいなければ1枚目を自動選択
            if self.selected_slot is None:
                self.selected_slot = 0 if self.state.turn == GameState.PLAYER_BLUE else 3
            self.draw_all()

if __name__ == "__main__":
    root = tk.Tk()
    app = OnitamaGUI(root)
    print(app.state)
    root.mainloop()
    gsta = app.state
    val = gsta.to_int()
    print(gsta, hex(val))
    gsta.set_int(val)
    print(gsta, hex(gsta.to_int()))

'''
Created on 2026/11/14

@author: sin
'''
from typing import ClassVar
from dataclasses import dataclass, field
from itertools import product
import random

@dataclass
class GameState:
    PLAYER_BLUE: ClassVar[int] = 0
    PLAYER_RED: ClassVar[int] = 1
    
    CARD_STAMP = {
        "Tiger": "blue",
        "Dragon": "red",
        "Frog": "red",
        "Rabbit": "blue",
        "Crab": "blue",
        "Elephant": "red",
        "Goose": "blue",
        "Rooster": "red",
        "Monkey": "blue",
        "Mantis": "red",
        "Horse": "red",
        "Ox": "blue",
        "Crane": "blue",
        "Boar": "red",
        "Eel": "blue",
        "Cobra": "red",
    }
    
    CARD_MOVES = {
        "Tiger":    [(0, 2), (0, -1)],
        "Dragon":   [(-2, 1), (2, 1), (-1, -1), (1, -1)],
        "Frog":     [(-2, 0), (-1, 1), (1, -1)],
        "Rabbit":  [(2, 0), (1, 1), (-1, -1)],
        "Crab":     [(0, 1), (-2, 0), (2, 0)],
        "Elephant": [(-1, 1), (1, 1), (-1, 0), (1, 0)],
        "Goose":    [(-1, 1), (-1, 0), (1, 0), (1, -1)],
        "Rooster": [(1, 1), (-1, 0), (1, 0), (-1, -1)],
        "Monkey":   [(-1, 1), (1, 1), (-1, -1), (1, -1)],
        "Mantis":   [(-1, 1), (1, 1), (0, -1)],
        "Horse":    [(0, 1), (-1, 0), (0, -1)],
        "Ox":       [(0, 1), (1, 0), (0, -1)],
        "Crane":    [(0, 1), (-1, -1), (1, -1)],
        "Boar":     [(0, 1), (-1, 0), (1, 0)],
        "Eel":      [(-1, 1), (1, 0), (-1, -1)],
        "Cobra":    [(1, 1), (-1, 0), (1, -1)],
    }
    
    CARD_NAMES = (
        "Tiger", "Dragon", "Frog", "Rabbit",
        "Crab", "Elephant", "Goose", "Rooster",
        "Monkey", "Mantis", "Horse", "Ox",
        "Crane", "Boar", "Eel", "Cobra",
    )
    
    CARD_ID = {name: i for i, name in enumerate(CARD_NAMES, start=1)}
    
    PIECE_NAMES = (
        " ", "onmyoji", "sikigami",
        "master", "student",
        "seirei", "sylph",
        ""
    )
    
    PIECE_ID = {"onmyoji":1, "shikigami": 2, "master":1, "student": 2, 
                "seirei":3, "sylph":3, "　": 0}
    
    board: bytearray = field(default_factory=lambda: bytearray(25))
    cards: bytearray = field(default_factory=lambda: bytearray(5))
    turn: int = PLAYER_BLUE
    first: int = PLAYER_BLUE
    
    @staticmethod
    def piece(cellval):
        player_id = (cellval >> 2)& 3
        piece_id = cellval&3
        return (player_id, piece_id)
        
    def __post_init__(self):
        cards_chosen = random.sample(self.CARD_NAMES, 5)
        count_stamp = {"blue": 0, "red": 0}
        for ix in range(5):
            self.cards[ix] = self.CARD_ID[cards_chosen[ix]]
            count_stamp[self.CARD_STAMP[cards_chosen[ix]]] += 1
        if count_stamp["blue"] < count_stamp["red"] :
            self.first = self.PLAYER_RED
            self.turn = self.PLAYER_RED
        else:
            self.turn = self.PLAYER_BLUE
            self.first = self.PLAYER_BLUE
    
        for col in range(0, 5) :
            if self.first == self.PLAYER_BLUE :
                self.board[self.rowcol(0,col)] = ((1<<self.PLAYER_BLUE)<<2) | (self.PIECE_ID["onmyoji"] if col == 2 else self.PIECE_ID["shikigami"])
                self.board[self.rowcol(4,col)] = ((1<<self.PLAYER_RED)<<2) | (self.PIECE_ID["onmyoji"] if col == 2 else self.PIECE_ID["shikigami"])
            elif self.first == self.PLAYER_RED :
                self.board[self.rowcol(4,col)] = ((1<<self.PLAYER_BLUE)<<2) | (self.PIECE_ID["onmyoji"] if col == 2 else self.PIECE_ID["shikigami"])
                self.board[self.rowcol(0,col)] = ((1<<self.PLAYER_RED)<<2) | (self.PIECE_ID["onmyoji"] if col == 2 else self.PIECE_ID["shikigami"])

    def rowcol(self, r, c):
        return r * 5 + c

    def square(self, row, col):
        return self.board[row*5 + col]
    
    def __str__(self):
        resstr = ""
        for cid in self.cards[:2]:
            resstr += self.CARD_NAMES[cid] + " "
        resstr += "\n+-+-+-+-+-+\n"
        for r, c in product(range(5), range(5)) :
            p = self.piece(self.square(r,c))
            resstr += '|'
            if p[0] == 0:
                resstr += ' '
            elif p[0] == (1<<self.first) :
                resstr += self.PIECE_NAMES[p[1]][0].upper()
            else:
                resstr += self.PIECE_NAMES[p[1]][0].lower()
            if (c % 5) == 4 :
                resstr += '|'
                if r == 2 :
                    resstr += ' ' + self.CARD_NAMES[self.cards[2]]
                resstr += '\n+-+-+-+-+-+\n'
        for cid in self.cards[3:]:
            resstr += self.CARD_NAMES[cid] + " "
        return resstr
            
if __name__ == '__main__':
    g = GameState(first=GameState.PLAYER_RED)
    print(g)
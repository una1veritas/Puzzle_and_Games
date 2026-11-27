'''
Created on 2026/01/23

@author: sin
'''
import sys
from collections import deque
#from itertools import product
from sqlite3intset import SQLite3IntSet
from bitarray import bitarray

class GobletGobblersBoard:
    # board : b12 .. b65 : 0b000000 goblets, 0b01 ... blue, 0b10 ... orange
    @staticmethod 
    def popcnt8(val):
        pc = (0, 1, 1, 2, 1, 2, 2, 3)[val & 0x0f]
        return pc + (0, 1, 1, 2, 1, 2, 2, 3)[val >> 4 & 0x0f]
    
    def __init__(self, board = None):
        bitarray.set_bitwidth(6)
        if board == None :
            self.board = bitarray(0)
        elif isinstance(board, GobletGobblersBoard) :
            self.board = bitarray(board.board)
        else:
            raise ValueError(f'{board} is not allowed as initializer ({type(board)})')
        return
    
    def __str__(self):
        out = ''
        for r in range(3):
            out += ''.join([self.cell_view(r, c) for c in range(3)])
            out += '\n'
        return out
    
    def __repr__(self):
        out = 'GobletGobblersBoard(\'n'
        out += self.__str__()
        out += '\')\n'
        return out
    
    def goblets_onboard(self):
        ttally = [0]*6
        for cx in range(9):
            cbits = self.board[cx]
            for bx in range(self.board.BITWIDTH) :
                ttally[bx] += cbits & 1
                cbits >>= 1
        return ttally
    
    def goblets_inhand(self):
        ttally = self.goblets_onboard()
        for bx in range(self.board.BITWIDTH) :
            ttally[bx] = 2 - ttally[bx]
        return ttally
    
    def goblets_count(self):
        total = 0
        for cx in range(9):
            total = self.popcnt8(self.board[cx])
        return total
    
    def player_in_turn(self):
        if (self.goblets_count() & 1) == 0 :
            return 0 #blue 
        else:
            return 1 # orange 
        #raise ValueError('goblets in hand {bc}, {oc} is incorrect.')
        
    def cell_view(self, r, c):
        bp = self.cell_top(r * 3 + c)
        return '_,˚xoXO'[bp]
    
    def cell_top(self, ix):
        p = self.board[ix]
        bit = 1<<5
        for pos in range(6,0,-1):
            if (p & bit) != 0 :
                return pos
            bit >>= 1
        return 0
        
    def place(self, r, c, sz):
        cellvalue = self.board[r*3+c]
        if (cellvalue >> 2*(sz-1)) > 0 :
            # already the goblet is placed which is bigger than or is the same size
            return False
        next_turn = self.player_in_turn()
        print(f'r = {r}, c = {c}, sz = {sz}, next_turn = {next_turn}')
        if next_turn == 0 and self.goblets_inhand()[(sz-1)*2 + next_turn] > 0 :
            self.board[r*3+c] |= 1 << ((sz - 1) * 2)
            return True
        elif next_turn == 1 and self.goblets_inhand()[(sz-1)*2 + next_turn] > 0 :
            self.board[r*3+c] |= 1 << ((sz) * 2 + 1)
            return True
        return False
    
    def winner(self):
        for s in ((0, 1, 2), (3, 4, 5),(6, 7, 8),(0, 3, 6),(1, 4, 7),(2, 5, 8),(0, 4, 8),(2, 4, 6)) :
            if all([self.cell_top(ix) % 2 == 1 for ix in s]) :
                #print([self.cell_top(ix) % 2 for ix in s])
                return 1
            elif all([ self.cell_top(ix) > 0 and (self.cell_top(ix) % 2 == 0) for ix in s]) :
                return 2
        return 0
    
    
def search(ggboard, intset):
    intset.clear()
    path = deque()
    path.append( [ggboard, 0] ) # board, search start move
    settled = 0
    while len(path) > 0 :
        board, startmove = path[-1]
        for ix in range(startmove, 3*3*(4-1)) : 
            r, c, sz = ix//3//3, (ix//3)%3, (ix%3)+1
            #print(r,c,sz)
            newboard = GobletGobblersBoard(board)
            if not newboard.place(r, c, sz) :
                continue
            if newboard.winner() > 0 :
                if int(newboard.board) in intset :
                    continue
                print(f'{newboard.board.hex()},{newboard.winner()}') #\n{newboard}')
                intset.add(int(newboard.board))
                #print(f'winner {newboard.winner()} moves {newboard.moves()}\n{newboard}')
                #if newboard.moves() > moves :
                settled += 1
                #if settled % 100 == 0 :
                sys.stderr.write(f'winner {newboard.winner()} moves {newboard.moves()}\n{newboard}')
                continue
            else:
                path[-1][1] = ix + 1
                path.append( [newboard, 0] )
                break
        else:
            path.pop()
        break
    return
    
if __name__ == '__main__':
    ggboard = GobletGobblersBoard()
    with SQLite3IntSet("/Volumes/Media_SSD/intset.db") as intset:
        search(ggboard,intset)
'''
Created on 2026/11/08

@author: sin
'''

def ctz(x: int) -> int:
    if x == 0:
        raise ValueError("ctz is undefined for 0")
    return (x & -x).bit_length() - 1

if __name__ == '__main__':
    #test bir set {1, .., n}
    args = [4, 3, 6, 1]
    for bits in args:
        print(f"bits={bits}, ctz={ctz(bits)}")
    
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
    for idstr in CARD_MOVES:
        print(ord(idstr[:1].upper()))
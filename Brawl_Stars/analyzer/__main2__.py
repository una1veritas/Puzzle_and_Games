'''
Created on 2026/11/21

@author: sin
'''
from datetime import datetime
#from dataclasses import dataclass, field
from collections import defaultdict
from itertools import combinations

defualt_input_csv = "../matches_RingofFire_1103-1110.csv"

class Brawler:
    b_name : str
    b_power : int
    p_rank : int
    p_id :int

    def __init__(self, first, pwr = None, rank = None, plid = None):
        if isinstance(first, str) :
            self.b_name = first
            self.b_power = pwr
            self.p_rank = rank
            self.p_id = int(plid, 16)
        elif isinstance(first, (list, tuple)) :
            self.b_name = first[0]
            self.b_power = int(first[1])
            self.p_rank = int(first[2])
            self.p_id = int(first[3], 16)
        else:
            raise ValueError("Brawler init error.")
    
    def name(self):
        return self.b_name
    
    def __eq__(self, other):
        return self.b_name == other.b_name and \
            self.b_power == other.b_power and \
            self.p_rank == other.p_rank and \
            self.p_id == other.p_id

    def __lt__(self, other):
        if not isinstance(other, Brawler) :
            raise ValueError("Brawler comparation error.")
        if self.b_name != other.b_name :
            return self.b_name < other.b_name
        if self.b_power != other.b_power :
            return self.b_power < other.b_power
        if self.p_rank != other.p_rank :
            return self.p_rank < other.p_rank
        return self.p_id < other.p_id

    def __hash__(self):
        return (hash(self.b_name) ^ (self.b_power << 8)) ^ \
            (self.p_rank << 4) ^ self.p_id 

    def __repr__(self):
        return (f'{self.b_name}({self.b_power}, {self.p_rank})')
    
    @staticmethod
    # Brawler に __eq__ と __hash__ を追加（または player_id のタプルをキーにする）
    # player id の組で試合の区別がつくものとする。　
    def match_key(brawlers_a, brawlers_b):
        ka = tuple(b.p_id for b in brawlers_a)
        kb = tuple(b.p_id for b in brawlers_b)
        # 念のため A/B が入れ替わって記録される可能性も吸収するなら正規化
        return (ka, kb) if ka < kb else (kb, ka)

#end of dataclass Brawler

if __name__ == '__main__':
    # logdb = list()
    matches = defaultdict(list)
    brawler_names = set()
    with open(defualt_input_csv, 'r') as csvfile :
        field_names = csvfile.readline().strip().replace("\ufeff", "").split(',');
        field_ids = {field_names[ix] : ix for ix in range(len(field_names))}
        #print(field_ids)
        for a_row in csvfile:
            cols = a_row.strip().split(',')
            #
            evtime = datetime.strptime(cols[field_ids['time']], '%Y-%m-%d %H:%M')
            winner = chr(int(cols[field_ids['winner']])+ord('A'))
            t = cols[3:]
            brawlers_a = [Brawler(tuple(t[ix::6])) for ix in range(3)]
            brawlers_a.sort()
            brawlers_b = [Brawler(tuple(t[ix::6])) for ix in range(3,6)]
            brawlers_b.sort()
            for ix in range(6):
                brawler_names.add(t[ix])
            #print(evtime, winner, brawlers_a, brawlers_b)
            # logdb.append( (evtime, winner, brawlers_a, brawlers_b) )
            # 1パスで O(N) 集約
            key = Brawler.match_key(brawlers_a, brawlers_b)
            matches[key].append((evtime, winner, brawlers_a, brawlers_b))
    print(field_names)
    print(f'records {len(matches)}')
    print(f'brawler_names {len(brawler_names)}')
    
    #[the sum of win-weights, the sum of lose-weights]
    #correlation_1vs1 = dict()
    correlation_1vs2 = defaultdict(lambda: [0, 0])
    brawler_pairs = set()
    
    limcnt = 50
    for key, val in matches.items():
        if limcnt <= 0 :
            break
        winnerq = [em[1] for em in val]
        matchpoint = {0: 0, 1: 1, 2: 3, 3: 2}
        wonby = 'A' if winnerq.count('A') > winnerq.count('B') else 'B'
        if wonby == 'A' :
            team_w = val[0][2]
            team_l = val[0][3]
        else:
            team_l = val[0][2]
            team_w = val[0][3]
        pt = matchpoint[len(winnerq)]
        for bw in team_w + team_l :
            brawler_names.add(bw.name())
        if len(winnerq) == 1 :
            #skip one shot game
            continue
        print(val[0][0].strftime('%y-%m-%d %H:%M'), end=', ')
        print(winnerq, wonby, matchpoint[len(winnerq)], team_w, team_l)
        for a in team_w:
            ally = tuple([x.name() for x in team_w if x != a ])
            brawler_pairs.add(ally)
            oppairs = [ (ea[0].name(), ea[1].name()) for ea in combinations(team_l, 2)]
            correlation_1vs2[(a.name(), ally)][0] += pt
            for a_pair in oppairs:
                brawler_pairs.add(a_pair)
                correlation_1vs2[(a.name(), a_pair)][1] += pt
        
        limcnt -= 1
    
    brawler_pairs_q = sorted( list(brawler_pairs) )
    print(len(brawler_pairs_q))
    for b1 in sorted(brawler_names):
        print(b1)
        for a_pair in brawler_pairs_q:
            if (b1, a_pair) in correlation_1vs2:
                p = correlation_1vs2[(b1, a_pair)]
                print(a_pair, p, end=', ')
        print()
    
'''
Created on 2026/11/21

@author: sin
'''
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, leaves_list
from datetime import datetime
#from dataclasses import dataclass, field
from collections import defaultdict, Counter
from itertools import combinations

default_input_csv = "../matches_RingofFire_1103-1110.csv"

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

def plot_1vs2_monotone_tile(
    stats_dict,
    brawler_freq,
    top_k=12,
    min_matches=5,
    title="1 vs 2 Tile Map",
    save_path=None,
):
    # 出現頻度上位 top_k 体を取得
    top_brawlers = [name for name, _ in brawler_freq.most_common(top_k)]
    # ペアのタプル順は集計キーと一致させるためアルファベット順にする
    top_sorted = sorted(top_brawlers)
    pairs = list(combinations(top_sorted, 2))

    # 勝率行列の構築（サンプル不足・該当なしは np.nan）
    mat = np.full((len(top_brawlers), len(pairs)), np.nan)
    for i, b1 in enumerate(top_brawlers):
        for j, pair in enumerate(pairs):
            w_pt, l_pt, w_cnt, l_cnt = stats_dict[(b1, pair)]
            if (w_cnt + l_cnt) >= min_matches and (w_pt + l_pt) > 0:
                mat[i, j] = w_pt / (w_pt + l_pt)

    # 階層的クラスタリング（Optimal Leaf Ordering）によるセレーション（並べ替え）
    mat_imp = np.where(np.isnan(mat), 0.5, mat)
    row_order = leaves_list(
        linkage(mat_imp, method="average", metric="euclidean", optimal_ordering=True)
    )
    col_order = leaves_list(
        linkage(mat_imp.T, method="average", metric="euclidean", optimal_ordering=True)
    )

    mat_reordered = mat[row_order][:, col_order]
    rows_reordered = [top_brawlers[i] for i in row_order]
    cols_reordered = [f"{pairs[j][0]}+{pairs[j][1]}" for j in col_order]

    # モノトーン濃淡プロット
    fig, ax = plt.subplots(figsize=(max(14, len(pairs) * 0.27), max(5.5, top_k * 0.52)))
    cmap = plt.cm.Greys.copy()
    cmap.set_bad(color="white")

    im = ax.imshow(mat_reordered, aspect="auto", cmap=cmap, vmin=0.25, vmax=0.75)

    # データなし・サンプル不足（NaN）のセルに斜線ハッチングを重ねる
    nan_mask = np.isnan(mat_reordered)
    for i in range(mat_reordered.shape[0]):
        for j in range(mat_reordered.shape[1]):
            if nan_mask[i, j]:
                ax.add_patch(
                    plt.Rectangle(
                        (j - 0.5, i - 0.5),
                        1,
                        1,
                        fill=True,
                        facecolor="#f8f8f8",
                        edgecolor="#b0b0b0",
                        hatch="///",
                        linewidth=0.3,
                    )
                )

    # タイル間の境界線
    ax.set_xticks(np.arange(-0.5, len(cols_reordered), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows_reordered), 1), minor=True)
    ax.grid(which="minor", color="#cccccc", linestyle="-", linewidth=0.4)
    ax.tick_params(which="minor", bottom=False, left=False)

    ax.set_yticks(range(len(rows_reordered)))
    ax.set_yticklabels(rows_reordered, fontsize=9, fontweight="bold")
    ax.set_xticks(range(len(cols_reordered)))
    ax.set_xticklabels(cols_reordered, rotation=90, fontsize=8)
    ax.set_title(
        f"{title} (Top {top_k}, Diagonal Hatch = N/A or n < {min_matches})",
        fontsize=12,
        fontweight="bold",
    )
    plt.colorbar(im, ax=ax, label="Weighted Win Rate (Darker = Higher)", pad=0.015)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")
    plt.show()

if __name__ == "__main__":
    matches = defaultdict(list)

    # 1. CSV読み込みとマッチ単位（BO3セット）への1パス集約
    with open(default_input_csv, "r", encoding="utf-8-sig") as csvfile:
        field_names = csvfile.readline().strip().split(",")
        field_ids = {field_names[ix]: ix for ix in range(len(field_names))}

        for a_row in csvfile:
            cols = a_row.strip().split(",")
            evtime = datetime.strptime(cols[field_ids["time"]], "%Y-%m-%d %H:%M")
            winner = chr(int(cols[field_ids["winner"]]) + ord("A"))
            t = cols[3:]
            brawlers_a = sorted([Brawler(tuple(t[ix::6])) for ix in range(3)])
            brawlers_b = sorted([Brawler(tuple(t[ix::6])) for ix in range(3, 6)])

            key = Brawler.match_key(brawlers_a, brawlers_b)
            matches[key].append((evtime, winner, brawlers_a, brawlers_b))

    print(f"Total unique matches: {len(matches)}")

    # 2. 1キャラ vs 2キャラペアの勝敗ポイント集計
    # 値: [win_pt, lose_pt, win_match_cnt, lose_match_cnt]
    ally_1vs2 = defaultdict(lambda: [0, 0, 0, 0])
    oppo_1vs2 = defaultdict(lambda: [0, 0, 0, 0])
    brawler_freq = Counter()
    matchpoint = {0: 0, 1: 1, 2: 3, 3: 2}

    for key, val in matches.items():
        winnerq = [em[1] for em in val]
        if len(winnerq) == 1:
            continue  # 単発ゲーム（ゴールド以下）を除外
        if winnerq.count("A") == winnerq.count("B"):
            continue  # 1-1等の未完了セットを除外

        wonby = "A" if winnerq.count("A") > winnerq.count("B") else "B"
        if wonby == "A":
            team_w, team_l = val[0][2], val[0][3]
        else:
            team_w, team_l = val[0][3], val[0][2]

        pt = matchpoint.get(len(winnerq), 0)
        for bw in team_w + team_l:
            brawler_freq[bw.name()] += 1

        # 勝ちチーム視点の加算
        for a in team_w:
            ally_pair = tuple(x.name() for x in team_w if x != a)
            ally_1vs2[(a.name(), ally_pair)][0] += pt
            ally_1vs2[(a.name(), ally_pair)][2] += 1

            for op_pair in combinations(team_l, 2):
                op_names = (op_pair[0].name(), op_pair[1].name())
                oppo_1vs2[(a.name(), op_names)][0] += pt
                oppo_1vs2[(a.name(), op_names)][2] += 1

        # 負けチーム視点の加算
        for a in team_l:
            ally_pair = tuple(x.name() for x in team_l if x != a)
            ally_1vs2[(a.name(), ally_pair)][1] += pt
            ally_1vs2[(a.name(), ally_pair)][3] += 1

            for op_pair in combinations(team_w, 2):
                op_names = (op_pair[0].name(), op_pair[1].name())
                oppo_1vs2[(a.name(), op_names)][1] += pt
                oppo_1vs2[(a.name(), op_names)][3] += 1

    # 3. モノトーン二次元タイルの描画
    plot_1vs2_monotone_tile(
        oppo_1vs2,
        brawler_freq,
        top_k=12,
        min_matches=5,
        title="Counter Matchup: Self 1 vs Opponent Pair 2",
        save_path="oppo_1vs2_monotone.png",
    )

    plot_1vs2_monotone_tile(
        ally_1vs2,
        brawler_freq,
        top_k=12,
        min_matches=5,
        title="Ally Synergy: Self 1 + Ally Pair 2",
        save_path="ally_1vs2_monotone.png",
    )

exit(0)

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
    
    # --- 集計フェーズ（勝ち点・負け点の両方をタプルキーで記録） ---
    # キー: (b1_name, (b2_name, b3_name)) -> [win_pt, lose_pt, win_cnt, lose_cnt]
    ally_1vs2 = defaultdict(lambda: [0, 0, 0, 0])
    oppo_1vs2 = defaultdict(lambda: [0, 0, 0, 0])
    brawler_freq = Counter()
    
    matchpoint = {0: 0, 1: 1, 2: 3, 3: 2}
    
    for key, val in matches.items():
        winnerq = [em[1] for em in val]
        if len(winnerq) == 1:
            continue  # 1ゲームのみの試合はスキップ
        if winnerq.count('A') == winnerq.count('B'):
            continue  # 引き分け（未完了セット）はスキップ
    
        wonby = 'A' if winnerq.count('A') > winnerq.count('B') else 'B'
        if wonby == 'A':
            team_w, team_l = val[0][2], val[0][3]
        else:
            team_w, team_l = val[0][3], val[0][2]
    
        pt = matchpoint[len(winnerq)]
        for bw in team_w + team_l:
            brawler_freq[bw.name()] += 1
    
        # 勝ちチーム視点の加算
        for a in team_w:
            ally_pair = tuple(x.name() for x in team_w if x != a)  # team_wはソート済みなので順序一意
            ally_1vs2[(a.name(), ally_pair)][0] += pt
            ally_1vs2[(a.name(), ally_pair)][2] += 1
    
            for op_pair in combinations(team_l, 2):
                op_names = (op_pair[0].name(), op_pair[1].name())
                oppo_1vs2[(a.name(), op_names)][0] += pt
                oppo_1vs2[(a.name(), op_names)][2] += 1
    
        # 負けチーム視点の加算
        for a in team_l:
            ally_pair = tuple(x.name() for x in team_l if x != a)
            ally_1vs2[(a.name(), ally_pair)][1] += pt
            ally_1vs2[(a.name(), ally_pair)][3] += 1
    
            for op_pair in combinations(team_w, 2):
                op_names = (op_pair[0].name(), op_pair[1].name())
                oppo_1vs2[(a.name(), op_names)][1] += pt
                oppo_1vs2[(a.name(), op_names)][3] += 1
    
    
    # --- 二次元タイル描画関数 ---
    def plot_1vs2_tile(stats_dict, top_k=12, min_matches=5, title="1 vs 2 Tile Map"):
        # 出現頻度上位 top_k 体を取得（アルファベット順にする場合は sorted(...)）
        top_brawlers = [name for name, _ in brawler_freq.most_common(top_k)]
        # ペアの列リスト（アルファベット順で統一）
        top_sorted = sorted(top_brawlers)
        pairs = list(combinations(top_sorted, 2))
    
        mat = np.full((len(top_brawlers), len(pairs)), np.nan)
    
         # 欠損値（NaN）を中立値の 0.5 で一時的に埋めて距離を計算
        mat_imp = np.where(np.isnan(mat), 0.5, mat)
        
        rows_reordered = leaves_list(linkage(mat_imp, method='average', metric='euclidean', optimal_ordering=True))
        cols_reordered = leaves_list(linkage(mat_imp.T, method='average', metric='euclidean', optimal_ordering=True))
        
        mat_reordered = mat[rows_reordered][:, cols_reordered]    
        # mat_reordered: 並べ替え済みの2次元配列（欠損・データ不足は np.nan）
        fig, ax = plt.subplots(figsize=(18, 6.8))
        
        # 勝率が高いほど黒く、低いほど白くなるグレースケール
        cmap = plt.cm.Greys.copy()
        cmap.set_bad(color='white')
        
        im = ax.imshow(mat_reordered, aspect='auto', cmap=cmap, vmin=0.25, vmax=0.75)
        
        # データなし（NaN）のマスに斜線ハッチング（///）を入れて50%グレーと区別する
        nan_mask = np.isnan(mat_reordered)
        for i in range(mat_reordered.shape[0]):
            for j in range(mat_reordered.shape[1]):
                if nan_mask[i, j]:
                    ax.add_patch(plt.Rectangle(
                        (j - 0.5, i - 0.5), 1, 1,
                        fill=True, facecolor='#f8f8f8', edgecolor='#b0b0b0',
                        hatch='///', linewidth=0.3
                    ))
        
        # タイル間の境界線を細く引く
        ax.set_xticks(np.arange(-0.5, len(cols_reordered), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(rows_reordered), 1), minor=True)
        ax.grid(which='minor', color='#cccccc', linestyle='-', linewidth=0.4)
        ax.tick_params(which='minor', bottom=False, left=False)
        
        ax.set_yticks(range(len(rows_reordered)))
        ax.set_yticklabels(rows_reordered, fontsize=9, fontweight='bold')
        ax.set_xticks(range(len(cols_reordered)))
        ax.set_xticklabels(cols_reordered, rotation=90, fontsize=8)
        ax.set_title("Counter Matchup (Monotone Grayscale, Hatch = N/A or n < 5)")
        
        plt.colorbar(im, ax=ax, label="Weighted Win Rate (Darker = Higher)", pad=0.015)
        plt.tight_layout()
        plt.show()
    
    # 味方1 vs 味方ペア2 のタイル表示
    plot_1vs2_tile(ally_1vs2, top_k=12, min_matches=5, title="Ally 1 vs Ally Pair 2")
    
    # 自分1 vs 相手ペア2 のタイル表示（非対称なのでこちらもおすすめ）
    plot_1vs2_tile(oppo_1vs2, top_k=12, min_matches=5, title="Self 1 vs Opponent Pair 2")
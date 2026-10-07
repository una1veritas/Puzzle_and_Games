'''
Created on 2026/10/07

@author: sin
'''

import gzip
import xml.etree.ElementTree as ET

# 牌ID(0-135)を人間が読める表記に変換する関数
SUITS = ["m", "p", "s"]
HONORS = ["東", "南", "西", "北", "白", "發", "中"]

def parse_tile(tile_id):
    tile_id = int(tile_id)
    raw = tile_id // 4
    if raw < 27:
        suit = SUITS[raw // 9]
        num = (raw % 9) + 1
        # 赤ドラ判定（5萬・5筒・5索の1枚目(ID % 4 == 0)を赤とする場合）
        # ※天鳳の赤牌ID定数: 5m=16, 5p=52, 5s=88
        if tile_id in (16, 52, 88):
            return f"0{suit}"
        return f"{num}{suit}"
    else:
        return HONORS[raw - 27]

def analyze_mjlog(file_path):
    # .mjlog は gzip 圧縮された XML データ
    with gzip.open(file_path, 'rb') as f:
        xml_content = f.read()

    root = ET.fromstring(xml_content)

    print("=== 天鳳 牌譜解析スタート ===")
    
    current_kyoku = 0
    for elem in root:
        tag = elem.tag

        # 局の開始 (INIT)
        if tag == "INIT":
            current_kyoku += 1
            attr = elem.attrib
            seed = attr["seed"].split(",")
            
            kyoku_num = int(seed[0])  # 0:東1局, 1:東2局...
            honba = seed[1]
            dora_indicator = parse_tile(seed[5])
            
            print(f"\n--------------------------------------------------")
            print(f"【第 {current_kyoku} 局】 (場: {kyoku_num//4 + 1}局 {kyoku_num%4 + 1}本場: {honba})")
            print(f"ドラ表示牌: [{dora_indicator}]")
            
            # 配牌 (hai0: 親, hai1: 南家, hai2: 西家, hai3: 北家)
            for p in range(4):
                hai_ids = attr[f"hai{p}"].split(",")
                tiles = [parse_tile(tid) for tid in hai_ids]
                print(f" プレイヤー {p} 配牌: {' '.join(tiles)}")
            print("--------------------------------------------------")

        # ツモおよび打牌イベントの解析
        # 天鳳XMLでは:
        # T, U, V, W + 牌ID -> プレイヤー0,1,2,3 のツモ
        # D, E, F, G + 牌ID -> プレイヤー0,1,2,3 の打牌
        elif tag[0] in ("T", "U", "V", "W") and tag[1:].isdigit():
            player_id = ord(tag[0]) - ord("T")
            tile = parse_tile(tag[1:])
            # ログを出力しすぎないようサンプル表示（必要に応じて調整）
            # print(f"P{player_id} ツモ: {tile}")

        elif tag[0] in ("D", "E", "F", "G") and tag[1:].isdigit():
            player_id = ord(tag[0]) - ord("D")
            tile = parse_tile(tag[1:])
            # print(f"P{player_id} 打牌: {tile}")

        # 鳴き (N)
        elif tag == "N":
            player_id = int(elem.attrib["who"])
            m_val = int(elem.attrib["m"])
            # ※副露(チー・ポン・カン)のデータは m_val ビット演算で復元可能
            # print(f"P{player_id} 副露(コード: {m_val})")

        # 和了 (AGARI) や 流局 (RYUUKYOKU)
        elif tag == "AGARI":
            who = int(elem.attrib["who"])
            from_who = int(elem.attrib["fromWho"])
            yaku_info = elem.attrib.get("yaku", "")
            target_str = "ツモ" if who == from_who else f"放銃: P{from_who}"
            print(f">> [和了] プレイヤー {who} ({target_str})")

        elif tag == "RYUUKYOKU":
            print(f">> [流局]")

if __name__ == "__main__":
    # 解析したい .mjlog ファイルのパス
    analyze_mjlog("test.mjlog")

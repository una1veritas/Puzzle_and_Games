#
#
#
import xml.etree.ElementTree as ET
import gzip, zipfile, zlib
import sys, re

# --- これまでの表示ルーチンの確認 ---
SUITS = ["m", "p", "s"]
HONORS = ["東", "南", "西", "北", "白", "發", "中"]

# ツモ・打牌タグの接頭辞マッピング
TSUMO_TAGS = {"T": 0, "U": 1, "V": 2, "W": 3}
DAHAI_TAGS = {"D": 0, "E": 1, "F": 2, "G": 3}

def mjlog_zip_reader(zip_path : str, pattern = None):
    pattern = pattern if pattern is not None else ".*"
    with zipfile.ZipFile(zip_path, "r") as z:
        # ディレクトリを除外し、実際のファイル（.mjlog）のみ抽出
        file_list = [
            f
            for f in z.namelist()
            if not f.endswith("/") and (f.endswith(".mjlog") or f.endswith(".xml")) and re.search(pattern, f)
        ]
        print(f"有効な牌譜ファイル数: {len(file_list)} 件")
    
        # 最初のファイルを取り出してパース
        sample_filename = file_list[0]
        print(f"処理対象: {sample_filename}")
    
        compressed_bytes = z.read(sample_filename)
    
        try:
            xml_str = zlib.decompress(compressed_bytes, -zlib.MAX_WBITS).decode(
                "utf-8", errors="ignore"
            )
        except Exception:
            xml_str = gzip.decompress(compressed_bytes).decode(
                "utf-8", errors="ignore"
            )
    
        root = ET.fromstring(xml_str)
        print("パース成功！")
    return sample_filename, root


def parse_tile(tile_id):
    tid = int(tile_id)
    raw = tid // 4
    if raw < 27:
        suit = SUITS[raw // 9]
        num = (raw % 9) + 1
        return f"0{suit}" if tid in (16, 52, 88) else f"{num}{suit}"
    return HONORS[raw - 27]

# def parse_tile(tile_str):
#     """牌ID(0~135)を文字列表記に変換する（赤ドラ対応版）"""
#     tile_id = int(tile_str)
#
#     # 赤ドラのピンポイント判定
#     if tile_id == 16:
#         return "0m"  # 赤5mを 0m と表記する場合
#     elif tile_id == 52:
#         return "0p"  # 赤5pを 0p と表記する場合
#     elif tile_id == 88:
#         return "0s"  # 赤5sを 0s と表記する場合
#
#     # 通常牌の計算
#     num = tile_id // 4
#     if num < 9:
#         return f"{num + 1}m"
#     elif num < 18:
#         return f"{num - 8}p"
#     elif num < 27:
#         return f"{num - 17}s"
#     else:
#         suits = ["東", "南", "西", "北", "白", "發", "中"]
#         return suits[num - 27]
#

def sort_tiles(tile_list):
    """手牌を見やすく並び替える(ID順)"""
    return sorted(tile_list, key=lambda x: int(x))

def print_table_state(hands, rivers, action_msg=""):
    """現在の全員の手牌と捨て牌を出力する"""
    print(f"\n--- {action_msg} ---")
    for p in range(4):
        # 牌IDを読みやすい文字列に変換して表示
        hand_str = " ".join([parse_tile(t) for t in hands[p]])
        river_str = " ".join([parse_tile(t) for t in rivers[p]])
        print(f"P{p} | 手牌 [{len(hands[p]):2d}枚]: {hand_str}")
        print(f"     | 捨て牌     : {river_str}")

def parse_kyoku_action(root):
    in_east_1 = False

    # 4人の手牌と捨て牌を保持するデータ構造
    hands = {0: [], 1: [], 2: [], 3: []}
    rivers = {0: [], 1: [], 2: [], 3: []}

    for elem in root:
        tag = elem.tag

        # 東1局の開始
        if tag == "INIT":
            seed = elem.attrib["seed"].split(",")
            if int(seed[0]) == 0:  # 東1局
                in_east_1 = True
                print("\n=== 東1局 開始 ===")

                # 手牌・捨て牌のリセット
                hands = {0: [], 1: [], 2: [], 3: []}
                rivers = {0: [], 1: [], 2: [], 3: []}

                # 配牌の読み込み
                for p in range(4):
                    hai_str = elem.attrib.get(f"hai{p}", "")
                    if hai_str:
                        # 牌IDのリストとして保持（理牌しておく）
                        hands[p] = sort_tiles(hai_str.split(","))

                print_table_state(hands, rivers, action_msg="配牌完了")
                continue
            elif in_east_1:
                break

        if not in_east_1:
            continue

        # --- ツモ動作 ---
        if len(tag) >= 2 and tag[0] in TSUMO_TAGS and tag[1:].isdigit():
            player = TSUMO_TAGS[tag[0]]
            tile = tag[1:]

            # 手牌にツモ牌を追加
            hands[player].append(tile)

            msg = f"P{player} ツモ: [{parse_tile(tile)}]"
            print_table_state(hands, rivers, action_msg=msg)

        # --- 打牌動作 ---
        elif len(tag) >= 2 and tag[0] in DAHAI_TAGS and tag[1:].isdigit():
            player = DAHAI_TAGS[tag[0]]
            tile = tag[1:]

            # 手牌から打牌を取り除き、河に追加
            if tile in hands[player]:
                hands[player].remove(tile)
            rivers[player].append(tile)

            # 打牌後に手牌を理牌（ソート）
            hands[player] = sort_tiles(hands[player])

            msg = f"P{player} 打牌: {parse_tile(tile)}"
            print_table_state(hands, rivers, action_msg=msg)

        # --- 和了 / 流局 ---
        elif tag in ("AGARI", "RYUUKYOKU"):
            print(f"\n=== 局終了 ({tag}) ===")
            break

def parse_all_kyoku(root, target_kyoku=None, target_honba=None):
    """すべての局（または指定した特定の局・本場）をパースする

    target_kyoku: 指定する場合 0(東1), 1(東2)...
    target_honba: 指定する場合 0(0本場), 1(1本場)...
    """
    in_target_kyoku = False

    hands = {0: [], 1: [], 2: [], 3: []}
    rivers = {0: [], 1: [], 2: [], 3: []}

    for elem in root:
        tag = elem.tag

        # === 局の開始 (<INIT>) ===
        if tag == "INIT":
            seed = elem.attrib["seed"].split(",")
            kyoku_num = int(seed[0])  # 0:東1局, 1:東2局 ...
            honba_num = int(seed[1])  # 本場数

            # 指定がない場合は全局出力、指定がある場合は一致するかチェック
            is_match_kyoku = target_kyoku is None or target_kyoku == kyoku_num
            is_match_honba = target_honba is None or target_honba == honba_num

            if is_match_kyoku and is_match_honba:
                in_target_kyoku = True

                # 局名の表示変換 (0->東1局, 1->東2局, 4->南1局 ...)
                bakaze = "東" if kyoku_num < 4 else "南"
                kyoku_in_ba = (kyoku_num % 4) + 1
                print(
                    f"\n==================== {bakaze}{kyoku_in_ba}局 {honba_num}本場 開始 ===================="
                )

                # 手牌・捨て牌のリセット
                hands = {0: [], 1: [], 2: [], 3: []}
                rivers = {0: [], 1: [], 2: [], 3: []}

                # 配牌の読み込み
                for p in range(4):
                    hai_str = elem.attrib.get(f"hai{p}", "")
                    if hai_str:
                        hands[p] = sort_tiles(hai_str.split(","))

                print_table_state(hands, rivers, action_msg="配牌完了")
            else:
                in_target_kyoku = False
            continue

        # 対象外の局のタグはスキップ
        if not in_target_kyoku:
            continue

        # === ツモ動作 ===
        if len(tag) >= 2 and tag[0] in TSUMO_TAGS and tag[1:].isdigit():
            player = TSUMO_TAGS[tag[0]]
            tile = tag[1:]
            hands[player].append(tile)
            msg = f"P{player} ツモ: [{parse_tile(tile)}]"
            print_table_state(hands, rivers, action_msg=msg)

        # === 打牌動作 ===
        elif len(tag) >= 2 and tag[0] in DAHAI_TAGS and tag[1:].isdigit():
            player = DAHAI_TAGS[tag[0]]
            tile = tag[1:]
            if tile in hands[player]:
                hands[player].remove(tile)
            rivers[player].append(tile)
            hands[player] = sort_tiles(hands[player])
            msg = f"P{player} 打牌: {parse_tile(tile)}"
            print_table_state(hands, rivers, action_msg=msg)

        # === 局の終了 (和了または流局) ===
        elif tag in ("AGARI", "RYUUKYOKU"):
            print(f"\n=== 局終了 ({tag}) ===")
            in_target_kyoku = False

            # 特定の1局だけを検索していた場合はここで終了してOK
            if target_kyoku is not None and target_honba is not None:
                break
    
if __name__ == "__main__":
    
    zip_path = "/Users/sin/Downloads/mjlog_pf4-20_n30.zip"
    
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
        
    filename, xmlroot = mjlog_zip_reader(zip_path)
    
    print("\n==================================================")
    print(f"【動作確認】 天鳳位対局 ({filename}) 東1局")
    print("==================================================")
    
    for elem in xmlroot:
        if elem.tag == "INIT":
            attr = elem.attrib
            seed = attr["seed"].split(",")
    
            kyoku_num = int(seed[0])
            dora_tile = parse_tile(seed[5])
    
            print(f"局: 東{kyoku_num + 1}局 {seed[1]}本場 | ドラ表示牌: [{dora_tile}]")
    
            for p in range(4):
                tile_ids = attr[f"hai{p}"].split(",")
                tiles = [parse_tile(tid) for tid in tile_ids]
                print(f" プレイヤー {p}: {' '.join(tiles)}")
    
            break
    
    # 実行（既存の root を渡す）
    print('\n')
    print('動作確認２')
    parse_all_kyoku(xmlroot)
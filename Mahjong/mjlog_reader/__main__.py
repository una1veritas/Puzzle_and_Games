import gzip
import io
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib

# タグの対応関係
TSUMO_TAGS = {"T": 0, "U": 1, "V": 2, "W": 3}
DAHAI_TAGS = {"D": 0, "E": 1, "F": 2, "G": 3}


def mjlog_zip_reader(zip_path: str, pattern=None):
    pattern = pattern if pattern is not None else ".*"
    with zipfile.ZipFile(zip_path, "r") as z:
        # ディレクトリを除外し、実際のファイル（.mjlog）のみ抽出
        file_list = [
            f
            for f in z.namelist()
            if not f.endswith("/")
            and (f.endswith(".mjlog") or f.endswith(".xml"))
            and re.search(pattern, f)
        ]
        print(f"有効な牌譜ファイル数: {len(file_list)} 件")

        if not file_list:
            raise FileNotFoundError(
                f"条件に一致する牌譜ファイルが見つかりません: {zip_path}"
            )

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


def parse_tile(tile_id_input):
    """牌ID(0~135)を表記文字列(0m~9m, 0p~9p, 0s~9s, 東~中)に変換する（赤ドラ対応）"""
    tile_id = int(tile_id_input)

    # 赤ドラの判定 (16:赤5m, 52:赤5p, 88:赤5s)
    if tile_id == 16:
        return "0m"
    elif tile_id == 52:
        return "0p"
    elif tile_id == 88:
        return "0s"

    num = tile_id // 4
    if num < 9:
        return f"{num + 1}m"
    elif num < 18:
        return f"{num - 8}p"
    elif num < 27:
        return f"{num - 17}s"
    else:
        suits = ["東", "南", "西", "北", "白", "發", "中"]
        return suits[num - 27]


def sort_tiles(tile_list):
    """牌IDリストを昇順（理牌）にソート"""
    return sorted(tile_list, key=lambda x: int(x))


def decode_n_tag(m_str):
    """<N m="..."> のビット演算デコード処理"""
    m = int(m_str)

    # 1. チー
    if m & 0x0004:
        # m & 0x0003 は「3枚の中でどの牌を拾ったか」のインデックス (0:最小, 1:中央, 2:最大)
        eaten_idx = m & 0x0003

        pattern = (m >> 3) & 0x003F
        base_num = pattern // 3
        base_num = (base_num // 7) * 9 + (base_num % 7)

        t0 = pattern % 3
        t1 = (m >> 9) & 0x0003
        t2 = (m >> 11) & 0x0003

        tiles = [
            (base_num + 0) * 4 + t0,
            (base_num + 1) * 4 + t1,
            (base_num + 2) * 4 + t2,
        ]

        # eaten_idx が 0, 1, 2 の範囲に収まるよう安全策を適用
        eaten_idx = min(max(0, eaten_idx), 2)

        called_tile = tiles[eaten_idx]
        hand_tiles = [t for i, t in enumerate(tiles) if i != eaten_idx]

        return {
            "type": "CHII",
            "from_who_rel": 3,  # チーは必ず上家(相対位置3)から
            "called_tile": called_tile,
            "hand_tiles": hand_tiles,
            "all_tiles": tiles,
        }

    # 2. ポン
    elif m & 0x0008:
        from_who_rel = m & 0x0003
        unused = (m >> 5) & 0x0003
        pattern = (m >> 9) & 0x007F
        base_tile = pattern // 3

        t_indices = [i for i in range(4) if i != unused]
        called_idx = (m >> 3) & 0x0003
        hand_indices = [i for i in t_indices if i != called_idx]

        called_tile = base_tile * 4 + called_idx
        hand_tiles = [base_tile * 4 + i for i in hand_indices]

        return {
            "type": "PON",
            "from_who_rel": from_who_rel,
            "called_tile": called_tile,
            "hand_tiles": hand_tiles,
            "all_tiles": [called_tile] + hand_tiles,
        }

    # 3. 加槓 (カカン)
    elif m & 0x0010:
        from_who_rel = m & 0x0003
        called_idx = (m >> 3) & 0x0003
        pattern = (m >> 9) & 0x007F
        base_tile = pattern // 3

        added_tile = base_tile * 4 + called_idx

        return {
            "type": "KAKAN",
            "from_who_rel": from_who_rel,
            "called_tile": added_tile,
            "hand_tiles": [added_tile],
            "all_tiles": [base_tile * 4 + i for i in range(4)],
        }

    # 4. 暗槓 または 大明槓
    else:
        from_who_rel = m & 0x0003
        pattern = (m >> 8) & 0x00FF
        base_tile = pattern // 4
        all_tiles = [base_tile * 4 + i for i in range(4)]

        if from_who_rel == 0:
            return {
                "type": "ANKAN",
                "from_who_rel": 0,
                "called_tile": None,
                "hand_tiles": all_tiles,
                "all_tiles": all_tiles,
            }
        else:
            called_idx = (m >> 3) & 0x0003
            called_tile = base_tile * 4 + called_idx
            hand_tiles = [t for t in all_tiles if t != called_tile]
            return {
                "type": "MINKAN",
                "from_who_rel": from_who_rel,
                "called_tile": called_tile,
                "hand_tiles": hand_tiles,
                "all_tiles": all_tiles,
            }


def print_table_state(hands, melds, rivers, action_msg=""):
    """現在の全員の手牌、副露、捨て牌を出力"""
    print(f"\n--- {action_msg} ---")
    for p in range(4):
        hand_str = " ".join([parse_tile(t) for t in hands[p]])

        meld_list = []
        for m in melds[p]:
            m_tiles = " ".join([parse_tile(t) for t in m["all_tiles"]])
            meld_list.append(f"[{m['type']}:{m_tiles}]")
        meld_str = " ".join(meld_list) if meld_list else "なし"

        river_str = " ".join([parse_tile(t) for t in rivers[p]])

        print(f"P{p} | 手牌 [{len(hands[p]):2d}枚]: {hand_str}")
        print(f"     | 副露        : {meld_str}")
        print(f"     | 捨て牌      : {river_str}")


def run_kyoku_simulation(root, target_kyoku=0, target_honba=0):
    """指定した局・本場のシミュレーションを実行"""
    in_target_kyoku = False

    hands = {p: [] for p in range(4)}
    melds = {p: [] for p in range(4)}
    rivers = {p: [] for p in range(4)}

    for elem in root:
        tag = elem.tag

        # === 局の開始 ===
        if tag == "INIT":
            seed = elem.attrib["seed"].split(",")
            kyoku_num = int(seed[0])
            honba_num = int(seed[1])

            if kyoku_num == target_kyoku and honba_num == target_honba:
                in_target_kyoku = True
                bakaze = "東" if kyoku_num < 4 else "南"
                kyoku_in_ba = (kyoku_num % 4) + 1
                print(
                    f"\n==================== 開始: {bakaze}{kyoku_in_ba}局 {honba_num}本場 ===================="
                )

                hands = {p: [] for p in range(4)}
                melds = {p: [] for p in range(4)}
                rivers = {p: [] for p in range(4)}

                for p in range(4):
                    hai_str = elem.attrib.get(f"hai{p}", "")
                    if hai_str:
                        hands[p] = sort_tiles(hai_str.split(","))

                print_table_state(hands, melds, rivers, action_msg="配牌完了")
            elif in_target_kyoku:
                break
            continue

        if not in_target_kyoku:
            continue

        # === ツモ ===
        if len(tag) >= 2 and tag[0] in TSUMO_TAGS and tag[1:].isdigit():
            player = TSUMO_TAGS[tag[0]]
            tile = tag[1:]
            hands[player].append(tile)

            msg = f"P{player} ツモ: [{parse_tile(tile)}]"
            print_table_state(hands, melds, rivers, action_msg=msg)

        # === 打牌 ===
        elif len(tag) >= 2 and tag[0] in DAHAI_TAGS and tag[1:].isdigit():
            player = DAHAI_TAGS[tag[0]]
            tile = tag[1:]

            if tile in hands[player]:
                hands[player].remove(tile)
            rivers[player].append(tile)
            hands[player] = sort_tiles(hands[player])

            msg = f"P{player} 打牌: {parse_tile(tile)}"
            print_table_state(hands, melds, rivers, action_msg=msg)

        # === 副露（鳴き） ===
        elif tag == "N":
            who = int(elem.attrib["who"])
            m_val = elem.attrib["m"]
            decoded = decode_n_tag(m_val)

            for h_tile in decoded["hand_tiles"]:
                h_tile_str = str(h_tile)
                if h_tile_str in hands[who]:
                    hands[who].remove(h_tile_str)

            if decoded["type"] == "KAKAN":
                base_tile_num = decoded["all_tiles"][0] // 4
                for m in melds[who]:
                    if m["all_tiles"][0] // 4 == base_tile_num:
                        m["type"] = "KAKAN"
                        m["all_tiles"] = decoded["all_tiles"]
                        break
            else:
                melds[who].append(decoded)

            hands[who] = sort_tiles(hands[who])

            from_who = (
                (who + decoded["from_who_rel"]) % 4
                if decoded["from_who_rel"] != 0
                else who
            )
            target_info = (
                f" (P{from_who}から)" if decoded["type"] != "ANKAN" else ""
            )

            msg = f"★ P{who} 副露 [{decoded['type']}]{target_info}"
            print_table_state(hands, melds, rivers, action_msg=msg)

        # === 局の終了 ===
        elif tag in ("AGARI", "RYUUKYOKU"):
            print(f"\n=== 局終了 ({tag}) ===")
            break


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    zip_path = "/Users/sin/Downloads/mjlog_pf4-20_n30.zip"

    if len(sys.argv) > 1:
        zip_path = sys.argv[1]

    filename, xmlroot = mjlog_zip_reader(zip_path)

    # 東1局0本場のシミュレーションを実行
    run_kyoku_simulation(xmlroot, target_kyoku=0, target_honba=0)

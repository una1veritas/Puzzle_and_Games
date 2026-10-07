import gzip
import xml.etree.ElementTree as ET
import zipfile
import zlib

zip_path = "/Users/sin/Downloads/mjlog_pf4-20_n30.zip"

with zipfile.ZipFile(zip_path, "r") as z:
    # ディレクトリを除外し、実際のファイル（.mjlog）のみ抽出
    file_list = [
        f
        for f in z.namelist()
        if not f.endswith("/") and (f.endswith(".mjlog") or f.endswith(".xml"))
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

# --- これまでの表示ルーチンの確認 ---
SUITS = ["m", "p", "s"]
HONORS = ["東", "南", "西", "北", "白", "發", "中"]


def parse_tile(tile_id):
    tid = int(tile_id)
    raw = tid // 4
    if raw < 27:
        suit = SUITS[raw // 9]
        num = (raw % 9) + 1
        return f"0{suit}" if tid in (16, 52, 88) else f"{num}{suit}"
    return HONORS[raw - 27]

# ツモ・打牌タグの接頭辞マッピング
TSUMO_TAGS = {"T": 0, "U": 1, "V": 2, "W": 3}
DAHAI_TAGS = {"D": 0, "E": 1, "F": 2, "G": 3}


def parse_kyoku_action(root):
    in_east_1 = False

    for elem in root:
        tag = elem.tag

        # 東1局の開始タグ
        if tag == "INIT":
            seed = elem.attrib["seed"].split(",")
            if int(seed[0]) == 0:  # 東1局
                in_east_1 = True
                print("\n=== 東1局 進行ログ ===")
                continue
            elif in_east_1:
                # 次の局に移ったら終了
                break

        if not in_east_1:
            continue

        # ツモ動作 (T, U, V, W + 牌ID)
        if len(tag) >= 2 and tag[0] in TSUMO_TAGS and tag[1:].isdigit():
            player = TSUMO_TAGS[tag[0]]
            tile = parse_tile(tag[1:])
            print(f"P{player} ツモ: [{tile}]")

        # 打牌動作 (D, E, F, G + 牌ID)
        elif len(tag) >= 2 and tag[0] in DAHAI_TAGS and tag[1:].isdigit():
            player = DAHAI_TAGS[tag[0]]
            tile = parse_tile(tag[1:])
            print(f"  P{player} 打牌: {tile}")

        # リーチ宣言
        elif tag == "REACH":
            p = elem.attrib["who"]
            step = elem.attrib["step"]
            if step == "1":
                print(f"★ P{p} リーチ宣言！")

        # 和了
        elif tag == "AGARI":
            who = elem.attrib["who"]
            from_who = elem.attrib["fromWho"]
            yaku = elem.attrib.get("yaku", "")
            ten = elem.attrib["ten"].split(",")[1]
            target = "ツモ" if who == from_who else f"ロン (放銃: P{from_who})"
            print(f"\n【和了】 P{who} {target} | {ten}点")
            break


print("\n==================================================")
print(f"【動作確認】 天鳳位対局 ({sample_filename}) 東1局")
print("==================================================")

for elem in root:
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
parse_kyoku_action(root)
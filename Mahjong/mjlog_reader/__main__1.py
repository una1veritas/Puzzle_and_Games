import gzip
import io
import re
import urllib.request
import xml.etree.ElementTree as ET
import zlib

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


def main():
    headers = {"User-Agent": "Mozilla/5.0"}

    # --- ステップ 1: list.cgi からログファイル一覧を取得 ---
    print("1. 天鳳サーバーの list.cgi からログファイル一覧を取得中...")
    cgi_url = "https://tenhou.net/sc/raw/list.cgi"

    try:
        req = urllib.request.Request(cgi_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            cgi_body = resp.read().decode("utf-8", errors="ignore")

        entries = re.findall(r"file:'(sca[^']+\.log\.gz)',size:(\d+)", cgi_body)
        valid_files = [e[0] for e in entries if int(e[1]) > 30000]

        if not valid_files:
            print("エラー: 有効な日別ログファイルが見つかりませんでした。")
            return

        # 直近から順にファイルを選択
        target_files = list(reversed(valid_files))
        print(f" -> 候補ファイル数: {len(target_files)} 件")

    except Exception as e:
        print(f"list.cgi の取得に失敗しました: {e}")
        return

    # --- ステップ 2: ログをダウンロードして対局IDを抽出（ヒットするまで試行） ---
    # --- ステップ 2: ログをダウンロードして解凍＆対局ID抽出 ---
    selected_log_id = None

    for f_name in target_files:
        print(f"\n2. [{f_name}] をダウンロードして解凍中...")
        file_url = f"https://tenhou.net/sc/raw/dat/{f_name}"

        try:
            req_file = urllib.request.Request(file_url, headers=headers)
            with urllib.request.urlopen(req_file) as resp:
                compressed_bytes = resp.read()

            # 1. 確実に GZIP 解凍を行う
            try:
                raw_bytes = gzip.decompress(compressed_bytes)
            except Exception as ge:
                print(f"  GZIP解凍エラー: {ge}")
                continue

            # 2. テキストへデコード (utf-8 -> euc-jp -> shift_jis の順で試行)
            raw_text = None
            for enc in ["utf-8", "euc-jp", "shift_jis"]:
                try:
                    raw_text = raw_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue

            if not raw_text:
                raw_text = raw_bytes.decode("utf-8", errors="ignore")

            # 生データの先頭2行を確認（デバッグ用）
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            print("--- [解凍成功！ 生データ構造 (先頭2行)] ---")
            for line in lines[:2]:
                print(f"  {line}")
            print("-------------------------------------------")

            # 3. 対局IDの抽出
            # 天鳳ログ内の "L" 付近または URL 内の ID (20XXXXXXXXgm-....) を抽出
            all_ids = re.findall(
                r"20\d{8}gm-[0-9a-zA-F]{4}-[0-9a-zA-F]{4}-[0-9a-zA-F]{8}",
                raw_text,
            )

            # 万が一ハイフン区切り数が異なる場合のフォールバックパターン
            if not all_ids:
                all_ids = re.findall(r"20\d{8}gm-[0-9a-zA-F\-]+", raw_text)

            print(f" -> 抽出成功数: {len(all_ids)} 件")

            if all_ids:
                selected_log_id = all_ids[0]
                print(f" -> 動作テストに使用する確定ID: {selected_log_id}")
                break

        except Exception as e:
            print(f"  {f_name} 処理中のエラー: {e}")
            continue

    if not selected_log_id:
        print("エラー: いずれのファイルからも対局IDを取得できませんでした。")
        return

    # --- ステップ 3: 該当対局の .mjlog を取得して解凍 ---
    print(f"\n3. 対局データ (.mjlog) を取得中... (ID: {selected_log_id})")
    mjlog_url = f"https://tenhou.net/0/log/?{selected_log_id}"

    try:
        req_mjlog = urllib.request.Request(mjlog_url, headers=headers)
        with urllib.request.urlopen(req_mjlog) as resp:
            compressed_xml = resp.read()

        try:
            xml_str = zlib.decompress(compressed_xml, -zlib.MAX_WBITS).decode(
                "utf-8", errors="ignore"
            )
        except Exception:
            xml_str = gzip.decompress(compressed_xml).decode(
                "utf-8", errors="ignore"
            )

        root = ET.fromstring(xml_str)
        print(" -> .mjlog の取得・XMLパースに成功しました！")

    except Exception as e:
        print(f".mjlog の取得・パースに失敗しました: {e}")
        return

    # --- ステップ 4: 東1局のデータ（配牌・ドラ）を表示 ---
    print("\n==================================================")
    print("【動作確認成功】 東1局 配牌・ドラ表示データ")
    print("==================================================")

    for elem in root:
        if elem.tag == "INIT":
            attr = elem.attrib
            seed = attr["seed"].split(",")

            kyoku_num = int(seed[0])
            dora_tile = parse_tile(seed[5])

            print(
                f"局: 東{kyoku_num + 1}局 {seed[1]}本場 | ドラ表示牌: [{dora_tile}]"
            )

            for p in range(4):
                tile_ids = attr[f"hai{p}"].split(",")
                tiles = [parse_tile(tid) for tid in tile_ids]
                print(f" プレイヤー {p}: {' '.join(tiles)}")

            break


if __name__ == "__main__":
    main()

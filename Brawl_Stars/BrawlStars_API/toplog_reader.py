#.json の内容をを duckdb にいれ、SQL で取り出すサンプル
import duckdb
import sys

JSONL_FILE = "battlelogs.jsonl"
DB_FILE = "brawl_data.duckdb"
GAME_MODES = ["gemGrab", "showdown", "brawlBall", "bounty", "heist", "siege", "hotZone", "knockout"]
GAMO_MODE_CHOICE = GAME_MODES[2]  # 例: brawlBall を選択

if len(sys.argv) > 1:
    JSONL_FILE = sys.argv[1]  # コマンドライン引数でJSONL_FILEを上書き可能
if len(sys.argv) > 2:
    GAMO_MODE_CHOICE = sys.argv[2]  # コマンドライン引数でゲームモードを指定可能
# DuckDBに接続（ファイル名を指定して永続化）
con = duckdb.connect(DB_FILE)

print("JSONL読み込みと3v3対戦データの抽出を行っています...")

# 1. 3v3対戦（teamsが2チームかつ各チーム3人）のみを抽出してテーブル作成
# ※DuckDBのリストインデックスは1始まりのため、teams[1] と teams[2] を使用します
con.execute(f"""
    CREATE OR REPLACE TABLE battles_3v3 AS
    SELECT 
        battleTime,
        event.mode AS mode,
        event.map AS map_name,
        battle.type AS battle_type,
        battle.result AS result,
        battle.duration AS duration_sec,
        battle.teams AS teams
    FROM read_json_auto('{JSONL_FILE}')
    WHERE battle.teams IS NOT NULL
      AND len(battle.teams) = 2
      AND len(battle.teams[1]) = 3
      AND len(battle.teams[2]) = 3;
""")

# 2. 統計情報（Stats）の集計・表示
print("\n=================== 集計結果 (Stats) ===================")
total_3v3 = con.execute("SELECT COUNT(*) FROM battles_3v3").fetchone()[0]
print(f"抽出された 3v3 対戦総数: {total_3v3} 件\n")

print("【モード別対戦数と平均試合時間】")
stats_df = con.execute("""
    SELECT 
        mode,
        COUNT(*) AS match_count,
        ROUND(AVG(duration_sec), 1) AS avg_duration_sec
    FROM battles_3v3
    GROUP BY mode
    ORDER BY match_count DESC
""").df()
print(stats_df.to_string(index=False))

# 3. 最初の 3v3 対戦情報の詳細出力
print("\n=================== 最初の3v3試合データ ===================")
matches = con.execute(f"""
    SELECT 
        battleTime,
        mode,
        map_name,
        result,
        duration_sec,
        teams
    FROM battles_3v3
    WHERE mode='{GAMO_MODE_CHOICE}'
    LIMIT 2
""")

for a_match in matches.fetchall():
    # b_time, mode, map_name, result, duration, teams = a_match
    # print(f"対戦日時  : {b_time}")
    # print(f"モード    : {mode}")
    # print(f"マップ    : {map_name}")
    # print(f"勝敗結果  : {result}")
    # print(f"試合時間  : {duration}秒\n")
    
    print("【チーム構成】")
    for idx, team in enumerate(teams, 1):
        print(f"  ■ チーム {idx} {'(target)' if idx == 1 else ''}:")
        for player in team:
            tag = player.get("tag", "N/A")
            brawler_name = player.get("brawler", {}).get("name", "UNKNOWN")
            brawler_plevel = player.get("brawler", {}).get("power", "??")
            brawler_id = player.get("brawler", {}).get("id", "N/A")
            brawler_trophies = player.get("brawler", {}).get("trophies", "0")
            print(f"    - プレイヤー: {tag:12s} | ブロラー: {brawler_name:12s} (ID: {brawler_id}) PLV: {str(brawler_plevel):>2s} TRP: {brawler_trophies:5} ")
    print("\n\n")

con.close()
print(f"\nDBファイルへの保存が完了しました（保存先: {DB_FILE}）。")

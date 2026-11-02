#brawler stars API によるグローバルランキング上位プレイヤーの対戦ログ取得
import asyncio
import json
import urllib.parse
import aiohttp

import sys

# --- 設定項目 ---
# Brawl Stars APIのエンドポイントURL, 自分で登録し取得したた API に変更すること
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjE5ZWNlOGQxLTg1NmEtNDMyMy05ZmM0LWU3ZDFlNmZjNjlhYSIsImlhdCI6MTc5MzM2ODk1Mywic3ViIjoiZGV2ZWxvcGVyL2M3YzNlOWEwLTY1MzQtNDgxZS04OTgzLWNmN2NkM2VkMjM0YyIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMTgwLjE2LjMxLjMiXSwidHlwZSI6ImNsaWVudCJ9XX0.tRfGum3vMmxcQS1P8Vp0QWYtQGWWVKq8q3XL_9Kz92tj7rxPiYFNzcnCcr9qDIYdd38fsJ7J8pOWHo_NqYLn4g"
# Developer Portalで発行したAPIキーを設定
BASE_URL = "https://api.brawlstars.com/v1"
CONCURRENCY_LIMIT = 5               # 同時リクエスト数制限（API負荷軽減のため）
LIMIT_RANKINGS = 50                 # 起点として取得するトッププレイヤー数
MAX_RECORDS = 5000                  # 収集する最大試合数
OUTPUT_FILE = "battlelogs.json"    # 保存先ファイル名


async def get_top_player_tags(session: aiohttp.ClientSession, api_key: str, limit: int = 50) -> list[str]:
    """事前処理：グローバルランキング上位プレイヤーのタグ一覧を自動取得"""
    url = f"{BASE_URL}/rankings/global/players?limit={limit}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                tags = [item["tag"] for item in data.get("items", [])]
                return tags
            else:
                print(f"[Error] Failed to fetch rankings. Status: {resp.status}")
                return []
    except Exception as e:
        print(f"[Error] Ranking request failed: {e}")
        return []


class BrawlStarsDataCrawler:
    def __init__(self, api_key: str, seed_tags: list[str]):
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.queue = asyncio.Queue()
        self.visited_players = set()
        self.visited_battles = set()
        self.semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        for tag in seed_tags:
            self.queue.put_nowait(self.clean_tag(tag))

    @staticmethod
    def clean_tag(tag: str) -> str:
        """タグの表記揺れ（#の有無など）を正規化"""
        tag = tag.strip().upper()
        if not tag.startswith("#"):
            tag = f"#{tag}"
        return tag

    async def fetch_battlelog(self, session: aiohttp.ClientSession, player_tag: str):
        """プレイヤーの対戦履歴を取得"""
        encoded_tag = urllib.parse.quote(player_tag)  # `#` を `%23` にエンコード
        url = f"{BASE_URL}/players/{encoded_tag}/battlelog"

        async with self.semaphore:
            try:
                async with session.get(url, headers=self.headers, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:  # Rate Limit Exceeded
                        print("[Warn] Rate limit hit. Waiting 5 seconds...")
                        await asyncio.sleep(5)
                        return None
                    else:
                        return None
            except Exception as e:
                print(f"[Error] Failed to fetch battlelog for {player_tag}: {e}")
                return None

    async def worker(self, session: aiohttp.ClientSession, file_handle, max_records: int):
        while not self.queue.empty() and len(self.visited_battles) < max_records:
            player_tag = await self.queue.get()

            if player_tag in self.visited_players:
                self.queue.task_done()
                continue

            self.visited_players.add(player_tag)
            data = await self.fetch_battlelog(session, player_tag)

            if data and "items" in data:
                for item in data["items"]:
                    # 試合の一意キーを作成してデデュープ（重複防止）
                    battle_time = item.get("battleTime")
                    event_id = item.get("event", {}).get("id")
                    battle_key = f"{battle_time}_{event_id}_{player_tag}"

                    if battle_key in self.visited_battles:
                        continue
                    self.visited_battles.add(battle_key)

                    # JSON Lines形式で1行ずつ保存
                    file_handle.write(json.dumps(item, ensure_ascii=False) + "\n")

                    # 参加プレイヤー全員のタグを抽出してキューに追加（ネットワーク拡張）
                    battle_info = item.get("battle", {})
                    teams = battle_info.get("teams", [])
                    for team in teams:
                        for player in team:
                            p_tag = player.get("tag")
                            if p_tag and p_tag not in self.visited_players:
                                await self.queue.put(p_tag)

            self.queue.task_done()
            await asyncio.sleep(0.1)  # サーバー負荷軽減用の微小ウェイト

    async def run(self, session: aiohttp.ClientSession, max_records: int = 5000):
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            print("2. BFSクロールを開始します...")
            while not self.queue.empty() and len(self.visited_battles) < max_records:
                tasks = [
                    asyncio.create_task(self.worker(session, f, max_records))
                    for _ in range(CONCURRENCY_LIMIT)
                ]
                await asyncio.gather(*tasks)

        print(f"\n[完了] 収集した一意な試合数: {len(self.visited_battles)} 件")
        print(f"データ保存先: {OUTPUT_FILE}")


async def main():
    # 1. 通信全体で共有する単一の ClientSession を作成
    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(connector=connector) as session:
        
        # 2. 事前処理：トッププレイヤーのタグを自動取得
        print("1. ランキングAPIから起点となるプレイヤータグを取得中...")
        seed_tags = await get_top_player_tags(session, API_KEY, limit=LIMIT_RANKINGS)

        if not seed_tags:
            print("[中断] 起点となるプレイヤータグが取得できませんでした。APIキーとIPアドレス設定を確認してください。")
            return

        print(f"   -> {len(seed_tags)} 名のトッププレイヤーを取得しました。")

        # 3. 本処理：同じ session を渡してクロール実行
        crawler = BrawlStarsDataCrawler(API_KEY, seed_tags)
        await crawler.run(session, max_records=MAX_RECORDS)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            LIMIT_RANKINGS = int(sys.argv[1])  # コマンドライン引数でLIMIT_RANKINGSを上書き可能
        except ValueError:
            print("python top_log_downloader.py [LIMIT_RANKINGS]") 
    # 実行に必要なライブラリの確認用メッセージ
    # インストールが必要な場合: pip install aiohttp
    asyncio.run(main())

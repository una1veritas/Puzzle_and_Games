import math
from collections import Counter
from typing import Any

# ==========================================
# 1. C4.5 決定木ノード定義とアルゴリズム本体
# ==========================================
class DecisionNode:
    def __init__(
        self,
        attribute: str | None = None,
        threshold: float | None = None,
        is_continuous: bool = False,
        branches: dict[Any, "DecisionNode"] | None = None,
        prediction: Any = None,
        samples: int = 0,
        distribution: dict[Any, int] | None = None,
    ):
        self.attribute = attribute          # 分岐に使う列名
        self.threshold = threshold          # 連続値の場合の閾値
        self.is_continuous = is_continuous  # True: 範囲クエリ (<=, >), False: 離散値 (==)
        self.branches = branches or {}      # 子ノードへの辞書
        self.prediction = prediction        # 葉ノード（または途中打ち切り）の予測ラベル
        self.samples = samples              # このノードのレコード数
        self.distribution = distribution or {}


def entropy(labels: list[Any]) -> float:
    total = len(labels)
    if total == 0:
        return 0.0
    counts = Counter(labels)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def split_info(subsets: list[list[dict]], total: int) -> float:
    info = 0.0
    for sub in subsets:
        if len(sub) > 0:
            p = len(sub) / total
            info -= p * math.log2(p)
    return info


def find_best_continuous_split(
    records: list[dict], attr: str, target_col: str
) -> tuple[float, float | None]:
    """スカラー値（連続値）に対する最適な閾値と Gain Ratio を探索"""
    total = len(records)
    base_ent = entropy([r[target_col] for r in records])

    # 属性値でソート
    sorted_recs = sorted(records, key=lambda r: r[attr])
    unique_vals = sorted(set(r[attr] for r in sorted_recs))

    if len(unique_vals) <= 1:
        return -1.0, None

    best_gain_ratio = -1.0
    best_thresh = None

    # 隣接する異なる値の中点を候補とする
    for i in range(len(unique_vals) - 1):
        thresh = (unique_vals[i] + unique_vals[i + 1]) / 2.0
        left = [r for r in sorted_recs if r[attr] <= thresh]
        right = [r for r in sorted_recs if r[attr] > thresh]

        if not left or not right:
            continue

        cond_ent = (len(left) / total) * entropy([r[target_col] for r in left]) + \
                   (len(right) / total) * entropy([r[target_col] for r in right])
        gain = base_ent - cond_ent
        s_info = split_info([left, right], total)

        if s_info > 0:
            gain_ratio = gain / s_info
            if gain_ratio > best_gain_ratio:
                best_gain_ratio = gain_ratio
                best_thresh = thresh

    return best_gain_ratio, best_thresh


def find_best_discrete_split(
    records: list[dict], attr: str, target_col: str
) -> float:
    """離散値（カテゴリ）に対する Gain Ratio を計算"""
    total = len(records)
    base_ent = entropy([r[target_col] for r in records])

    groups: dict[Any, list[dict]] = {}
    for r in records:
        groups.setdefault(r[attr], []).append(r)

    if len(groups) <= 1:
        return -1.0

    cond_ent = sum(
        (len(sub) / total) * entropy([r[target_col] for r in sub])
        for sub in groups.values()
    )
    gain = base_ent - cond_ent
    s_info = split_info(list(groups.values()), total)

    return (gain / s_info) if s_info > 0 else -1.0


def build_c45_tree(
    records: list[dict],
    features: dict[str, str],  # {列名: "continuous" or "discrete"}
    target_col: str,
    max_depth: int = 4,
    min_samples_split: int = 2,
    depth: int = 0,
) -> DecisionNode:
    labels = [r[target_col] for r in records]
    dist = dict(Counter(labels))
    majority_label = Counter(labels).most_common(1)[0][0]

    # 停止条件: 純粋ノード / 最大深さ / サンプル数不足
    if len(set(labels)) == 1 or depth >= max_depth or len(records) < min_samples_split:
        return DecisionNode(
            prediction=majority_label, samples=len(records), distribution=dist
        )

    best_attr = None
    best_gain_ratio = 0.0
    best_thresh = None
    best_is_cont = False

    for attr, ftype in features.items():
        if ftype == "continuous":
            gr, thresh = find_best_continuous_split(records, attr, target_col)
            if gr > best_gain_ratio:
                best_gain_ratio = gr
                best_attr = attr
                best_thresh = thresh
                best_is_cont = True
        else:
            gr = find_best_discrete_split(records, attr, target_col)
            if gr > best_gain_ratio:
                best_gain_ratio = gr
                best_attr = attr
                best_thresh = None
                best_is_cont = False

    # 情報利得が改善しない場合は葉ノードにする
    if best_attr is None or best_gain_ratio <= 0:
        return DecisionNode(
            prediction=majority_label, samples=len(records), distribution=dist
        )

    branches = {}
    if best_is_cont:
        left = [r for r in records if r[best_attr] <= best_thresh]
        right = [r for r in records if r[best_attr] > best_thresh]
        branches[f"<= {best_thresh:.2f}"] = build_c45_tree(
            left, features, target_col, max_depth, min_samples_split, depth + 1
        )
        branches[f"> {best_thresh:.2f}"] = build_c45_tree(
            right, features, target_col, max_depth, min_samples_split, depth + 1
        )
    else:
        # 離散値は使った属性を次の候補から外す（連続値は別閾値で再分割可能）
        next_features = {k: v for k, v in features.items() if k != best_attr}
        groups: dict[Any, list[dict]] = {}
        for r in records:
            groups.setdefault(r[best_attr], []).append(r)
        for val, sub in groups.items():
            branches[f"== {val}"] = build_c45_tree(
                sub, next_features, target_col, max_depth, min_samples_split, depth + 1
            )

    return DecisionNode(
        attribute=best_attr,
        threshold=best_thresh,
        is_continuous=best_is_cont,
        branches=branches,
        prediction=majority_label,
        samples=len(records),
        distribution=dist,
    )


def print_tree(node: DecisionNode, indent: str = "") -> None:
    """人間が読める IF-THEN ルール形式で木を出力"""
    if not node.branches:
        print(f"{indent}--> 【理由: {node.prediction}】 (n={node.samples}, 内訳={node.distribution})")
        return

    for cond, child in node.branches.items():
        print(f"{indent}IF {node.attribute} {cond}:")
        print_tree(child, indent + "    ")


# ==========================================
# 2. RDBレコード形式（麻雀盤面特徴量テーブル）の実行例
# ==========================================
if __name__ == "__main__":
    # スキーマ定義: スカラー値(continuous) と カテゴリ値(discrete) の混在
    schema = {
        "has_riichi": "discrete",       # 他家リーチ有無 (True/False)
        "shanten_diff": "continuous",   # 打牌によるシャンテン数変化 (-1: 戻し, 0: 維持)
        "ukeire_cnt": "continuous",     # 受け入れ枚数 (スカラー値)
        "genbutsu_cnt": "continuous",   # 手牌の現物枚数 (スカラー値)
        "is_suji": "discrete",          # 切った牌がスジか (True/False)
    }

    # RDBから SELECT したようなレコード群（学生に作らせたいデータ構造）
    records = [
        {"has_riichi": True,  "shanten_diff": -1, "ukeire_cnt": 4,  "genbutsu_cnt": 3, "is_suji": True,  "reason": "ベタオリ（現物抜き）"},
        {"has_riichi": True,  "shanten_diff": -1, "ukeire_cnt": 8,  "genbutsu_cnt": 2, "is_suji": False, "reason": "ベタオリ（現物抜き）"},
        {"has_riichi": True,  "shanten_diff": 0,  "ukeire_cnt": 16, "genbutsu_cnt": 0, "is_suji": True,  "reason": "回し打ち（スジ処理）"},
        {"has_riichi": True,  "shanten_diff": 0,  "ukeire_cnt": 24, "genbutsu_cnt": 1, "is_suji": False, "reason": "全ツッパ（聴牌・良形維持）"},
        {"has_riichi": False, "shanten_diff": 0,  "ukeire_cnt": 20, "genbutsu_cnt": 0, "is_suji": False, "reason": "牌効率（受け入れ最大）"},
        {"has_riichi": False, "shanten_diff": 0,  "ukeire_cnt": 12, "genbutsu_cnt": 0, "is_suji": True,  "reason": "牌効率（受け入れ最大）"},
        {"has_riichi": False, "shanten_diff": 0,  "ukeire_cnt": 6,  "genbutsu_cnt": 2, "is_suji": True,  "reason": "安牌抱え・守備意識"},
        {"has_riichi": False, "shanten_diff": -1, "ukeire_cnt": 10, "genbutsu_cnt": 1, "is_suji": False, "reason": "手役狙い（三色・一通等）"},
    ]

    tree = build_c45_tree(records, schema, target_col="reason", max_depth=3)
    print_tree(tree)

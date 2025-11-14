#!/usr/bin/env python3
"""
CSV Test Data Generator

レターパックラベル生成用のテストCSVデータを生成するスクリプト。
複数のパターン（標準、エッジケース、ストレステスト、不正データ）をサポート。
"""

import csv
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

# 都道府県リスト（47都道府県）
PREFECTURES = [
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
]

# 市区町村の例
CITIES = [
    "千代田区",
    "中央区",
    "港区",
    "新宿区",
    "渋谷区",
    "豊島区",
    "横浜市西区",
    "横浜市中区",
    "大阪市北区",
    "大阪市中央区",
    "名古屋市中区",
    "札幌市中央区",
    "福岡市博多区",
    "福岡市中央区",
    "仙台市青葉区",
    "広島市中区",
    "京都市中京区",
    "京都市下京区",
    "神戸市中央区",
    "川崎市川崎区",
]

# 名前（姓と名）
LAST_NAMES = [
    "佐藤",
    "鈴木",
    "高橋",
    "田中",
    "伊藤",
    "渡辺",
    "山本",
    "中村",
    "小林",
    "加藤",
    "吉田",
    "山田",
    "佐々木",
    "山口",
    "松本",
    "井上",
    "木村",
    "林",
    "斉藤",
    "清水",
]

FIRST_NAMES = [
    "太郎",
    "花子",
    "一郎",
    "美咲",
    "健太",
    "さくら",
    "翔太",
    "優子",
    "大輔",
    "真理子",
    "拓也",
    "恵美",
    "雄一",
    "由美",
    "和也",
    "智子",
    "誠",
    "紀子",
    "修",
    "明美",
]

# 敬称
HONORIFICS = ["様", "殿", ""]

# 建物名のプリフィックス
BUILDING_PREFIXES = ["ABC", "XYZ", "第一", "第二", "パール", "ガーデン", "プラザ"]


def generate_postal_code() -> str:
    """郵便番号を生成（XXX-XXXX形式）"""
    return f"{random.randint(0, 999):03d}-{random.randint(0, 9999):04d}"


def generate_address() -> Dict[str, str]:
    """住所データを生成"""
    prefecture = random.choice(PREFECTURES)
    city = random.choice(CITIES)
    street = f"{random.randint(1, 99)}-{random.randint(1, 99)}"

    # 建物名を生成（50%の確率で生成）
    building = ""
    if random.random() < 0.5:
        building = (
            f"{random.choice(BUILDING_PREFIXES)}ビル{random.randint(1, 10)}F"
        )

    return {
        "postal_code": generate_postal_code(),
        "address1": f"{prefecture}{city}",
        "address2": street,
        "address3": building or None,
    }


def generate_name() -> str:
    """名前を生成（苗字と名前の組み合わせ）"""
    return f"{random.choice(LAST_NAMES)}{random.choice(FIRST_NAMES)}"


def generate_standard_data(count: int = 10) -> List[Dict[str, Any]]:
    """標準的なテストデータを生成"""
    data = []
    for _ in range(count):
        to_addr = generate_address()
        from_addr = generate_address()

        data.append({
            "to_postal": to_addr["postal_code"],
            "to_address1": to_addr["address1"],
            "to_address2": to_addr["address2"],
            "to_address3": to_addr["address3"] or "",
            "to_name": generate_name(),
            "to_phone": "",
            "to_honorific": random.choice(HONORIFICS),
            "from_postal": from_addr["postal_code"],
            "from_address1": from_addr["address1"],
            "from_address2": from_addr["address2"],
            "from_address3": from_addr["address3"] or "",
            "from_name": generate_name(),
            "from_phone": "",
            "from_honorific": random.choice(["", "様"]),  # 差出人は敬称なしまたは「様」
        })

    return data


def generate_edge_case_data() -> List[Dict[str, Any]]:
    """エッジケースのテストデータを生成"""
    edge_cases = [
        # 長い住所
        {
            "to_postal": "100-0001",
            "to_address1": "東京都千代田区千代田",
            "to_address2": "1-2-3-4-5-6-7-8-9-10",
            "to_address3": "超長い建物名マンション第一号館第二棟第三階",
            "to_name": "物凄く長い名前の人物アンダーソン",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "100-0001",
            "from_address1": "東京都千代田区",
            "from_address2": "1-1",
            "from_address3": "",
            "from_name": "差出人",
            "from_phone": "",
            "from_honorific": "",
        },
        # 短い住所
        {
            "to_postal": "000-0000",
            "to_address1": "東京都千代田区",
            "to_address2": "1",
            "to_address3": "",
            "to_name": "田中",
            "to_phone": "",
            "to_honorific": "",
            "from_postal": "999-9999",
            "from_address1": "大阪府大阪市",
            "from_address2": "2",
            "from_address3": "",
            "from_name": "山田",
            "from_phone": "",
            "from_honorific": "",
        },
        # 敬称：御中（組織向け）
        {
            "to_postal": "150-0001",
            "to_address1": "東京都渋谷区",
            "to_address2": "1-1",
            "to_address3": "",
            "to_name": "株式会社ABC",
            "to_phone": "",
            "to_honorific": "御中",
            "from_postal": "100-0001",
            "from_address1": "東京都千代田区",
            "from_address2": "1-1",
            "from_address3": "",
            "from_name": "営業部",
            "from_phone": "",
            "from_honorific": "様",
        },
        # 敬称：各位（複数宛先向け）
        {
            "to_postal": "200-0001",
            "to_address1": "神奈川県横浜市",
            "to_address2": "1-1",
            "to_address3": "ビジネスビル5F",
            "to_name": "営業チーム",
            "to_phone": "",
            "to_honorific": "各位",
            "from_postal": "100-0001",
            "from_address1": "東京都千代田区",
            "from_address2": "2-2",
            "from_address3": "",
            "from_name": "田中太郎",
            "from_phone": "",
            "from_honorific": "",
        },
        # 殿（フォーマル）
        {
            "to_postal": "600-0000",
            "to_address1": "京都府京都市",
            "to_address2": "1-1",
            "to_address3": "京都ビル10F",
            "to_name": "山田次郎",
            "to_phone": "",
            "to_honorific": "殿",
            "from_postal": "100-0001",
            "from_address1": "東京都千代田区",
            "from_address2": "3-3",
            "from_address3": "",
            "from_name": "斉藤花子",
            "from_phone": "",
            "from_honorific": "様",
        },
    ]
    return edge_cases


def generate_stress_data(count: int = 1000) -> List[Dict[str, Any]]:
    """ストレステスト用データを生成"""
    return generate_standard_data(count)


def generate_invalid_data() -> List[Dict[str, Any]]:
    """不正なテストデータを生成（バリデーション検証用）"""
    invalid_cases = [
        # 郵便番号が空
        {
            "to_postal": "",
            "to_address1": "東京都千代田区",
            "to_address2": "1-1",
            "to_address3": "",
            "to_name": "山田太郎",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "100-0001",
            "from_address1": "東京都千代田区",
            "from_address2": "1-1",
            "from_address3": "",
            "from_name": "差出人",
            "from_phone": "",
            "from_honorific": "",
        },
        # 住所が空
        {
            "to_postal": "100-0001",
            "to_address1": "",
            "to_address2": "",
            "to_address3": "",
            "to_name": "山田太郎",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "100-0001",
            "from_address1": "東京都千代田区",
            "from_address2": "1-1",
            "from_address3": "",
            "from_name": "差出人",
            "from_phone": "",
            "from_honorific": "",
        },
        # 名前が空
        {
            "to_postal": "100-0001",
            "to_address1": "東京都千代田区",
            "to_address2": "1-1",
            "to_address3": "",
            "to_name": "",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "100-0001",
            "from_address1": "東京都千代田区",
            "from_address2": "1-1",
            "from_address3": "",
            "from_name": "差出人",
            "from_phone": "",
            "from_honorific": "",
        },
        # 差出人の郵便番号が空
        {
            "to_postal": "100-0001",
            "to_address1": "東京都千代田区",
            "to_address2": "1-1",
            "to_address3": "",
            "to_name": "山田太郎",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "",
            "from_address1": "東京都千代田区",
            "from_address2": "1-1",
            "from_address3": "",
            "from_name": "差出人",
            "from_phone": "",
            "from_honorific": "",
        },
    ]
    return invalid_cases


def save_csv(data: List[Dict[str, Any]], filename: str) -> Path:
    """CSVファイルに保存"""
    output_dir = Path("examples")
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        if data:
            fieldnames = [
                "to_postal",
                "to_address1",
                "to_address2",
                "to_address3",
                "to_name",
                "to_phone",
                "to_honorific",
                "from_postal",
                "from_address1",
                "from_address2",
                "from_address3",
                "from_name",
                "from_phone",
                "from_honorific",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    return filepath


def calculate_pages(count: int) -> int:
    """4upレイアウトでのページ数を計算"""
    return (count + 3) // 4


def count_honorifics(data: List[Dict[str, Any]], honorific_field: str) -> Dict[str, int]:
    """敬称の分布を集計"""
    counts: Dict[str, int] = {}
    for row in data:
        h = row[honorific_field] or "なし"
        counts[h] = counts.get(h, 0) + 1
    return counts


def main() -> None:
    """メイン処理"""
    # 引数を解析
    pattern = sys.argv[1] if len(sys.argv) > 1 else "standard"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    # パターンに応じてデータを生成
    if pattern == "standard":
        data = generate_standard_data(count)
        filename = f"test_addresses_standard_{count}.csv"
        pattern_name = "標準"
    elif pattern == "edge_case":
        data = generate_edge_case_data()
        filename = "test_addresses_edge_case.csv"
        pattern_name = "エッジケース"
    elif pattern == "stress":
        data = generate_stress_data(count)
        filename = f"test_addresses_stress_{count}.csv"
        pattern_name = "ストレステスト"
    elif pattern == "invalid":
        data = generate_invalid_data()
        filename = "test_addresses_invalid.csv"
        pattern_name = "不正データ"
    else:
        print(f"❌ 不明なパターン: {pattern}")
        print("利用可能なパターン: standard, edge_case, stress, invalid")
        sys.exit(1)

    # CSVファイルに保存
    filepath = save_csv(data, filename)

    # サマリーを出力
    print("✅ テストCSVデータを生成しました\n")
    print("【ファイル】")
    print(f"- パス: {filepath}")
    print(f"- 件数: {len(data)}件")
    print(f"- パターン: {pattern_name}")
    print(f"- 推定ページ数: {calculate_pages(len(data))}ページ（4upレイアウト）\n")

    # 敬称の集計
    to_honorifics = count_honorifics(data, "to_honorific")
    from_honorifics = count_honorifics(data, "from_honorific")

    print("【内容サマリー】")
    to_summary = ", ".join([f"{k}: {v}件" for k, v in to_honorifics.items()])
    from_summary = ", ".join([f"{k}: {v}件" for k, v in from_honorifics.items()])
    print(f"- 宛先: {len(data)}件（{to_summary}）")
    print(f"- 差出人: {len(data)}件（{from_summary}）")

    # 都道府県の集計
    prefectures_used = set()
    for row in data:
        address1 = row["to_address1"]
        for pref in PREFECTURES:
            if pref in address1:
                prefectures_used.add(pref)
                break

    if prefectures_used:
        print(f"- 使用都道府県: {len(prefectures_used)}都道府県")

    # 郵便番号の検証
    valid_postal = 0
    for row in data:
        postal = row["to_postal"]
        if postal and "-" in postal:
            parts = postal.split("-")
            if len(parts) == 2 and len(parts[0]) == 3 and len(parts[1]) == 4:
                if parts[0].isdigit() and parts[1].isdigit():
                    valid_postal += 1

    print(f"- 郵便番号: {valid_postal}/{len(data)}件が正しい形式\n")

    # 次のステップを提示
    print("【次のステップ】")
    print("以下のコマンドでラベルを生成できます：")
    print(f"```bash")
    print(f"uv run python -m letterpack.cli --csv {filepath} --output output/test_labels.pdf")
    print(f"```")


if __name__ == "__main__":
    main()

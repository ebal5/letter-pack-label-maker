# CSV Test Data Generator Skill - 使用ガイド

## 概要

このSkillは、レターパックラベル用のテストCSVデータを自動生成するためのツールです。
開発・テスト・デモンストレーション用として、多様なパターンのデータを効率的に生成できます。

## 対応パターン

### 1. 標準パターン（Standard）
実際の使用例に近いリアルなデータを生成します。

**特徴：**
- 実在する日本の都道府県・市区町村
- 一般的な日本人名
- 正しい郵便番号形式（XXX-XXXX）
- 様々な敬称（様、殿、なし）
- ビジネスライクな建物名

**使用例：**
```bash
python tools/generate_test_csv.py standard 100
```

### 2. エッジケースパターン（Edge Case）
境界値テストやコーナーケース検証用のデータを生成します。

**特徴：**
- 長い住所（最大文字数に近い）
- 短い住所（最小文字数）
- 特殊な敬称（御中など）
- 会社名や団体名のような長い名前
- 境界値の郵便番号（000-0000、999-9999）

**使用例：**
```bash
python tools/generate_test_csv.py edge_case
```

### 3. ストレステストパターン（Stress Test）
大量のデータを生成し、パフォーマンステストに使用します。

**特徴：**
- 指定した件数のランダムデータ生成
- 多様な都道府県・市区町村の組み合わせ
- メモリ効率を考慮した実装

**使用例：**
```bash
python tools/generate_test_csv.py stress 10000
```

### 4. 不正データパターン（Invalid）
バリデーション機能のテスト用に意図的に不正なデータを生成します。

**特徴：**
- 郵便番号の形式エラー
- 必須フィールドの欠落
- 不正な文字形式

**使用例：**
```bash
python tools/generate_test_csv.py invalid
```

## スクリプト利用方法

### 基本的な使い方

```bash
# 標準的な使用方法（デフォルト: 標準パターン10件）
python tools/generate_test_csv.py

# 100件の標準パターンデータを生成
python tools/generate_test_csv.py standard 100

# エッジケースデータを生成
python tools/generate_test_csv.py edge_case

# 1000件のストレステストデータを生成
python tools/generate_test_csv.py stress 1000

# 不正データを生成
python tools/generate_test_csv.py invalid
```

### 出力ファイル

生成されたCSVファイルは `examples/` ディレクトリに自動保存されます。

ファイル命名規則：
- 標準パターン: `test_addresses_standard_<件数>.csv`
- エッジケース: `test_addresses_edge_case.csv`
- ストレステスト: `test_addresses_stress_<件数>.csv`
- 不正データ: `test_addresses_invalid.csv`

## 生成されたデータの確認

```bash
# ファイルの内容を確認
cat examples/test_addresses_standard_100.csv | head -5

# 件数を確認（ヘッダーを除外）
tail -n +2 examples/test_addresses_standard_100.csv | wc -l
```

## ラベル生成への利用

生成されたCSVを使用してPDFラベルを生成できます：

```bash
# 標準パターン10件でラベル生成
python tools/generate_test_csv.py standard 10
uv run python -m letterpack.cli --csv examples/test_addresses_standard_10.csv --output output/test_labels.pdf

# 大量データでテスト
python tools/generate_test_csv.py stress 100
uv run python -m letterpack.cli --csv examples/test_addresses_stress_100.csv --output output/large_test_labels.pdf

# エッジケーステスト
python tools/generate_test_csv.py edge_case
uv run python -m letterpack.cli --csv examples/test_addresses_edge_case.csv --output output/edge_case_labels.pdf
```

## よくある使用シナリオ

### シナリオ1: 新機能のテスト
```bash
# 多様なテストデータで新機能を検証
python tools/generate_test_csv.py edge_case
uv run python -m letterpack.cli --csv examples/test_addresses_edge_case.csv --output output/feature_test.pdf
```

### シナリオ2: パフォーマンス測定
```bash
# 大量データでのパフォーマンスを測定
python tools/generate_test_csv.py stress 5000
time uv run python -m letterpack.cli --csv examples/test_addresses_stress_5000.csv --output output/perf_test.pdf
```

### シナリオ3: デモンストレーション
```bash
# 標準的なデータでデモ用PDFを生成
python tools/generate_test_csv.py standard 20
uv run python -m letterpack.cli --csv examples/test_addresses_standard_20.csv --output output/demo.pdf
```

### シナリオ4: バリデーションテスト
```bash
# 不正データの処理を検証
python tools/generate_test_csv.py invalid
uv run python -m letterpack.cli --csv examples/test_addresses_invalid.csv --output output/error_test.pdf 2>&1 | head -20
```

## CSV形式の詳細

生成されるCSVは以下の形式です：

```csv
to_postal,to_address,to_name,to_phone,to_honorific,from_postal,from_address,from_name,from_phone,from_honorific
100-0001,東京都千代田区千代田1-1 XXXビル15F,山田太郎,,様,150-0001,東京都渋谷区渋谷1-1,佐藤花子,,
```

**カラム説明：**
| カラム | 説明 | 必須 | 例 |
|--------|------|------|-----|
| `to_postal` | お届け先郵便番号 | ○ | 100-0001 |
| `to_address` | お届け先住所 | ○ | 東京都千代田区千代田1-1 |
| `to_name` | お届け先名前 | ○ | 山田太郎 |
| `to_phone` | お届け先電話番号 | - | 03-1234-5678 |
| `to_honorific` | お届け先敬称 | - | 様（デフォルト） |
| `from_postal` | ご依頼主郵便番号 | ○ | 150-0001 |
| `from_address` | ご依頼主住所 | ○ | 東京都渋谷区渋谷1-1 |
| `from_name` | ご依頼主名前 | ○ | 佐藤花子 |
| `from_phone` | ご依頼主電話番号 | - | 06-9876-5432 |
| `from_honorific` | ご依頼主敬称 | - | 空（デフォルト） |

## トラブルシューティング

### Q: ファイルが生成されない
**A:** `examples/` ディレクトリの存在確認と書き込み権限を確認してください。
```bash
ls -la examples/
chmod 755 examples/
```

### Q: 郵便番号形式エラーが出る
**A:** 不正データパターンで意図的にエラーを含んでいる場合があります。
標準パターンを使用してください。

### Q: 大量データ生成が遅い
**A:** メモリ使用量が多い場合があります。
10000件以上の場合は、複数回に分けて生成することをお勧めします。

### Q: 文字化けが発生する
**A:** UTF-8でエンコードされています。
Shift_JISが必要な場合は、別途変換してください。

## 関連資料

- [CSV Parser仕様](../../src/letterpack/csv_parser.py)
- [レターパック仕様](../../README.md)
- [テストコード](../../tests/test_csv_parser.py)

## ライセンス

このツールはプロジェクトと同じライセンスの下で提供されます。

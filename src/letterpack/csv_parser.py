"""
CSVファイルからレターパック情報を読み込むモジュール
"""

import csv
from pathlib import Path
from typing import NamedTuple, Optional

from .label import AddressInfo


class LabelData(NamedTuple):
    """1件分のラベルデータ（お届け先とご依頼主のペア）"""

    to_address: AddressInfo
    from_address: AddressInfo


class CSVValidationError(Exception):
    """CSV検証エラー"""

    def __init__(self, row_number: int, field: str, message: str):
        self.row_number = row_number
        self.field = field
        self.message = message
        super().__init__(f"行 {row_number}, フィールド '{field}': {message}")


def parse_csv(csv_path: str) -> list[LabelData]:
    """
    CSVファイルからラベルデータを読み込む

    Args:
        csv_path: CSVファイルのパス

    Returns:
        LabelDataのリスト

    Raises:
        FileNotFoundError: CSVファイルが見つからない場合
        CSVValidationError: CSV検証エラーが発生した場合
        ValueError: その他のバリデーションエラー

    CSV形式:
        - ヘッダー行必須
        - カラム: to_postal, to_address, to_name, to_phone, to_honorific,
                 from_postal, from_address, from_name, from_phone, from_honorific
        - to_honorific省略時は「様」、from_honorific省略時は敬称なし
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_path}")

    labels = []
    errors = []

    # 必須カラムと任意カラムの定義（Shift_JISフォールバック処理でも使用するため、tryブロック外で定義）
    required_columns = {
        "to_postal",
        "to_address",
        "to_name",
        "from_postal",
        "from_address",
        "from_name",
    }
    optional_columns = {"to_phone", "to_honorific", "from_phone", "from_honorific"}
    all_columns = required_columns | optional_columns

    try:
        with open(csv_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                raise ValueError("CSVファイルにヘッダー行がありません")

            missing_columns = required_columns - set(reader.fieldnames)
            if missing_columns:
                raise ValueError(f"必須カラムが不足しています: {', '.join(missing_columns)}")

            # 不明なカラムの警告（エラーにはしない）
            unknown_columns = set(reader.fieldnames) - all_columns
            if unknown_columns:
                print(f"警告: 不明なカラムがあります（無視されます）: {', '.join(unknown_columns)}")

            # 各行を処理
            for row_number, row in enumerate(reader, start=2):  # ヘッダーが1行目なので2から開始
                try:
                    # お届け先
                    to_postal = row.get("to_postal", "").strip()
                    to_address = row.get("to_address", "").strip()
                    to_name = row.get("to_name", "").strip()
                    to_phone = row.get("to_phone", "").strip() or None
                    to_honorific = row.get("to_honorific", "").strip()
                    if not to_honorific:
                        to_honorific = "様"  # デフォルト

                    # ご依頼主
                    from_postal = row.get("from_postal", "").strip()
                    from_address = row.get("from_address", "").strip()
                    from_name = row.get("from_name", "").strip()
                    from_phone = row.get("from_phone", "").strip() or None
                    from_honorific = row.get("from_honorific", "").strip()
                    # from_honorificは空文字列でもOK（敬称なし）

                    # AddressInfoを作成（バリデーション含む）
                    try:
                        to_info = AddressInfo(
                            postal_code=to_postal,
                            address=to_address,
                            name=to_name,
                            phone=to_phone,
                            honorific=to_honorific,
                        )
                    except ValueError as e:
                        errors.append((row_number, "お届け先", str(e)))
                        continue

                    try:
                        from_info = AddressInfo(
                            postal_code=from_postal,
                            address=from_address,
                            name=from_name,
                            phone=from_phone,
                            honorific=from_honorific,
                        )
                    except ValueError as e:
                        errors.append((row_number, "ご依頼主", str(e)))
                        continue

                    labels.append(LabelData(to_address=to_info, from_address=from_info))

                except Exception as e:
                    errors.append((row_number, "全体", str(e)))

    except UnicodeDecodeError:
        # UTF-8で読めない場合はShift_JISを試す
        try:
            with open(csv_file, encoding="shift_jis") as f:
                reader = csv.DictReader(f)

                if reader.fieldnames is None:
                    raise ValueError("CSVファイルにヘッダー行がありません")

                missing_columns = required_columns - set(reader.fieldnames)
                if missing_columns:
                    raise ValueError(f"必須カラムが不足しています: {', '.join(missing_columns)}")

                for row_number, row in enumerate(reader, start=2):
                    try:
                        to_postal = row.get("to_postal", "").strip()
                        to_address = row.get("to_address", "").strip()
                        to_name = row.get("to_name", "").strip()
                        to_phone = row.get("to_phone", "").strip() or None
                        to_honorific = row.get("to_honorific", "").strip() or "様"

                        from_postal = row.get("from_postal", "").strip()
                        from_address = row.get("from_address", "").strip()
                        from_name = row.get("from_name", "").strip()
                        from_phone = row.get("from_phone", "").strip() or None
                        from_honorific = row.get("from_honorific", "").strip()

                        try:
                            to_info = AddressInfo(
                                postal_code=to_postal,
                                address=to_address,
                                name=to_name,
                                phone=to_phone,
                                honorific=to_honorific,
                            )
                        except ValueError as e:
                            errors.append((row_number, "お届け先", str(e)))
                            continue

                        try:
                            from_info = AddressInfo(
                                postal_code=from_postal,
                                address=from_address,
                                name=from_name,
                                phone=from_phone,
                                honorific=from_honorific,
                            )
                        except ValueError as e:
                            errors.append((row_number, "ご依頼主", str(e)))
                            continue

                        labels.append(LabelData(to_address=to_info, from_address=from_info))

                    except Exception as e:
                        errors.append((row_number, "全体", str(e)))

        except Exception as e:
            raise ValueError(f"CSVファイルの読み込みに失敗しました: {e}") from e

    # エラーがあれば詳細を表示して例外を投げる
    if errors:
        error_messages = [f"  行 {row}: [{section}] {msg}" for row, section, msg in errors]
        error_summary = "\n".join(error_messages)
        raise ValueError(f"CSVファイルに {len(errors)} 件のエラーがあります:\n{error_summary}")

    if not labels:
        raise ValueError("CSVファイルに有効なデータがありません")

    return labels


def validate_csv(csv_path: str) -> tuple[bool, Optional[str], int]:
    """
    CSVファイルを検証（PDF生成前のチェック用）

    Args:
        csv_path: CSVファイルのパス

    Returns:
        (成功/失敗, エラーメッセージ, 有効なレコード数) のタプル
    """
    try:
        labels = parse_csv(csv_path)
        return (True, None, len(labels))
    except Exception as e:
        return (False, str(e), 0)

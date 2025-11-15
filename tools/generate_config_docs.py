#!/usr/bin/env python3
"""
Pydanticモデルから設定ドキュメントを自動生成するスクリプト

このスクリプトは、src/letterpack/label.py の Pydantic モデル定義から、
以下のドキュメントを自動生成します：
- config/label_layout.yaml: YAML設定ファイル（デフォルト値、コメント、説明を含む）
- README.md: 設定リファレンステーブル
- CONFIGURABLE_LAYOUT.md: パラメータ詳細ドキュメント

使い方:
    uv run python tools/generate_config_docs.py

オプション:
    --dry-run: 生成結果を表示するのみで、ファイルを更新しない
    --yaml-only: YAMLファイルのみ生成
    --markdown-only: Markdownドキュメントのみ生成
"""

import argparse
import sys
from pathlib import Path
from typing import get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from letterpack.label import (  # noqa: E402
    AddressLayoutConfig,
    BorderConfig,
    DottedLineConfig,
    FontsConfig,
    LayoutConfig,
    PhoneConfig,
    PostalBoxConfig,
    SamaConfig,
    SectionHeightConfig,
    SpacingConfig,
)


def get_field_type_string(field_info: FieldInfo) -> str:
    """フィールドの型を文字列として取得"""
    annotation = field_info.annotation

    # Optional型の処理
    origin = get_origin(annotation)
    if origin is type(None) or (
        hasattr(annotation, "__args__") and type(None) in get_args(annotation)
    ):
        # Optional[int] -> int | None の場合
        args = get_args(annotation)
        if args:
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                return non_none_types[0].__name__ + " | None"

    if hasattr(annotation, "__name__"):
        return annotation.__name__

    return str(annotation)


def get_constraint_range(field_info: FieldInfo) -> str | None:
    """制約情報から推奨範囲を生成"""
    if not field_info.metadata:
        return None

    constraints = {}
    for constraint in field_info.metadata:
        constraint_type = type(constraint).__name__
        if constraint_type == "Gt":
            constraints["gt"] = constraint.gt
        elif constraint_type == "Ge":
            constraints["ge"] = constraint.ge
        elif constraint_type == "Lt":
            constraints["lt"] = constraint.lt
        elif constraint_type == "Le":
            constraints["le"] = constraint.le

    if not constraints:
        return None

    # 範囲を文字列で表現
    parts = []
    if "gt" in constraints:
        parts.append(f"{constraints['gt']} <")
    elif "ge" in constraints:
        parts.append(f"{constraints['ge']} ≤")

    parts.append("x")

    if "lt" in constraints:
        parts.append(f"< {constraints['lt']}")
    elif "le" in constraints:
        parts.append(f"≤ {constraints['le']}")

    return " ".join(parts) if len(parts) > 1 else None


def get_unit_from_description(description: str | None) -> str:
    """説明文から単位を抽出"""
    if not description:
        return "-"

    # 単位のパターンマッチング
    if "(mm)" in description:
        return "mm"
    elif "(pt)" in description:
        return "pt"
    elif "(px)" in description:
        return "px"
    else:
        return "-"


def generate_yaml_for_model(
    model_class: type[BaseModel], section_name: str, section_title: str, indent: int = 0
) -> list[str]:
    """1つのPydanticモデルからYAML設定を生成"""
    lines = []
    indent_str = "  " * indent

    # セクションヘッダー
    if indent == 0:
        lines.append("")
        lines.append(f"# {'=' * 40}")
        lines.append(f"# {section_title}")
        lines.append(f"# {'=' * 40}")

    lines.append(f"{indent_str}{section_name}:")

    for field_name, field_info in model_class.model_fields.items():
        # フィールドの説明コメント
        if field_info.description:
            lines.append(f"{indent_str}  # {field_info.description}")

        # デフォルト値
        default_value = field_info.default

        # 型による値の表現調整
        if isinstance(default_value, bool):
            yaml_value = "true" if default_value else "false"
        elif isinstance(default_value, str):
            yaml_value = default_value
        elif default_value is None:
            yaml_value = "null"
        else:
            yaml_value = str(default_value)

        # 制約範囲をコメントとして追加
        constraint_range = get_constraint_range(field_info)
        if constraint_range:
            lines.append(f"{indent_str}  # 範囲: {constraint_range}")

        lines.append(f"{indent_str}  {field_name}: {yaml_value}")
        lines.append("")

    return lines


def generate_yaml_config() -> str:
    """完全なYAML設定ファイルを生成"""
    lines = []

    # ヘッダー
    lines.extend(
        [
            "# " + "=" * 78,
            "# レターパックラベル レイアウト設定ファイル",
            "# " + "=" * 78,
            "#",
            "# このファイルは tools/generate_config_docs.py によって自動生成されています。",
            "# 手動で編集する場合は、src/letterpack/label.py のPydanticモデルを更新してから、",
            "# このスクリプトを実行してください。",
            "#",
            "# 使用方法:",
            "#   - CLI版: uv run python -m letterpack.cli --config custom_config.yaml",
            '#   - Pythonコード: create_label(..., config_path="custom_config.yaml")',
            "#",
            "# " + "=" * 78,
        ]
    )

    # 各セクションを生成
    sections = [
        (LayoutConfig, "layout", "Layout Settings（レイアウト設定）"),
        (FontsConfig, "fonts", "Font Sizes（フォントサイズ）"),
        (SpacingConfig, "spacing", "Spacing（スペーシング）"),
        (PostalBoxConfig, "postal_box", "Postal Box（郵便番号ボックス）"),
        (AddressLayoutConfig, "address", "Address Layout（住所レイアウト）"),
        (DottedLineConfig, "dotted_line", "Dotted Line（点線）"),
        (SamaConfig, "sama", "Sama（「様」設定）"),
        (BorderConfig, "border", "Border（枠線）"),
        (PhoneConfig, "phone", "Phone（電話番号）"),
        (SectionHeightConfig, "section_height", "Section Heights（セクション高さ）"),
    ]

    for model_class, section_name, section_title in sections:
        lines.extend(generate_yaml_for_model(model_class, section_name, section_title))

    # フッター（カスタマイズ例）
    lines.extend(
        [
            "",
            "# " + "=" * 78,
            "# カスタマイズ例",
            "# " + "=" * 78,
            "#",
            "# 例1: フォントサイズを大きくする",
            "# fonts:",
            "#   name: 16  # デフォルト: 14pt",
            "#   address: 13  # デフォルト: 11pt",
            "#",
            "# 例2: デバッグ用枠線を非表示にする",
            "# layout:",
            "#   draw_border: false",
            "#",
            "# 例3: 4upレイアウトで印刷",
            "# layout:",
            "#   layout_mode: grid_4up",
            "#",
            "# " + "=" * 78,
        ]
    )

    return "\n".join(lines) + "\n"


def generate_markdown_table_for_model(model_class: type[BaseModel], section_name: str) -> list[str]:
    """1つのPydanticモデルからMarkdownテーブルを生成"""
    lines = []

    # テーブルヘッダー
    lines.append("| パラメータ | 型 | デフォルト | 説明 | 範囲 |")
    lines.append("|-----------|-----|-----------|------|------|")

    for field_name, field_info in model_class.model_fields.items():
        # フルパスのパラメータ名
        param_name = f"`{section_name}.{field_name}`"

        # 型
        type_str = get_field_type_string(field_info)

        # デフォルト値
        default_value = field_info.default
        if isinstance(default_value, bool):
            default_str = "true" if default_value else "false"
        elif isinstance(default_value, str):
            default_str = f'"{default_value}"'
        elif default_value is None:
            default_str = "null"
        else:
            default_str = str(default_value)

        # 説明
        description = field_info.description or "-"

        # 範囲
        constraint_range = get_constraint_range(field_info) or "-"

        lines.append(
            f"| {param_name} | {type_str} | {default_str} | {description} | {constraint_range} |"
        )

    return lines


def generate_readme_config_reference() -> str:
    """README.md用の設定リファレンステーブルを生成"""
    lines = []

    lines.extend(
        [
            "## 設定リファレンス（Configuration Reference）",
            "",
            "このセクションは `tools/generate_config_docs.py` によって自動生成されています。",
            "",
            "レイアウト設定のカスタマイズ方法については、[CONFIGURABLE_LAYOUT.md](./CONFIGURABLE_LAYOUT.md) を参照してください。",
            "",
        ]
    )

    # 各セクションを生成
    sections = [
        (LayoutConfig, "layout", "### Layout Settings（レイアウト設定）"),
        (FontsConfig, "fonts", "### Font Sizes（フォントサイズ）"),
        (SpacingConfig, "spacing", "### Spacing（スペーシング）"),
        (PostalBoxConfig, "postal_box", "### Postal Box（郵便番号ボックス）"),
        (AddressLayoutConfig, "address", "### Address Layout（住所レイアウト）"),
        (DottedLineConfig, "dotted_line", "### Dotted Line（点線）"),
        (SamaConfig, "sama", "### Sama（「様」設定）"),
        (BorderConfig, "border", "### Border（枠線）"),
        (PhoneConfig, "phone", "### Phone（電話番号）"),
        (SectionHeightConfig, "section_height", "### Section Heights（セクション高さ）"),
    ]

    for model_class, section_name, section_title in sections:
        lines.append(section_title)
        lines.append("")
        lines.extend(generate_markdown_table_for_model(model_class, section_name))
        lines.append("")

    return "\n".join(lines) + "\n"


def generate_configurable_layout_section(
    model_class: type[BaseModel], section_name: str, section_number: int, section_title: str
) -> str:
    """CONFIGURABLE_LAYOUT.md用のセクションを生成"""
    lines = []

    lines.append(f"### {section_number}. {section_title}")
    lines.append("")
    lines.append(model_class.__doc__ or "")
    lines.append("")
    lines.extend(generate_markdown_table_for_model(model_class, section_name))
    lines.append("")

    return "\n".join(lines) + "\n"


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="Pydanticモデルから設定ドキュメントを自動生成")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="生成結果を表示するのみで、ファイルを更新しない",
    )
    parser.add_argument(
        "--yaml-only",
        action="store_true",
        help="YAMLファイルのみ生成",
    )
    parser.add_argument(
        "--markdown-only",
        action="store_true",
        help="Markdownドキュメントのみ生成",
    )
    args = parser.parse_args()

    # YAMLファイル生成
    if not args.markdown_only:
        print("Generating YAML configuration file...")
        yaml_content = generate_yaml_config()

        if args.dry_run:
            print("\n--- config/label_layout.yaml (preview) ---")
            print(yaml_content[:500] + "...\n(truncated)")
        else:
            yaml_path = project_root / "config" / "label_layout.yaml"
            yaml_path.write_text(yaml_content, encoding="utf-8")
            print(f"✓ Generated: {yaml_path}")

    # Markdownドキュメント生成
    if not args.yaml_only:
        print("Generating Markdown documentation...")
        readme_content = generate_readme_config_reference()

        if args.dry_run:
            print("\n--- README.md section (preview) ---")
            print(readme_content[:500] + "...\n(truncated)")
        else:
            # 注意: README.mdの更新は別途手動で行う必要がある
            # （既存コンテンツとの統合が必要なため）
            output_path = project_root / "config" / "readme_config_reference.md"
            output_path.write_text(readme_content, encoding="utf-8")
            print(f"✓ Generated: {output_path}")
            print("  Note: Please manually merge this into README.md")

    print("\nDone!")


if __name__ == "__main__":
    main()

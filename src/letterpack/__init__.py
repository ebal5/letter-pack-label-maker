"""
Letter Pack Label Maker

レターパック用のラベルPDFを作成するツール
"""

__version__ = "0.1.0"

from .label import LabelGenerator, AddressInfo

__all__ = ["LabelGenerator", "AddressInfo", "__version__"]

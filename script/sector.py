"""
QMT 板块成分股解析器

读取板块文件中的逗号分隔股票代码列表。
板块文件路径格式: datadir/Sector/{category}/{sector_name}
内容格式: "000635.SZ,000837.SZ,600114.SH,..."
"""

import os
from typing import Optional, Dict, Any, List


def parse_sector_file(file_path: str) -> List[Dict[str, Any]]:
    """
    解析板块成分股文件

    Args:
        file_path: 板块文件路径

    Returns:
        成分股列表，每项包含 code 字段
        例: [{"code": "000635.SZ"}, {"code": "000837.SZ"}, ...]
    """
    if not isinstance(file_path, str):
        raise TypeError(f"file_path 必须是字符串类型，当前类型: {type(file_path)}")

    if not file_path.strip():
        raise ValueError("文件路径不能为空")

    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
    except OSError:
        return []

    if not content:
        return []

    # 格式: "000635.SZ,000837.SZ,600114.SH,..."
    codes = [s.strip() for s in content.split(",") if s.strip()]

    return [{"code": code, "index": idx + 1} for idx, code in enumerate(codes)]

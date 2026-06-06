"""
QMT 财务数据 (.DAT) 解析器

参照 FINANCE.md 二进制格式规范，支持 7001-7008 类型。
所有数据采用小端序 (Little-Endian)，定长记录格式。
"""

import struct
import os
import math
from typing import Optional, Dict, Any, List

import pandas as pd

# ============================================================
# 财务类型定义
# ============================================================

FINANCE_TYPE_MAP: Dict[str, Dict[str, Any]] = {
    "7001": {"name": "资产负债表", "stride": 1264, "num_columns": 156},
    "7002": {"name": "利润表", "stride": 664, "num_columns": 80},
    "7003": {"name": "现金流量表", "stride": 920, "num_columns": 111},
    "7004": {"name": "股本结构", "stride": 56, "num_columns": 4},
    "7005": {"name": "股东户数", "stride": 64, "num_columns": 6},
    "7006": {"name": "十大流通股东", "stride": 416, "num_columns": 5},
    "7007": {"name": "十大股东", "stride": 416, "num_columns": 5},
    "7008": {"name": "财务比率", "stride": 344, "num_columns": 41},
}

# 有效时间戳范围 (1990年 - 2050年, 毫秒)
_MIN_VALID_TS: int = 631_152_000_000
_MAX_VALID_TS: int = 2_524_608_000_000

# QMT NaN 标记 (IEEE 754)
_QMT_NAN_HEX: int = 0x7FEFFFFFFFFFFFFF


def _is_valid_timestamp(ts_ms: int) -> bool:
    """检查毫秒级时间戳是否在有效范围内"""
    return _MIN_VALID_TS <= ts_ms <= _MAX_VALID_TS


def _read_f64_or_nan(raw_bytes: bytes) -> Optional[float]:
    """读取 8 字节 double，如果是 QMT NaN 标记则返回 None"""
    value = struct.unpack("<d", raw_bytes)[0]
    raw_int = struct.unpack("<Q", raw_bytes)[0]
    if raw_int == _QMT_NAN_HEX or math.isnan(value):
        return None
    return value


def _ts_to_datetime(ts_ms: int) -> Optional[str]:
    """将毫秒级时间戳转为 ISO 格式日期字符串 (北京时间 UTC+8)"""
    if not _is_valid_timestamp(ts_ms):
        return None
    try:
        return pd.to_datetime(ts_ms, unit="ms", utc=True).tz_convert("Asia/Shanghai").strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return None


def _detect_finance_type(file_path: str) -> Optional[str]:
    """从文件名自动检测财务类型 (如 000001_7001.DAT -> 7001)"""
    name = os.path.basename(file_path)
    for type_id in FINANCE_TYPE_MAP:
        if f"_{type_id}." in name:
            return type_id
    return None


def _parse_report_record(
    record_bytes: bytes, type_id: str
) -> Optional[Dict[str, Any]]:
    """
    解析 7001/7002/7003 报表类记录

    结构:
      - 7001: [ReportDate(8)] [AnnounceDate(8)] [Columns(156 * 8)]
      - 7002: [LeadDate(8)] [ReportDate(8)] [AnnounceDate(8)] [Columns(80 * 8)]
      - 7003: [LeadDate(8)] [ReportDate(8)] [AnnounceDate(8)] [Columns(111 * 8)]
    """
    type_info = FINANCE_TYPE_MAP[type_id]
    num_cols = type_info["num_columns"]
    row: Dict[str, Any] = {"type": type_id, "type_name": type_info["name"]}

    if type_id == "7001":
        # 7001: 直接以 ReportDate 开头
        report_ts = struct.unpack("<q", record_bytes[0:8])[0]
        announce_ts = struct.unpack("<q", record_bytes[8:16])[0]
        data_offset = 16
    else:
        # 7002/7003: LeadDate + ReportDate + AnnounceDate
        lead_ts = struct.unpack("<q", record_bytes[0:8])[0]
        report_ts = struct.unpack("<q", record_bytes[8:16])[0]
        announce_ts = struct.unpack("<q", record_bytes[16:24])[0]
        data_offset = 24
        row["lead_date"] = _ts_to_datetime(lead_ts)

    row["report_date"] = _ts_to_datetime(report_ts)
    row["announce_date"] = _ts_to_datetime(announce_ts)

    # 解析数据列
    columns: List[Optional[float]] = []
    for i in range(num_cols):
        offset = data_offset + i * 8
        if offset + 8 <= len(record_bytes):
            val = _read_f64_or_nan(record_bytes[offset : offset + 8])
            columns.append(val)
        else:
            columns.append(None)

    row["columns"] = columns
    return row


def _parse_capital_record(record_bytes: bytes) -> Dict[str, Any]:
    """解析 7004 股本结构记录 (stride=56)"""
    report_ts = struct.unpack("<q", record_bytes[0:8])[0]
    announce_ts = struct.unpack("<q", record_bytes[8:16])[0]
    total_share = _read_f64_or_nan(record_bytes[16:24])
    flow_share = _read_f64_or_nan(record_bytes[24:32])
    restricted = _read_f64_or_nan(record_bytes[32:40])
    free_float = _read_f64_or_nan(record_bytes[40:48])

    return {
        "type": "7004",
        "type_name": "股本结构",
        "report_date": _ts_to_datetime(report_ts),
        "announce_date": _ts_to_datetime(announce_ts),
        "total_share": total_share,
        "flow_share": flow_share,
        "restricted": restricted,
        "free_float_share": free_float,
    }


def _parse_holder_count_record(record_bytes: bytes) -> Dict[str, Any]:
    """解析 7005 股东户数记录 (stride=64)"""
    announce_ts = struct.unpack("<q", record_bytes[0:8])[0]
    report_ts = struct.unpack("<q", record_bytes[8:16])[0]
    total_holders = _read_f64_or_nan(record_bytes[16:24])
    a_holders = _read_f64_or_nan(record_bytes[24:32])
    b_holders = _read_f64_or_nan(record_bytes[32:40])
    h_holders = _read_f64_or_nan(record_bytes[40:48])
    float_holders = _read_f64_or_nan(record_bytes[48:56])
    other_holders = _read_f64_or_nan(record_bytes[56:64])

    return {
        "type": "7005",
        "type_name": "股东户数",
        "report_date": _ts_to_datetime(report_ts),
        "announce_date": _ts_to_datetime(announce_ts),
        "total_holders": total_holders,
        "a_holders": a_holders,
        "b_holders": b_holders,
        "h_holders": h_holders,
        "float_holders": float_holders,
        "other_holders": other_holders,
    }


def _parse_top_holder_record(record_bytes: bytes, type_id: str) -> Dict[str, Any]:
    """解析 7006/7007 十大股东记录 (stride=416)"""
    announce_ts = struct.unpack("<q", record_bytes[0:8])[0]
    report_ts = struct.unpack("<q", record_bytes[8:16])[0]

    # 股东名称: offset 0x10, 192 字节, UTF-8, \0 截断
    name_raw = record_bytes[0x10:0xD0]
    name = name_raw.split(b"\x00")[0].decode("utf-8", errors="replace").strip()

    # 股东类型: offset 0xD8, 56 字节
    holder_type_raw = record_bytes[0xD8:0x110]
    holder_type = holder_type_raw.split(b"\x00")[0].decode("utf-8", errors="replace").strip()

    # 持股数量: offset 0x110
    hold_amount = _read_f64_or_nan(record_bytes[0x110:0x118])

    # 变动原因: offset 0x118, 16 字节
    change_reason_raw = record_bytes[0x118:0x128]
    change_reason = change_reason_raw.split(b"\x00")[0].decode("utf-8", errors="replace").strip()

    # 持股比例: offset 0x130
    hold_ratio = _read_f64_or_nan(record_bytes[0x130:0x138])

    # 股份性质: offset 0x138, 96 字节
    share_type_raw = record_bytes[0x138:0x198]
    share_type = share_type_raw.split(b"\x00")[0].decode("utf-8", errors="replace").strip()

    # 排名: offset 0x19C
    rank = struct.unpack("<I", record_bytes[0x19C:0x1A0])[0]

    type_info = FINANCE_TYPE_MAP[type_id]
    return {
        "type": type_id,
        "type_name": type_info["name"],
        "report_date": _ts_to_datetime(report_ts),
        "announce_date": _ts_to_datetime(announce_ts),
        "name": name,
        "holder_type": holder_type,
        "hold_amount": hold_amount,
        "change_reason": change_reason,
        "hold_ratio": hold_ratio,
        "share_type": share_type,
        "rank": rank,
    }


def _parse_ratios_record(record_bytes: bytes) -> Dict[str, Any]:
    """解析 7008 财务比率记录 (stride=344)"""
    report_ts = struct.unpack("<q", record_bytes[0:8])[0]
    announce_ts = struct.unpack("<q", record_bytes[8:16])[0]

    num_cols = 41
    columns: List[Optional[float]] = []
    for i in range(num_cols):
        offset = 16 + i * 8
        if offset + 8 <= len(record_bytes):
            val = _read_f64_or_nan(record_bytes[offset : offset + 8])
            columns.append(val)
        else:
            columns.append(None)

    return {
        "type": "7008",
        "type_name": "财务比率",
        "report_date": _ts_to_datetime(report_ts),
        "announce_date": _ts_to_datetime(announce_ts),
        "columns": columns,
    }


def parse_finance(file_path: str) -> Optional[pd.DataFrame]:
    """
    解析 QMT 财务数据文件 (.DAT)

    自动识别 7001-7008 类型，按定长步长读取记录。

    Args:
        file_path: 财务数据文件路径

    Returns:
        解析成功返回 DataFrame，失败返回 None
    """
    if not isinstance(file_path, str):
        raise TypeError(f"file_path 必须是字符串类型，当前类型: {type(file_path)}")

    if not file_path.strip():
        raise ValueError("文件路径不能为空")

    if not file_path.lower().endswith(".dat"):
        raise ValueError("文件必须是 .dat 或 .DAT 格式")

    if not os.path.exists(file_path):
        return None

    # 检测财务类型
    type_id = _detect_finance_type(file_path)
    if type_id is None:
        return None

    type_info = FINANCE_TYPE_MAP[type_id]
    stride = type_info["stride"]
    records: List[Dict[str, Any]] = []

    try:
        with open(file_path, "rb") as f:
            while True:
                record_bytes = f.read(stride)
                if not record_bytes or len(record_bytes) < stride:
                    break

                if type_id in ("7001", "7002", "7003"):
                    record = _parse_report_record(record_bytes, type_id)
                elif type_id == "7004":
                    record = _parse_capital_record(record_bytes)
                elif type_id == "7005":
                    record = _parse_holder_count_record(record_bytes)
                elif type_id in ("7006", "7007"):
                    record = _parse_top_holder_record(record_bytes, type_id)
                elif type_id == "7008":
                    record = _parse_ratios_record(record_bytes)
                else:
                    continue

                if record is not None:
                    records.append(record)

    except Exception as e:
        return None

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # 对于报表类 (7001/7002/7003/7008)，将 columns 列展平为独立列
    if "columns" in df.columns:
        # 保留非 columns 列
        meta_cols = [c for c in df.columns if c != "columns"]
        expanded = pd.DataFrame(df["columns"].tolist())
        expanded.columns = [f"col_{i}" for i in range(len(expanded.columns))]
        df = pd.concat([df[meta_cols].reset_index(drop=True), expanded], axis=1)

    return df

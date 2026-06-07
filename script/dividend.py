"""
QMT 除权数据 LevelDB 解析器

读取 QMT 客户端本地 DividData 目录中的 LevelDB 数据库，
解析除权除息记录。

LevelDB Key 格式: {market}|{code}|{timestamp_ms}  (如 SH|600000|1640995200000)
LevelDB Value 格式: 96 字节 little-endian 二进制结构

二进制布局 (96 bytes):
  Offset  0-7:   unknown (跳过)
  Offset  8-15:  timestamp_raw (i64, 毫秒时间戳)
  Offset 16-23:  interest (f64, 每股现金红利)
  Offset 24-31:  stock_bonus (f64, 每股送股)
  Offset 32-39:  stock_gift (f64, 每股转赠)
  Offset 40-47:  allot_num (f64, 配股数量)
  Offset 48-55:  allot_price (f64, 配股价格)
  Offset 56-63:  gugai (f64, 股改值)
  Offset 64-71:  unknown64_raw (f64, 保留)
  Offset 72-79:  adjust_factor (f64, 复权系数)
  Offset 80-83:  record_date (u32, YYYYMMDD)
  Offset 84-87:  padding
  Offset 88-91:  ex_dividend_date (u32, YYYYMMDD)
  Offset 92-95:  padding
"""

import logging
import os
import struct
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

try:
    import plyvel
except ImportError:
    plyvel = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _ensure_ascii_path(path: str) -> str:
    """
    确保 LevelDB 路径只包含 ASCII 字符。

    plyvel-ci (Windows) 的 C 扩展无法处理包含非 ASCII 字符的路径（如中文）。
    此函数尝试以下策略：
    1. 若路径已是纯 ASCII，直接返回
    2. 尝试获取 Windows 8.3 短路径名
    3. 创建 junction 链接到纯 ASCII 临时目录
    """
    if sys.platform != "win32":
        return path

    # 策略 1：路径已是纯 ASCII
    try:
        path.encode("ascii")
        return path
    except UnicodeEncodeError:
        pass

    # 策略 2：尝试 Windows 8.3 短路径名
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.kernel32.GetShortPathNameW(path, buf, 512)
        result = buf.value
        if result:
            try:
                result.encode("ascii")
                logger.info("使用短路径: %s -> %s", path, result)
                return result
            except UnicodeEncodeError:
                pass  # 短路径仍含非 ASCII，尝试策略 3
    except Exception:
        pass

    # 策略 3：创建 junction 到纯 ASCII 临时目录
    try:
        import tempfile
        import uuid
        junction_dir = os.path.join(
            tempfile.gettempdir(), f"qmt_leveldb_{uuid.uuid4().hex[:8]}"
        )
        os.makedirs(junction_dir, exist_ok=True)
        junction_path = os.path.join(junction_dir, os.path.basename(path))

        if not os.path.exists(junction_path):
            import subprocess

            subprocess.run(
                ["cmd", "/c", "mklink", "/J", junction_path, path],
                check=True,
                capture_output=True,
            )
            logger.info("创建 junction: %s -> %s", junction_path, path)

        return junction_path
    except Exception as e:
        logger.warning("创建 junction 失败: %s，使用原始路径", e)
        return path


# 二进制值结构大小 (字节)
VALUE_SIZE = 96

# struct 格式字符串: little-endian, 96 字节
# 1q (unknown) + 1q (timestamp) + 8d (f64 fields) + 4I (u32 fields)
VALUE_STRUCT = struct.Struct("<qq8d4I")

# Key 中时间戳的有效范围 (毫秒)
MIN_TIMESTAMP = 0
MAX_TIMESTAMP = 3_000_000_000_000


def _check_leveldb() -> None:
    """检查 LevelDB 依赖是否可用"""
    if plyvel is None:
        raise ImportError(
            "plyvel 未安装。Windows 用户请运行: pip install plyvel-ci"
        )


def _parse_yyyymmdd(raw: int) -> Optional[date]:
    """将 u32 YYYYMMDD 格式转换为 date 对象"""
    if raw == 0:
        return None
    try:
        year = raw // 10_000
        month = (raw // 100) % 100
        day = raw % 100
        return date(year, month, day)
    except (ValueError, ZeroDivisionError):
        return None


def _date_from_timestamp_ms(ts_ms: int) -> Optional[date]:
    """将毫秒时间戳转换为 date 对象 (北京时间 UTC+8)"""
    if ts_ms <= 0:
        return None
    try:
        dt = datetime.utcfromtimestamp(ts_ms / 1000.0)
        # UTC+8 偏移
        from datetime import timedelta
        dt = dt + timedelta(hours=8)
        return dt.date()
    except (ValueError, OSError):
        return None


def list_dividend_codes(db_path: str, market: str) -> List[str]:
    """
    列出指定市场下有除权数据的所有股票代码。

    参数:
        db_path: DividData 目录路径
        market: 市场代码 (SH/SZ/BJ)

    返回:
        排序后的股票代码列表
    """
    _check_leveldb()

    db_dir = Path(db_path)
    if not db_dir.exists() or not db_dir.is_dir():
        raise FileNotFoundError(f"LevelDB 目录不存在: {db_path}")

    codes: set[str] = set()
    prefix = f"{market}|".encode("utf-8")

    try:
        db = plyvel.DB(_ensure_ascii_path(str(db_dir)), create_if_missing=False)
    except Exception as e:
        raise RuntimeError(f"无法打开 LevelDB: {e}") from e

    try:
        for key, _value in db:
            if not key.startswith(prefix):
                continue
            try:
                key_str = key.decode("utf-8")
                parts = key_str.split("|")
                if len(parts) >= 4:
                    codes.add(parts[1])
            except (UnicodeDecodeError, IndexError):
                continue
    finally:
        db.close()

    return sorted(codes)


def parse_dividend_records(
    db_path: str,
    market: str,
    code: str,
) -> Optional[pd.DataFrame]:
    """
    查询指定市场和证券代码的除权除息记录。

    参数:
        db_path: DividData 目录路径
        market: 市场代码 (SH/SZ/BJ)
        code: 证券代码 (如 600000)

    返回:
        包含除权记录的 DataFrame，列包括:
        ex_dividend_date, record_date, interest, stock_bonus,
        stock_gift, allot_num, allot_price, gugai, adjust_factor
        如果无数据返回 None
    """
    _check_leveldb()

    db_dir = Path(db_path)
    if not db_dir.exists() or not db_dir.is_dir():
        raise FileNotFoundError(f"LevelDB 目录不存在: {db_path}")

    prefix = f"{market}|{code}|".encode("utf-8")

    try:
        db = plyvel.DB(_ensure_ascii_path(str(db_dir)), create_if_missing=False)
    except Exception as e:
        raise RuntimeError(f"无法打开 LevelDB: {e}") from e

    records: List[Dict[str, object]] = []

    try:
        for key, value in db:
            if not key.startswith(prefix):
                continue
            if len(value) < VALUE_SIZE:
                logger.warning("Value 过短: %d bytes (期望 >= %d)", len(value), VALUE_SIZE)
                continue

            # 验证 key 中的时间戳
            try:
                key_str = key.decode("utf-8")
                ts_key = int(key_str.split("|")[-1])
                if ts_key <= MIN_TIMESTAMP or ts_key > MAX_TIMESTAMP:
                    continue
            except (UnicodeDecodeError, ValueError, IndexError):
                continue

            record = _parse_value(value)
            if record is not None:
                records.append(record)
    finally:
        db.close()

    if not records:
        return None

    df = pd.DataFrame(records)
    # 按除权日排序
    df = df.sort_values("ex_dividend_date", ascending=False).reset_index(drop=True)
    return df


def _parse_value(data: bytes) -> Optional[Dict[str, object]]:
    """解析单条 96 字节的 LevelDB Value 为字典"""
    try:
        fields = VALUE_STRUCT.unpack(data[:VALUE_SIZE])
    except struct.error:
        return None

    (
        _unknown,       # 0-7: skip
        timestamp_raw,  # 8-15: i64 ms
        interest,       # 16-23: f64
        stock_bonus,    # 24-31: f64
        stock_gift,     # 32-39: f64
        allot_num,      # 40-47: f64
        allot_price,    # 48-55: f64
        gugai,          # 56-63: f64
        _unknown64,     # 64-71: f64 skip
        adjust_factor,  # 72-79: f64
        record_date_raw,  # 80-83: u32 YYYYMMDD
        _pad1,          # 84-87
        ex_div_date_raw,  # 88-91: u32 YYYYMMDD
        _pad2,          # 92-95
    ) = fields

    if timestamp_raw <= 0:
        return None

    # 解析除权除息日 (优先使用 u32 格式，fallback 到时间戳)
    ex_dividend_date = _parse_yyyymmdd(int(ex_div_date_raw))
    if ex_dividend_date is None:
        ex_dividend_date = _date_from_timestamp_ms(int(timestamp_raw))
    if ex_dividend_date is None:
        return None

    # 解析股权登记日
    record_date = _parse_yyyymmdd(int(record_date_raw))

    return {
        "ex_dividend_date": str(ex_dividend_date),
        "record_date": str(record_date) if record_date else "-",
        "interest": round(interest, 4),
        "stock_bonus": round(stock_bonus, 4),
        "stock_gift": round(stock_gift, 4),
        "allot_num": round(allot_num, 4),
        "allot_price": round(allot_price, 4),
        "gugai": round(gugai, 4),
        "adjust_factor": round(adjust_factor, 6),
    }

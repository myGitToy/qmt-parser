"""
QMT数据服务
用于扫描和读取QMT客户端本地缓存数据
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# 市场代码映射
MARKET_MAP = {
    "SH": {"name": "上海证券交易所", "short": "沪", "suffix": ".SH"},
    "SZ": {"name": "深圳证券交易所", "short": "深", "suffix": ".SZ"},
    "BJ": {"name": "北京证券交易所", "short": "京", "suffix": ".BJ"},
    "SZO": {"name": "深圳期权", "short": "深期权", "suffix": ".SZO"},
    "SHO": {"name": "上海期权", "short": "沪期权", "suffix": ".SHO"},
}

# 周期代码映射
PERIOD_MAP = {
    "0": {"name": "Tick分笔", "unit": "tick", "desc": "逐笔成交数据", "record_size": 100},
    "60": {"name": "1分钟", "unit": "1m", "desc": "1分钟K线数据", "record_size": 40},
    "300": {"name": "5分钟", "unit": "5m", "desc": "5分钟K线数据", "record_size": 40},
    "1800": {"name": "15分钟", "unit": "15m", "desc": "15分钟K线数据", "record_size": 40},
    "3600": {"name": "1小时", "unit": "1h", "desc": "1小时K线数据", "record_size": 40},
    "86400": {"name": "日线", "unit": "1d", "desc": "日K线数据", "record_size": 36},
    "43200": {"name": "周线", "unit": "1w", "desc": "周K线数据", "record_size": 36},
    "1209600": {"name": "月线", "unit": "1M", "desc": "月K线数据", "record_size": 36},
}

# 财务数据类型映射
FINANCE_TYPE_MAP = {
    "7001": {"name": "资产负债表", "file_suffix": "_7001.DAT"},
    "7002": {"name": "利润表", "file_suffix": "_7002.DAT"},
    "7003": {"name": "现金流量表", "file_suffix": "_7003.DAT"},
    "7004": {"name": "杜邦分析", "file_suffix": "_7004.DAT"},
    "7005": {"name": "盈利能力", "file_suffix": "_7005.DAT"},
    "7006": {"name": "成长能力", "file_suffix": "_7006.DAT"},
    "7007": {"name": "偿债能力", "file_suffix": "_7007.DAT"},
    "7008": {"name": "营运能力", "file_suffix": "_7008.DAT"},
}


class QmtDataService:
    """QMT数据服务"""

    def __init__(self):
        """初始化QMT数据服务"""
        self.qmt_client_path = settings.qmt_client_path
        self.datadir: Optional[Path] = None
        self._init_datadir()

    def _init_datadir(self):
        """初始化datadir路径"""
        if not self.qmt_client_path:
            logger.warning("QMT_CLIENT_PATH 未配置")
            return

        # datadir 在 QMT 客户端安装目录下
        self.datadir = Path(self.qmt_client_path) / "datadir"

        if not self.datadir.exists():
            logger.warning(f"datadir 不存在: {self.datadir}")

    def validate_path(self) -> Dict[str, Any]:
        """
        验证QMT路径配置

        Returns:
            包含验证结果的字典
        """
        result = {
            "qmt_client_path": self.qmt_client_path,
            "datadir": str(self.datadir) if self.datadir else None,
            "valid": False,
            "error": None
        }

        if not self.qmt_client_path:
            result["error"] = "QMT_CLIENT_PATH 未配置"
            return result

        client_path = Path(self.qmt_client_path)
        if not client_path.exists():
            result["error"] = f"QMT客户端路径不存在: {self.qmt_client_path}"
            return result

        if not self.datadir:
            result["error"] = "datadir 路径初始化失败"
            return result

        if not self.datadir.exists():
            result["error"] = f"datadir 不存在: {self.datadir}"
            return result

        result["valid"] = True
        return result

    def get_summary(self) -> Dict[str, Any]:
        """
        获取数据总览统计

        Returns:
            包含市场数、文件数、总大小等统计信息的字典
        """
        if not self.datadir or not self.datadir.exists():
            return {
                "valid": False,
                "error": "datadir 不可用"
            }

        total_markets = 0
        total_files = 0
        total_size = 0
        market_stats = []

        for market_dir in self.datadir.iterdir():
            if not market_dir.is_dir():
                continue

            market_code = market_dir.name
            if market_code not in MARKET_MAP:
                continue

            total_markets += 1
            market_files = 0
            market_size = 0
            period_stats = []

            for period_dir in market_dir.iterdir():
                if not period_dir.is_dir():
                    continue

                period_code = period_dir.name
                if period_code not in PERIOD_MAP:
                    continue

                # 统计该周期下的文件
                period_files = 0
                period_size = 0

                if period_code == "0":  # Tick数据特殊处理
                    for stock_dir in period_dir.iterdir():
                        if stock_dir.is_dir():
                            for dat_file in stock_dir.glob("*.dat"):
                                if dat_file.is_file():
                                    period_files += 1
                                    period_size += dat_file.stat().st_size
                else:
                    for dat_file in period_dir.glob("*.DAT"):
                        if dat_file.is_file():
                            period_files += 1
                            period_size += dat_file.stat().st_size

                if period_files > 0:
                    period_stats.append({
                        "code": period_code,
                        "name": PERIOD_MAP[period_code]["name"],
                        "files": period_files,
                        "size": period_size,
                        "size_human": self._format_size(period_size)
                    })

                market_files += period_files
                market_size += period_size

            if market_files > 0:
                market_stats.append({
                    "code": market_code,
                    "name": MARKET_MAP[market_code]["name"],
                    "files": market_files,
                    "size": market_size,
                    "size_human": self._format_size(market_size),
                    "periods": period_stats
                })

                total_files += market_files
                total_size += market_size

        return {
            "valid": True,
            "summary": {
                "total_markets": total_markets,
                "total_files": total_files,
                "total_size": total_size,
                "total_size_human": self._format_size(total_size),
                "last_scan": datetime.now().isoformat()
            },
            "markets": market_stats
        }

    def list_markets(self) -> List[Dict[str, Any]]:
        """
        列出所有市场

        Returns:
            市场列表
        """
        if not self.datadir or not self.datadir.exists():
            return []

        markets = []
        for market_dir in self.datadir.iterdir():
            if not market_dir.is_dir():
                continue

            market_code = market_dir.name
            if market_code in MARKET_MAP:
                markets.append({
                    "code": market_code,
                    "name": MARKET_MAP[market_code]["name"],
                    "short": MARKET_MAP[market_code]["short"],
                    "suffix": MARKET_MAP[market_code]["suffix"]
                })

        return sorted(markets, key=lambda x: x["code"])

    def list_periods(self, market: str) -> List[Dict[str, Any]]:
        """
        列出指定市场的所有周期

        Args:
            market: 市场代码 (SH/SZ/BJ等)

        Returns:
            周期列表
        """
        if not self.datadir or not self.datadir.exists():
            return []

        market_path = self.datadir / market
        if not market_path.exists() or not market_path.is_dir():
            return []

        periods = []
        for period_dir in market_path.iterdir():
            if not period_dir.is_dir():
                continue

            period_code = period_dir.name
            if period_code in PERIOD_MAP:
                # 统计该周期的文件数
                file_count = self._count_period_files(market, period_code)
                periods.append({
                    "code": period_code,
                    "name": PERIOD_MAP[period_code]["name"],
                    "unit": PERIOD_MAP[period_code]["unit"],
                    "desc": PERIOD_MAP[period_code]["desc"],
                    "files": file_count
                })

        return sorted(periods, key=lambda x: int(x["code"]) if x["code"].isdigit() else 0)

    def list_files(
        self,
        market: str,
        period: str,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        列出指定市场、周期下的文件

        Args:
            market: 市场代码
            period: 周期代码
            page: 页码 (从1开始)
            page_size: 每页大小

        Returns:
            文件列表及分页信息
        """
        if not self.datadir or not self.datadir.exists():
            return {"valid": False, "error": "datadir 不可用"}

        period_path = self.datadir / market / period
        if not period_path.exists() or not period_path.is_dir():
            return {"valid": False, "error": f"路径不存在: {market}/{period}"}

        files = []

        if period == "0":  # Tick数据特殊处理
            for stock_dir in period_path.iterdir():
                if not stock_dir.is_dir():
                    continue

                stock_code = stock_dir.name
                for dat_file in stock_dir.glob("*.dat"):
                    if dat_file.is_file():
                        files.append(self._get_file_info(dat_file, f"{stock_code}/{dat_file.name}"))
        else:
            for dat_file in period_path.glob("*.DAT"):
                if dat_file.is_file():
                    files.append(self._get_file_info(dat_file, dat_file.name))

        # 按文件名排序
        files.sort(key=lambda x: x["name"])

        # 分页
        total = len(files)
        start = (page - 1) * page_size
        end = start + page_size
        page_files = files[start:end]

        return {
            "valid": True,
            "files": page_files,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取单个文件的详细信息

        Args:
            file_path: 相对于datadir的文件路径

        Returns:
            文件详细信息
        """
        if not self.datadir or not self.datadir.exists():
            return {"valid": False, "error": "datadir 不可用"}

        full_path = self.datadir / file_path
        if not full_path.exists() or not full_path.is_file():
            return {"valid": False, "error": f"文件不存在: {file_path}"}

        return self._get_file_info(full_path, file_path, detailed=True)

    def _get_file_info(self, file_path: Path, relative_path: str, detailed: bool = False) -> Dict[str, Any]:
        """获取文件信息"""
        stat = file_path.stat()

        info = {
            "name": file_path.name,
            "path": relative_path,
            "size": stat.st_size,
            "size_human": self._format_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "modified_timestamp": stat.st_mtime
        }

        if detailed:
            # 从路径解析股票代码
            stock_code = self._extract_stock_code(relative_path)
            if stock_code:
                info["stock_code"] = stock_code

            # 估算记录数
            record_count = self._estimate_record_count(file_path, relative_path)
            info["estimated_records"] = record_count

            # 文件类型判断
            info["file_type"] = self._detect_file_type(relative_path)

        return info

    def _count_period_files(self, market: str, period: str) -> int:
        """统计某周期下的文件数"""
        period_path = self.datadir / market / period
        if not period_path.exists() or not period_path.is_dir():
            return 0

        count = 0
        if period == "0":  # Tick数据
            for stock_dir in period_path.iterdir():
                if stock_dir.is_dir():
                    count += len(list(stock_dir.glob("*.dat")))
        else:
            count = len(list(period_path.glob("*.DAT")))

        return count

    def _extract_stock_code(self, file_path: str) -> Optional[str]:
        """从文件路径提取股票代码"""
        # 处理 Tick 数据格式: stock/YYYYMMDD.dat
        if "/" in file_path:
            parts = file_path.split("/")
            if len(parts) >= 2 and parts[0].isdigit() and len(parts[0]) == 6:
                return parts[0]

        # 处理K线数据格式: 000001.SZ.DAT
        name = Path(file_path).stem
        if "." in name and len(name.split(".")[0]) == 6:
            return name

        # 处理纯6位数字格式
        if len(name) == 6 and name.isdigit():
            return name

        return None

    def _estimate_record_count(self, file_path: Path, relative_path: str) -> int:
        """估算文件记录数"""
        file_size = file_path.stat().st_size
        if file_size == 0:
            return 0

        # 根据路径判断周期类型
        period = None
        parts = str(relative_path).replace("\\", "/").split("/")
        for i, part in enumerate(parts):
            if part in PERIOD_MAP:
                period = part
                break

        if not period:
            # 默认使用日线记录大小
            record_size = 36
        else:
            record_size = PERIOD_MAP[period].get("record_size", 40)

        return file_size // record_size

    def _detect_file_type(self, file_path: str) -> str:
        """检测文件类型"""
        parts = str(file_path).replace("\\", "/").split("/")

        # Tick数据
        if len(parts) >= 3 and parts[-3].isdigit() and len(parts[-3]) == 6:
            return "tick"

        # 检查周期代码
        for part in parts:
            if part in PERIOD_MAP:
                period_info = PERIOD_MAP[part]
                if part == "0":
                    return "tick"
                else:
                    return f"kline_{period_info['unit']}"

        return "unknown"

    def list_finance_types(self) -> List[Dict[str, Any]]:
        """
        列出所有财务数据类型及其文件统计

        Returns:
            财务数据类型列表，包含文件数量和总大小
        """
        if not self.datadir or not self.datadir.exists():
            return []

        qmt_root = self.datadir.parent
        finance_types: List[Dict[str, Any]] = []

        for type_code, type_info in FINANCE_TYPE_MAP.items():
            total_files = 0
            total_size = 0
            file_suffix = type_info["file_suffix"]

            # 扫描各市场目录下的财务数据文件
            for market_dir in self.datadir.iterdir():
                if not market_dir.is_dir():
                    continue
                market_code = market_dir.name
                if market_code not in MARKET_MAP:
                    continue

                # 查找匹配后缀的文件（如 _7001.DAT）
                pattern = f"*{file_suffix}"
                for dat_file in market_dir.glob(pattern):
                    if dat_file.is_file():
                        total_files += 1
                        total_size += dat_file.stat().st_size

            # 也扫描 finance 目录
            finance_dir = qmt_root / "finance"
            if finance_dir.exists():
                for dat_file in finance_dir.glob(f"*{file_suffix}"):
                    if dat_file.is_file():
                        total_files += 1
                        total_size += dat_file.stat().st_size

            finance_types.append({
                "code": type_code,
                "name": type_info["name"],
                "file_suffix": file_suffix,
                "files": total_files,
                "size": total_size,
                "size_human": self._format_size(total_size),
            })

        return finance_types

    def list_finance_files(
        self,
        finance_type: str,
        market: str,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        列出指定财务类型和市场的文件

        Args:
            finance_type: 财务类型代码 (7001-7008)
            market: 市场代码 (SH/SZ/BJ等)
            page: 页码
            page_size: 每页大小

        Returns:
            文件列表及分页信息
        """
        if not self.datadir or not self.datadir.exists():
            return {"valid": False, "error": "datadir 不可用"}

        if finance_type not in FINANCE_TYPE_MAP:
            return {"valid": False, "error": f"未知财务类型: {finance_type}"}

        file_suffix = FINANCE_TYPE_MAP[finance_type]["file_suffix"]
        files: List[Dict[str, Any]] = []

        # 在 datadir/{market}/ 下查找匹配后缀的文件
        market_path = self.datadir / market
        if market_path.exists() and market_path.is_dir():
            pattern = f"*{file_suffix}"
            for dat_file in market_path.glob(pattern):
                if dat_file.is_file():
                    file_info = self._get_file_info(dat_file, f"{market}/{dat_file.name}")
                    # 从文件名提取股票代码 (如 000001_7001.DAT -> 000001)
                    stem = dat_file.stem
                    stock_code = stem.replace(f"_{finance_type}", "")
                    file_info["stock_code"] = stock_code
                    file_info["finance_type"] = finance_type
                    files.append(file_info)

        # 也在 finance 目录查找
        qmt_root = self.datadir.parent
        finance_dir = qmt_root / "finance"
        if finance_dir.exists():
            for dat_file in finance_dir.glob(f"*{file_suffix}"):
                if dat_file.is_file():
                    file_info = self._get_file_info(dat_file, f"finance/{dat_file.name}")
                    stem = dat_file.stem
                    stock_code = stem.replace(f"_{finance_type}", "")
                    file_info["stock_code"] = stock_code
                    file_info["finance_type"] = finance_type
                    files.append(file_info)

        files.sort(key=lambda x: x["name"])

        total = len(files)
        start = (page - 1) * page_size
        end = start + page_size
        page_files = files[start:end]

        return {
            "valid": True,
            "files": page_files,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
            },
        }

    def list_tick_stocks(self, market: str) -> List[Dict[str, Any]]:
        """
        列出指定市场下有Tick分笔数据的股票代码

        Args:
            market: 市场代码

        Returns:
            股票代码列表，包含文件数量和大小
        """
        if not self.datadir or not self.datadir.exists():
            return []

        tick_path = self.datadir / market / "0"
        if not tick_path.exists() or not tick_path.is_dir():
            return []

        stocks: List[Dict[str, Any]] = []
        for stock_dir in tick_path.iterdir():
            if not stock_dir.is_dir():
                continue

            stock_code = stock_dir.name
            dat_files = list(stock_dir.glob("*.dat"))
            file_count = len(dat_files)
            total_size = sum(f.stat().st_size for f in dat_files if f.is_file())

            if file_count > 0:
                stocks.append({
                    "code": stock_code,
                    "market": market,
                    "files": file_count,
                    "size": total_size,
                    "size_human": self._format_size(total_size),
                })

        return sorted(stocks, key=lambda x: x["code"])

    def list_dividend_files(
        self,
        market: str,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        列出除权数据文件

        Args:
            market: 市场代码
            page: 页码
            page_size: 每页大小

        Returns:
            除权文件列表及分页信息
        """
        if not self.datadir or not self.datadir.exists():
            return {"valid": False, "error": "datadir 不可用"}

        qmt_root = self.datadir.parent

        # DividData 是 LevelDB 数据库目录
        dividend_dir = qmt_root / "DividData"
        if not dividend_dir.exists():
            return {
                "valid": True,
                "files": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                    "total_pages": 0,
                },
                "note": "DividData目录不存在",
            }

        files: List[Dict[str, Any]] = []

        # LevelDB 目录包含 .ldb, .log, .manifest 等文件
        for f in dividend_dir.iterdir():
            if f.is_file():
                stat_info = f.stat()
                files.append({
                    "name": f.name,
                    "path": f"DividData/{f.name}",
                    "size": stat_info.st_size,
                    "size_human": self._format_size(stat_info.st_size),
                    "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "modified_timestamp": stat_info.st_mtime,
                    "file_type": "leveldb",
                })

        # 也扫描 datadir 下可能的除权相关文件
        for suffix in ["*divid*", "*exright*", "*xr*"]:
            for f in self.datadir.rglob(suffix):
                if f.is_file():
                    stat_info = f.stat()
                    files.append({
                        "name": f.name,
                        "path": str(f.relative_to(self.datadir)),
                        "size": stat_info.st_size,
                        "size_human": self._format_size(stat_info.st_size),
                        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "modified_timestamp": stat_info.st_mtime,
                        "file_type": "dividend_data",
                    })

        files.sort(key=lambda x: x["name"])

        total = len(files)
        start = (page - 1) * page_size
        end = start + page_size
        page_files = files[start:end]

        return {
            "valid": True,
            "files": page_files,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
            },
        }

    def list_etf_codes(self, market: str) -> List[Dict[str, Any]]:
        """
        列出指定市场下有ETF申赎数据的代码

        Args:
            market: 市场代码

        Returns:
            ETF代码列表
        """
        if not self.datadir or not self.datadir.exists():
            return []

        qmt_root = self.datadir.parent
        etf_codes: List[Dict[str, Any]] = []

        # 尝试多种可能的ETF数据路径
        possible_paths = [
            self.datadir / market / "etf",
            self.datadir / market / "ETF",
            qmt_root / "etf" / market,
            qmt_root / "ETF" / market,
        ]

        scanned_dirs: List[Path] = []
        for etf_path in possible_paths:
            if etf_path.exists() and etf_path.is_dir():
                scanned_dirs.append(etf_path)

        # 如果没有专门的ETF目录，尝试在日线数据中识别ETF代码
        # ETF代码通常以 51xxxx(SH) 或 15xxxx(SZ) 开头
        if not scanned_dirs:
            daily_path = self.datadir / market / "86400"
            if daily_path.exists() and daily_path.is_dir():
                suffix = MARKET_MAP.get(market, {}).get("suffix", "")
                etf_prefixes = self._get_etf_prefixes(market)

                for dat_file in daily_path.glob("*.DAT"):
                    if not dat_file.is_file():
                        continue
                    stem = dat_file.stem
                    if any(stem.startswith(p) for p in etf_prefixes):
                        stat_info = dat_file.stat()
                        etf_codes.append({
                            "code": stem.replace(suffix, "") if suffix else stem,
                            "market": market,
                            "size": stat_info.st_size,
                            "size_human": self._format_size(stat_info.st_size),
                            "source": "daily_kline",
                        })

        # 扫描专门的ETF目录
        for etf_dir in scanned_dirs:
            for item in etf_dir.iterdir():
                if item.is_dir():
                    dat_files = list(item.glob("*.dat")) + list(item.glob("*.DAT"))
                    file_count = len(dat_files)
                    total_size = sum(f.stat().st_size for f in dat_files if f.is_file())
                    if file_count > 0:
                        etf_codes.append({
                            "code": item.name,
                            "market": market,
                            "files": file_count,
                            "size": total_size,
                            "size_human": self._format_size(total_size),
                            "source": "etf_directory",
                        })
                elif item.is_file():
                    stat_info = item.stat()
                    etf_codes.append({
                        "code": item.stem,
                        "market": market,
                        "size": stat_info.st_size,
                        "size_human": self._format_size(stat_info.st_size),
                        "source": "etf_directory",
                    })

        return sorted(etf_codes, key=lambda x: x["code"])

    def list_etf_files(
        self,
        market: str,
        etf_code: str,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        列出指定ETF的申赎清单文件

        Args:
            market: 市场代码
            etf_code: ETF代码
            page: 页码
            page_size: 每页大小

        Returns:
            ETF文件列表及分页信息
        """
        if not self.datadir or not self.datadir.exists():
            return {"valid": False, "error": "datadir 不可用"}

        qmt_root = self.datadir.parent
        files: List[Dict[str, Any]] = []

        # 搜索多种可能的路径
        possible_paths = [
            self.datadir / market / "etf" / etf_code,
            self.datadir / market / "ETF" / etf_code,
            qmt_root / "etf" / market / etf_code,
            qmt_root / "ETF" / market / etf_code,
        ]

        for etf_path in possible_paths:
            if etf_path.exists() and etf_path.is_dir():
                for dat_file in etf_path.iterdir():
                    if dat_file.is_file():
                        files.append(self._get_file_info(dat_file, str(dat_file.relative_to(self.datadir))))

        # 如果ETF数据在日线K线中
        if not files:
            suffix = MARKET_MAP.get(market, {}).get("suffix", "")
            daily_path = self.datadir / market / "86400"
            if daily_path.exists():
                target_name = f"{etf_code}{suffix}.DAT" if suffix else f"{etf_code}.DAT"
                target_file = daily_path / target_name
                if target_file.exists() and target_file.is_file():
                    files.append(self._get_file_info(target_file, f"{market}/86400/{target_name}"))

        files.sort(key=lambda x: x["name"])

        total = len(files)
        start = (page - 1) * page_size
        end = start + page_size
        page_files = files[start:end]

        return {
            "valid": True,
            "files": page_files,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
            },
        }

    def _get_etf_prefixes(self, market: str) -> List[str]:
        """获取指定市场的ETF代码前缀"""
        etf_prefix_map = {
            "SH": ["51", "56", "58", "59", "50"],  # 上交所ETF
            "SZ": ["15", "16"],                      # 深交所ETF
            "BJ": [],                                 # 北交所暂无ETF
        }
        return etf_prefix_map.get(market, [])

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def scan_other_files(self) -> Dict[str, Any]:
        """
        扫描其他QMT文件(财务、分红、节假日等)

        Returns:
            其他文件信息
        """
        if not self.datadir or not self.datadir.exists():
            return {"valid": False, "error": "datadir 不可用"}

        result = {
            "valid": True,
            "files": []
        }

        qmt_root = self.datadir.parent

        # 检查财务数据目录
        finance_dir = qmt_root / "finance"
        if finance_dir.exists():
            finance_files = []
            for dat_file in finance_dir.glob("*.DAT"):
                if dat_file.is_file():
                    file_info = {
                        "name": dat_file.name,
                        "path": f"finance/{dat_file.name}",
                        "size": dat_file.stat().st_size,
                        "size_human": self._format_size(dat_file.stat().st_size),
                        "type": "finance"
                    }
                    finance_files.append(file_info)

            result["files"].append({
                "category": "财务数据",
                "path": "finance/",
                "count": len(finance_files),
                        "items": finance_files
            })

        # 检查分红数据目录
        dividend_dir = qmt_root / "DividData"
        if dividend_dir.exists():
            result["files"].append({
                "category": "分红送股",
                "path": "DividData/",
                "count": "-",  # LevelDB数据库
                "type": "leveldb"
            })

        # 检查其他元数据文件
        metadata_files = []
        for filename in ["holiday.csv", "holiday.dat", "IndustryData.txt",
                         "sectorlist.DAT", "sectorWeightData.txt"]:
            metadata_path = qmt_root / filename
            if metadata_path.exists() and metadata_path.is_file():
                metadata_files.append({
                    "name": filename,
                    "size": metadata_path.stat().st_size,
                    "size_human": self._format_size(metadata_path.stat().st_size)
                })

        if metadata_files:
            result["files"].append({
                "category": "元数据文件",
                "items": metadata_files
            })

        return result

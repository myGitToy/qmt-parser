"""akshare (vendor) package shim

这是一个安全且规范的包初始化模板，旨在：
- 在导入时避免副作用（不进行网络/IO/长计算）
- 提供包版本（优先使用 importlib.metadata）
- 支持懒加载子模块（PEP 562）以减少初次导入开销
- 为类型检查器提供友好的导入点
"""

from __future__ import annotations

__all__ = ["__version__", "Error"]

# 轻量级 logger（不要在包导入时配置 handler 或改变级别）
import logging
logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING

# 版本信息优先尝试从安装元数据读取（importlib.metadata），失败回退到包内
try:
    from importlib import metadata as _importlib_metadata  # type: ignore
except Exception:
    _importlib_metadata = None  # type: ignore

__version__ = "0.0.0"  # 默认回退值
try:
    if _importlib_metadata is not None:
        # 如果该包通过 pip 安装，importlib.metadata 会找到真实版本
        __version__ = _importlib_metadata.version("akshare")
except Exception:
    # 回退到本地模块（如果存在 _version.py）
    try:
        from ._version import __version__ as _v  # type: ignore
        __version__ = _v
    except Exception:
        # 保持默认，不在导入时抛出错误
        pass

# 包级异常（可按需扩展）
class Error(Exception):
    """Base exception for akshare vendor package."""

# 懒加载映射：名字 -> 子模块路径
# 例如：{"stock": "apt.vendor.akshare.stock"}
_import_structure: dict[str, str] = {}

if TYPE_CHECKING:
    # 在静态类型检查时，你可以在这里导入类型，避免运行时开销
    # from .core import SomeClass  # type: ignore
    pass
else:
    import importlib

    def __getattr__(name: str):
        """实现按需导入：当访问未在模块 globals 中的名字时触发。

        如果 name 在 _import_structure 中，会导入对应子模块并返回模块或模块里的同名属性。
        否则抛出 AttributeError，符合 PEP 562。
        """
        if name in _import_structure:
            module_name = _import_structure[name]
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError as e:
                # 给出更友好的错误信息，提示缺失的可选依赖或子模块
                raise ModuleNotFoundError(
                    f"Optional dependency or submodule for '{name}' not available: {e}"
                ) from e
            if hasattr(module, name):
                value = getattr(module, name)
            else:
                # 如果子模块本身就是要导出的对象，直接返回模块
                value = module
            globals()[name] = value  # 缓存，避免重复导入
            if name not in __all__:
                __all__.append(name)
            return value
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    def __dir__():
        return sorted(list(globals().keys()) + list(_import_structure.keys()))

# 可选：若你希望将某些核心函数直接放到包顶层并且它们很轻量，可在此显式导入
# from .core import fetch_data as fetch_data
# __all__.append("fetch_data")

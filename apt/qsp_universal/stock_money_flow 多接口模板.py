"""
统一的资金流向适配器。

封装各数据供应商的资金流向接口，统一在量化选股系统中调用。
"""
from datetime import datetime
from typing import Any, Type

from apt.qsp_universal.base import base
from apt.vendor.akshare.money_flow import money_flow as ak_money_flow
from apt.vendor.tspro.money_flow import money_flow as ts_money_flow


class money_flow(base):
    def __init__(self, *, vendor: base.vendor = base.vendor.tusharePro, **kwargs):
        """简化版资金流向适配器，直接复用 `base` 的初始化参数。"""

        super().__init__(vendor=vendor, **kwargs)
        self._vendor_adapter = None

    def _resolve_vendor_cls(self) -> Type:
        if self.vendor == self.vendor.akshare:
            return ak_money_flow
        if self.vendor == self.vendor.tusharePro:
            return ts_money_flow
        raise ValueError(f"暂不支持的数据供应商: {self.vendor}")

    def _ensure_vendor_adapter(self):
        vendor_cls = self._resolve_vendor_cls()
        if self._vendor_adapter is None or not isinstance(self._vendor_adapter, vendor_cls):
            self._vendor_adapter = vendor_cls()
        self._sync_state_to_adapter(self._vendor_adapter)
        return self._vendor_adapter

    def _sync_state_to_adapter(self, adapter: Any) -> None:
        attrs = ["code", "start_date", "end_date", "ktype", "fq", "myauth", "server"]
        for attr in attrs:
            if hasattr(adapter, attr):
                setattr(adapter, attr, getattr(self, attr, None))

        for attr in ["engine", "pro"]:
            if hasattr(self, attr) and hasattr(adapter, attr):
                setattr(adapter, attr, getattr(self, attr))

    def _sync_state_from_adapter(self, adapter: Any) -> None:
        attrs = ["code", "start_date", "end_date", "ktype", "fq", "myauth", "server"]
        for attr in attrs:
            if hasattr(adapter, attr):
                setattr(self, attr, getattr(adapter, attr))

    def _delegate(self, method_name: str, *args, **kwargs):
        adapter = self._ensure_vendor_adapter()
        if not hasattr(adapter, method_name):
            raise NotImplementedError(
                f"{adapter.__class__.__name__} 不支持 {method_name} 方法，请确认供应商能力"
            )
        result = getattr(adapter, method_name)(*args, **kwargs)
        self._sync_state_from_adapter(adapter)
        return result

    def get_money_flow(self, *args, **kwargs):
        """获取资金流向数据。"""
        return self._delegate("get_money_flow", *args, **kwargs)

    def daily_update(self, *args, **kwargs):
        """按供应商规则执行每日更新。"""
        return self._delegate("daily_update", *args, **kwargs)

    def calculate_money_flow_min(self, *args, **kwargs):
        """基于分时数据计算资金流向，仅 akshare 支持。"""
        if self.vendor != self.vendor.akshare:
            raise ValueError("calculate_money_flow_min 仅支持 akshare 供应商")
        return self._delegate("calculate_money_flow_min", *args, **kwargs)

    def update_money_flow_min(self, *args, **kwargs):
        """更新分时资金流向，仅 akshare 支持。"""
        if self.vendor != self.vendor.akshare:
            raise ValueError("update_money_flow_min 仅支持 akshare 供应商")
        return self._delegate("update_money_flow_min", *args, **kwargs)

    def get_money_flow_1min(self, *args, **kwargs):
        """获取 1 分钟颗粒度的资金流向，仅 akshare 支持。"""
        if self.vendor != self.vendor.akshare:
            raise ValueError("get_money_flow_1min 仅支持 akshare 供应商")
        return self._delegate("get_money_flow_1min", *args, **kwargs)


if __name__ == "__main__":
    demo= money_flow()
    demo.vendor = base.vendor.akshare
    demo.start_date = datetime(2025,10,4)
    demo.end_date = datetime.now()
    demo.code = "688349.sh"
    df = demo.update_money_flow_min()
    print(df)
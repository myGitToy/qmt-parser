/**
 * 共享类型定义
 * 用于前后端类型契约
 */

/**
 * 实时行情报价
 */
export interface Quote {
    symbol: string;
    name?: string;
    price: number;
    change: number;
    change_pct: number;
    volume?: number;
    amount?: number;
    high?: number;
    low?: number;
    open?: number;
    close_prev?: number;
    timestamp: string;
    market?: string;
}

/**
 * K线数据
 */
export interface Bar {
    symbol: string;
    timeframe: string;
    datetime: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    amount?: number;
}

/**
 * 市场指数
 */
export interface MarketIndex {
    code: string;
    name: string;
    price: number;
    change: number;
    change_pct: number;
    volume?: number;
    amount?: number;
    timestamp: string;
}

/**
 * 市场概览
 */
export interface MarketOverview {
    indexes: MarketIndex[];
    market_status: string;
    timestamp: string;
}

/**
 * K线周期类型
 */
export type Timeframe =
    | "1min"
    | "5min"
    | "15min"
    | "30min"
    | "60min"
    | "daily"
    | "weekly"
    | "monthly";

/**
 * 持仓信息
 */
export interface Position {
    symbol: string;
    name: string;
    quantity: number;
    cost_price: number;
    current_price: number;
    market_value: number;
    pnl: number;
    pnl_pct: number;
}

/**
 * 组合概览
 */
export interface PortfolioSummary {
    total_asset: number;
    available_cash: number;
    position_value: number;
    today_pnl: number;
    today_pnl_pct: number;
}

/**
 * API 响应包装
 */
export interface ApiResponse<T> {
    data: T;
    success: boolean;
    message?: string;
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
}

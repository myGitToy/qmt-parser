/**
 * QMT API 客户端
 */

import client from "./client";

// ============================================================
// 数据类别枚举
// ============================================================

export type DataType = "kline" | "finance" | "dividend" | "tick" | "etf";

// ============================================================
// 基础类型定义
// ============================================================

export type QmtStatus = {
    qmt_client_path: string;
    datadir: string | null;
    valid: boolean;
    error: string | null;
};

export type MarketInfo = {
    code: string;
    name: string;
    short: string;
    suffix: string;
};

export type PeriodInfo = {
    code: string;
    name: string;
    unit: string;
    desc: string;
    files: number;
};

export type FileInfo = {
    name: string;
    path: string;
    size: number;
    size_human: string;
    modified: string;
    modified_timestamp: number;
    stock_code?: string;
    estimated_records?: number;
    file_type?: string;
    finance_type?: string;
};

export type QmtSummary = {
    valid: boolean;
    summary?: {
        total_markets: number;
        total_files: number;
        total_size: number;
        total_size_human: string;
        last_scan: string;
    };
    markets?: Array<{
        code: string;
        name: string;
        files: number;
        size: number;
        size_human: string;
        periods: Array<{
            code: string;
            name: string;
            files: number;
            size: number;
            size_human: string;
        }>;
    }>;
};

// ============================================================
// 财务数据类型
// ============================================================

export type FinanceTypeInfo = {
    code: string;
    name: string;
    file_suffix: string;
    files: number;
    size: number;
    size_human: string;
};

// ============================================================
// 分笔成交 (Tick) 股票信息
// ============================================================

export type TickStockInfo = {
    code: string;
    market: string;
    files: number;
    size: number;
    size_human: string;
};

// ============================================================
// ETF 信息
// ============================================================

export type EtfInfo = {
    code: string;
    market: string;
    files?: number;
    size: number;
    size_human: string;
    source: string;
};

// ============================================================
// 通用分页响应类型
// ============================================================

export type PaginatedResponse<T> = {
    valid: boolean;
    files: T[];
    pagination: {
        page: number;
        page_size: number;
        total: number;
        total_pages: number;
    };
    error?: string;
    note?: string;
};

// ============================================================
// API 方法
// ============================================================

export const qmtApi = {
    // 获取QMT状态
    getStatus: () => client.get<QmtStatus>("/qmt/status"),

    // 获取数据总览
    getSummary: () => client.get<QmtSummary>("/qmt/summary"),

    // 列出市场
    getMarkets: () => client.get<{ markets: MarketInfo[]; total: number }>("/qmt/markets"),

    // 列出周期
    getPeriods: (market: string) =>
        client.get<{ market: string; periods: PeriodInfo[]; total: number }>(
            `/qmt/markets/${market}/periods`
        ),

    // 列出K线文件（兼容现有逻辑）
    getFiles: (market: string, period: string, page = 1, pageSize = 100) =>
        client.get<PaginatedResponse<FileInfo>>(
            `/qmt/markets/${market}/periods/${period}/files`,
            { params: { page, page_size: pageSize } }
        ),

    // 获取文件详情
    getFileInfo: (path: string) =>
        client.get<FileInfo>("/qmt/file-info", { params: { path } }),

    // 获取其他文件
    getOtherFiles: () => client.get("/qmt/other-files"),

    // ============================================================
    // 财务数据 API
    // ============================================================

    // 列出财务数据类型
    getFinanceTypes: () =>
        client.get<{ types: FinanceTypeInfo[]; total: number }>("/qmt/finance/types"),

    // 列出财务文件
    getFinanceFiles: (financeType: string, market: string, page = 1, pageSize = 100) =>
        client.get<PaginatedResponse<FileInfo>>(
            `/qmt/finance/${financeType}/markets/${market}/files`,
            { params: { page, page_size: pageSize } }
        ),

    // ============================================================
    // 分笔成交 (Tick) API
    // ============================================================

    // 列出有Tick数据的股票
    getTickStocks: (market: string) =>
        client.get<{ market: string; stocks: TickStockInfo[]; total: number }>(
            `/qmt/tick/markets/${market}/stocks`
        ),

    // ============================================================
    // ETF申赎 API
    // ============================================================

    // 列出ETF代码
    getEtfCodes: (market: string) =>
        client.get<{ market: string; codes: EtfInfo[]; total: number }>(
            `/qmt/etf/markets/${market}/codes`
        ),

    // 列出ETF文件
    getEtfFiles: (market: string, code: string, page = 1, pageSize = 100) =>
        client.get<PaginatedResponse<FileInfo>>(
            `/qmt/etf/markets/${market}/codes/${code}/files`,
            { params: { page, page_size: pageSize } }
        ),

    // ============================================================
    // 除权数据 API
    // ============================================================

    // 列出除权文件
    getDividendFiles: (market: string, page = 1, pageSize = 100) =>
        client.get<PaginatedResponse<FileInfo>>(
            `/qmt/dividend/markets/${market}/files`,
            { params: { page, page_size: pageSize } }
        ),
};

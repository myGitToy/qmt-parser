/**
 * QMT API 客户端
 */

import client from "./client";

// 类型定义
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

    // 列出文件
    getFiles: (market: string, period: string, page = 1, pageSize = 100) =>
        client.get<{
            valid: boolean;
            files: FileInfo[];
            pagination: {
                page: number;
                page_size: number;
                total: number;
                total_pages: number;
            };
        }>(`/qmt/markets/${market}/periods/${period}/files`, {
            params: { page, page_size: pageSize },
        }),

    // 获取文件详情
    getFileInfo: (path: string) =>
        client.get<FileInfo>("/qmt/file-info", { params: { path } }),

    // 获取其他文件
    getOtherFiles: () => client.get("/qmt/other-files"),
};

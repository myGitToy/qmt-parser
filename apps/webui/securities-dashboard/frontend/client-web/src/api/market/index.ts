/**
 * 市场数据 API
 */

import client from "../client";
import type {
    Bar,
    MarketOverview,
    Quote,
    StockSearchResult,
    Timeframe,
} from "../../types/market";

/**
 * 获取市场概览
 */
export const getMarketOverview = (): Promise<MarketOverview> => {
    return client.get("/market/overview");
};

/**
 * 获取实时行情报价
 * @param symbol 股票代码
 */
export const getQuote = (symbol: string): Promise<Quote> => {
    return client.get(`/market/quote/${symbol}`);
};

/**
 * 批量获取实时行情报价
 * @param symbols 股票代码列表
 */
export const getBatchQuotes = (symbols: string[]): Promise<Quote[]> => {
    return client.post("/market/quote/batch", symbols);
};

/**
 * 获取历史K线数据
 * @param symbol 股票代码
 * @param timeframe K线周期
 * @param startDate 开始日期
 * @param endDate 结束日期
 * @param limit 返回条数限制
 */
export const getBars = (
    symbol: string,
    timeframe: Timeframe = "daily",
    startDate?: Date,
    endDate?: Date,
    limit = 1000
): Promise<Bar[]> => {
    const params: Record<string, string | number> = {
        symbol,
        timeframe,
        limit,
    };

    if (startDate) {
        params.start_date = startDate.toISOString();
    }
    if (endDate) {
        params.end_date = endDate.toISOString();
    }

    return client.get("/market/bars/" + symbol, { params });
};

/**
 * 获取市场主要指数
 */
export const getIndexes = (): Promise<Quote[]> => {
    return client.get("/market/indexes");
};

/**
 * 搜索股票
 * @param keyword 搜索关键词
 */
export const searchStocks = (keyword: string): Promise<StockSearchResult[]> => {
    return client.get("/market/search", { params: { keyword } });
};

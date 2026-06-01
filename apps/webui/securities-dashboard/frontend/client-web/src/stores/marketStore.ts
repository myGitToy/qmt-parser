/**
 * 市场数据状态管理
 * 使用 Zustand
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { MarketOverview, Quote, Bar, Timeframe } from "../types/market";

interface MarketState {
    // 市场概览
    marketOverview: MarketOverview | null;
    // 选中的股票
    selectedSymbol: string | null;
    // 当前K线周期
    currentTimeframe: Timeframe;
    // K线数据缓存
    barsCache: Map<string, Bar[]>;
    // 自选股列表
    watchlist: string[];

    // Actions
    setMarketOverview: (overview: MarketOverview) => void;
    setSelectedSymbol: (symbol: string | null) => void;
    setCurrentTimeframe: (timeframe: Timeframe) => void;
    setBars: (symbol: string, timeframe: Timeframe, bars: Bar[]) => void;
    getBars: (symbol: string, timeframe: Timeframe) => Bar[] | undefined;
    addToWatchlist: (symbol: string) => void;
    removeFromWatchlist: (symbol: string) => void;
}

export const useMarketStore = create<MarketState>()(
    devtools(
        (set, get) => ({
            // 初始状态
            marketOverview: null,
            selectedSymbol: null,
            currentTimeframe: "daily",
            barsCache: new Map(),
            watchlist: [],

            // Actions
            setMarketOverview: (overview) => set({ marketOverview: overview }),

            setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),

            setCurrentTimeframe: (timeframe) => set({ currentTimeframe: timeframe }),

            setBars: (symbol, timeframe, bars) =>
                set((state) => {
                    const cache = new Map(state.barsCache);
                    const key = `${symbol}_${timeframe}`;
                    cache.set(key, bars);
                    return { barsCache: cache };
                }),

            getBars: (symbol, timeframe) => {
                const key = `${symbol}_${timeframe}`;
                return get().barsCache.get(key);
            },

            addToWatchlist: (symbol) =>
                set((state) => ({
                    watchlist: state.watchlist.includes(symbol)
                        ? state.watchlist
                        : [...state.watchlist, symbol],
                })),

            removeFromWatchlist: (symbol) =>
                set((state) => ({
                    watchlist: state.watchlist.filter((s) => s !== symbol),
                })),
        }),
        { name: "MarketStore" }
    )
);

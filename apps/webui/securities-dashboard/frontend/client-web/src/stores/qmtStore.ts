/**
 * QMT 数据状态管理
 * 使用 Zustand
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { qmtApi, MarketInfo, PeriodInfo, FileInfo, QmtSummary, QmtStatus } from "../api/qmt";

interface QmtState {
    // 数据状态
    qmtStatus: QmtStatus | null;
    summary: QmtSummary | null;
    markets: MarketInfo[];
    periods: PeriodInfo[];
    files: FileInfo[];
    selectedMarket: string | null;
    selectedPeriod: string | null;
    selectedFile: FileInfo | null;
    pagination: {
        page: number;
        pageSize: number;
        total: number;
        totalPages: number;
    } | null;

    // 加载状态
    loading: boolean;
    error: string | null;

    // Actions
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;

    fetchStatus: () => Promise<void>;
    fetchSummary: () => Promise<void>;
    fetchMarkets: () => Promise<void>;
    fetchPeriods: (market: string) => Promise<void>;
    fetchFiles: (market: string, period: string, page?: number) => Promise<void>;
    fetchFileInfo: (filePath: string) => Promise<void>;

    selectMarket: (market: string) => void;
    selectPeriod: (period: string) => void;
    selectFile: (file: FileInfo) => void;
    clearSelection: () => void;
}

export const useQmtStore = create<QmtState>()(
    devtools(
        (set, get) => ({
            // 初始状态
            qmtStatus: null,
            summary: null,
            markets: [],
            periods: [],
            files: [],
            selectedMarket: null,
            selectedPeriod: null,
            selectedFile: null,
            pagination: null,
            loading: false,
            error: null,

            // Actions
            setLoading: (loading) => set({ loading }),
            setError: (error) => set({ error }),

            fetchStatus: async () => {
                set({ loading: true, error: null });
                try {
                    const status = await qmtApi.getStatus();
                    set({ qmtStatus: status, loading: false });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取QMT状态失败",
                        loading: false,
                    });
                }
            },

            fetchSummary: async () => {
                set({ loading: true, error: null });
                try {
                    const summary = await qmtApi.getSummary();
                    set({ summary, loading: false });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取数据总览失败",
                        loading: false,
                    });
                }
            },

            fetchMarkets: async () => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getMarkets();
                    set({ markets: response.markets, loading: false });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取市场列表失败",
                        loading: false,
                    });
                }
            },

            fetchPeriods: async (market: string) => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getPeriods(market);
                    set({ periods: response.periods, loading: false });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取周期列表失败",
                        loading: false,
                    });
                }
            },

            fetchFiles: async (market: string, period: string, page = 1) => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getFiles(market, period, page, 100);
                    set({
                        files: response.files,
                        pagination: response.pagination,
                        loading: false,
                    });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取文件列表失败",
                        loading: false,
                    });
                }
            },

            fetchFileInfo: async (filePath: string) => {
                set({ loading: true, error: null });
                try {
                    const fileInfo = await qmtApi.getFileInfo(filePath);
                    set({ selectedFile: fileInfo, loading: false });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取文件详情失败",
                        loading: false,
                    });
                }
            },

            selectMarket: (market: string) => {
                set({ selectedMarket: market, selectedPeriod: null, files: [], pagination: null });
                get().fetchPeriods(market);
            },

            selectPeriod: (period: string) => {
                set({ selectedPeriod: period, files: [], pagination: null });
                const { selectedMarket } = get();
                if (selectedMarket) {
                    get().fetchFiles(selectedMarket, period);
                }
            },

            selectFile: (file: FileInfo) => {
                set({ selectedFile: file });
            },

            clearSelection: () => {
                set({
                    selectedMarket: null,
                    selectedPeriod: null,
                    selectedFile: null,
                    files: [],
                    pagination: null,
                });
            },
        }),
        { name: "QmtStore" }
    )
);

/**
 * QMT 数据状态管理
 * 使用 Zustand
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { qmtApi } from "../api/qmt";
import type {
    DataType,
    MarketInfo,
    PeriodInfo,
    FileInfo,
    QmtSummary,
    QmtStatus,
    FinanceTypeInfo,
    TickStockInfo,
    EtfInfo,
    SectorCategory,
    SectorFileInfo,
} from "../api/qmt";

interface QmtState {
    // === 基础状态 ===
    qmtStatus: QmtStatus | null;
    summary: QmtSummary | null;
    markets: MarketInfo[];
    loading: boolean;
    error: string | null;

    // === 数据类别 ===
    activeDataType: DataType;

    // === K线数据 ===
    periods: PeriodInfo[];
    selectedMarket: string | null;
    selectedPeriod: string | null;

    // === 财务数据 ===
    financeTypes: FinanceTypeInfo[];
    selectedFinanceType: string | null;

    // === 分笔成交 ===
    tickStocks: TickStockInfo[];
    selectedTickStock: string | null;

    // === ETF申赎 ===
    etfList: EtfInfo[];
    selectedEtf: string | null;

    // === 板块分类 ===
    sectorCategories: SectorCategory[];
    sectorFiles: SectorFileInfo[];
    selectedSectorCategory: string | null;

    // === 通用文件列表 ===
    files: FileInfo[];
    selectedFile: FileInfo | null;
    pagination: {
        page: number;
        page_size: number;
        total: number;
        total_pages: number;
    } | null;

    // === Actions ===
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;

    // 基础数据
    fetchStatus: () => Promise<void>;
    fetchSummary: () => Promise<void>;
    fetchMarkets: () => Promise<void>;

    // 数据类别切换
    setActiveDataType: (type: DataType) => void;

    // K线数据
    fetchPeriods: (market: string) => Promise<void>;
    fetchFiles: (market: string, period: string, page?: number) => Promise<void>;
    selectMarket: (market: string) => void;
    selectPeriod: (period: string) => void;

    // 财务数据
    fetchFinanceTypes: () => Promise<void>;
    fetchFinanceFiles: (type: string, market: string, page?: number) => Promise<void>;
    selectFinanceType: (type: string) => void;

    // 分笔成交
    fetchTickStocks: (market: string) => Promise<void>;
    fetchTickFiles: (market: string, stock: string, page?: number) => Promise<void>;
    selectTickStock: (stock: string) => void;

    // ETF申赎
    fetchEtfList: (market: string) => Promise<void>;
    fetchEtfFiles: (market: string, etfCode: string, page?: number) => Promise<void>;
    selectEtf: (etf: string) => void;

    // 除权数据
    fetchDividendFiles: (market: string, page?: number) => Promise<void>;

    // 板块分类
    fetchSectorCategories: () => Promise<void>;
    fetchSectorFiles: (category: string, page?: number) => Promise<void>;
    selectSectorCategory: (category: string) => void;

    // 通用
    selectFile: (file: FileInfo) => void;
    clearSelection: () => void;
}

export const useQmtStore = create<QmtState>()(
    devtools(
        (set, get) => ({
            // === 初始状态 ===
            qmtStatus: null,
            summary: null,
            markets: [],
            loading: false,
            error: null,

            activeDataType: "kline" as DataType,

            periods: [],
            selectedMarket: null,
            selectedPeriod: null,

            financeTypes: [],
            selectedFinanceType: null,

            tickStocks: [],
            selectedTickStock: null,

            etfList: [],
            selectedEtf: null,

            sectorCategories: [],
            sectorFiles: [],
            selectedSectorCategory: null,

            files: [],
            selectedFile: null,
            pagination: null,

            // === Actions ===
            setLoading: (loading) => set({ loading }),
            setError: (error) => set({ error }),

            // --- 基础数据 ---
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

            // --- 数据类别切换 ---
            setActiveDataType: (type: DataType) => {
                set({
                    activeDataType: type,
                    files: [],
                    pagination: null,
                    error: null,
                });
            },

            // --- K线数据 ---
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

            // --- 财务数据 ---
            fetchFinanceTypes: async () => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getFinanceTypes();
                    set({ financeTypes: response.types, loading: false });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取财务类型列表失败",
                        loading: false,
                    });
                }
            },

            fetchFinanceFiles: async (type: string, market: string, page = 1) => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getFinanceFiles(type, market, page, 100);
                    set({
                        files: response.files,
                        pagination: response.pagination,
                        loading: false,
                    });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取财务文件列表失败",
                        loading: false,
                    });
                }
            },

            selectFinanceType: (type: string) => {
                set({ selectedFinanceType: type, files: [], pagination: null });
            },

            // --- 分笔成交 ---
            fetchTickStocks: async (market: string) => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getTickStocks(market);
                    set({ tickStocks: response.stocks, loading: false });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取分笔成交股票列表失败",
                        loading: false,
                    });
                }
            },

            fetchTickFiles: async (market: string, stock: string, page = 1) => {
                set({ loading: true, error: null });
                try {
                    // Tick数据使用 period=0 的现有API
                    const response = await qmtApi.getFiles(market, "0", page, 100);
                    // 过滤出指定股票的文件
                    const filtered = response.files.filter(
                        (f) => f.path.startsWith(stock) || f.stock_code === stock
                    );
                    set({
                        files: filtered,
                        pagination: {
                            ...response.pagination,
                            total: filtered.length,
                            total_pages: Math.max(1, Math.ceil(filtered.length / 100)),
                        },
                        loading: false,
                    });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取分笔成交文件列表失败",
                        loading: false,
                    });
                }
            },

            selectTickStock: (stock: string) => {
                set({ selectedTickStock: stock, files: [], pagination: null });
            },

            // --- ETF申赎 ---
            fetchEtfList: async (market: string) => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getEtfCodes(market);
                    set({ etfList: response.codes, loading: false });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取ETF列表失败",
                        loading: false,
                    });
                }
            },

            fetchEtfFiles: async (market: string, etfCode: string, page = 1) => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getEtfFiles(market, etfCode, page, 100);
                    set({
                        files: response.files,
                        pagination: response.pagination,
                        loading: false,
                    });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取ETF文件列表失败",
                        loading: false,
                    });
                }
            },

            selectEtf: (etf: string) => {
                set({ selectedEtf: etf, files: [], pagination: null });
            },

            // --- 除权数据 ---
            fetchDividendFiles: async (market: string, page = 1) => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getDividendFiles(market, page, 100);
                    set({
                        files: response.files,
                        pagination: response.pagination,
                        loading: false,
                    });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取除权文件列表失败",
                        loading: false,
                    });
                }
            },

            // --- 板块分类 ---
            fetchSectorCategories: async () => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getSectorCategories();
                    set({ sectorCategories: response.categories, loading: false });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取板块分类列表失败",
                        loading: false,
                    });
                }
            },

            fetchSectorFiles: async (category: string, page = 1) => {
                set({ loading: true, error: null });
                try {
                    const response = await qmtApi.getSectorFiles(category, page, 100);
                    set({
                        sectorFiles: response.files,
                        files: response.files.map((f) => ({
                            name: f.name,
                            path: f.path,
                            size: f.size,
                            size_human: f.size_human,
                            modified: f.modified,
                            modified_timestamp: f.modified_timestamp,
                            stock_count: f.stock_count,
                            category: f.category,
                        })),
                        pagination: response.pagination,
                        loading: false,
                    });
                } catch (error: any) {
                    set({
                        error: error?.userMessage || "获取板块文件列表失败",
                        loading: false,
                    });
                }
            },

            selectSectorCategory: (category: string) => {
                set({ selectedSectorCategory: category, files: [], pagination: null });
            },

            // --- 通用 ---
            selectFile: (file: FileInfo) => {
                set({ selectedFile: file });
            },

            clearSelection: () => {
                set({
                    selectedMarket: null,
                    selectedPeriod: null,
                    selectedFinanceType: null,
                    selectedTickStock: null,
                    selectedEtf: null,
                    selectedSectorCategory: null,
                    selectedFile: null,
                    files: [],
                    sectorFiles: [],
                    pagination: null,
                });
            },
        }),
        { name: "QmtStore" }
    )
);

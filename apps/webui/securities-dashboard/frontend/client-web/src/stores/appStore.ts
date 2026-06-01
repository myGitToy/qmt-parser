/**
 * 应用全局状态管理
 * 使用 Zustand
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";

interface AppState {
    // 侧边栏状态
    sidebarCollapsed: boolean;
    // 全局加载状态
    isLoading: boolean;
    // 错误消息
    errorMessage: string | null;
    // 功能树选中的功能
    selectedFunction: string | null;

    // Actions
    setSidebarCollapsed: (collapsed: boolean) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    setSelectedFunction: (func: string | null) => void;
}

export const useAppStore = create<AppState>()(
    devtools(
        (set) => ({
            // 初始状态
            sidebarCollapsed: false,
            isLoading: false,
            errorMessage: null,
            selectedFunction: null,

            // Actions
            setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
            setLoading: (loading) => set({ isLoading: loading }),
            setError: (error) => set({ errorMessage: error }),
            setSelectedFunction: (func) => set({ selectedFunction: func }),
        }),
        { name: "AppStore" }
    )
);

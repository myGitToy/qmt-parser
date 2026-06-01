/**
 * 暗色主题配置
 * 参考彭博终端和同花顺的配色方案
 */

import { theme } from "antd";

const { defaultAlgorithm } = theme;

// 颜色常量
export const colors = {
    // 主背景色
    background: "#0d1117",
    // 次级背景色（面板、卡片）
    backgroundSecondary: "#161b22",
    // 边框颜色
    border: "#30363d",
    // 文字主色
    textPrimary: "#c9d1d9",
    // 文字次色
    textSecondary: "#8b949e",
    // 涨（红）
    up: "#f85149",
    // 跌（绿）
    down: "#3fb950",
    // 强调色
    primary: "#58a6ff",
    // 警告色
    warning: "#d29922",
    // 错误色
    error: "#f85149",
    // 成功色
    success: "#3fb950",
};

// Ant Design 暗色主题配置
export const darkTheme = {
    algorithm: theme.darkAlgorithm,
    token: {
        // 主色调
        colorPrimary: colors.primary,
        colorSuccess: colors.success,
        colorWarning: colors.warning,
        colorError: colors.error,
        colorInfo: colors.primary,

        // 背景色
        colorBgBase: colors.background,
        colorBgContainer: colors.backgroundSecondary,
        colorBgElevated: colors.backgroundSecondary,
        colorBgLayout: colors.background,

        // 边框色
        colorBorder: colors.border,
        colorBorderSecondary: colors.border,

        // 文字色
        colorText: colors.textPrimary,
        colorTextSecondary: colors.textSecondary,
        colorTextTertiary: colors.textSecondary,
        colorTextQuaternary: colors.textSecondary,

        // 分割线
        colorSplit: colors.border,

        // 其他
        borderRadius: 4,
        fontSize: 14,
        fontSizeHeading1: 24,
        fontSizeHeading2: 20,
        fontSizeHeading3: 16,
    },
    components: {
        // 组件级别的主题覆盖
        Layout: {
            headerBg: colors.background,
            headerHeight: 48,
            siderBg: colors.background,
            bodyBg: colors.background,
        },
        Menu: {
            darkItemBg: colors.background,
            darkItemSelectedBg: colors.backgroundSecondary,
            darkItemHoverBg: colors.backgroundSecondary,
        },
        Table: {
            headerBg: colors.background,
            headerColor: colors.textPrimary,
            rowHoverBg: colors.backgroundSecondary,
            borderColor: colors.border,
        },
        Card: {
            backgroundColor: colors.backgroundSecondary,
            borderColor: colors.border,
        },
        Input: {
            colorBgContainer: colors.backgroundSecondary,
            colorBorder: colors.border,
            colorText: colors.textPrimary,
        },
        Select: {
            colorBgContainer: colors.backgroundSecondary,
            colorBorder: colors.border,
            optionSelectedBg: colors.backgroundSecondary,
        },
    },
};

// 获取涨跌颜色
export const getColorByChange = (value: number): string => {
    if (value > 0) return colors.up;
    if (value < 0) return colors.down;
    return colors.textPrimary;
};

// 获取涨跌符号
export const getArrowByChange = (value: number): string => {
    if (value > 0) return "▲";
    if (value < 0) return "▼";
    return "-";
};

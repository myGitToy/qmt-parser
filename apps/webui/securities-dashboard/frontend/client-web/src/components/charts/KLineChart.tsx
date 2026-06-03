/**
 * K线图组件
 * 使用 TradingView Lightweight Charts
 */

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType } from "lightweight-charts";
import type { Bar } from "../../types/market";

// 使用类型推断替代直接导入类型（lightweight-charts v5.x 不再导出这些类型）
type ChartApi = ReturnType<typeof createChart>;
type SeriesApi = ReturnType<ChartApi["addCandlestickSeries"]>;

interface KLineChartProps {
    symbol: string;
    bars: Bar[];
    height?: number;
}

export const KLineChart = ({ symbol, bars, height = 400 }: KLineChartProps) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<ChartApi | null>(null);
    const seriesRef = useRef<SeriesApi | null>(null);
    const [chartReady, setChartReady] = useState(false);

    // 初始化图表
    useEffect(() => {
        if (!chartContainerRef.current) return;

        // 创建图表实例
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: height,
            layout: {
                background: { type: ColorType.Solid, color: "#0d1117" },
                textColor: "#c9d1d9",
            },
            grid: {
                vertLines: { color: "#161b22" },
                horzLines: { color: "#161b22" },
            },
            crosshair: {
                mode: 1,
            },
            rightPriceScale: {
                borderColor: "#30363d",
            },
            timeScale: {
                borderColor: "#30363d",
                timeVisible: true,
                secondsVisible: false,
            },
        });

        // 创建K线系列
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: "#f85149", // 涨（红）
            downColor: "#3fb950", // 跌（绿）
            borderVisible: false,
            wickUpColor: "#f85149",
            wickDownColor: "#3fb950",
        });

        chartRef.current = chart;
        seriesRef.current = candlestickSeries;
        setChartReady(true);

        // 响应窗口大小变化
        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                });
            }
        };

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.remove();
        };
    }, [height]);

    // 更新数据
    useEffect(() => {
        if (!chartReady || !seriesRef.current || !bars.length) return;

        // 转换数据格式
        const data = bars.map((bar) => ({
            time: (new Date(bar.datetime).getTime() / 1000) as any,
            open: bar.open,
            high: bar.high,
            low: bar.low,
            close: bar.close,
        }));

        seriesRef.current.setData(data);

        // 自动调整视图
        if (chartRef.current) {
            chartRef.current.timeScale().fitContent();
        }
    }, [bars, chartReady]);

    return (
        <div
            ref={chartContainerRef}
            style={{
                width: "100%",
                height: `${height}px`,
                background: "#0d1117",
                borderRadius: "4px",
            }}
        />
    );
};

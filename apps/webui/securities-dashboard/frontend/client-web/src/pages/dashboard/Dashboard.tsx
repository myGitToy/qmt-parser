/**
 * 主看板页面
 */

import { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, Input } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { KLineChart } from "../../components/charts/KLineChart";
import { QuoteTable } from "../../components/grids/QuoteTable";
import { getMarketOverview, getBars, getQuote } from "../../api/market";
import { useMarketStore } from "../../stores/marketStore";
import type { Quote, Bar } from "../../types/market";
import { darkTheme, getColorByChange, getArrowByChange } from "../../theme/darkTheme";

export const Dashboard = () => {
    const { marketOverview, setMarketOverview, selectedSymbol, setSelectedSymbol, setBars } =
        useMarketStore();

    const [loading, setLoading] = useState(true);
    const [bars, setLocalBars] = useState<Bar[]>([]);
    const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null);
    const [searchValue, setSearchValue] = useState("");

    // 加载市场概览
    useEffect(() => {
        loadMarketOverview();

        // 每30秒刷新一次
        const interval = setInterval(loadMarketOverview, 30000);
        return () => clearInterval(interval);
    }, []);

    // 加载K线数据
    useEffect(() => {
        if (selectedSymbol) {
            loadBars(selectedSymbol);
        }
    }, [selectedSymbol]);

    const loadMarketOverview = async () => {
        try {
            const data = await getMarketOverview();
            setMarketOverview(data);
        } catch (error) {
            console.error("加载市场概览失败:", error);
        } finally {
            setLoading(false);
        }
    };

    const loadBars = async (symbol: string) => {
        try {
            // 获取最近一年的日线数据
            const endDate = new Date();
            const startDate = new Date();
            startDate.setFullYear(startDate.getFullYear() - 1);

            const data = await getBars(symbol, "daily", startDate, endDate);
            setLocalBars(data);
            setBars(symbol, "daily", data);

            // 获取实时报价
            const quote = await getQuote(symbol);
            setSelectedQuote(quote);
        } catch (error) {
            console.error("加载K线数据失败:", error);
        }
    };

    const handleQuoteClick = (quote: Quote) => {
        setSelectedSymbol(quote.symbol);
    };

    const handleSearch = async () => {
        if (searchValue.trim()) {
            setSelectedSymbol(searchValue.trim());
        }
    };

    return (
        <div style={{ height: "100%", overflow: "auto" }}>
            {/* 市场指数概览 */}
            <Row gutter={[8, 8]} style={{ marginBottom: 8 }}>
                {marketOverview?.indexes.map((index) => (
                    <Col key={index.code} span={4}>
                        <Card
                            size="small"
                            style={{
                                background: darkTheme.token.colorBgContainer,
                                borderColor: darkTheme.token.colorBorder,
                            }}
                            bodyStyle={{ padding: "8px 12px" }}
                        >
                            <Statistic
                                title={index.name}
                                value={index.price}
                                precision={2}
                                valueStyle={{
                                    fontSize: 18,
                                    color: getColorByChange(index.change),
                                    fontWeight: "bold",
                                }}
                                suffix={
                                    <span style={{ fontSize: 12 }}>
                                        {getArrowByChange(index.change)}
                                        {Math.abs(index.change_pct).toFixed(2)}%
                                    </span>
                                }
                            />
                        </Card>
                    </Col>
                ))}
            </Row>

            {/* K线图表区域 */}
            <Row gutter={[8, 8]} style={{ marginBottom: 8 }}>
                <Col span={16}>
                    <Card
                        size="small"
                        title={
                            <Input
                                placeholder="输入股票代码 (如: 000001.SZ)"
                                value={selectedSymbol || searchValue}
                                onChange={(e) => setSearchValue(e.target.value)}
                                onPressEnter={handleSearch}
                                suffix={<SearchOutlined onClick={handleSearch} style={{ cursor: "pointer" }} />}
                                style={{ width: 200 }}
                                size="small"
                            />
                        }
                        extra={selectedQuote ? (
                            <span style={{ fontSize: 12 }}>
                                <span style={{ marginRight: 8 }}>
                                    {selectedQuote.name || selectedQuote.symbol}
                                </span>
                                <span style={{ color: getColorByChange(selectedQuote.change), fontWeight: "bold" }}>
                                    {selectedQuote.price.toFixed(2)}
                                </span>
                                <span style={{ marginLeft: 8, color: getColorByChange(selectedQuote.change) }}>
                                    {getArrowByChange(selectedQuote.change)}
                                    {selectedQuote.change > 0 ? "+" : ""}{selectedQuote.change.toFixed(2)}
                                    ({selectedQuote.change_pct > 0 ? "+" : ""}{selectedQuote.change_pct.toFixed(2)}%)
                                </span>
                            </span>
                        ) : null}
                        style={{
                            background: darkTheme.token.colorBgContainer,
                            borderColor: darkTheme.token.colorBorder,
                        }}
                        bodyStyle={{ padding: 8 }}
                    >
                        <KLineChart symbol={selectedSymbol || ""} bars={bars} height={400} />
                    </Card>
                </Col>

                {/* 自选股列表 */}
                <Col span={8}>
                    <Card
                        size="small"
                        title="自选股"
                        style={{
                            background: darkTheme.token.colorBgContainer,
                            borderColor: darkTheme.token.colorBorder,
                        }}
                        bodyStyle={{ padding: 8 }}
                    >
                        <QuoteTable
                            quotes={marketOverview?.indexes.map((idx, i) => ({
                                symbol: idx.code,
                                name: idx.name,
                                price: idx.price,
                                change: idx.change,
                                change_pct: idx.change_pct,
                                timestamp: idx.timestamp,
                            })) || []}
                            loading={loading}
                            onRowClick={handleQuoteClick}
                        />
                    </Card>
                </Col>
            </Row>

            {/* 实时行情表格 */}
            <Row>
                <Col span={24}>
                    <Card
                        size="small"
                        title="市场行情"
                        style={{
                            background: darkTheme.token.colorBgContainer,
                            borderColor: darkTheme.token.colorBorder,
                        }}
                        bodyStyle={{ padding: 8 }}
                    >
                        <QuoteTable
                            quotes={marketOverview?.indexes.map((idx, i) => ({
                                symbol: idx.code,
                                name: idx.name,
                                price: idx.price,
                                change: idx.change,
                                change_pct: idx.change_pct,
                                timestamp: idx.timestamp,
                            })) || []}
                            loading={loading}
                            onRowClick={handleQuoteClick}
                        />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

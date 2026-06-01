/**
 * 市场数据测试页面
 * 用于测试后端 API 接口
 */

import { useState } from "react";
import { Card, Row, Col, Statistic, Table, Button, Input, Spin, Alert } from "antd";
import { ReloadOutlined, SearchOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { getMarketOverview, getQuote, getBars, getIndexes, searchStocks } from "../api/market";
import type { MarketOverview, Quote, Bar } from "../types/market";
import { darkTheme, getColorByChange, getArrowByChange } from "../theme/darkTheme";

export const MarketTest = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 市场概览数据
    const [overview, setOverview] = useState<MarketOverview | null>(null);

    // K线数据
    const [symbol, setSymbol] = useState("000001.SZ");
    const [bars, setBars] = useState<Bar[]>([]);
    const [quote, setQuote] = useState<Quote | null>(null);

    // 搜索结果
    const [searchKeyword, setSearchKeyword] = useState("");
    const [searchResults, setSearchResults] = useState<any[]>([]);

    // 加载市场概览
    const loadMarketOverview = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getMarketOverview();
            setOverview(data);
        } catch (err: any) {
            setError(`加载市场概览失败: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // 加载K线数据
    const loadBars = async () => {
        setLoading(true);
        setError(null);
        try {
            const endDate = new Date();
            const startDate = new Date();
            startDate.setFullYear(startDate.getFullYear() - 1);

            const data = await getBars(symbol, "daily", startDate, endDate);
            setBars(data);
        } catch (err: any) {
            setError(`加载K线数据失败: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // 加载实时行情
    const loadQuote = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getQuote(symbol);
            setQuote(data);
        } catch (err: any) {
            setError(`加载实时行情失败: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // 搜索股票
    const handleSearch = async () => {
        if (!searchKeyword.trim()) return;

        setLoading(true);
        setError(null);
        try {
            const results = await searchStocks(searchKeyword);
            setSearchResults(results);
        } catch (err: any) {
            setError(`搜索失败: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // 指数表格列定义
    const indexColumns: ColumnsType<any> = [
        {
            title: "代码",
            dataIndex: "code",
            key: "code",
            width: 100,
        },
        {
            title: "名称",
            dataIndex: "name",
            key: "name",
            width: 100,
        },
        {
            title: "点位",
            dataIndex: "price",
            key: "price",
            width: 100,
            align: "right",
            render: (value) => value?.toFixed(2) || "-",
        },
        {
            title: "涨跌",
            dataIndex: "change",
            key: "change",
            width: 80,
            align: "right",
            render: (value) => {
                const color = getColorByChange(value);
                return <span style={{ color }}>{value?.toFixed(2) || "-"}</span>;
            },
        },
        {
            title: "涨跌幅",
            dataIndex: "change_pct",
            key: "change_pct",
            width: 80,
            align: "right",
            render: (value) => {
                const color = getColorByChange(value);
                return <span style={{ color }}>{value?.toFixed(2) || "-"}%</span>;
            },
        },
    ];

    // 搜索结果表格列定义
    const searchColumns: ColumnsType<any> = [
        {
            title: "代码",
            dataIndex: "code",
            key: "code",
            width: 120,
        },
        {
            title: "名称",
            dataIndex: "name",
            key: "name",
            width: 150,
        },
        {
            title: "市场",
            dataIndex: "market",
            key: "market",
            width: 60,
        },
        {
            title: "操作",
            key: "action",
            width: 80,
            render: (_, record) => (
                <Button
                    size="small"
                    onClick={() => {
                        setSymbol(record.code);
                        loadBars();
                        loadQuote();
                    }}
                >
                    查看K线
                </Button>
            ),
        },
    ];

    return (
        <div style={{ padding: 16, background: darkTheme.token.colorBgBase, minHeight: "100vh" }}>
            <h1 style={{ color: darkTheme.token.colorTextPrimary }}>市场数据测试</h1>

            {error && (
                <Alert
                    message="错误"
                    description={error}
                    type="error"
                    closable
                    style={{ marginBottom: 16 }}
                />
            )}

            <Spin spinning={loading}>
                {/* API 测试按钮 */}
                <Card
                    size="small"
                    title="API 测试"
                    style={{ marginBottom: 16, background: darkTheme.token.colorBgContainer }}
                >
                    <Row gutter={[16, 16]}>
                        <Col>
                            <Button
                                type="primary"
                                icon={<ReloadOutlined />}
                                onClick={loadMarketOverview}
                            >
                                加载市场概览
                            </Button>
                        </Col>
                    </Row>
                </Card>

                {/* 市场概览 */}
                {overview && (
                    <Card
                        size="small"
                        title="市场概览"
                        style={{ marginBottom: 16, background: darkTheme.token.colorBgContainer }}
                    >
                        <Row gutter={[16, 16]}>
                            {overview.indexes.map((idx) => (
                                <Col key={idx.code} span={4}>
                                    <Statistic
                                        title={idx.name}
                                        value={idx.price}
                                        precision={2}
                                        valueStyle={{
                                            fontSize: 18,
                                            color: getColorByChange(idx.change),
                                            fontWeight: "bold",
                                        }}
                                        suffix={
                                            <span style={{ fontSize: 12 }}>
                                                {getArrowByChange(idx.change)}
                                                {Math.abs(idx.change_pct).toFixed(2)}%
                                            </span>
                                        }
                                    />
                                </Col>
                            ))}
                        </Row>
                        <div style={{ marginTop: 8, color: darkTheme.token.colorTextSecondary }}>
                            市场状态: {overview.market_status} | 更新时间: {new Date(overview.timestamp).toLocaleString()}
                        </div>
                    </Card>
                )}

                {/* 股票查询 */}
                <Card
                    size="small"
                    title="股票查询"
                    style={{ marginBottom: 16, background: darkTheme.token.colorBgContainer }}
                >
                    <Row gutter={[16, 16]} align="middle">
                        <Col flex="200px">
                            <Input
                                placeholder="股票代码 (如: 000001.SZ)"
                                value={symbol}
                                onChange={(e) => setSymbol(e.target.value)}
                            />
                        </Col>
                        <Col>
                            <Button onClick={() => { loadBars(); loadQuote(); }}>
                                查询K线
                            </Button>
                        </Col>
                    </Row>

                    {quote && (
                        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                            <Col span={6}>
                                <Statistic
                                    title="最新价"
                                    value={quote.price}
                                    precision={2}
                                    valueStyle={{ color: getColorByChange(quote.change) }}
                                />
                            </Col>
                            <Col span={6}>
                                <Statistic
                                    title="涨跌额"
                                    value={quote.change}
                                    precision={2}
                                    valueStyle={{ color: getColorByChange(quote.change) }}
                                />
                            </Col>
                            <Col span={6}>
                                <Statistic
                                    title="涨跌幅"
                                    value={quote.change_pct}
                                    precision={2}
                                    suffix="%"
                                    valueStyle={{ color: getColorByChange(quote.change_pct) }}
                                />
                            </Col>
                            <Col span={6}>
                                <Statistic
                                    title="成交量"
                                    value={quote.volume}
                                    formatter={(value) => {
                                        if (!value) return "-";
                                        if (value >= 100000000) {
                                            return `${(value / 100000000).toFixed(2)}亿`;
                                        } else if (value >= 10000) {
                                            return `${(value / 10000).toFixed(2)}万`;
                                        }
                                        return value.toLocaleString();
                                    }}
                                />
                            </Col>
                        </Row>
                    )}
                </Card>

                {/* K线数据表格 */}
                {bars.length > 0 && (
                    <Card
                        size="small"
                        title={`K线数据 (${bars.length} 条)`}
                        style={{ marginBottom: 16, background: darkTheme.token.colorBgContainer }}
                    >
                        <Table
                            columns={[
                                { title: "日期", dataIndex: "datetime", width: 150 },
                                { title: "开盘", dataIndex: "open", width: 80, align: "right" },
                                { title: "最高", dataIndex: "high", width: 80, align: "right" },
                                { title: "最低", dataIndex: "low", width: 80, align: "right" },
                                { title: "收盘", dataIndex: "close", width: 80, align: "right" },
                                { title: "成交量", dataIndex: "volume", width: 100, align: "right" },
                            ]}
                            dataSource={bars.slice(-20).reverse()}
                            rowKey="datetime"
                            size="small"
                            pagination={false}
                            scroll={{ y: 300 }}
                        />
                    </Card>
                )}

                {/* 股票搜索 */}
                <Card
                    size="small"
                    title="股票搜索"
                    style={{ background: darkTheme.token.colorBgContainer }}
                >
                    <Row gutter={[16, 16]} align="middle">
                        <Col flex="300px">
                            <Input
                                placeholder="输入股票代码或名称"
                                value={searchKeyword}
                                onChange={(e) => setSearchKeyword(e.target.value)}
                                onPressEnter={handleSearch}
                            />
                        </Col>
                        <Col>
                            <Button
                                type="primary"
                                icon={<SearchOutlined />}
                                onClick={handleSearch}
                            >
                                搜索
                            </Button>
                        </Col>
                    </Row>

                    {searchResults.length > 0 && (
                        <Table
                            columns={searchColumns}
                            dataSource={searchResults}
                            rowKey="code"
                            size="small"
                            pagination={false}
                            style={{ marginTop: 16 }}
                        />
                    )}
                </Card>
            </Spin>
        </div>
    );
};

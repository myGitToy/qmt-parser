/**
 * 主看板页面
 */

import { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, Input, Alert, Button } from "antd";
import { SearchOutlined, ReloadOutlined } from "@ant-design/icons";
import { KLineChart } from "../../components/charts/KLineChart";
import { QuoteTable } from "../../components/grids/QuoteTable";
import { getMarketOverview, getBars, getQuote, getHealthCheck } from "../../api/market";
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
    const [error, setError] = useState<string | null>(null);
    const [errorType, setErrorType] = useState<string>("");
    const [warnings, setWarnings] = useState<string[]>([]);

    // 启动时检查健康状态
    useEffect(() => {
        checkHealth();
    }, []);

    const checkHealth = async () => {
        try {
            const health = await getHealthCheck();

            // 显示警告信息
            if (health.warnings && health.warnings.length > 0) {
                const warningMessages = health.warnings.map(w => w.message);
                setWarnings(warningMessages);
                console.warn("数据源配置警告:", health.warnings);
            }

            // 检查数据源状态
            if (!health.providers.tushare.configured && !health.providers.akshare.available) {
                setError("所有数据源都未配置或不可用");
                setErrorType("NO_DATA_SOURCE");
            }
        } catch (err: any) {
            console.error("健康检查失败:", err);
            // 健康检查失败说明后端未启动
            setError("后端服务未启动或无法连接");
            setErrorType("NETWORK_ERROR");
        }
    };

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
            setError(null);
            setErrorType("");
            const data = await getMarketOverview();
            setMarketOverview(data);
        } catch (err: any) {
            console.error("加载市场概览失败:", err);
            // 使用扩展的错误信息
            const errorMessage = err.userMessage || "加载市场概览失败";
            const errorDetail = err.errorDetail || {};

            setError(errorMessage);
            setErrorType(errorDetail.type || "UNKNOWN_ERROR");

            // 如果是网络错误，提示检查后端服务
            if (errorDetail.type === "NETWORK_ERROR") {
                setError("后端服务未启动或端口配置错误。请确保后端运行在 http://localhost:8011");
            }
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
        } catch (error: any) {
            console.error("加载K线数据失败:", error);
            // K线加载失败不影响整体页面，只提示用户
            console.warn("K线数据加载失败，可能股票代码不正确或数据源暂时不可用");
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
            {/* 错误提示区域 */}
            {error && (
                <Alert
                    message="数据加载失败"
                    description={
                        <div>
                            <p>{error}</p>
                            {errorType === "NETWORK_ERROR" && (
                                <p style={{ marginTop: 8 }}>
                                    <strong>解决方案：</strong>
                                    <br />1. 检查后端服务是否启动：访问 http://localhost:8011/docs
                                    <br />2. 检查端口配置是否正确（前端：5073，后端：8011）
                                    <br />3. 查看后端控制台是否有错误信息
                                </p>
                            )}
                            {errorType === "SERVER_ERROR" && (
                                <p style={{ marginTop: 8 }}>
                                    <strong>可能的原因：</strong>
                                    <br />1. Tushare Token 未配置或配置错误
                                    <br />2. 数据源暂时不可用
                                    <br />3. 后端配置错误
                                </p>
                            )}
                            <Button
                                type="primary"
                                size="small"
                                icon={<ReloadOutlined />}
                                onClick={loadMarketOverview}
                                style={{ marginTop: 8 }}
                            >
                                重试
                            </Button>
                        </div>
                    }
                    type="error"
                    showIcon
                    closable
                    onClose={() => setError(null)}
                    style={{ marginBottom: 16 }}
                />
            )}

            {/* 警告提示区域 */}
            {warnings.length > 0 && !error && (
                <Alert
                    message="数据源配置警告"
                    description={
                        <div>
                            {warnings.map((warning, index) => (
                                <p key={index}>⚠️ {warning}</p>
                            ))}
                            <p style={{ marginTop: 8 }}>
                                <strong>建议：</strong>虽然系统可以正常运行，但建议配置 Tushare Token 以获得更稳定的数据服务。
                                <br />
                                请在 <code style={{ background: "#f5f5f5", padding: "2px 6px", borderRadius: "3px" }}>apps/webui/.env</code> 文件中设置 <code style={{ background: "#f5f5f5", padding: "2px 6px", borderRadius: "3px" }}>TUSHARE_TOKEN</code> 环境变量。
                            </p>
                        </div>
                    }
                    type="warning"
                    showIcon
                    closable
                    onClose={() => setWarnings([])}
                    style={{ marginBottom: 16 }}
                />
            )}

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

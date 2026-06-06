/**
 * QMT数据校验主页面
 * 金融终端风格 — Segmented功能区切换 + 左右主从面板
 */

import { useEffect, useMemo, useCallback } from "react";
import {
    Card, Row, Col, Segmented, Tree, Table, Button, Spin, Alert, Statistic,
} from "antd";
import {
    ReloadOutlined,
    FolderOutlined,
    FileOutlined,
    LineChartOutlined,
    AccountBookOutlined,
    ScissorOutlined,
    ThunderboltOutlined,
    SwapOutlined,
} from "@ant-design/icons";
import { useQmtStore } from "../../stores/qmtStore";
import type { DataType } from "../../api/qmt";
import type { ColumnsType } from "antd/es/table";
import type { TablePaginationConfig } from "antd/es/table";
import type { DataNode } from "antd/es/tree";
import "./QmtDataExplorer.css";

// ============================================================
// 数据类别配置
// ============================================================

const DATA_TYPE_OPTIONS = [
    { label: "K线数据", value: "kline" as DataType, icon: <LineChartOutlined /> },
    { label: "财务数据", value: "finance" as DataType, icon: <AccountBookOutlined /> },
    { label: "除权数据", value: "dividend" as DataType, icon: <ScissorOutlined /> },
    { label: "分笔成交", value: "tick" as DataType, icon: <ThunderboltOutlined /> },
    { label: "ETF申赎", value: "etf" as DataType, icon: <SwapOutlined /> },
];

// ============================================================
// 表格列定义
// ============================================================

const klineColumns: ColumnsType = [
    {
        title: "文件名",
        dataIndex: "name",
        key: "name",
        width: 160,
        render: (text: string) => (
            <span>
                <FileOutlined style={{ marginRight: 8 }} />
                {text}
            </span>
        ),
    },
    { title: "大小", dataIndex: "size_human", key: "size", width: 80 },
    { title: "修改时间", dataIndex: "modified", key: "modified", width: 140 },
    {
        title: "估算记录",
        dataIndex: "estimated_records",
        key: "records",
        width: 90,
        render: (count?: number) => (count ? count.toLocaleString() : "-"),
    },
];

const financeColumns: ColumnsType = [
    {
        title: "文件名",
        dataIndex: "name",
        key: "name",
        width: 160,
        render: (text: string) => (
            <span>
                <FileOutlined style={{ marginRight: 8 }} />
                {text}
            </span>
        ),
    },
    { title: "股票代码", dataIndex: "stock_code", key: "stock_code", width: 100 },
    { title: "大小", dataIndex: "size_human", key: "size", width: 80 },
    { title: "修改时间", dataIndex: "modified", key: "modified", width: 140 },
];

const dividendColumns: ColumnsType = [
    {
        title: "文件名",
        dataIndex: "name",
        key: "name",
        width: 200,
        render: (text: string) => (
            <span>
                <FileOutlined style={{ marginRight: 8 }} />
                {text}
            </span>
        ),
    },
    { title: "大小", dataIndex: "size_human", key: "size", width: 80 },
    { title: "修改时间", dataIndex: "modified", key: "modified", width: 140 },
    { title: "类型", dataIndex: "file_type", key: "file_type", width: 100 },
];

const tickColumns: ColumnsType = [
    {
        title: "文件名",
        dataIndex: "name",
        key: "name",
        width: 140,
        render: (text: string) => (
            <span>
                <FileOutlined style={{ marginRight: 8 }} />
                {text}
            </span>
        ),
    },
    { title: "大小", dataIndex: "size_human", key: "size", width: 80 },
    { title: "修改时间", dataIndex: "modified", key: "modified", width: 140 },
    {
        title: "估算记录",
        dataIndex: "estimated_records",
        key: "records",
        width: 90,
        render: (count?: number) => (count ? count.toLocaleString() : "-"),
    },
];

const etfColumns: ColumnsType = [
    {
        title: "文件名",
        dataIndex: "name",
        key: "name",
        width: 160,
        render: (text: string) => (
            <span>
                <FileOutlined style={{ marginRight: 8 }} />
                {text}
            </span>
        ),
    },
    { title: "ETF代码", dataIndex: "stock_code", key: "stock_code", width: 100 },
    { title: "大小", dataIndex: "size_human", key: "size", width: 80 },
    { title: "修改时间", dataIndex: "modified", key: "modified", width: 140 },
];

const TABLE_COLUMNS: Record<DataType, ColumnsType> = {
    kline: klineColumns,
    finance: financeColumns,
    dividend: dividendColumns,
    tick: tickColumns,
    etf: etfColumns,
};

// ============================================================
// 主组件
// ============================================================

export const QmtDataExplorer = () => {
    const store = useQmtStore();
    const {
        qmtStatus,
        summary,
        markets,
        periods,
        financeTypes,
        tickStocks,
        etfList,
        files,
        activeDataType,
        selectedMarket,
        selectedPeriod,
        selectedFinanceType,
        selectedTickStock,
        selectedEtf,
        pagination,
        loading,
        error,
        fetchStatus,
        fetchSummary,
        fetchMarkets,
        setActiveDataType,
        selectMarket,
        selectPeriod,
        selectFinanceType,
        selectTickStock,
        selectEtf,
        fetchPeriods,
        fetchFinanceTypes,
        fetchTickStocks,
        fetchEtfList,
        fetchFiles,
        fetchFinanceFiles,
        fetchTickFiles,
        fetchEtfFiles,
        fetchDividendFiles,
    } = store;

    // --- 初始化 ---
    useEffect(() => {
        fetchStatus();
        fetchSummary();
        fetchMarkets();
    }, []);

    // --- Segmented 选项（带图标） ---
    const segmentedOptions = useMemo(
        () => DATA_TYPE_OPTIONS.map((opt) => ({ label: opt.label, value: opt.value })),
        []
    );

    // ============================================================
    // 目录树构建
    // ============================================================

    const buildKlineTree = useCallback((): DataNode[] => {
        return markets.map((market) => ({
            title: `${market.short}市 (${market.name})`,
            key: `mkt:${market.code}`,
            icon: <FolderOutlined />,
            children: periods
                .filter((p) => p.files > 0)
                .map((period) => ({
                    title: `${period.name} (${period.files}个文件)`,
                    key: `period:${market.code}:${period.code}`,
                    icon: <FolderOutlined />,
                    isLeaf: true,
                })),
        }));
    }, [markets, periods]);

    const buildFinanceTree = useCallback((): DataNode[] => {
        const financeChildren = financeTypes.map((ft) => ({
            title: `${ft.name} (${ft.files}个文件)`,
            key: `finType:${ft.code}`,
            icon: <FolderOutlined />,
            children: markets.map((mkt) => ({
                title: `${mkt.short}市`,
                key: `finFile:${ft.code}:${mkt.code}`,
                icon: <FolderOutlined />,
                isLeaf: true,
            })),
        }));
        return financeChildren.length > 0
            ? [{ title: "财务报表", key: "finRoot", icon: <FolderOutlined />, children: financeChildren }]
            : [];
    }, [financeTypes, markets]);

    const buildDividendTree = useCallback((): DataNode[] => {
        return markets.map((mkt) => ({
            title: `${mkt.short}市 (${mkt.name})`,
            key: `div:${mkt.code}`,
            icon: <FolderOutlined />,
            isLeaf: true,
        }));
    }, [markets]);

    const buildTickTree = useCallback((): DataNode[] => {
        return markets.map((mkt) => ({
            title: `${mkt.short}市 (${mkt.name})`,
            key: `tickMkt:${mkt.code}`,
            icon: <FolderOutlined />,
            children: tickStocks
                .filter((s) => s.market === mkt.code)
                .slice(0, 200)
                .map((stock) => ({
                    title: `${stock.code} (${stock.files}个文件)`,
                    key: `tickStock:${mkt.code}:${stock.code}`,
                    icon: <FileOutlined />,
                    isLeaf: true,
                })),
        }));
    }, [markets, tickStocks]);

    const buildEtfTree = useCallback((): DataNode[] => {
        return markets
            .filter((m) => m.code === "SH" || m.code === "SZ")
            .map((mkt) => ({
                title: `${mkt.short}市 (${mkt.name})`,
                key: `etfMkt:${mkt.code}`,
                icon: <FolderOutlined />,
                children: etfList
                    .filter((e) => e.market === mkt.code)
                    .slice(0, 200)
                    .map((etf) => ({
                        title: `${etf.code}${etf.files ? ` (${etf.files}个文件)` : ""}`,
                        key: `etfCode:${mkt.code}:${etf.code}`,
                        icon: <FileOutlined />,
                        isLeaf: true,
                    })),
            }));
    }, [markets, etfList]);

    const treeBuilders: Record<DataType, () => DataNode[]> = useMemo(
        () => ({
            kline: buildKlineTree,
            finance: buildFinanceTree,
            dividend: buildDividendTree,
            tick: buildTickTree,
            etf: buildEtfTree,
        }),
        [buildKlineTree, buildFinanceTree, buildDividendTree, buildTickTree, buildEtfTree]
    );

    const treeData = useMemo(
        () => treeBuilders[activeDataType](),
        [treeBuilders, activeDataType]
    );

    // ============================================================
    // 树节点选择处理
    // ============================================================

    const handleTreeSelect = useCallback(
        (selectedKeys: React.Key[]) => {
            if (selectedKeys.length === 0) return;

            const key = selectedKeys[0] as string;
            const parts = key.split(":");

            switch (parts[0]) {
                // K线
                case "mkt": {
                    const marketCode = parts[1];
                    if (marketCode !== selectedMarket) {
                        selectMarket(marketCode);
                    }
                    break;
                }
                case "period": {
                    const [, mkt, period] = parts;
                    if (mkt !== selectedMarket) {
                        selectMarket(mkt);
                    }
                    selectPeriod(period);
                    break;
                }
                // 财务
                case "finType": {
                    selectFinanceType(parts[1]);
                    break;
                }
                case "finFile": {
                    const [, fType, mkt] = parts;
                    selectFinanceType(fType);
                    fetchFinanceFiles(fType, mkt);
                    break;
                }
                // 除权
                case "div": {
                    fetchDividendFiles(parts[1]);
                    break;
                }
                // 分笔成交
                case "tickMkt": {
                    const mkt = parts[1];
                    if (mkt !== selectedMarket) {
                        selectMarket(mkt);
                    }
                    fetchTickStocks(mkt);
                    break;
                }
                case "tickStock": {
                    const [, mkt, stock] = parts;
                    selectTickStock(stock);
                    fetchTickFiles(mkt, stock);
                    break;
                }
                // ETF
                case "etfMkt": {
                    const mkt = parts[1];
                    fetchEtfList(mkt);
                    break;
                }
                case "etfCode": {
                    const [, mkt, code] = parts;
                    selectEtf(code);
                    fetchEtfFiles(mkt, code);
                    break;
                }
            }
        },
        [selectedMarket, selectMarket, selectPeriod, selectFinanceType, selectTickStock, selectEtf,
            fetchFinanceFiles, fetchDividendFiles, fetchTickStocks, fetchTickFiles, fetchEtfList, fetchEtfFiles]
    );

    // ============================================================
    // 分页处理
    // ============================================================

    const handleTableChange = useCallback(
        (pag: TablePaginationConfig) => {
            const page = pag.current || 1;
            switch (activeDataType) {
                case "kline":
                    if (selectedMarket && selectedPeriod) {
                        fetchFiles(selectedMarket, selectedPeriod, page);
                    }
                    break;
                case "finance":
                    if (selectedFinanceType && selectedMarket) {
                        fetchFinanceFiles(selectedFinanceType, selectedMarket, page);
                    }
                    break;
                case "tick":
                    if (selectedMarket && selectedTickStock) {
                        fetchTickFiles(selectedMarket, selectedTickStock, page);
                    }
                    break;
                case "etf":
                    if (selectedMarket && selectedEtf) {
                        fetchEtfFiles(selectedMarket, selectedEtf, page);
                    }
                    break;
                case "dividend":
                    if (selectedMarket) {
                        fetchDividendFiles(selectedMarket, page);
                    }
                    break;
            }
        },
        [activeDataType, selectedMarket, selectedPeriod, selectedFinanceType,
            selectedTickStock, selectedEtf, fetchFiles, fetchFinanceFiles,
            fetchTickFiles, fetchEtfFiles, fetchDividendFiles]
    );

    // ============================================================
    // 刷新
    // ============================================================

    const handleRefresh = useCallback(() => {
        fetchStatus();
        fetchSummary();
        fetchMarkets();
    }, [fetchStatus, fetchSummary, fetchMarkets]);

    // ============================================================
    // 面板标题
    // ============================================================

    const getPanelTitle = useCallback((): string => {
        switch (activeDataType) {
            case "kline":
                return selectedPeriod
                    ? `${periods.find((p) => p.code === selectedPeriod)?.name || ""}文件列表`
                    : "请选择市场目录";
            case "finance":
                return selectedFinanceType
                    ? `${financeTypes.find((f) => f.code === selectedFinanceType)?.name || ""}文件列表`
                    : "请选择报表类型和市场";
            case "dividend":
                return "除权数据文件";
            case "tick":
                return selectedTickStock
                    ? `${selectedTickStock} 分笔成交文件`
                    : "请选择市场和股票";
            case "etf":
                return selectedEtf
                    ? `${selectedEtf} ETF申赎清单`
                    : "请选择市场和ETF代码";
            default:
                return "请选择目录";
        }
    }, [activeDataType, selectedPeriod, selectedFinanceType, selectedTickStock, selectedEtf,
        periods, financeTypes]);

    // ============================================================
    // 状态栏文本
    // ============================================================

    const statusBarText = useMemo((): string => {
        const parts: string[] = [];
        const currentType = DATA_TYPE_OPTIONS.find((o) => o.value === activeDataType);
        if (currentType) parts.push(currentType.label);
        if (selectedMarket) parts.push(selectedMarket);
        if (selectedPeriod) {
            const p = periods.find((p) => p.code === selectedPeriod);
            if (p) parts.push(p.name);
        }
        if (selectedFinanceType) {
            const ft = financeTypes.find((f) => f.code === selectedFinanceType);
            if (ft) parts.push(ft.name);
        }
        if (selectedTickStock) parts.push(selectedTickStock);
        if (selectedEtf) parts.push(selectedEtf);
        if (pagination) parts.push(`第${pagination.page}页`);
        return parts.length > 0 ? parts.join(" / ") : "就绪";
    }, [activeDataType, selectedMarket, selectedPeriod, selectedFinanceType,
        selectedTickStock, selectedEtf, pagination, periods, financeTypes]);

    // ============================================================
    // 渲染：错误状态
    // ============================================================

    if (error) {
        return (
            <div style={{ padding: 24 }}>
                <Alert type="error" message="错误" description={error} showIcon closable />
            </div>
        );
    }

    if (qmtStatus && !qmtStatus.valid) {
        return (
            <div style={{ padding: 24 }}>
                <Alert
                    type="warning"
                    message="QMT未配置"
                    description="请在 .env 文件中设置 QMT_CLIENT_PATH 环境变量，指向QMT客户端安装目录"
                    showIcon
                />
            </div>
        );
    }

    // ============================================================
    // 渲染：主页面
    // ============================================================

    return (
        <div className="qmt-data-explorer">
            {/* 标题栏 */}
            <div className="qmt-header">
                <h2>QMT数据校验</h2>
                <Button
                    icon={<ReloadOutlined />}
                    onClick={handleRefresh}
                    loading={loading}
                    size="small"
                >
                    刷新
                </Button>
            </div>

            {/* 功能区切换 */}
            <Segmented
                className="qmt-segmented"
                options={segmentedOptions}
                value={activeDataType}
                onChange={(val) => setActiveDataType(val as DataType)}
                block
            />

            {/* 统计卡片 */}
            <Spin spinning={loading && !summary}>
                {summary && summary.valid && (
                    <Row gutter={[8, 8]} className="qmt-stat-cards" style={{ marginTop: 12 }}>
                        <Col span={6}>
                            <Card size="small">
                                <Statistic title="市场数量" value={summary.summary?.total_markets || 0} />
                            </Card>
                        </Col>
                        <Col span={6}>
                            <Card size="small">
                                <Statistic title="文件总数" value={summary.summary?.total_files || 0} />
                            </Card>
                        </Col>
                        <Col span={6}>
                            <Card size="small">
                                <Statistic title="总大小" value={summary.summary?.total_size_human || "-"} />
                            </Card>
                        </Col>
                        <Col span={6}>
                            <Card size="small">
                                <Statistic
                                    title="最后扫描"
                                    value={
                                        summary.summary?.last_scan
                                            ? new Date(summary.summary.last_scan).toLocaleString()
                                            : "-"
                                    }
                                />
                            </Card>
                        </Col>
                    </Row>
                )}
            </Spin>

            {/* 主从面板 */}
            <Row gutter={[8, 0]} style={{ marginTop: 12 }}>
                {/* 左侧：目录导航 */}
                <Col span={6}>
                    <Card title="目录导航" size="small" className="qmt-nav-card">
                        <Tree
                            showIcon
                            defaultExpandAll
                            onSelect={handleTreeSelect}
                            treeData={treeData}
                            style={{ fontSize: 13 }}
                        />
                    </Card>
                </Col>

                {/* 右侧：数据面板 */}
                <Col span={18}>
                    <Card title={getPanelTitle()} size="small" className="qmt-data-card">
                        {files.length > 0 || pagination ? (
                            <Table
                                columns={TABLE_COLUMNS[activeDataType]}
                                dataSource={files}
                                rowKey="path"
                                size="small"
                                pagination={{
                                    current: pagination?.page,
                                    pageSize: pagination?.page_size || 100,
                                    total: pagination?.total || 0,
                                    showTotal: (total) => `共 ${total} 条`,
                                    size: "small",
                                }}
                                onChange={handleTableChange}
                                scroll={{ y: 400 }}
                            />
                        ) : (
                            <div className="qmt-empty-hint">
                                请在左侧选择目录查看文件
                            </div>
                        )}
                    </Card>
                </Col>
            </Row>

            {/* 底部状态栏 */}
            <div className="qmt-status-bar">
                <span>{statusBarText}</span>
                <span>
                    最后更新:{" "}
                    {summary?.summary?.last_scan
                        ? new Date(summary.summary.last_scan).toLocaleString()
                        : "-"}
                </span>
            </div>
        </div>
    );
};

/**
 * QMT数据校验主页面
 */

import { useEffect } from "react";
import { Card, Row, Col, Tabs, Tree, Table, Tag, Button, Spin, Alert, Statistic } from "antd";
import { ReloadOutlined, FolderOutlined, FileOutlined } from "@ant-design/icons";
import { useQmtStore } from "../../stores/qmtStore";
import type { ColumnsType } from "antd/es/table";
import type { DataNode } from "antd/es/tree";
import "./QmtDataExplorer.css";

export const QmtDataExplorer = () => {
    const {
        qmtStatus,
        summary,
        markets,
        periods,
        files,
        selectedMarket,
        selectedPeriod,
        pagination,
        loading,
        error,
        fetchStatus,
        fetchSummary,
        fetchMarkets,
        fetchFiles,
        selectMarket,
        selectPeriod,
    } = useQmtStore();

    useEffect(() => {
        fetchStatus();
        fetchSummary();
        fetchMarkets();
    }, []);

    // 刷新所有数据
    const handleRefresh = () => {
        fetchStatus();
        fetchSummary();
        if (selectedMarket) {
            fetchMarkets();
        }
    };

    // 文件表格列定义
    const fileColumns: ColumnsType = [
        {
            title: "文件名",
            dataIndex: "name",
            key: "name",
            width: 150,
            render: (text: string) => (
                <span>
                    <FileOutlined style={{ marginRight: 8 }} />
                    {text}
                </span>
            ),
        },
        {
            title: "大小",
            dataIndex: "size_human",
            key: "size",
            width: 100,
        },
        {
            title: "修改时间",
            dataIndex: "modified",
            key: "modified",
            width: 160,
        },
        {
            title: "估算记录",
            dataIndex: "estimated_records",
            key: "records",
            width: 100,
            render: (count?: number) => (count ? count.toLocaleString() : "-"),
        },
    ];

    // 构建市场树数据
    const buildMarketTree = (): DataNode[] => {
        return markets.map((market) => ({
            title: `${market.short}市 (${market.name})`,
            key: market.code,
            icon: <FolderOutlined />,
            children: periods
                .filter((p) => p.files > 0)
                .map((period) => ({
                    title: `${period.name} (${period.files}个文件)`,
                    key: `${market.code}/${period.code}`,
                    icon: <FolderOutlined />,
                    isLeaf: false,
                })),
        }));
    };

    // 树节点选择
    const handleTreeSelect = (selectedKeys: React.Key[], info: any) => {
        if (selectedKeys.length === 0) return;

        const key = selectedKeys[0] as string;
        if (key.includes("/")) {
            // 选择的是周期
            const [market, period] = key.split("/");
            if (market !== selectedMarket) {
                selectMarket(market);
            }
            selectPeriod(period);
        } else {
            // 选择的是市场
            selectMarket(key);
        }
    };

    // 分页处理
    const handleTableChange = (pagination: any) => {
        if (selectedMarket && selectedPeriod) {
            fetchFiles(selectedMarket, selectedPeriod, pagination.current);
        }
    };

    // 渲染状态警告
    if (error) {
        return (
            <div style={{ padding: 24 }}>
                <Alert
                    type="error"
                    message="错误"
                    description={error}
                    showIcon
                    closable
                />
            </div>
        );
    }

    // 渲染QMT未配置提示
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

    return (
        <div className="qmt-data-explorer">
            {/* 头部操作栏 */}
            <div className="qmt-header">
                <h2>QMT数据校验</h2>
                <Button
                    icon={<ReloadOutlined />}
                    onClick={handleRefresh}
                    loading={loading}
                >
                    刷新
                </Button>
            </div>

            {/* 内容区域 */}
            <Spin spinning={loading && !summary}>
                {summary && summary.valid && (
                    <Row gutter={16} style={{ marginBottom: 16 }}>
                        <Col span={6}>
                            <Card>
                                <Statistic
                                    title="市场数量"
                                    value={summary.summary?.total_markets || 0}
                                />
                            </Card>
                        </Col>
                        <Col span={6}>
                            <Card>
                                <Statistic
                                    title="文件总数"
                                    value={summary.summary?.total_files || 0}
                                />
                            </Card>
                        </Col>
                        <Col span={6}>
                            <Card>
                                <Statistic
                                    title="总大小"
                                    value={summary.summary?.total_size_human || "-"}
                                />
                            </Card>
                        </Col>
                        <Col span={6}>
                            <Card>
                                <Statistic
                                    title="最后扫描"
                                    value={
                                        summary.summary?.last_scan
                                            ? new Date(
                                                  summary.summary.last_scan
                                              ).toLocaleString()
                                            : "-"
                                    }
                                />
                            </Card>
                        </Col>
                    </Row>
                )}
            </Spin>

            {/* 主内容区 */}
            <Row gutter={16} style={{ marginTop: 16 }}>
                {/* 左侧：目录树 */}
                <Col span={8}>
                    <Card title="市场目录" size="small">
                        <Tree
                            showIcon
                            defaultExpandAll
                            onSelect={handleTreeSelect}
                            treeData={buildMarketTree()}
                            style={{ fontSize: 13 }}
                        />
                    </Card>
                </Col>

                {/* 右侧：文件列表 */}
                <Col span={16}>
                    <Card
                        title={
                            selectedPeriod
                                ? `${periods.find((p) => p.code === selectedPeriod)?.name || ""}文件列表`
                                : "请选择市场目录"
                        }
                        size="small"
                    >
                        {selectedMarket && selectedPeriod ? (
                            <Table
                                columns={fileColumns}
                                dataSource={files}
                                rowKey="name"
                                size="small"
                                pagination={{
                                    current: pagination?.page,
                                    pageSize: pagination?.page_size,
                                    total: pagination?.total,
                                    showTotal: (total) => `共 ${total} 条`,
                                }}
                                onChange={handleTableChange}
                                scroll={{ y: 400 }}
                            />
                        ) : (
                            <div
                                style={{
                                    textAlign: "center",
                                    color: "#8b949e",
                                    padding: 40,
                                }}
                            >
                                请在左侧选择市场目录查看文件
                            </div>
                        )}
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

/**
 * 报价表格组件
 * 使用 Ant Design Table
 */

import { Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";
import type { Quote } from "../../types/market";
import { getColorByChange } from "../../theme/darkTheme";

interface QuoteTableProps {
    quotes: Quote[];
    loading?: boolean;
    onRowClick?: (quote: Quote) => void;
}

export const QuoteTable = ({ quotes, loading, onRowClick }: QuoteTableProps) => {
    const [flashingCells, setFlashingCells] = useState<Set<string>>(new Set());

    // 检测数据更新并闪烁
    useEffect(() => {
        const newFlashingCells = new Set<string>();

        quotes.forEach((quote, index) => {
            newFlashingCells.add(`${index}-price`);
            newFlashingCells.add(`${index}-change`);
            newFlashingCells.add(`${index}-change_pct`);
        });

        setFlashingCells(newFlashingCells);

        // 0.5秒后移除闪烁效果
        const timer = setTimeout(() => {
            setFlashingCells(new Set());
        }, 500);

        return () => clearTimeout(timer);
    }, [quotes]);

    const columns: ColumnsType<Quote> = [
        {
            title: "代码",
            dataIndex: "symbol",
            key: "symbol",
            width: 120,
            fixed: "left",
            render: (text) => <span style={{ color: "#58a6ff" }}>{text}</span>,
        },
        {
            title: "名称",
            dataIndex: "name",
            key: "name",
            width: 100,
        },
        {
            title: "最新价",
            dataIndex: "price",
            key: "price",
            width: 100,
            align: "right",
            render: (value, record, index) => (
                <span
                    style={{
                        color: getColorByChange(record.change),
                        fontWeight: "bold",
                        transition: "background-color 0.3s",
                        backgroundColor: flashingCells.has(`${index}-price`)
                            ? "rgba(248, 81, 73, 0.2)"
                            : "transparent",
                    }}
                >
                    {value?.toFixed(2)}
                </span>
            ),
        },
        {
            title: "涨跌额",
            dataIndex: "change",
            key: "change",
            width: 80,
            align: "right",
            render: (value, record, index) => (
                <span
                    style={{
                        color: getColorByChange(value),
                        transition: "background-color 0.3s",
                        backgroundColor: flashingCells.has(`${index}-change`)
                            ? "rgba(248, 81, 73, 0.2)"
                            : "transparent",
                    }}
                >
                    {value > 0 ? "+" : ""}{value?.toFixed(2)}
                </span>
            ),
        },
        {
            title: "涨跌幅",
            dataIndex: "change_pct",
            key: "change_pct",
            width: 80,
            align: "right",
            render: (value, record, index) => (
                <span
                    style={{
                        color: getColorByChange(value),
                        transition: "background-color 0.3s",
                        backgroundColor: flashingCells.has(`${index}-change_pct`)
                            ? "rgba(248, 81, 73, 0.2)"
                            : "transparent",
                    }}
                >
                    {value > 0 ? "+" : ""}{value?.toFixed(2)}%
                </span>
            ),
        },
        {
            title: "成交量",
            dataIndex: "volume",
            key: "volume",
            width: 100,
            align: "right",
            render: (value) => {
                if (!value) return "-";
                if (value >= 100000000) {
                    return `${(value / 100000000).toFixed(2)}亿`;
                } else if (value >= 10000) {
                    return `${(value / 10000).toFixed(2)}万`;
                }
                return value.toLocaleString();
            },
        },
        {
            title: "最高",
            dataIndex: "high",
            key: "high",
            width: 80,
            align: "right",
            render: (value) => value?.toFixed(2) || "-",
        },
        {
            title: "最低",
            dataIndex: "low",
            key: "low",
            width: 80,
            align: "right",
            render: (value) => value?.toFixed(2) || "-",
        },
        {
            title: "今开",
            dataIndex: "open",
            key: "open",
            width: 80,
            align: "right",
            render: (value) => value?.toFixed(2) || "-",
        },
        {
            title: "昨收",
            dataIndex: "close_prev",
            key: "close_prev",
            width: 80,
            align: "right",
            render: (value) => value?.toFixed(2) || "-",
        },
        {
            title: "市场",
            dataIndex: "market",
            key: "market",
            width: 60,
            render: (value) => (
                <Tag color={value === "SH" ? "blue" : "green"}>{value}</Tag>
            ),
        },
    ];

    return (
        <Table
            columns={columns}
            dataSource={quotes}
            rowKey="symbol"
            loading={loading}
            size="small"
            scroll={{ x: 1200, y: 400 }}
            pagination={false}
            onRow={(record) => ({
                onClick: () => onRowClick?.(record),
                style: { cursor: onRowClick ? "pointer" : "default" },
            })}
            style={{ background: "#0d1117" }}
            rowClassName={() => "dark-table-row"}
        />
    );
};

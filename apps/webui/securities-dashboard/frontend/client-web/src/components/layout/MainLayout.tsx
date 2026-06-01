/**
 * 主布局组件
 * 三栏布局：功能树 + 主工作区 + 信息栏
 */

import { Layout, Menu, Row, Col } from "antd";
import { Outlet } from "react-router-dom";
import {
    LineChartOutlined,
    PieChartOutlined,
    BarChartOutlined,
    ToolOutlined,
    BellOutlined,
} from "@ant-design/icons";
import { useAppStore } from "../../stores/appStore";
import { darkTheme } from "../../theme/darkTheme";

const { Sider, Content, Header, Footer } = Layout;

export const MainLayout = () => {
    const { sidebarCollapsed, setSidebarCollapsed, selectedFunction, setSelectedFunction } =
        useAppStore();

    // 功能菜单配置
    const functionMenuItems = [
        { key: "market", icon: <LineChartOutlined />, label: "行情" },
        { key: "portfolio", icon: <PieChartOutlined />, label: "组合" },
        { key: "analysis", icon: <BarChartOutlined />, label: "分析" },
        { key: "tools", icon: <ToolOutlined />, label: "工具" },
        { key: "alerts", icon: <BellOutlined />, label: "预警" },
    ];

    return (
        <Layout style={{ minHeight: "100vh", background: darkTheme.token.colorBgBase }}>
            {/* 标题栏 */}
            <Header
                style={{
                    height: 32,
                    background: darkTheme.token.colorBgBase,
                    borderBottom: `1px solid ${darkTheme.token.colorBorder}`,
                    display: "flex",
                    alignItems: "center",
                    padding: "0 16px",
                    fontSize: 12,
                }}
            >
                <span style={{ color: darkTheme.token.colorPrimary, fontWeight: "bold" }}>
                    证券看板 v0.1.0
                </span>
                <span style={{ marginLeft: "auto", color: darkTheme.token.colorTextSecondary }}>
                    市场状态: 开市
                </span>
            </Header>

            <Layout>
                {/* 功能树 */}
                <Sider
                    width={180}
                    collapsed={sidebarCollapsed}
                    collapsedWidth={48}
                    style={{
                        background: darkTheme.token.colorBgBase,
                        borderRight: `1px solid ${darkTheme.token.colorBorder}`,
                    }}
                    trigger={null}
                >
                    <Menu
                        theme="dark"
                        mode="inline"
                        selectedKeys={selectedFunction ? [selectedFunction] : []}
                        items={functionMenuItems}
                        onClick={({ key }) => setSelectedFunction(key)}
                        style={{ background: "transparent" }}
                    />
                </Sider>

                {/* 主工作区 */}
                <Content
                    style={{
                        background: darkTheme.token.colorBgBase,
                        padding: 8,
                        overflow: "auto",
                    }}
                >
                    <Outlet />
                </Content>

                {/* 信息栏 */}
                <Sider
                    width={240}
                    style={{
                        background: darkTheme.token.colorBgBase,
                        borderLeft: `1px solid ${darkTheme.token.colorBorder}`,
                    }}
                >
                    <div style={{ padding: 8 }}>
                        <h4 style={{ color: darkTheme.token.colorTextPrimary, margin: "8px 0" }}>
                            资讯
                        </h4>
                        <div style={{ color: darkTheme.token.colorTextSecondary, fontSize: 12 }}>
                            暂无资讯
                        </div>
                    </div>
                </Sider>
            </Layout>

            {/* 状态栏 */}
            <Footer
                style={{
                    height: 24,
                    background: darkTheme.token.colorBgBase,
                    borderTop: `1px solid ${darkTheme.token.colorBorder}`,
                    padding: "0 8px",
                    fontSize: 11,
                    display: "flex",
                    alignItems: "center",
                }}
            >
                <span style={{ color: darkTheme.token.colorTextSecondary }}>
                    F2 搜索股票 | F6 切换周期 | Esc 返回
                </span>
            </Footer>
        </Layout>
    );
};

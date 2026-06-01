/**
 * 技术分析页面
 */

import { Card } from "antd";
import { darkTheme } from "../../theme/darkTheme";

export const Analysis = () => {
    return (
        <div style={{ padding: 16 }}>
            <Card
                size="small"
                title="技术分析"
                style={{ background: darkTheme.token.colorBgContainer }}
            >
                <div style={{ textAlign: "center", padding: 40, color: darkTheme.token.colorTextSecondary }}>
                    技术分析功能开发中...
                </div>
            </Card>
        </div>
    );
};

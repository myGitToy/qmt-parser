/**
 * 组合管理页面
 */

import { Card, Row, Col, Statistic } from "antd";
import { darkTheme } from "../../theme/darkTheme";

export const Portfolio = () => {
    return (
        <div style={{ padding: 16 }}>
            <Row gutter={[16, 16]}>
                <Col span={6}>
                    <Card size="small">
                        <Statistic title="总资产" value={0} precision={2} />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card size="small">
                        <Statistic title="可用资金" value={0} precision={2} />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card size="small">
                        <Statistic title="持仓市值" value={0} precision={2} />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card size="small">
                        <Statistic title="今日盈亏" value={0} precision={2} />
                    </Card>
                </Col>
            </Row>

            <Card
                size="small"
                title="持仓明细"
                style={{ marginTop: 16, background: darkTheme.token.colorBgContainer }}
            >
                <div style={{ textAlign: "center", padding: 40, color: darkTheme.token.colorTextSecondary }}>
                    暂无持仓数据
                </div>
            </Card>
        </div>
    );
};

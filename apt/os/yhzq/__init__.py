# -*- coding: utf-8 -*-

"""
【银河证券荐股系统】
根据银河证券推荐的股票，进行数据分析，统计其推荐股票的成功率
数据库共有三张表：
    yhzq_fortune_list
    yhzq_fortune_record
    XX

表结构如下：

    CREATE TABLE `stock`.`Untitled`  (
  `fortune_product_id` int NOT NULL AUTO_INCREMENT COMMENT '财富星产品id',
  `name` varchar(48) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '财富星产品名称',
  `valid` bit(1) NOT NULL COMMENT '是否有效',
  PRIMARY KEY (`fortune_product_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '银河证券财富星产品列表' ROW_FORMAT = Dynamic;

CREATE TABLE `stock`.`Untitled`  (
  `fortune_record_id` int NOT NULL AUTO_INCREMENT COMMENT '财富星记录id',
  `fortune_product_id` int NOT NULL COMMENT '财富星产品id',
  `code` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '证券代码',
  `name` varchar(24) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '证券名称',
  `operation` enum('买入操作','卖出操作') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '操作方向',
  `price_range_up` decimal(10, 3) NULL DEFAULT NULL COMMENT '价格区间（上）',
  `price_range_down` decimal(10, 3) NULL DEFAULT NULL COMMENT '价格区间（下）',
  `price_cut_loss` decimal(10, 3) NULL DEFAULT NULL COMMENT '止损价格',
  `amount` int NULL DEFAULT NULL COMMENT '份额',
  `reason` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '调入调出理由',
  PRIMARY KEY (`fortune_record_id` DESC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;
"""

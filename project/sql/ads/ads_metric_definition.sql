-- ADS Layer: ads_metric_definition
-- 指标定义表（元数据）

CREATE TABLE IF NOT EXISTS ads_metric_definition (
    metric_id VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT '指标编码',
    metric_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '指标名称',
    metric_name_en VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '指标英文名',
    metric_description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '指标描述',
    calculation_logic TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '计算逻辑',
    update_frequency VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '更新频率',
    source_table VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '来源表',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    owner VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '负责人',
    create_time DATETIME COMMENT '创建时间',
    update_time DATETIME COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='指标定义表';
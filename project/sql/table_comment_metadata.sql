-- Table Comment Metadata
-- 元数据表存储表和字段的中文注释

CREATE TABLE IF NOT EXISTS table_comment_metadata (
    table_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '表名',
    column_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '字段名',
    comment_type VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '注释类型',
    comment_text VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '注释内容',
    PRIMARY KEY (table_name, column_name, comment_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='表字段注释元数据';

-- 表级注释 (comment_type = 'table')
-- 字段级注释 (comment_type = 'column')
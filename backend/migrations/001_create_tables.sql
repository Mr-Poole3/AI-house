-- 房屋中介管理系统数据库表结构
-- 创建时间: 2025-08-03

-- 创建用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 创建房源表
CREATE TABLE properties (
    id INT PRIMARY KEY AUTO_INCREMENT,
    community_name VARCHAR(100) NOT NULL COMMENT '小区名称',
    street_address VARCHAR(200) NOT NULL COMMENT '街道地址',
    floor_info VARCHAR(50) COMMENT '楼层信息',
    price DECIMAL(12,2) NOT NULL COMMENT '价格(租房为月租金，售房为总价)',
    property_type ENUM('sale', 'rent') NOT NULL COMMENT '房屋类型(sale=售房, rent=租房)',
    furniture_appliances TEXT COMMENT '家具家电配置',
    decoration_status VARCHAR(100) COMMENT '装修情况',
    room_count VARCHAR(20) COMMENT '房间数量(如: 2室1厅)',
    area DECIMAL(8,2) COMMENT '面积(平米)',
    description TEXT COMMENT '原始描述文本',
    parsed_confidence DECIMAL(3,2) COMMENT '解析置信度',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

-- 索引优化
INDEX idx_community (community_name),
    INDEX idx_street (street_address),
    INDEX idx_type_price (property_type, price),  -- 复合索引，支持按类型和价格范围查询
    INDEX idx_type (property_type),
    INDEX idx_price (price),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建房源图片表
CREATE TABLE property_images (
    id INT PRIMARY KEY AUTO_INCREMENT,
    property_id INT NOT NULL,
    file_path VARCHAR(500) NOT NULL COMMENT '图片文件路径',
    file_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_size INT NOT NULL COMMENT '文件大小(字节)',
    mime_type VARCHAR(50) NOT NULL COMMENT 'MIME类型',
    is_primary BOOLEAN DEFAULT FALSE COMMENT '是否为主图',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

-- 外键约束
FOREIGN KEY (property_id) REFERENCES properties (id) ON DELETE CASCADE,

-- 索引优化
INDEX idx_property (property_id),
    INDEX idx_primary (is_primary)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建用户会话表
CREATE TABLE user_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL COMMENT 'JWT令牌哈希',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

-- 外键约束
FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,

-- 索引优化
INDEX idx_user (user_id),
    INDEX idx_token (token_hash),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员用户 (密码: admin123, 使用bcrypt哈希)
INSERT INTO
    users (username, password_hash)
VALUES (
        'admin',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5e'
    );
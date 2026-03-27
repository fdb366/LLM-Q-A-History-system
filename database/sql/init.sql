-- 数据库初始化脚本
-- 执行顺序：创建数据库 -> 创建用户 -> 导入表结构

-- 1. 创建数据库
DROP DATABASE IF EXISTS history_qa;
CREATE DATABASE history_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 使用数据库
USE history_qa;

-- 3. 创建表（导入上面的tables.sql内容）
-- 历史问答系统数据库设计

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    role ENUM('student', 'teacher', 'admin') DEFAULT 'student' COMMENT '用户角色',
    avatar_url VARCHAR(255) COMMENT '头像URL',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    last_login TIMESTAMP NULL COMMENT '最后登录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 2. 对话会话表
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '会话ID',
    user_id INT NOT NULL COMMENT '用户ID',
    title VARCHAR(200) DEFAULT '新对话' COMMENT '对话标题',
    session_id VARCHAR(100) UNIQUE NOT NULL COMMENT '会话标识',
    message_count INT DEFAULT 0 COMMENT '消息数量',
    last_message TEXT COMMENT '最后一条消息',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否活跃',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话会话表';

-- 3. 消息记录表
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '消息ID',
    conversation_id INT NOT NULL COMMENT '会话ID',
    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '消息角色',
    content TEXT NOT NULL COMMENT '消息内容',
    tokens_used INT DEFAULT 0 COMMENT '使用的token数量',
    processing_time FLOAT DEFAULT 0 COMMENT '处理时间(秒)',
    source_documents JSON COMMENT '来源文档',
    metadata JSON COMMENT '元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息记录表';

-- 4. 知识库文档表
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文档ID',
    title VARCHAR(200) NOT NULL COMMENT '文档标题',
    source_type ENUM('textbook', 'reference_book', 'website', 'paper') DEFAULT 'textbook' COMMENT '来源类型',
    source_name VARCHAR(200) NOT NULL COMMENT '来源名称',
    grade_level VARCHAR(50) COMMENT '年级层次',
    subject_area VARCHAR(100) COMMENT '学科领域',
    file_path VARCHAR(500) COMMENT '文件路径',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小(字节)',
    content_hash VARCHAR(64) UNIQUE COMMENT '内容哈希',
    chunk_count INT DEFAULT 0 COMMENT '分块数量',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '处理状态',
    vectorized_at DATETIME NULL COMMENT '向量化时间',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_source_type (source_type),
    INDEX idx_grade_level (grade_level),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档表';

-- 5. 知识库分块表
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分块ID',
    document_id INT NOT NULL COMMENT '文档ID',
    chunk_index INT NOT NULL COMMENT '分块序号',
    content TEXT NOT NULL COMMENT '分块内容',
    content_length INT NOT NULL COMMENT '内容长度',
    chunk_hash VARCHAR(64) COMMENT '分块哈希',
    vector_id VARCHAR(100) COMMENT '向量ID',
    meta_data JSON COMMENT '元数据(包含位置、关键词等)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    UNIQUE KEY uk_document_chunk (document_id, chunk_index),
    INDEX idx_document_id (document_id),
    INDEX idx_vector_id (vector_id),
    INDEX idx_chunk_hash (chunk_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库分块表';

-- 6. 问答反馈表
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '反馈ID',
    message_id INT NOT NULL COMMENT '消息ID',
    user_id INT NOT NULL COMMENT '用户ID',
    rating TINYINT CHECK (rating >= 1 AND rating <= 5) COMMENT '评分(1-5)',
    feedback_type ENUM('accuracy', 'helpfulness', 'clarity', 'speed', 'other') COMMENT '反馈类型',
    comment TEXT COMMENT '评论',
    is_resolved BOOLEAN DEFAULT FALSE COMMENT '是否已处理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_message_id (message_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答反馈表';

-- 7. 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    level VARCHAR(20) NOT NULL COMMENT '日志级别',
    module VARCHAR(100) COMMENT '模块名称',
    action VARCHAR(100) NOT NULL COMMENT '操作',
    user_id INT COMMENT '用户ID',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    details JSON COMMENT '详细信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_level (level),
    INDEX idx_module (module),
    INDEX idx_action (action),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统日志表';
-- 4. 插入初始数据
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@history-qa.com', '$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'admin'),
('teacher1', 'teacher1@history-qa.com', '$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'teacher'),
('student1', 'student1@history-qa.com', '$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'student');

-- 5. 创建测试数据
INSERT INTO knowledge_documents (title, source_type, source_name, grade_level, subject_area, status) VALUES
('七年级历史上册', 'textbook', '人教版历史教材', '七年级', '中国历史', 'completed'),
('八年级历史下册', 'textbook', '北师大版历史教材', '八年级', '世界历史', 'completed'),
('中国通史（青少年版）', 'reference_book', '中国通史出版社', '全年级', '综合历史', 'completed');

-- 6. 创建视图
CREATE VIEW v_user_conversations AS
SELECT 
    u.username,
    u.email,
    c.id as conversation_id,
    c.title,
    c.message_count,
    c.created_at as conversation_start,
    c.updated_at as last_activity
FROM users u
JOIN conversations c ON u.id = c.user_id
WHERE c.is_active = TRUE;

CREATE VIEW v_document_statistics AS
SELECT 
    kd.title,
    kd.source_type,
    kd.grade_level,
    kd.status,
    COUNT(kc.id) as chunk_count,
    SUM(kc.content_length) as total_length
FROM knowledge_documents kd
LEFT JOIN knowledge_chunks kc ON kd.id = kc.document_id
GROUP BY kd.id;

-- 7. 创建存储过程
DELIMITER $$

CREATE PROCEDURE sp_get_conversation_history(
    IN p_user_id INT,
    IN p_limit INT
)
BEGIN
    SELECT 
        c.id,
        c.title,
        c.message_count,
        c.last_message,
        c.created_at,
        COUNT(m.id) as total_messages
    FROM conversations c
    LEFT JOIN messages m ON c.id = m.conversation_id
    WHERE c.user_id = p_user_id
    GROUP BY c.id
    ORDER BY c.updated_at DESC
    LIMIT p_limit;
END$$

CREATE PROCEDURE sp_get_daily_stats(
    IN p_date DATE
)
BEGIN
    SELECT 
        COUNT(DISTINCT c.user_id) as active_users,
        COUNT(c.id) as new_conversations,
        COUNT(m.id) as total_messages,
        AVG(m.processing_time) as avg_response_time
    FROM conversations c
    LEFT JOIN messages m ON c.id = m.conversation_id
    WHERE DATE(c.created_at) = p_date;
END$$

DELIMITER ;

-- 8. 创建触发器
DELIMITER $$

CREATE TRIGGER tr_update_conversation_message_count
AFTER INSERT ON messages
FOR EACH ROW
BEGIN
    UPDATE conversations 
    SET 
        message_count = message_count + 1,
        last_message = LEFT(NEW.content, 200),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
END$$

DELIMITER ;
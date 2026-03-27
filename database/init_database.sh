#!/bin/bash
# 数据库初始化脚本
# 请确保在database目录下运行此脚本

echo "开始初始化历史问答系统数据库..."

# ========== 核心修改：添加 MySQL 路径 ==========
# 替换成你自己的 MySQL 8.4.7 bin 目录路径！
MYSQL_PATH="C:/Program Files/MySQL/MySQL Server 8.4/bin/mysql.exe"
# 注意：MINGW64 中路径用 / 或 \\，不能用 \

# 设置变量
DB_HOST="localhost"
DB_PORT="3306"
DB_ROOT_USER="root"
DB_ROOT_PASS="123456"  
DB_NAME="history_qa"
DB_USER="history_user"
DB_PASS="History@2023"

echo "当前目录: $(pwd)"
echo "SQL脚本路径: sql/init.sql"

# 检查SQL文件是否存在
if [ ! -f "sql/init.sql" ]; then
    echo "错误: sql/init.sql 文件不存在！"
    exit 1
fi

# 1. 使用root用户执行初始化脚本（修改：用 MYSQL_PATH 替代 mysql）
echo "执行SQL初始化脚本..."
"$MYSQL_PATH" -h $DB_HOST -P $DB_PORT -u $DB_ROOT_USER -p"$DB_ROOT_PASS" < sql/init.sql

# 检查执行是否成功
if [ $? -eq 0 ]; then
    echo "✓ SQL脚本执行成功"
else
    echo "✗ SQL脚本执行失败"
    exit 1
fi

# 2. 验证数据库创建（修改：用 MYSQL_PATH 替代 mysql）
echo "验证数据库创建..."
"$MYSQL_PATH" -h $DB_HOST -P $DB_PORT -u $DB_ROOT_USER -p"$DB_ROOT_PASS" -e "SHOW DATABASES LIKE '$DB_NAME';"

# 3. 验证用户权限（修改：用 MYSQL_PATH 替代 mysql）
echo "验证用户权限..."
"$MYSQL_PATH" -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASS" -e "USE $DB_NAME; SHOW TABLES;"

echo "数据库初始化完成！"
echo "数据库: $DB_NAME"
echo "用户: $DB_USER"
echo "密码: $DB_PASS"
read -p "按任意键继续..." -n1 -s
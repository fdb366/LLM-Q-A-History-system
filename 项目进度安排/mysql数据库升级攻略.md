# MySQL 8.4 版本升级（MSI安装包）完整攻略指南
## 一、升级前准备
### 1. 环境检查
- 操作系统：Windows（支持Windows 10/11、Windows Server 2016+）
- 依赖组件：提前安装/修复 .NET Framework 4.8 和 Visual C++ 2019 运行库
- 权限：全程使用**管理员身份**执行命令/运行安装包
- 备份：升级前备份原有MySQL数据（如使用 `mysqldump` 导出数据库）

### 2. 下载安装包
从MySQL官网(https://dev.mysql.com/downloads/mysql/)下载对应版本的MSI安装包（MySQL 8.4 Server MSI），建议选择“Full”或“Custom”安装模式。

## 二、安装流程（解决MSI配置器报错问题）
### 1. 跳过安装时的服务配置
MSI安装向导中遇到“Configure MySQL Server as a Windows Service”环节时：
1. 默认勾选“Configure MySQL Server as a Windows Service”，继续完成安装，若弹出“Internal error (值不能为 null)”报错，点击“OK”关闭；
2.
<!-- 2. 取消勾选“Configure MySQL Server as a Windows Service”，继续完成安装；
3. 安装完成后，不运行“MySQL Configurator”，直接进行手动配置。 -->

### 2. 手动配置my.ini文件
#### （1）创建/修改配置文件
在MySQL安装目录（默认 `C:\Program Files\MySQL\MySQL Server 8.4`）下：
- 若存在 `my-default.ini`，复制并重命名为 `my.ini`；
- 若无模板，直接创建 `my.ini`，写入以下基础配置（路径需匹配实际安装目录）：
```ini
[mysqld]
# 基础路径配置
basedir=C:\Program Files\MySQL\MySQL Server 8.4
datadir=C:\ProgramData\MySQL\MySQL Server 8.4\Data
# 网络配置
port=3306
# 字符集与存储引擎
character-set-server=utf8mb4
default-storage-engine=INNODB
# 时区配置
default-time_zone='+8:00'

[mysql]
default-character-set=utf8mb4

[client]
port=3306
default-character-set=utf8mb4
```

#### （2）创建数据目录并配置权限
1. 手动创建数据目录：`C:\ProgramData\MySQL\MySQL Server 8.4\Data`（`ProgramData` 为隐藏目录，需显示隐藏项目或直接输入路径）；
2. 给Data目录赋权（解决权限不足问题）：
   - 图形界面：右键Data目录 → 属性 → 安全 → 编辑 → 添加 `NETWORK SERVICE` 用户，勾选“完全控制”权限；
   - 命令行（推荐，避免图形界面“应用不了”问题）：
   ```bash
   # 管理员身份执行
   takeown /f "C:\ProgramData\MySQL\MySQL Server 8.4\Data" /r /d y
   icacls "C:\ProgramData\MySQL\MySQL Server 8.4\Data" /grant "NETWORK SERVICE":F /t /c
   ```

### 3. 初始化数据库
以管理员身份打开命令行，进入MySQL的bin目录，执行初始化命令（`--defaults-file` 必须放在最前）：
```bash
cd "C:\Program Files\MySQL\MySQL Server 8.4\bin"
# 生成临时密码（推荐，生产环境）
mysqld --defaults-file="C:\Program Files\MySQL\MySQL Server 8.4\my.ini" --initialize --console
# 或免密码初始化（仅测试环境）
# mysqld --defaults-file="C:\Program Files\MySQL\MySQL Server 8.4\Data" --initialize-insecure --console
```
✅ 成功标志：日志显示 `A temporary password is generated for root@localhost: [临时密码]`（需记录临时密码）。

### 4. 注册并启动服务
```bash
# 注册服务（服务名MySQL84，可自定义）
mysqld.exe --install MySQL84 --defaults-file="C:\Program Files\MySQL\MySQL Server 8.4\my.ini"
# 启动服务
net start MySQL84
```
✅ 验证服务状态：`sc query MySQL84`，显示 `STATE: 4 RUNNING` 即为启动成功。

## 三、后续配置（必做）
### 1. 修改root临时密码
登录MySQL并修改临时密码（临时密码仅可使用一次）：
```bash
# 登录（输入初始化生成的临时密码）
mysql -u root -p
```
```sql
-- 修改为自定义密码（示例：123456，生产环境建议强密码）
ALTER USER 'root'@'localhost' IDENTIFIED BY '你的新密码';
-- 刷新权限
FLUSH PRIVILEGES;
-- 退出
exit;
```

### 2. 弱密码策略调整（可选）
若MySQL 8.4默认密码策略限制简单密码，可先调整策略再修改密码：
```sql
-- 登录后执行
SET GLOBAL validate_password.policy=0;  -- 降低密码强度要求
SET GLOBAL validate_password.length=6; -- 设置密码最小长度
```

## 四、常见问题排查
| 报错现象 | 核心原因 | 解决方案 |
|----------|----------|----------|
| 服务无法启动，提示“服务没有报告任何错误” | 数据目录未初始化/权限不足 | 1. 清空Data目录；2. 重新初始化；3. 配置NETWORK SERVICE权限 |
| 初始化报错“unknown variable 'defaults-file=xxx'” | --defaults-file参数位置错误 | 把--defaults-file放在命令最开头 |
| 初始化报错“data directory has files in it” | Data目录有残留文件 | 清空Data目录所有文件后重新初始化 |
| 权限配置“应用不了” | 未获取目录所有权 | 用takeown+icacls命令行强制赋权 |
| 修改密码报1064语法错误 | SQL语句缺少分号 | 每条语句末尾加`;`，分开执行ALTER和FLUSH命令 |

## 五、验证升级成功
```bash
# 重新登录MySQL
mysql -u root -p
# 查看版本
SELECT VERSION();
```
输出 `8.4.8`（对应安装版本）即为升级完成，可正常使用数据库。

## 六、注意事项
1. 安装/配置全程使用**管理员身份**，避免权限不足问题；
2. 数据目录建议放在非系统盘（如D盘），避免C盘空间不足；
3. 生产环境请勿使用弱密码，建议开启密码强度策略；
4. 若需卸载重装，需先停止服务→删除服务→清空Data目录→重新安装。
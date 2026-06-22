# 银行卡记账系统

基于 Django 6 的个人银行卡记账系统，默认使用 SQLite 本地数据库，也可以通过环境变量切换到 MySQL。支持多用户数据隔离，响应式设计，适配电脑和手机。

## 🚀 功能特性

### 核心功能
- ✅ **用户认证系统**：注册、登录、退出，数据完全隔离
- 💳 **银行卡管理**：添加、编辑、删除银行卡，自动汇总总余额
- 📝 **消费记账**：快速记账，自动扣减余额，支持8种消费分类
- 📊 **数据统计**：今日支出、本月支出、记录总数实时显示
- 📋 **消费流水**：按时间倒序展示，支持分类筛选
- 🔒 **数据安全**：数据库持久化存储，用户数据完全隔离

### 技术特点
- 🎨 响应式设计，完美适配手机/平板/电脑
- 🎯 Bootstrap 5 现代UI，美观简洁
- 🚄 Django ORM 自动建表，无需手写SQL
- 🔐 Django 自带认证系统，安全可靠
- 💾 默认 SQLite，支持按需切换到 MySQL

## 📦 项目结构

```
bank_ledger_django/
├── bank_ledger/          # Django 项目配置
│   ├── __init__.py
│   ├── settings.py      # 项目设置
│   ├── urls.py          # 路由配置
│   ├── wsgi.py
│   └── asgi.py
├── ledger/              # 记账应用
│   ├── migrations/      # 数据库迁移文件
│   ├── templates/       # 模板文件
│   │   └── ledger/
│   │       ├── base.html
│   │       ├── login.html
│   │       ├── register.html
│   │       ├── dashboard.html
│   │       ├── add_bank_card.html
│   │       ├── edit_bank_card.html
│   │       ├── delete_bank_card.html
│   │       ├── delete_expense.html
│   │       └── expenses_list.html
│   ├── __init__.py
│   ├── admin.py        # 后台管理
│   ├── apps.py
│   ├── models.py       # 数据模型
│   ├── views.py        # 视图函数
│   ├── forms.py        # 表单
│   └── urls.py         # 路由
├── manage.py           # Django 管理脚本
├── requirements.txt    # 依赖包
├── .env.example       # 环境变量示例
└── README.md          # 项目说明
```

## 🛠️ 安装步骤

### 1. 环境要求

- Python 3.12+
- SQLite（默认）或 MySQL 5.7+/8.0+
- pip 包管理器

### 2. 克隆项目

```bash
cd C:\Users\Kanyun\bank_ledger_django
```

### 3. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置数据库

默认使用项目根目录下的 `db.sqlite3`，本地开发可以直接跳到第 6 步。

如果要使用 MySQL，先在 MySQL 中创建数据库：


```sql
CREATE DATABASE bank_ledger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
copy .env.example .env
```

编辑 `.env` 文件，填写你的数据库信息：

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_ENGINE=sqlite
SQLITE_NAME=db.sqlite3

# MySQL Database Settings（DB_ENGINE=mysql 时使用）
DB_NAME=bank_ledger
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
```

如果要使用 MySQL，把 `DB_ENGINE` 改成 `mysql` 并填写 MySQL 连接信息。

### 7. 数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations

# 执行迁移（自动创建表）
python manage.py migrate
```

### 8. 创建超级管理员（可选）

```bash
python manage.py createsuperuser
```

按提示输入用户名、邮箱和密码。

### 9. 启动开发服务器

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 即可使用！

## 📱 使用说明

### 用户注册/登录
1. 访问首页会自动跳转到登录页
2. 点击"立即注册"创建新账户
3. 注册成功后自动登录

### 添加银行卡
1. 登录后进入首页
2. 点击"添加银行卡"按钮
3. 填写卡名、初始余额，选择图标
4. 保存后自动更新总余额

### 快速记账
1. 在首页找到"快速记账"表单
2. 选择银行卡、输入金额、选择分类
3. 可选填写备注和日期（默认今天）
4. 提交后自动扣减银行卡余额

### 查看记录
1. 首页显示最近20条消费记录
2. 点击"查看全部"可查看所有记录
3. 支持按分类筛选
4. 可删除记录，删除后自动恢复余额

### 后台管理
访问 http://127.0.0.1:8000/admin/ 使用超级管理员账号登录，可以管理所有用户和数据。

## 🗄️ 数据库设计

### BankCard（银行卡表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigAutoField | 主键 |
| user | ForeignKey | 关联用户 |
| name | CharField(100) | 卡名 |
| balance | DecimalField(12,2) | 余额 |
| icon | CharField(50) | 图标 |
| created_at | DateTimeField | 创建时间 |
| updated_at | DateTimeField | 更新时间 |

### Expense（消费记录表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigAutoField | 主键 |
| user | ForeignKey | 关联用户 |
| bank_card | ForeignKey | 关联银行卡 |
| amount | DecimalField(10,2) | 金额 |
| category | CharField(20) | 分类 |
| note | CharField(200) | 备注 |
| expense_date | DateField | 消费日期 |
| created_at | DateTimeField | 创建时间 |

## 🎨 界面预览

- **响应式布局**：自动适配手机、平板、电脑
- **现代简约风格**：渐变背景、毛玻璃卡片、柔和阴影
- **蓝色主色调**：科技感十足
- **绿色余额、红色支出**：直观的视觉反馈

## 🔧 常见问题

### 1. MySQL 连接失败
确保：
- MySQL 服务已启动
- `.env` 中的数据库配置正确
- `DB_ENGINE=mysql`
- 数据库已创建
- 已安装 `PyMySQL` 包

### 2. 迁移失败
```bash
# 删除所有迁移文件（保留 __init__.py）
# 删除数据库重新创建
python manage.py makemigrations
python manage.py migrate
```

### 3. 静态文件不显示
```bash
python manage.py collectstatic
```

### 4. MySQL 驱动问题
项目使用 `PyMySQL` 连接 MySQL，正常执行依赖安装即可：

```bash
pip install -r requirements.txt
```

## 🚀 生产部署

### 1. 关闭 DEBUG 模式
在 `.env` 中设置：
```env
DEBUG=False
```

### 2. 设置 ALLOWED_HOSTS
在 `.env` 中设置：
```env
ALLOWED_HOSTS=yourdomain.com,your-ip
```

### 3. 收集静态文件
```bash
python manage.py collectstatic
```

### 4. 使用 WSGI 服务器
推荐使用 Gunicorn + Nginx：
```bash
pip install gunicorn
gunicorn bank_ledger.wsgi:application --bind 0.0.0.0:8000
```

## 📄 License

MIT License

## 👨‍💻 作者

开发者：AI Assistant
日期：2026-04-22

---

**享受记账带来的理财乐趣！** 💰📊

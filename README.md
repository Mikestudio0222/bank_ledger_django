# 银行卡记账系统

基于 Django 4.2 的多用户个人记账系统，支持 SQLite / MySQL 双后端，Bootstrap 5 响应式 UI，邮箱验证注册。

## 功能

- **用户系统** — 注册（邮箱验证）、登录、退出，数据完全隔离
- **银行卡管理** — 添加/编辑/删除银行卡，余额自动汇总
- **消费记账** — AJAX 无刷新提交，8 种分类，原子化余额扣减
- **统计面板** — 今日支出、本月支出、记录总数实时更新
- **消费流水** — 无限滚动加载，按分类筛选
- **安全机制** — 注册/登录频率限制、CSRF 防护、HSTS、自动 session 超时

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 4.2, PyMySQL |
| 前端 | Bootstrap 5.3, Font Awesome 6.4, 原生 JS |
| 数据库 | SQLite（默认）/ MySQL |
| 部署 | Docker / Gunicorn + Nginx |

## 快速开始

### 环境要求

- Python 3.10+
- SQLite（默认）或 MySQL 5.7+

### 1. 克隆项目

```bash
git clone https://github.com/Mikestudio0222/bank_ledger_django.git
cd bank_ledger_django
```

### 2. 虚拟环境 & 依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置文件

```bash
cp .env.example .env
```

编辑 `.env`，必填项：

```env
SECRET_KEY=<生成随机密钥>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=sqlite

# 邮箱验证（必填，否则注册无法发送验证邮件）
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

> 开发阶段可将 `EMAIL_BACKEND` 设为 `django.core.mail.backends.console.EmailBackend`，验证链接会打印在终端。

### 4. 数据库迁移

```bash
python manage.py migrate
```

### 5. 启动

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/

## Docker 部署

```bash
docker-compose up -d
```

## 生产部署检查清单

- [ ] `.env` 中 `DEBUG=False`
- [ ] `SECRET_KEY` 已更换为随机值
- [ ] `ALLOWED_HOSTS` 包含真实域名
- [ ] `CSRF_TRUSTED_ORIGINS` 配置了 HTTPS 地址
- [ ] 邮箱 SMTP 配置正确
- [ ] 数据库从 SQLite 切换到 MySQL
- [ ] 运行 `python manage.py collectstatic` 收集静态文件
- [ ] 前端挂 Nginx 反代 + Gunicorn

## 项目结构

```
bank_ledger_django/
├── bank_ledger/          # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── ledger/               # 记账应用
│   ├── models.py         # BankCard / Expense 数据模型
│   ├── views.py          # 视图函数
│   ├── forms.py          # 表单 & 验证
│   ├── urls.py           # 路由
│   ├── admin.py          # Django Admin 配置
│   ├── tests.py          # 单元测试
│   ├── migrations/       # 数据库迁移
│   ├── static/           # CSS / JS / 字体（本地托管）
│   └── templates/        # Django 模板
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── manage.py
```

## 数据库表

### bank_cards
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigAuto | 主键 |
| user_id | FK → User | 所属用户 |
| name | CharField(100) | 卡名 |
| balance | DecimalField(12,2) | 余额 |
| icon | CharField(50) | Font Awesome 图标类名 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### expenses
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigAuto | 主键 |
| user_id | FK → User | 所属用户 |
| bank_card_id | FK → BankCard | 关联银行卡 |
| amount | DecimalField(10,2) | 金额 |
| category | CharField(20) | 分类（8 种） |
| note | CharField(200) | 备注 |
| expense_date | DateField | 消费日期 |
| created_at | DateTime | 创建时间 |

消费分类：餐饮 🍜 / 购物 🛍️ / 交通 🚗 / 娱乐 🎮 / 医疗 💊 / 教育 📚 / 住房 🏠 / 其他 📦

## License

MIT

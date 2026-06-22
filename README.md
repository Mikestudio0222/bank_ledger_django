# 记账工具

基于 Django 4.2 的多人记账系统，支持 SQLite / MySQL，Bootstrap 5 响应式 UI，邮箱验证注册。适配手机端，左滑删除、按压反馈等触觉交互。

## 功能

- **收支记录** — 支出 / 收入双类型，9 种分类，AJAX 无刷新提交，原子化余额变更
- **银行卡管理** — 弹窗增删改，余额独立显隐，渐变卡面
- **统计面板** — 今日支出 / 今日收入 / 本月支出 / 本月收入
- **触觉交互** — 按钮按压缩放、左滑露出删除、删除滑出动画
- **安全** — 邮箱验证注册、登录/注册频率限制、CSRF、HSTS、session 超时
- **无限滚动** — 全部记录页滚动自动加载

## 技术栈

| 层 | 技术 |
|------|------|
| 后端 | Django 4.2, PyMySQL, Gunicorn |
| 前端 | Bootstrap 5.3, Font Awesome 6.4, 原生 JS |
| 数据库 | SQLite / MySQL |
| 部署 | systemd + Gunicorn + Nginx，或 Docker Compose |

## 本地开发

### 环境

- Python 3.10+
- SQLite（默认）

### 启动

```bash
git clone https://github.com/Mikestudio0222/bank_ledger_django.git
cd bank_ledger_django
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env: 设置 SECRET_KEY, 配置邮箱 SMTP（或用 console backend）
python manage.py migrate
python manage.py runserver
```

访问 http://127.0.0.1:8000/

> 开发阶段可在 `.env` 中设 `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`，验证链接会打印在终端。

## 生产部署（裸机，推荐）

适用于阿里云 2C2G 等轻量服务器。

### 1. 环境

```bash
apt update && apt install -y python3 python3-pip python3-venv nginx mysql-server
systemctl enable --now mysql
```

### 2. 创建数据库

```bash
mysql -u root <<SQL
CREATE DATABASE bank_ledger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'ledger'@'localhost' IDENTIFIED BY '你的密码';
GRANT ALL PRIVILEGES ON bank_ledger.* TO 'ledger'@'localhost';
FLUSH PRIVILEGES;
SQL
```

### 3. 部署项目

```bash
cd /opt
git clone https://github.com/Mikestudio0222/bank_ledger_django.git ledger
cd ledger
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env: DEBUG=False, ALLOWED_HOSTS=你的IP, DB_ENGINE=mysql, 填写数据库和邮箱
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 4. 配置 Gunicorn（systemd）

创建 `/etc/systemd/system/ledger.service`：

```ini
[Unit]
Description=Ledger Gunicorn
After=network.target mysql.service

[Service]
User=root
WorkingDirectory=/opt/ledger
EnvironmentFile=/opt/ledger/.env
ExecStart=/opt/ledger/venv/bin/gunicorn bank_ledger.wsgi:application \
    --bind 127.0.0.1:8000 --workers 2 --threads 2
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now ledger
```

### 5. 配置 Nginx

创建 `/etc/nginx/sites-available/ledger`：

```nginx
server {
    listen 80;
    server_name _;

    location /static/ {
        alias /opt/ledger/staticfiles/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/ledger /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

### 6. 阿里云安全组放行 80 端口

控制台 → 安全组 → 入方向 → 添加 80 端口。

### 更新代码

```bash
cd /opt/ledger
git pull
source venv/bin/activate
python manage.py migrate
systemctl restart ledger
```

## Docker 部署

如果更习惯容器方案：

```bash
cp .env.example .env  # 编辑配置
docker compose up -d
```

架构：Nginx (80) → Gunicorn (8000) → Django，MySQL 8.0 独立容器。

## 项目结构

```
├── bank_ledger/          # Django 项目配置
│   ├── settings.py, urls.py, wsgi.py, asgi.py
├── ledger/               # 记账应用
│   ├── models.py         # BankCard / Expense 数据模型
│   ├── views.py          # 视图 & AJAX 接口
│   ├── forms.py          # 表单 & 验证
│   ├── admin.py          # Django Admin 配置
│   ├── tests.py          # 单元测试
│   ├── migrations/       # 数据库迁移
│   ├── static/           # CSS/JS/字体（Bootstrap + FA 本地托管）
│   └── templates/        # Django 模板
├── manage.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── nginx.conf            # Nginx 配置（Docker 用）
└── entrypoint.sh         # Docker 入口脚本
```

## 数据库

### bank_cards

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigAuto | 主键 |
| user_id | FK → User | 所属用户 |
| name | CharField(100) | 卡名 |
| balance | DecimalField(12,2) | 余额 |
| icon | CharField(50) | Font Awesome 图标 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### expenses

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigAuto | 主键 |
| user_id | FK → User | 所属用户 |
| bank_card_id | FK → BankCard | 关联银行卡 |
| record_type | CharField(10) | expense / income |
| amount | DecimalField(10,2) | 金额 |
| category | CharField(20) | 分类（9 种） |
| note | CharField(200) | 备注 |
| expense_date | DateField | 日期 |
| created_at | DateTime | 创建时间 |

分类：🍜 餐饮 / 🛍️ 购物 / 🚗 交通 / 🎮 娱乐 / 💊 医疗 / 📚 教育 / 🏠 住房 / 💰 薪资 / 📦 其他

## License

MIT

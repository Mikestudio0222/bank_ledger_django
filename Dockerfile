# 使用官方轻量级 Python 3.12 环境
FROM python:3.12-slim

# 2. 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. 设置工作目录（在容器内部创建一个叫 /app 的文件夹）
WORKDIR /app

# 4. 复制装备清单并安装依赖
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 把当前目录下的所有项目文件复制到容器的 /app 里
COPY . /app/

# 6. 暴露 8000 端口
EXPOSE 8000

# 7. 启动命令（和你在本地敲的一模一样）
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
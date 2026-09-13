# CUMCM Coach Skill v7 Dockerfile
# 基于 Python 3.13 slim 镜像

FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 系统依赖：构建工具 + XeLaTeX（含中文支持，用于编译论文）
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    git \
    texlive-xetex \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-lang-chinese \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p logs output state reports

# 默认命令：运行烟雾测试
CMD ["python", "-m", "pytest", "tests/test_algorithms_smoke.py", "-v"]

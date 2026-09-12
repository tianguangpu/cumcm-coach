# CUMCM Coach Skill v7 Makefile
# 自动化命令集合

.PHONY: help install test lint format benchmark paper clean docker

# 默认目标
help:
	@echo "CUMCM Coach Skill v7 - 可用命令:"
	@echo ""
	@echo "  make install      安装依赖"
	@echo "  make test         运行单元测试"
	@echo "  make test-cov     运行测试并生成覆盖率报告"
	@echo "  make lint         代码规范检查"
	@echo "  make format       代码格式化"
	@echo "  make benchmark    运行基准测试"
	@echo "  make paper        编译论文"
	@echo "  make docker       Docker 构建并运行测试"
	@echo "  make clean        清理临时文件"
	@echo "  make pre-commit   安装 pre-commit hooks"
	@echo ""

# 安装依赖（含开发工具：pytest / ruff / black / mypy / pre-commit）
install:
	pip install -e ".[dev]"

# 仅安装核心依赖
install-core:
	pip install -e .

# 运行单元测试
test:
	python -m pytest tests/ -v -x

# 运行测试并生成覆盖率报告
test-cov:
	python -m pytest tests/ -v --cov=algorithms --cov-report=html --cov-report=term-missing
	@echo "覆盖率报告已生成: htmlcov/index.html"

# 运行烟雾测试
smoke:
	python -m pytest tests/test_algorithms_smoke.py -v

# 代码规范检查（配置见 pyproject.toml [tool.ruff]）
lint:
	ruff check algorithms/ scripts/ utils/ tests/
	black --check algorithms/ scripts/ utils/ tests/

# 代码格式化
# 注：ruff format 在 0.16.x 对部分含多字节字符的文件会触发 Rust panic
# （上游 bug，非本项目代码问题），故格式化改用 black，import 排序仍由 ruff 负责
format:
	black algorithms/ scripts/ utils/ tests/
	ruff check --fix algorithms/ scripts/ utils/ tests/

# 基准测试
benchmark:
	python scripts/benchmark_viz.py --output reports/benchmark.png
	@echo "基准测试报告已生成: reports/benchmark.png"

# 编译论文（XeLaTeX）
paper:
	cd paper && xelatex main.tex && xelatex main.tex
	@echo "论文已编译: paper/main.pdf"

# Docker 构建并运行测试
docker:
	docker-compose build
	docker-compose run --rm test

# 清理临时文件
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	@echo "临时文件已清理"

# 安装 pre-commit hooks
pre-commit:
	pre-commit install
	@echo "pre-commit hooks 已安装"

# 运行 pre-commit 检查
pre-commit-run:
	pre-commit run --all-files

# 项目初始化
init:
	python scripts/init_project.py --team "202600001" --members "成员1,成员2,成员3" --type B
	@echo "项目已初始化"

# 运行全链流水线（干跑）
dry-run:
	python scripts/run_all.py --dry

# 运行全链流水线
run:
	python scripts/run_all.py

# 生成代码清单
manifest:
	python scripts/gen_code_manifest.py --check-deps --check-syntax

# 参考文献检查
refs:
	python scripts/check_references.py --tex paper/main.tex

# AI 合规检查
ai-check:
	python scripts/ai_compliance.py all

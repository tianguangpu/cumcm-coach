# 贡献指南

感谢您对 CUMCM Coach Skill v7 的关注！本文档将指导您如何参与项目贡献。

---

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境](#开发环境)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [测试要求](#测试要求)
- [文档贡献](#文档贡献)

---

## 行为准则

本项目采用开放、包容的态度。请尊重每一位贡献者，保持专业和友善的沟通。

---

## 如何贡献

### 报告 Bug

1. 检查 [Issues](../../issues) 确认问题未被报告
2. 创建新 Issue，包含：
   - 清晰的标题和描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（Python版本、OS等）
   - 相关日志/截图

### 提交功能请求

1. 创建 Issue，标签为 `enhancement`
2. 描述功能的使用场景和预期效果
3. 等待讨论和确认

### 提交代码

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改（遵循提交规范）
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

---

## 开发环境

### 环境准备

```bash
# 克隆项目
git clone <repo-url>
cd cumcm-coach

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt  # 如果存在
pip install pytest pytest-cov black flake8 pre-commit

# 安装 pre-commit hooks
pre-commit install
```

### 目录结构

```
cumcm-coach/
├── scripts/          # 工具脚本
├── algorithms/       # 算法库
├── templates/        # 论文模板
├── references/       # 参考文档
├── tests/            # 测试套件
├── vault/            # Obsidian知识库
└── utils/            # 工具模块
```

---

## 代码规范

### Python 风格

- 遵循 [PEP 8](https://peps.python.org/pep-0008/)
- 使用 Black 格式化（行宽 120）
- 使用 Flake8 检查

### 命名约定

| 类型 | 风格 | 示例 |
|------|------|------|
| 模块/函数 | snake_case | `genetic_algorithm.py`, `solve_vrp()` |
| 类 | PascalCase | `GeneticAlgorithm`, `SolverResult` |
| 常量 | UPPER_SNAKE_CASE | `MAX_ITERATIONS`, `DEFAULT_POP_SIZE` |
| 私有成员 | _leading_underscore | `_validate_params()` |

### Docstring 格式

使用 Google 风格 docstring：

```python
def solve(self, objective: Callable, bounds: List[Tuple]) -> SolverResult:
    """
    求解优化问题。

    Args:
        objective: 目标函数，接受参数 x 返回标量值
        bounds: 变量边界列表，每个元素为 (lower, upper) 元组

    Returns:
        SolverResult: 包含最优解 x_opt、最优值 f_opt、收敛历史 history

    Raises:
        ValueError: 当 bounds 格式不正确时

    Examples:
        >>> def sphere(x):
        ...     return sum(xi**2 for xi in x)
        >>> result = solver.solve(sphere, [(-5, 5)] * 3)
        >>> print(result.f_opt)
        0.00123
    """
    pass
```

### 类型提示

- 所有公共函数必须有类型提示
- 使用 `typing` 模块的类型定义

```python
from typing import List, Tuple, Callable, Optional
from dataclasses import dataclass

@dataclass
class SolverResult:
    x_opt: List[float]
    f_opt: float
    history: Optional[List[float]] = None
```

---

## 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具链 |
| `ci` | CI/CD 相关 |

### 示例

```
feat(algorithm): 新增 NSGA-II 多目标优化算法

- 实现非支配排序
- 实现拥挤度计算
- 添加单元测试

Closes #123
```

---

## Pull Request 流程

### PR 标题

遵循 Commit Message 格式。

### PR 描述模板

```markdown
## 变更说明

简要描述本次变更的内容。

## 变更类型

- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 重构
- [ ] 性能优化
- [ ] 测试相关

## 测试

- [ ] 已添加/更新单元测试
- [ ] 所有测试通过
- [ ] 覆盖率 ≥ 80%

## 检查清单

- [ ] 代码遵循项目规范
- [ ] 已更新相关文档
- [ ] 已更新 CHANGELOG.md
- [ ] 无 merge 冲突
```

### PR 流程

1. 确保所有测试通过：`make test`
2. 确保代码规范：`make lint`
3. 更新 CHANGELOG.md
4. 创建 PR，填写描述模板
5. 等待 Code Review
6. 根据反馈修改
7. 合并到主分支

---

## 测试要求

### 测试框架

- 使用 pytest
- 目标覆盖率 ≥ 80%

### 测试文件组织

```
tests/
├── conftest.py              # pytest 配置和 fixtures
├── test_algorithms.py       # 算法单元测试
├── test_scripts.py          # 脚本测试
└── test_e2e.py              # 端到端测试
```

### 测试命名规范

```python
# 文件名：test_<模块名>.py
# 类名：Test<功能名>
# 函数名：test_<行为描述>

class TestGeneticAlgorithm:
    def test_convergence_on_sphere_function(self):
        """GA 应在 200 代内找到 Sphere 函数近似最优解"""
        pass
    
    def test_invalid_bounds_raises_error(self):
        """无效边界应抛出 ValueError"""
        pass
```

### 运行测试

```bash
# 运行所有测试
make test

# 运行特定测试
pytest tests/test_algorithms.py -v

# 生成覆盖率报告
pytest --cov=algorithms --cov-report=html

# 运行烟雾测试
pytest tests/test_algorithms_smoke.py -v
```

### 测试最佳实践

- 每个测试只验证一个行为
- 使用 fixtures 管理测试数据
- 使用 mock 隔离外部依赖
- 测试边界条件和异常情况

---

## 文档贡献

### 文档类型

| 文档 | 位置 | 说明 |
|------|------|------|
| README | `README.md` | 项目概览 |
| CHANGELOG | `CHANGELOG.md` | 版本历史 |
| API 文档 | Docstring | 自动生成 |
| 知识库 | `vault/` | Obsidian 笔记 |
| 参考文档 | `references/` | 使用指南 |

### 文档规范

- 使用中文撰写
- 保持简洁清晰
- 包含代码示例
- 及时更新

---

## 算法贡献

### 新增算法模板

```python
"""
算法名称

简要描述算法原理和适用场景。

Reference:
    - 论文引用
"""

from typing import List, Tuple, Callable, Optional
from dataclasses import dataclass
from algorithms.base import BaseSolver, SolverResult

class NewAlgorithm(BaseSolver):
    """算法描述"""
    
    def __init__(self, pop_size: int = 50, max_iter: int = 200):
        """
        初始化算法参数。
        
        Args:
            pop_size: 种群大小
            max_iter: 最大迭代次数
        """
        self.pop_size = pop_size
        self.max_iter = max_iter
    
    def solve(self, objective: Callable, bounds: List[Tuple]) -> SolverResult:
        """
        求解优化问题。
        
        Args:
            objective: 目标函数
            bounds: 变量边界
            
        Returns:
            SolverResult: 求解结果
        """
        # 实现算法逻辑
        pass
    
    def validate_params(self) -> bool:
        """验证参数有效性"""
        if self.pop_size <= 0:
            raise ValueError("pop_size must be positive")
        if self.max_iter <= 0:
            raise ValueError("max_iter must be positive")
        return True
```

### 算法测试模板

```python
import pytest
from algorithms.optimization.new_algorithm import NewAlgorithm

class TestNewAlgorithm:
    def test_sphere_function(self):
        """测试 Sphere 函数收敛性"""
        def sphere(x):
            return sum(xi**2 for xi in x)
        
        algo = NewAlgorithm(pop_size=50, max_iter=200)
        result = algo.solve(sphere, [(-5, 5)] * 3)
        
        assert result.f_opt < 0.01
        assert len(result.x_opt) == 3
    
    def test_invalid_params(self):
        """测试无效参数处理"""
        with pytest.raises(ValueError):
            algo = NewAlgorithm(pop_size=-1)
            algo.validate_params()
```

---

## 获取帮助

- 创建 Issue 提问
- 查看 [README.md](README.md) 了解项目结构
- 查看 [CHANGELOG.md](CHANGELOG.md) 了解版本历史

---

## 致谢

感谢所有贡献者的付出！

---

**[⬆ 回到顶部](#贡献指南)**

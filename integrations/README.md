# 集成模块

本目录收录**本仓库作者开发、或许可兼容（MIT）**的绘图与图表模块，使
cumcm-coach 在克隆后即可自包含使用，无需额外安装其他 Skill。

---

## 许可与来源

| 目录 | 来源 | 许可 |
|------|------|------|
| [`figure-skill/`](figure-skill/) | 本仓库作者 | MIT |
| [`diagram-design/`](diagram-design/) | 第三方，MIT 许可 | MIT（保留原声明） |
| [`mathmodel-figure-templates/`](mathmodel-figure-templates/) | 本仓库作者 | MIT |
| [`nature-plot-repro/`](nature-plot-repro/) | 本仓库作者（方法论部分） | MIT |

### 各模块职责

| 模块 | 负责 | 触发场景 |
|------|------|---------|
| `figure-skill` | 常规数据图（折线/柱状/散点/热图/雷达/收敛/3D 曲面） | Python 出图；SimHei 字体、5 套学术色板、300dpi PNG + 矢量 PDF 双导出 |
| `diagram-design` | 流程图 / 概念图（技术路线、算法流程、泳道图、时间线等 27 种图型） | 需要编辑级 HTML+SVG 图表；灰度无彩色规范 |
| `mathmodel-figure-templates` | Python 高级图型（SHAP、山脊图、蜂群图、小提琴图、UpSet、冲积图） | 需要 `figure-skill` 覆盖不到的高级图型，且无 MATLAB |
| `nature-plot-repro` | 图型选型方法与工作流（复刻顶刊配图） | "Nature 同款""顶刊风格""期刊配图" |

四者的完整分工与调用顺序见
[`../references/figure-routing.md`](../references/figure-routing.md)。

---

## 关于 nature-plot-repro 的案例库（重要）

`nature-plot-repro` 的完整版包含 **26 个 MATLAB 案例**（环形柱状图、桑基图、
弦图、泰勒图、扇形热图、小提琴图、UpSet 图等）。**本仓库未收录这些案例。**

**原因**：案例代码源自 [slandarer/PLTreprint](https://github.com/slandarer/PLTreprint)
开源项目，采用 **GPL-2** 协议。GPL-2 是 copyleft 许可，要求衍生作品同样以
GPL-2 分发；将其并入本仓库（MIT）会造成许可冲突。

**如需使用这些案例**：

1. 从上述项目自行获取，并遵守其 GPL-2 协议
2. 使用时**必须保留原作者署名注释**（案例文件中已包含）
3. 注意：若你的项目因此以 GPL-2 分发，其后将不能用于商业闭源场景

本目录中的 `nature-plot-repro/` **仅含作者自写的选型方法与工作流说明**
（`SKILL.md` 与 `references/figure-recipes.md`），不含任何第三方 GPL 代码，
可安全地以 MIT 方式使用。

---

## 与原 Skill 的关系

这四个模块原本是独立安装的 Claude Code Skill。此处收录一份副本，目的是：

- **自包含**：克隆本仓库即可使用，无需另外安装四个 Skill
- **版本锁定**：集成内容随本仓库版本一起演进，避免 Skill 版本漂移导致行为不一致

若你已在 `~/.claude/skills/` 下安装了同名 Skill，两者可以共存；
本仓库内的副本仅在其自身路径下被 `references/figure-routing.md` 的路由引用。

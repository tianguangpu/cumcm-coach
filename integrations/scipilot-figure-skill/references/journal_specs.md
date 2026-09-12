# 期刊图表规范
主流期刊对投稿图表的硬性要求汇总。

## 目录
- [Nature 系列](#nature-系列)
- [Science](#science)
- [IEEE](#ieee)
- [Elsevier 系列](#elsevier-系列)
- [PNAS](#pnas)
- [中文核心期刊通用要求](#中文核心期刊通用要求)
- [跨期刊速查表](#跨期刊速查表)
- [中文字体安装指南](#中文字体安装指南)

---

## Nature 系列
涵盖 *Nature*、*Nature Methods*、*Nature Communications* 等。
| 维度 | 要求 |
|---|---|
| 单栏宽 | **89 mm ≈ 3.5 inch** |
| 双栏宽 | **183 mm ≈ 7.2 inch** |
| 最大高 | 247 mm ≈ 9.7 inch |
| 字号 | 标签/刻度 5–7 pt，绝不小于 5 pt |
| 推荐字体 | **Helvetica / Arial**（无衬线） |
| 矢量首选 | **EPS** / PDF / AI |
| 位图 | TIFF / PNG，**>= 300 DPI**；线条图 >= 600 DPI |
| 行宽 | 0.25–1 pt（建议 0.6） |
| 颜色 | RGB；色盲安全；避免红绿对比 |
| 子图标签 | **a, b, c**（小写、加粗、放左上角） |

## Science
| 维度 | 要求 |
|---|---|
| 单栏宽 | **55 mm ≈ 2.2 inch**（极窄）|
| 双栏宽 | **183 mm ≈ 7.2 inch** |
| 字号 | 5–7 pt |
| 推荐字体 | **Helvetica / Arial** |
| 矢量首选 | PDF / EPS / AI |
| 位图 | TIFF / PNG **>= 300 DPI** |
| 子图标签 | **A, B, C**（大写、加粗、左上） |

## IEEE
涵盖 *Trans on PAMI* / *Trans on Image Processing* / 会议（CVPR、ICCV 等）。
| 维度 | 要求 |
|---|---|
| 单栏宽 | **3.5 inch ≈ 88.9 mm** |
| 双栏宽 | **7.16 inch ≈ 181.9 mm** |
| 字号 | 8–10 pt |
| 推荐字体 | **Times New Roman**（衬线） |
| 矢量首选 | PDF / EPS |
| 位图 | **600 DPI**（线条图）/ 300 DPI（照片） |
| 黑白可读 | **明确要求**——线型 + marker + 颜色三重冗余编码 |
| 子图标签 | (a) (b) (c) 小写带括号 |

## Elsevier 系列
涵盖 *Cell* / *Neuron* / *Cell Reports* 等。
| 维度 | 要求 |
|---|---|
| 单栏宽 | **90 mm ≈ 3.54 inch** |
| 双栏宽 | **190 mm ≈ 7.48 inch** |
| 字号 | 7–9 pt |
| 推荐字体 | Helvetica / Arial（无衬线） |
| 矢量首选 | EPS / PDF |
| 位图 | **300 DPI（彩色 + 灰度）**；线条图 1000 DPI |
| 子图标签 | (A) (B) (C) 大写带括号 |

## PNAS
| 维度 | 要求 |
|---|---|
| 单栏宽 | **8.7 cm ≈ 3.42 inch** |
| 双栏宽 | **17.8 cm ≈ 7.0 inch** |
| 字号 | 6–8 pt |
| 推荐字体 | Helvetica / Arial / Times |
| 矢量首选 | PDF / EPS |
| 位图 | 300 DPI（彩色）/ 600 DPI（黑白） |
| 子图标签 | (A) (B) (C) |

## 中文核心期刊通用要求
适用于 *中国科学* 系列、*物理学报*、*中华医学杂志* 等。
| 维度 | 通用要求 |
|---|---|
| 单栏宽 | **8 cm ≈ 3.15 inch** |
| 双栏宽 | **17 cm ≈ 6.7 inch** |
| 字号 | 中文 6 号（≈8 pt）/ 小 5 号（≈9 pt） |
| 字体 | **中文宋体 + 西文/数字 Times New Roman** 混排 |
| 矢量 | EPS / PDF（部分接受 TIFF） |
| 位图 | **>= 600 DPI**（线条图）/ 300 DPI（照片） |
| 子图标签 | (a) (b) (c) 或 (甲) (乙) (丙) |

## 跨期刊速查表
| 期刊 | 单栏 (inch) | 双栏 (inch) | 字号 (pt) | 推荐字体 | DPI | 矢量首选 |
|---|---|---|---|---|---|---|
| Nature | 3.5 | 7.2 | 5–7 | Helvetica/Arial | 300+ | EPS/PDF |
| Science | 2.2 | 7.2 | 5–7 | Helvetica/Arial | 300+ | PDF/EPS |
| IEEE | 3.5 | 7.16 | 8–10 | Times | 600 | PDF/EPS |
| Elsevier | 3.54 | 7.48 | 7–9 | Helvetica/Arial | 300+ | EPS/PDF |
| PNAS | 3.42 | 7.0 | 6–8 | Helvetica/Times | 300+ | PDF/EPS |
| 中文核心 | 3.15 | 6.7 | 8–9 | 宋体+TNR | 600 | PDF |

## 中文字体安装指南
`setup_style(lang='zh')` 会按优先级查找：
```
Noto Sans CJK SC  >  Source Han Sans SC  >  SimHei  >  Microsoft YaHei
```
宋体混排（`serif_for_zh=True`）时优先：
```
Noto Serif CJK SC  >  Source Han Serif SC  >  SimSun  >  STSong
```
如果一个都没有，会抛出清晰的安装指南。

### Windows
1. 去 https://github.com/notofonts/noto-cjk/releases 下载
2. 解压，全选 `.otf`/`.ttf` 文件，右键 **"为所有用户安装"**
3. 重启 Python，或删 matplotlib 缓存

### 验证
```bash
python scripts/setup_style.py --list-fonts
```
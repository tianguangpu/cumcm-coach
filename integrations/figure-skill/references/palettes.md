# 5 套学术调色板（Python/matplotlib 版）

## 1. Nature — 顶级综合刊
- **适用**：多线对比、散点分组、雷达图
- **特点**：柔和不刺眼，Nature/Science 通用
```python
pal = get_palette('Nature', n=4)
# 色值: #0072B2, #E64B35, #5B9ED5, #F5A000
```

## 2. Science — 高饱和
- **适用**：强调对比、关键指标高亮
- **特点**：高饱和，Cell 风格
```python
pal = get_palette('Science', n=3)
# 色值: #FF0000, #0000FF, #00AA00
```

## 3. Qualitative — ColorBrewer 12 色
- **适用**：热力图分类、离散分组（≥6 类）
- **特点**：色盲安全
```python
pal = get_palette('Qualitative', n=8)
```

## 4. Diverging — 发散色
- **适用**：相关性热力图、残差图、3D 曲面
- **特点**：红蓝发散，0 值居中白
```python
cmap = get_colormap('Diverging')
```

## 5. IEEE — 专业工程
- **适用**：工程优化、控制、信号处理
- **特点**：稳重专业
```python
pal = get_palette('IEEE', n=4)
```

## 按图型选择

| 图型 | 推荐调色板 |
|------|-----------|
| 热力图/相关性 | Diverging |
| 雷达图/多方案 | Nature 或 Qualitative |
| 收敛曲线/多算法 | Nature |
| 3D 曲面 | Diverging |
| 单变量趋势 | Science 双色 |

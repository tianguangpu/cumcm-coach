# 10 种高级绘图技法（Python 版）

## 技法1：3D 曲面 + 等高线投影
```python
from mpl_toolkits.mplot3d import axes3d
fig = plt.figure(figsize=(14,9))
ax = fig.add_subplot(111, projection='3d')
X, Y = np.meshgrid(np.linspace(-3,3,80), np.linspace(-3,3,80))
Z = np.sin(X) * np.cos(Y)
cmap = get_colormap('Diverging')
surf = ax.plot_surface(X, Y, Z, cmap=cmap, alpha=0.9, edgecolor='none')
ax.contour(X, Y, Z, zdir='z', offset=Z.min(), cmap=cmap, levels=15)
fig.colorbar(surf, shrink=0.5)
```

## 技法2：双变量编码散点
```python
pal = get_palette('Nature', 4)
for i, grp in enumerate(groups):
    ax.scatter(x[grp], y[grp], w[grp], c=[pal[i]], alpha=0.6,
               edgecolors='black', linewidth=0.3, label=f'类别{i+1}')
```

## 技法3：多子图组合 (2×2)
```python
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.flatten()
# (a) 3D曲面
ax3d = fig.add_subplot(221, projection='3d')
# (b) XZ剖面
axes[1].plot(x, z_x, 'r-', linewidth=2)
# (c) YZ剖面
axes[2].plot(y, z_y, 'b-', linewidth=2)
# (d) 等高线
axes[3].contourf(X, Y, Z, cmap=get_colormap('Diverging'))
for ax, label in zip(axes, ['(a)','(b)','(c)','(d)']):
    ax.set_title(label, fontsize=10)
```

## 技法4：可行域填充
```python
x = np.linspace(0, 10, 200)
yy = np.minimum(8-0.5*x, 6)
ax.fill_between(x, 0, yy, color=get_palette('Nature',1), alpha=0.18)
ax.plot(x, 8-0.5*x, '--', color=get_palette('Nature',2), linewidth=1.5)
ax.plot(4, 6, 'r*', markersize=15, label='最优解')
```

## 技法5：收敛曲线对比
```python
pal = get_palette('Nature', 2)
ax.semilogy(x, conv1, '-', color=pal[0], linewidth=2, marker='o', markersize=3)
ax.semilogy(x, conv2, '--', color=pal[1], linewidth=2, marker='s', markersize=3)
ax.text(120, 7, '改进算法提升41%', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
```

## 技法6：极坐标玫瑰图
```python
angles = np.linspace(0, 2*np.pi, 24, endpoint=False)
ax = fig.add_subplot(111, projection='polar')
ax.bar(angles, values, width=0.2, color=get_palette('Qualitative', 6), alpha=0.8)
```

## 技法7：雷达图多维对比
```python
# 参见 SKILL.md 示例3
```

## 技法8：热力图 + 显著性星号
```python
# 参见 SKILL.md 示例2
```

## 技法9：图中图放大 (inset)
```python
ax_main = fig.add_subplot(111)
axins = ax_main.inset_axes([0.55, 0.55, 0.35, 0.35])
axins.plot(x[350:450], y[350:450], 'r-', linewidth=1.5)
axins.set_title('局部放大', fontsize=9)
ax_main.indicate_inset_zoom(axins)
```

## 技法10：置信带 + 阈值线
```python
ax.fill_between(t, lo, hi, color=get_palette('Science',1), alpha=0.2)
ax.plot(t, mu, '-', color=get_palette('Science',1), linewidth=2.5)
ax.axhline(60, '--', color=get_palette('Science',2), linewidth=2)
```

## 标注优化

```python
# 不遮挡的标注方式
ax.annotate('峰值', xy=(x_max, y_max), xytext=(x_max+2, y_max+2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
            fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9,
                     edgecolor='black', linewidth=0.8))
```

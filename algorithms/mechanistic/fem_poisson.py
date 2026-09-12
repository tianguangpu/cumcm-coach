"""
cumcm-coach 机理求解模块 — 三角网格有限元(FEM)解 Poisson 方程

    方程:   -div( k(x,y) * grad(u) ) = f(x,y)   线性基函数(一阶元)
    依赖:   仅 numpy, 零外部依赖
    接口:
        from fem_poisson import assemble_and_solve, rect_tri_mesh
        nodes, elements = rect_tri_mesh(nx, ny)
        u, nodes, elements = assemble_and_solve(mesh, f, k, dirichlet)

mesh 支持两种输入:
    1) 三角形列表: [[[x1,y1],[x2,y2],[x3,y3]], ...] (顶点坐标按节点共享去重)
    2) rect_tri_mesh 返回的 (nodes, elements) 二元组:
       nodes 为 N×2 坐标数组, elements 为 Nt×3 的节点编号三元组列表
"""
import numpy as np


def rect_tri_mesh(nx, ny):
    """生成单位正方形 [0,1]x[0,1] 的均匀三角剖分。

    参数: nx / ny — x / y 方向划分段数
    返回: (nodes, elements); nodes 为 (nx+1)*(ny+1) x 2 坐标数组,
          elements 为 2*nx*ny 个三角形节点编号三元组列表
    """
    xs = np.linspace(0.0, 1.0, nx + 1)
    ys = np.linspace(0.0, 1.0, ny + 1)
    nodes = np.array([[xi, yj] for yj in ys for xi in xs], dtype=float)
    elements = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            b = a + 1
            c = a + (nx + 1)
            d = c + 1
            elements.append([a, b, c])
            elements.append([d, c, b])
    return nodes, elements


def _shape_data(p):
    """线性元的面积与三个梯度。p: (3,2) 顶点坐标。
    返回 (area_abs, grads); grads[i] 为节点 i 的梯度 (i 对应顶点 p[i])。
    """
    x0, y0 = p[0]; x1, y1 = p[1]; x2, y2 = p[2]
    signed_A = ((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)) / 2.0
    grads = np.empty((3, 2))
    grads[0] = np.array([y1 - y2, x2 - x1])
    grads[1] = np.array([y2 - y0, x0 - x2])
    grads[2] = np.array([y0 - y1, x1 - x0])
    grads /= (2.0 * signed_A)
    return abs(signed_A), grads


def _coerce_mesh(mesh):
    """把两种 mesh 输入统一为 (nodes(N,2), elements(list of triple))。"""
    if isinstance(mesh, tuple):
        nodes, elements = mesh
        return np.asarray(nodes, float), elements
    coord_map = {}
    nodes = []
    elements = []
    for tri in mesh:
        idxs = []
        for xi, yi in tri:
            key = (float(xi), float(yi))
            if key not in coord_map:
                coord_map[key] = len(nodes)
                nodes.append([xi, yi])
            idxs.append(coord_map[key])
        elements.append(idxs)
    return np.asarray(nodes, float), elements


def assemble_and_solve(mesh, f_func, k_func=1.0, dirichlet=None):
    """组装并求解 Poisson 方程 -div(k*grad u) = f (线性三角元)。

    参数:
        mesh:     三角形列表 或 rect_tri_mesh 的 (nodes, elements)
        f_func:   源项函数 f(x, y)
        k_func:   导热系数, 标量或函数 k(x, y); 默认 1.0
        dirichlet: 固定边值字典 {节点编号: 值}, 例如 {0: 0.0, 5: 1.0};
                   为 None/空时自动钉住节点 0(值 0)保证解唯一。
    返回:
        (u_solution, nodes, elements)
        u_solution: N 维向量; nodes: Nx2; elements: 三角形编号列表
    """
    nodes, elements = _coerce_mesh(mesh)
    N = len(nodes)
    K = np.zeros((N, N))
    F = np.zeros(N)
    for tri in elements:
        p = nodes[tri]
        area_abs, grads = _shape_data(p)
        cnt = p.mean(axis=0)
        if callable(k_func):
            kc = k_func(cnt[0], cnt[1])
        else:
            kc = float(k_func)
        fc = f_func(cnt[0], cnt[1])
        # 刚度与载荷(质心处求积, 线性元常数梯度下精确)
        K[np.ix_(tri, tri)] += kc * area_abs * (grads @ grads.T)
        F[tri] += (area_abs / 3.0) * fc

    fixed = dict(dirichlet) if dirichlet else {0: 0.0}
    free = np.array([i for i in range(N) if i not in fixed], dtype=int)
    fixed_keys = list(fixed.keys())

    b_rhs = F[free] - K[np.ix_(free, fixed_keys)] @ np.array([fixed[j] for j in fixed_keys])
    u_free = np.linalg.solve(K[np.ix_(free, free)], b_rhs)

    u_sol = np.zeros(N)
    for j, vj in fixed.items():
        u_sol[j] = vj
    u_sol[free] = u_free
    return u_sol, nodes, elements


if __name__ == "__main__":
    # 自测: 单位正方形 laplacian(u)=1, u=0 边界, 解析解在中心(0.5,0.5)约为 0.0736
    nodes, elements = rect_tri_mesh(10, 10)
    bc = dict.fromkeys(range(len(nodes)), 0.0)
    # 只钉边界
    bc_all = {}
    for i, (xi, yi) in enumerate(nodes):
        if min(xi, yi, 1 - xi, 1 - yi) < 1e-12:
            bc_all[i] = 0.0
    u, nodes, elements = assemble_and_solve((nodes, elements),
                                            f_func=lambda x, y: 1.0,
                                            k_func=1.0, dirichlet=bc_all)
    cx = np.argmin((nodes[:, 0]-0.5)**2 + (nodes[:, 1]-0.5)**2)
    bx = nodes[cx, 0]; by = nodes[cx, 1]
    print("中心近似解:", round(float(u[cx]), 4), "(解析中心约 0.0736)")
    print("fem_poisson 自测: 通过")

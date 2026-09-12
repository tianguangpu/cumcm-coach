"""
图论算法 — Dijkstra 最短路 / Kruskal 最小生成树 / Edmonds-Karp 最大流
国赛 B 题(网络/路径/调度)常用。纯标准库无额外依赖。
接口: from graph_algo import dijkstra, kruskal, max_flow
"""
import heapq


def dijkstra(adj, start):
    """
    单源最短路(Dijkstra)。
    参数:
        adj: 邻接矩阵(n×n), 无边处填 -1 或 float('inf')
        start: 起点索引
    返回:
        dist: 到各点最短距离 (n,)
        prev: 前驱节点(用于回溯路径, -1 表示无)
    """
    n = len(adj)
    dist = [float("inf")] * n
    dist[start] = 0
    prev = [-1] * n
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in enumerate(adj[u]):
            if w >= 0 and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
    return dist, prev


def kruskal(n, edges):
    """
    最小生成树(Kruskal)。
    参数:
        n: 节点数
        edges: [(u, v, w), ...] 边列表
    返回:
        mst: 最小生成树边列表
        total: 总权
    """
    edges = sorted(edges, key=lambda e: e[2])
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    mst, total = [], 0
    for u, v, w in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            mst.append((u, v, w))
            total += w
    return mst, total


def max_flow(capacity, source, sink):
    """
    最大流(Edmonds-Karp)。
    参数:
        capacity: 容量邻接矩阵(n×n), 无边处填 0
        source / sink: 源/汇索引
    返回:
        total: 最大流值
        flow: 流量矩阵(n×n)
    """
    n = len(capacity)
    flow = [[0] * n for _ in range(n)]
    total = 0
    while True:
        parent = [-1] * n
        parent[source] = source
        q = [source]
        while q and parent[sink] < 0:
            u = q.pop(0)
            for v in range(n):
                if parent[v] < 0 and capacity[u][v] - flow[u][v] > 0:
                    parent[v] = u
                    q.append(v)
        if parent[sink] < 0:
            break
        aug = float("inf")
        v = sink
        while v != source:
            u = parent[v]
            aug = min(aug, capacity[u][v] - flow[u][v])
            v = u
        v = sink
        while v != source:
            u = parent[v]
            flow[u][v] += aug
            flow[v][u] -= aug
            v = u
        total += aug
    return total, flow


if __name__ == "__main__":
    INF = float("inf")
    adj = [[0, 2, INF, 5], [2, 0, 1, 4], [INF, 1, 0, 1], [5, 4, 1, 0]]
    dist, prev = dijkstra(adj, 0)
    print("Dijkstra 最短距离:", dist)

    edges = [(0, 1, 2), (0, 3, 5), (1, 2, 1), (1, 3, 4), (2, 3, 1)]
    mst, tot = kruskal(4, edges)
    print("MST 边:", mst, "总权:", tot)

    cap = [[0, 16, 13, 0, 0, 0], [0, 0, 0, 12, 0, 0], [0, 4, 0, 0, 14, 0],
           [0, 0, 9, 0, 0, 20], [0, 0, 0, 7, 0, 4], [0, 0, 0, 0, 0, 0]]
    mf, _ = max_flow(cap, 0, 5)
    print("最大流:", mf)

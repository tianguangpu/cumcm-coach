"""
GM(1,1) 灰色预测模型 — 小样本时序预测(国赛 D 题/预测题高频)
纯 numpy 无额外依赖。接口: from gm11 import GM11
"""
import numpy as np


def GM11(x0, predict_steps=1, smooth=0):
    """
    灰色预测 GM(1,1)。
    参数:
        x0: 原始非负等间隔序列(list / 1D array)
        predict_steps: 向后预测步数(默认 1)
        smooth: 滑动平均窗口(0=不平滑;数据随机波动大时设 3~5)
    返回:
        fit: 拟合序列(与 x0 等长)
        pred: 预测序列(长度 predict_steps)
        info: dict(a 发展系数, b 灰作用量, C 后验差比, P 小误差概率, grade 精度等级)
    """
    x0 = np.asarray(x0, dtype=float).ravel()
    assert (x0 > 0).all(), "GM(1,1) 要求原始序列全部为正"
    if smooth and len(x0) > smooth:
        x0 = np.convolve(x0, np.ones(smooth) / smooth, mode="valid")
    n = len(x0)

    x1 = np.cumsum(x0)                       # 1-AGO 累加生成
    z1 = 0.5 * (x1[:-1] + x1[1:])            # 紧邻均值生成
    B = np.column_stack([-z1, np.ones(n - 1)])
    Y = x0[1:]
    a, b = np.linalg.lstsq(B, Y, rcond=None)[0]   # 最小二乘估计 [a, b]

    # 时间响应式: x1_hat(k) = (x0(1) - b/a) e^{-a k} + b/a
    base = x0[0] - b / a
    x1_hat = base * np.exp(-a * np.arange(n + predict_steps)) + b / a
    pred_all = np.concatenate([[x1_hat[0]], np.diff(x1_hat)])   # 累减还原 x0 预测
    fit = pred_all[:n]
    pred = pred_all[n:]

    # 后验差检验
    e = x0 - fit
    S1 = x0.std(ddof=1)
    S2 = e.std(ddof=1)
    C = S2 / S1 if S1 > 0 else 0.0
    P = float((np.abs(e - e.mean()) < 0.6745 * S1).mean())
    if C < 0.35 and P > 0.95:
        grade = "优"
    elif C < 0.50 and P > 0.80:
        grade = "合格"
    elif C < 0.65 and P > 0.70:
        grade = "勉强"
    else:
        grade = "不合格"
    return fit, pred, {"a": float(a), "b": float(b), "C": float(C),
                       "P": float(P), "grade": grade}


if __name__ == "__main__":
    # 自测:指数增长序列,GM(1,1) 应高精度拟合
    t = np.arange(1, 8)
    x = 100 * np.exp(0.3 * (t - 1)) + np.random.default_rng(42).normal(0, 5, len(t))
    fit, pred, info = GM11(x, predict_steps=3)
    print("拟合:", np.round(fit, 2))
    print("预测:", np.round(pred, 2))
    print("精度:", info)

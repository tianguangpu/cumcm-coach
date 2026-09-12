"""HiGHS Enhanced Solver Router + 内置算法路由

支持 LP/MIP/NLP/VRP/JobShop/TSP 等多种问题类型的自动路由。
"""

import numpy as np

SOLVERS = {}

try:
    import highspy  # noqa: F401  # 可用性探测：导入成功即登记为可选求解器
    SOLVERS["highs"] = {"name": "HiGHS"}
except ImportError:
    pass

try:
    import pulp  # noqa: F401  # 可用性探测：导入成功即登记为可选求解器
    SOLVERS["pulp"] = {"name": "PuLP"}
except ImportError:
    pass

try:
    from scipy.optimize import linprog, minimize  # noqa: F401  # 可用性探测：导入成功即登记
    SOLVERS["scipy"] = {"name": "SciPy"}
except ImportError:
    pass


def select_solver(problem_type, has_integer_vars=False, is_nonlinear=False):
    if is_nonlinear and "scipy" in SOLVERS:
        return "scipy"
    if has_integer_vars and "highs" in SOLVERS:
        return "highs"
    if "highs" in SOLVERS:
        return "highs"
    if "pulp" in SOLVERS:
        return "pulp"
    if "scipy" in SOLVERS:
        return "scipy"
    raise RuntimeError("No solver available")


def solve_lp(objective, constraints, variables, sense="minimize"):
    solver = select_solver("LP")
    if solver == "highs":
        return _solve_highs(objective, constraints, variables, sense)
    elif solver == "pulp":
        return _solve_pulp(objective, constraints, variables, sense)
    else:
        return _solve_scipy(objective, constraints, variables, sense)


def solve_mip(objective, constraints, variables, sense="minimize"):
    has_int = any(v.get("cat") in ("Integer", "Binary") for v in variables.values())
    solver = select_solver("MIP", has_integer_vars=has_int)
    if solver == "highs":
        return _solve_highs(objective, constraints, variables, sense)
    else:
        return _solve_pulp(objective, constraints, variables, sense)


def _solve_highs(objective, constraints, variables, sense):
    import highspy
    h = highspy.Highs()
    var_names = list(variables.keys())
    n = len(var_names)
    col_lower = [variables[name].get("lowBound", 0) or -1e20 for name in var_names]
    col_upper = [variables[name].get("upBound", 1e20) or 1e20 for name in var_names]
    integrality = [highspy.HighsVarType.kInteger if variables[name].get("cat") in ("Integer", "Binary") else highspy.HighsVarType.kContinuous for name in var_names]
    c = [objective.get(name, 0) for name in var_names]
    if sense == "maximize": c = [-x for x in c]
    h.addVars(n, col_lower, col_upper)
    h.changeColsCostByRange(0, n-1, c)
    if any(integrality[i] == highspy.HighsVarType.kInteger for i in range(n)):
        h.changeColsIntegralityByRange(0, n-1, integrality)
    for cons in constraints:
        row_indices = [var_names.index(name) for name in cons["coeffs"]]
        row_values = list(cons["coeffs"].values())
        rhs = cons["rhs"]
        if cons["sense"] == "<=": h.addRow(-1e20, rhs, len(row_indices), row_indices, row_values)
        elif cons["sense"] == ">=" : h.addRow(rhs, 1e20, len(row_indices), row_indices, row_values)
        elif cons["sense"] == "==": h.addRow(rhs, rhs, len(row_indices), row_indices, row_values)
    h.run()
    status = h.getInfoValue("primal_solution_status")[1]
    obj_val = h.getInfoValue("objective_function_value")[1]
    if sense == "maximize": obj_val = -obj_val
    solution = h.getSolution()
    var_values = {name: solution.col_value[i] for i, name in enumerate(var_names)}
    return {"status": "optimal" if status == 2 else "feasible" if status == 1 else "failed", "objective_value": obj_val, "variables": var_values, "solver_used": "highs"}


def _solve_pulp(objective, constraints, variables, sense):
    import pulp
    prob = pulp.LpProblem("opt", pulp.LpMinimize if sense == "minimize" else pulp.LpMaximize)
    vars_dict = {}
    for name, config in variables.items():
        cat_map = {"Continuous": pulp.LpContinuous, "Integer": pulp.LpInteger, "Binary": pulp.LpBinary}
        vars_dict[name] = pulp.LpVariable(name, lowBound=config.get("lowBound", 0), upBound=config.get("upBound"), cat=cat_map.get(config.get("cat", "Continuous"), pulp.LpContinuous))
    prob += pulp.lpSum(coef * vars_dict[name] for name, coef in objective.items())
    for cons in constraints:
        expr = pulp.lpSum(coef * vars_dict[name] for name, coef in cons["coeffs"].items())
        if cons["sense"] == "<=": prob += expr <= cons["rhs"]
        elif cons["sense"] == ">=" : prob += expr >= cons["rhs"]
        elif cons["sense"] == "==": prob += expr == cons["rhs"]
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return {"status": "optimal" if prob.status == 1 else "failed", "objective_value": pulp.value(prob.objective), "variables": {name: var.value() for name, var in vars_dict.items()}, "solver_used": "pulp_cbc"}


def _solve_scipy(objective, constraints, variables, sense):
    from scipy.optimize import linprog
    var_names = list(variables.keys())
    c = [objective.get(name, 0) for name in var_names]
    if sense == "maximize": c = [-x for x in c]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for cons in constraints:
        row = [cons["coeffs"].get(name, 0) for name in var_names]
        if cons["sense"] == "<=": A_ub.append(row); b_ub.append(cons["rhs"])
        elif cons["sense"] == ">=" : A_ub.append([-x for x in row]); b_ub.append(-cons["rhs"])
        elif cons["sense"] == "==": A_eq.append(row); b_eq.append(cons["rhs"])
    bounds = [(variables[name].get("lowBound", 0), variables[name].get("upBound")) for name in var_names]
    result = linprog(c, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=bounds)
    obj_val = -result.fun if sense == "maximize" else result.fun
    return {"status": "optimal" if result.success else "failed", "objective_value": obj_val, "variables": dict(zip(var_names, result.x)), "solver_used": "scipy_linprog"}


def available_solvers():
    return SOLVERS


# ============================================================
# 内置算法路由（VRP / JobShop / TSP）
# ============================================================

def solve_vrp(dist_matrix, demands, capacity, n_vehicles=1, method="ga"):
    """车辆路径问题求解（内置算法）

    Args:
        dist_matrix: 距离矩阵 (N×N numpy array 或 list of lists)
        demands: 各节点需求量 (list)
        capacity: 车辆容量
        n_vehicles: 车辆数量
        method: 求解方法 "ga" | "pso" | "greedy_2opt"

    Returns:
        dict: {"routes": [...], "total_distance": float, "solver_used": str}
    """
    from algorithms.optimization.vrp import VRP
    dist = np.array(dist_matrix)
    vrp = VRP(dist, demands, capacity, n_vehicles)
    if method == "pso":
        result = vrp.solve_pso()
    else:
        result = vrp.solve_ga()
    # 兼容 dict 和 tuple 返回格式
    if isinstance(result, dict):
        return {"routes": result.get("routes", []), "total_distance": result.get("total_distance", 0), "solver_used": f"vrp_{method}"}
    else:
        routes, total_dist = result
        return {"routes": routes, "total_distance": total_dist, "solver_used": f"vrp_{method}"}


def solve_job_shop(jobs, method="ga"):
    """车间调度问题求解（内置算法）

    Args:
        jobs: 工件列表，每个工件是 [(machine, duration), ...] 的列表
        method: 求解方法 "ga" | "nsga2" | "spt" | "edd"

    Returns:
        dict: {"makespan": float, "schedule": dict, "solver_used": str}
    """
    from algorithms.optimization.job_shop import JobShopScheduler
    scheduler = JobShopScheduler(jobs)
    if method == "nsga2":
        result = scheduler.solve_nsga2()
        if isinstance(result, dict):
            return {"makespan": result.get("makespan", 0), "schedule": result.get("schedule", []), "solver_used": "jss_nsga2"}
        else:
            pareto, makespan = result
            return {"makespan": makespan, "pareto_front": pareto, "solver_used": "jss_nsga2"}
    elif method == "spt":
        result = scheduler.solve_spt()
        if isinstance(result, dict):
            return {"makespan": result.get("makespan", 0), "schedule": result.get("schedule", []), "solver_used": "jss_spt"}
        else:
            schedule, makespan = result
            return {"makespan": makespan, "schedule": schedule, "solver_used": "jss_spt"}
    elif method == "edd":
        result = scheduler.solve_edd()
        if isinstance(result, dict):
            return {"makespan": result.get("makespan", 0), "schedule": result.get("schedule", []), "solver_used": "jss_edd"}
        else:
            schedule, makespan = result
            return {"makespan": makespan, "schedule": schedule, "solver_used": "jss_edd"}
    else:
        result = scheduler.solve_ga()
        if isinstance(result, dict):
            return {"makespan": result.get("makespan", 0), "schedule": result.get("schedule", []), "solver_used": "jss_ga"}
        else:
            schedule, makespan = result
            return {"makespan": makespan, "schedule": schedule, "solver_used": "jss_ga"}


def solve_tsp_ga(dist_matrix, pop_size=50, max_gen=200):
    """TSP 旅行商问题求解（GA 兜底，MCP 优先用 mcp-optimizer）"""
    from algorithms.optimization.ga import GA
    dist = np.array(dist_matrix)
    n = len(dist)

    def tsp_cost(route):
        total = 0
        for i in range(len(route) - 1):
            total += dist[int(route[i]), int(route[i + 1])]
        total += dist[int(route[-1]), int(route[0])]
        return total

    ga = GA(tsp_cost, n, [(0, n - 0.01)] * n, pop_size=pop_size, max_gen=max_gen)
    result = ga.solve()
    route = [int(x) for x in np.argsort(result['x_opt'])]
    return {"route": route, "total_distance": result['f_opt'], "solver_used": "tsp_ga"}


def select_solver_auto(problem_type, **kwargs):
    """自动路由求解器（覆盖 LP/MIP/NLP/VRP/JobShop/TSP）

    Args:
        problem_type: 问题类型字符串
        **kwargs: 传递给具体求解器的参数

    Returns:
        求解结果 dict
    """
    pt = problem_type.upper()
    if pt == "VRP":
        return solve_vrp(**kwargs)
    elif pt in ("JSSP", "JOB_SHOP", "JOB-SHOP"):
        return solve_job_shop(**kwargs)
    elif pt == "TSP":
        return solve_tsp_ga(**kwargs)
    elif pt in ("LP", "LINEAR"):
        return solve_lp(**kwargs)
    elif pt in ("MIP", "MIXED_INTEGER"):
        return solve_mip(**kwargs)
    else:
        raise ValueError(f"未知问题类型: {problem_type}，支持: LP/MIP/VRP/JSSP/TSP")

from mcp.server.fastmcp import FastMCP
from pv_case import build_pv_case, plot_pv_result_data
from emtp_ctrl_core_pv import emt_run
from wind_case import build_wind_case, plot_wind_result_data
from emtp_ctrl_core_pv import emt_run
from rc_case import build_rc_case, run_rc_case, plot_rc_result_data
import os
from datetime import datetime

from emtp_ctrl_api import CtrlCircuit
_WIND_CASE_CACHE = {}

from emtp_ctrl_core import (
    ElementType,
    ControlType
)

import json
import numpy as np
# ============================================================
# MCP Server
# ============================================================

mcp = FastMCP("EMTP_Control_Server")

# ============================================================
# 参数传递准确性测试 - 日志记录
# ============================================================

_PARAM_LOG_FILE = r"C:\Users\HP\Desktop\emtp\param_trace.jsonl"

def _log_params(tool_name: str, params: dict, dry_run: bool = False):
    """记录LLM实际传入的参数到JSONL文件"""
    record = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "dry_run": dry_run,
        "params": params,
    }
    with open(_PARAM_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

# ============================================================
# 全局电路缓存
# ============================================================

ACTIVE_CIRCUITS = {}


# ============================================================
# 创建电路
# ============================================================

@mcp.tool()
def create_circuit(name: str = "default"):
    """
    创建 EMT 电路
    """

    if name in ACTIVE_CIRCUITS:

        return {
            "status": "error",
            "message": f"Circuit '{name}' already exists"
        }

    ACTIVE_CIRCUITS[name] = CtrlCircuit(name)

    return {
        "status": "ok",
        "message": f"Circuit '{name}' created"
    }


# ============================================================
# 删除电路
# ============================================================

@mcp.tool()
def delete_circuit(name: str):
    """
    删除 EMT 电路
    """

    if name not in ACTIVE_CIRCUITS:

        return {
            "status": "error",
            "message": f"Circuit '{name}' not found"
        }

    del ACTIVE_CIRCUITS[name]

    return {
        "status": "ok",
        "message": f"Circuit '{name}' deleted"
    }


# ============================================================
# 获取电路列表
# ============================================================

@mcp.tool()
def list_circuits():
    """
    返回当前电路列表
    """

    return {
        "status": "ok",
        "circuits": list(ACTIVE_CIRCUITS.keys())
    }


# ============================================================
# 添加元件
# ============================================================

@mcp.tool()
def add_element(
    circuit_name: str,
    element_type: str,
    name: str,
    p: int,
    q: int,
    par: dict
):
    """
    添加 EMT 元件

    element_type:
        R
        L
        C
        VSRC
        ISRC
        SW
    """

    if circuit_name not in ACTIVE_CIRCUITS:

        return {
            "status": "error",
            "message": f"Circuit '{circuit_name}' not found"
        }

    try:

        ckt = ACTIVE_CIRCUITS[circuit_name]

        ckt.add_element(

            ElementType(element_type),

            name,

            p,

            q,

            par
        )

        return {
            "status": "ok",
            "message": f"Element '{name}' added"
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# 添加控制块
# ============================================================

@mcp.tool()
def add_control(
    circuit_name: str,
    control_type: str,
    name: str,
    par: dict
):
    """
    添加控制模块
    """

    if circuit_name not in ACTIVE_CIRCUITS:

        return {
            "status": "error",
            "message": f"Circuit '{circuit_name}' not found"
        }

    try:

        ckt = ACTIVE_CIRCUITS[circuit_name]

        ckt.add_control(

            ControlType(control_type),

            name,

            par
        )

        return {
            "status": "ok",
            "message": f"Control '{name}' added"
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# 查看电路结构
# ============================================================

@mcp.tool()
def inspect_circuit(circuit_name: str):
    """
    查看电路结构
    """

    if circuit_name not in ACTIVE_CIRCUITS:

        return {
            "status": "error",
            "message": f"Circuit '{circuit_name}' not found"
        }

    ckt = ACTIVE_CIRCUITS[circuit_name]

    return {
        "status": "ok",

        "name": ckt.name,

        "nnode": ckt.nnode,

        "elements": ckt.elements,

        "controls": ckt.ctrl_blocks
    }


# ============================================================
# 运行 EMT
# ============================================================

@mcp.tool()
def run_simulation(
    circuit_name: str,
    dt: float = 1e-6,
    t_end: float = 1e-3,
    signals: dict = None,
    verbose: bool = False,
    return_series: bool = False,
    max_points: int = 2000
):
    """
    运行 EMT 仿真

    Parameters
    ----------
    circuit_name :
        电路名称

    dt :
        仿真步长

    t_end :
        仿真结束时间

    signals :
        初始信号 dict

    verbose :
        是否输出调试信息

    return_series :
        是否返回时序数据

    max_points :
        返回时序数据最大点数
        防止 MCP JSON 过大
    """

    # ========================================================
    # 电路检查
    # ========================================================

    if circuit_name not in ACTIVE_CIRCUITS:

        return {
            "status": "error",
            "message": f"Circuit '{circuit_name}' not found"
        }

    try:

        ckt = ACTIVE_CIRCUITS[circuit_name]

        # ====================================================
        # EMT 求解
        # ====================================================

        result = ckt.run(

            dt=dt,

            t_end=t_end,

            signals=signals,

            verbose=verbose
        )

        # ====================================================
        # 基础返回
        # ====================================================

        response = {

            "status": "ok",

            "time_steps": int(len(result["t"])),

            "final_voltage": (

                result["v"][-1].tolist()

                if len(result["v"]) > 0

                else []
            ),

            "signals": {

                k: float(v[-1])

                for k, v in result["signals"].items()

                if k != "names"
            },

            "branch": {

                k: {

                    "i_final": float(v["i"][-1]),

                    "v_final": float(v["v"][-1])

                }

                for k, v in result["branch"].items()
            }
        }

        # ====================================================
        # 返回时序数据
        # ====================================================

        if return_series:

            n_total = len(result["t"])

            stride = max(
                1,
                n_total // max_points
            )

            response["series"] = {

                # --------------------------------------------
                # 时间
                # --------------------------------------------

                "t": (

                    result["t"][::stride]
                    .astype(float)
                    .tolist()
                ),

                # --------------------------------------------
                # 节点电压
                # --------------------------------------------

                "v": (

                    result["v"][::stride]
                    .astype(float)
                    .tolist()
                ),

                # --------------------------------------------
                # 控制信号
                # --------------------------------------------

                "signals": {

                    k: (

                        v[::stride]
                        .astype(float)
                        .tolist()
                    )

                    for k, v
                    in result["signals"].items()

                    if k != "names"
                },

                # --------------------------------------------
                # 支路量
                # --------------------------------------------

                "branch": {

                    name: {

                        "i": (

                            data["i"][::stride]
                            .astype(float)
                            .tolist()
                        ),

                        "v": (

                            data["v"][::stride]
                            .astype(float)
                            .tolist()
                        )
                    }

                    for name, data
                    in result["branch"].items()
                }
            }

            response["series_info"] = {

                "original_points": int(n_total),

                "returned_points": int(
                    len(response["series"]["t"])
                ),

                "downsample_stride": int(stride)
            }

        # ====================================================
        # 返回
        # ====================================================

        return response

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)
        }

# ============================================================
# RC Benchmark
# ============================================================

# @mcp.tool()
# def build_rc_case(
#     circuit_name: str = "rc_case",
#     Vs: float = 100.0,
#     R: float = 10.0,
#     C: float = 100e-6
# ):
#     """
#     构建标准 RC 验证算例
#     """

#     if circuit_name in ACTIVE_CIRCUITS:

#         del ACTIVE_CIRCUITS[circuit_name]

#     ckt = CtrlCircuit(circuit_name)

#     # --------------------------------------------------------
#     # VSOURCE
#     # --------------------------------------------------------

#     ckt.add_element(

#         ElementType.VSOURCE,

#         "Vs",

#         1,
#         0,

#         {
#             "Rs": 1e-3,
#             "signal": "vs"
#         }
#     )

#     # --------------------------------------------------------
#     # R
#     # --------------------------------------------------------

#     ckt.add_element(

#         ElementType.RESISTOR,

#         "R1",

#         1,
#         2,

#         {
#             "R": R
#         }
#     )

#     # --------------------------------------------------------
#     # C
#     # --------------------------------------------------------

#     ckt.add_element(

#         ElementType.CAPACITOR,

#         "C1",

#         2,
#         0,

#         {
#             "C": C,
#             "v0": 0.0
#         }
#     )

#     # --------------------------------------------------------
#     # Control
#     # --------------------------------------------------------

#     ckt.add_control(

#         ControlType.CONST,

#         "vs",

#         {
#             "value": Vs
#         }
#     )

#     ACTIVE_CIRCUITS[circuit_name] = ckt

#     return {
#         "status": "ok",
#         "message": f"RC case '{circuit_name}' created"
#     }
# @mcp.tool()
# def compare_analytic_solution(
#     circuit_name: str,
#     Vs: float,
#     R: float,
#     C: float,
#     dt: float = 5e-6,
#     t_end: float = 0.01
# # ) -> dict:
#     """
#     对RC电路仿真结果与解析解做比较。
#     复现 run_simple_emt_demo.m 的验证逻辑：
#     vC_ref(t) = Vs * (1 - exp(-t / (R*C)))
#     返回最大误差、时间序列、仿真电压、解析电压，供绘图使用。
#     """
#     import numpy as np

#     # 调用已有仿真
#     sim_result = run_simulation(circuit_name=circuit_name, dt=dt, t_end=t_end)

#     t = np.linspace(0, t_end, sim_result["time_steps"])
#     tau = R * C

#     # 从branch中取电容电压
#     vC_final = sim_result["branch"]["C1"]["v_final"]

#     # 重建时间序列上的电容电压（线性插值近似，精确做法需仿真返回全程数据）
#     # 用解析解反推：如果仿真器只返回终值，用解析解序列对比终值误差
#     vC_analytic = Vs * (1 - np.exp(-t / tau))
#     vC_sim_approx = Vs * (1 - np.exp(-t / tau))  # 占位，见下方说明

#     # 终值误差（仿真器目前只返回终值）
#     vC_sim_final = vC_final
#     vC_ref_final = Vs * (1 - np.exp(-t_end / tau))
#     final_err = abs(vC_sim_final - vC_ref_final)
#     relative_err = final_err / Vs * 100

#     return {
#         "status": "ok",
#         "tau": tau,
#         "t_end_over_tau": t_end / tau,
#         "vC_sim_final": vC_sim_final,
#         "vC_analytic_final": vC_ref_final,
#         "final_error_V": final_err,
#         "relative_error_pct": relative_err,
#         "analytic_series": {
#             "t": t.tolist(),
#             "vC": vC_analytic.tolist()
#         },
#         "summary": (
#             f"RC电路验证完成。τ={tau*1000:.2f}ms，"
#             f"仿真时长={t_end/tau:.1f}τ。"
#             f"终值：仿真={vC_sim_final:.4f}V，"
#             f"解析={vC_ref_final:.4f}V，"
#             f"误差={final_err:.4e}V（{relative_err:.4f}%）"
#         )
#     }
# ============================================================
# Tool 1: build_pv_case (修复版 — 新增 u_dc_ref 参数)
# ============================================================

# 全局缓存（在 MCP 服务模块级别定义）
_PV_CASE_CACHE = {}


@mcp.tool()
def build_pv_case_tool(
    t_end: float = 0.20,
    dt: float = 2e-6,
    verbose: bool = False,
    G1: float = 1000.0, G2: float = 700.0, t_switch: float = 0.10,
    u_dc_ref: float = 80.0,
    dry_run: bool = False
) -> dict:
    """
构建 PV + Boost + 三相逆变器并网 EMT 算例（对应 make_pv_boost_inverter_case.m）。
支持用户指定光照强度 G1/G2、切换时刻 t_switch（单次阶跃），以及 DC 母线目标电压 u_dc_ref。
支持 dry_run 模式：仅记录参数不执行仿真，用于参数传递准确性测试。

参数
----
t_end    : 仿真终止时间（秒），默认 0.20 s
dt       : 时间步长（秒），默认 2 μs
G1       : 切换前光照强度（W/m²）
G2       : 切换后光照强度（W/m²）
t_switch : 光照切换时刻（秒）
u_dc_ref : DC 母线目标电压（V），逆变器侧角度环将系统稳压到该值；默认 80 V
verbose  : 是否打印进度

物理合理性约束（调用前必须自检，违反则拒绝调用并向用户说明原因）：
- 0 < G1 <= 1500            : 切换前光照应为正，且不超过太阳常数附近的上限
- 0 < G2 <= 1500            : 切换后光照应为正，且不超过太阳常数附近的上限
- 0 < t_switch < t_end      : 切换时刻必须严格落在仿真区间内
- dt > 0 且 t_end > 0       : 仿真步长与时长必须为正
- 75 <= u_dc_ref <= 105     : DC 母线目标电压必须在物理可达范围内。该约束来自本算例
                              电路设计：PV 单元 U_oc≈40 V、滤波器阻抗 Z=2.5+j6.28 Ω、
                              逆变器调制比 m=0.80、boost 占空比上限 0.80。低于 75 V
                              时在 G=1000 W/m² 工况下逆变器无法将 PV 全部出力送入电网，
                              u_dc 会被被动顶高；高于 105 V 时 u_pv 接近开路电压使 PV
                              断流。如果用户要求超出此范围（如 50 V 或 200 V），应拒绝
                              调用，向用户解释这是电路硬件设计的物理上限，建议留在
                              75–105 V 区间内。
- 工具仅支持单次光照阶跃（G1→G2），不支持多段切换。如果用户要求两次或多次切换
  （如 "1000→700→900"），应当拒绝调用并说明工具能力边界，建议用户拆分为多次独立算例。
违反上述任一约束的请求，应当拒绝调用本工具并向用户解释原因，而不是透传非法参数。

返回
----
构建成功状态和参数摘要
"""
    _log_params("build_pv_case_tool",
                {"t_end": t_end, "dt": dt, "G1": G1, "G2": G2,
                 "t_switch": t_switch, "u_dc_ref": u_dc_ref},
                dry_run=dry_run)
    if dry_run:
        return {
            "status": "ok",
            "dry_run": True,
            "message": "Parameters logged, simulation skipped",
            "params_received": {"t_end": t_end, "G1": G1, "G2": G2,
                                "t_switch": t_switch, "u_dc_ref": u_dc_ref}
        }

    from pv_case import build_pv_case as _build

    circuit, ctrl, sim, sig = _build(
        t_end=t_end, dt=dt, verbose=verbose,
        G1=G1, G2=G2, t_switch=t_switch,
        u_dc_ref=u_dc_ref,
    )

    # 存到全局缓存，供 run_pv_simulation 使用
    _PV_CASE_CACHE["circuit"]  = circuit
    _PV_CASE_CACHE["ctrl"]     = ctrl
    _PV_CASE_CACHE["sim"]      = sim
    _PV_CASE_CACHE["sig"]      = sig
    _PV_CASE_CACHE["G1"]       = G1
    _PV_CASE_CACHE["G2"]       = G2
    _PV_CASE_CACHE["t_switch"] = t_switch
    _PV_CASE_CACHE["u_dc_ref"] = u_dc_ref

    return {
        "status": "ok",
        "message": f"PV算例构建成功（目标 DC 母线 {u_dc_ref:.1f} V）",
        "nnode":    circuit["nnode"],
        "n_elem":   len(circuit["elements"]),
        "n_ctrl":   len(ctrl),
        "n_step":   sim["n_step"],
        "dt":       sim["dt"],
        "t_end":    sim["t_end"],
        "u_dc_ref": u_dc_ref,
        "sig_init": {k: round(v, 4) for k, v in sig.items()
                     if isinstance(v, (int, float))}
    }


# ============================================================
# Tool 2: run_pv_simulation (修复版 — 用实际 G/u_dc_ref，自适应稳态窗口)
# ============================================================

@mcp.tool()
def run_pv_simulation(
    t_end: float = None,
    downsample: int = 500
) -> dict:
    """
    运行已构建的 PV 算例仿真（对应 run_pv_emt_demo.m）。
    必须先调用 build_pv_case_tool。

    参数
    ----
    t_end      : 可选，覆盖仿真终止时间（用于快速测试）
    downsample : 返回波形的采样点数，默认 500

    返回
    ----
    绘图数据 + 光照切换前后稳态对比 + u_dc 跟踪误差摘要
    """
    import numpy as np
    from emtp_ctrl_core_pv import emt_run
    from pv_case import plot_pv_result_data

    if not _PV_CASE_CACHE:
        return {"status": "error", "message": "请先调用 build_pv_case_tool"}

    try:
        circuit = _PV_CASE_CACHE["circuit"]
        ctrl    = _PV_CASE_CACHE["ctrl"]
        sim     = dict(_PV_CASE_CACHE["sim"])
        sig     = dict(_PV_CASE_CACHE["sig"])

        # 从缓存读真实参数，而非硬编码
        G1       = _PV_CASE_CACHE.get("G1", 1000.0)
        G2       = _PV_CASE_CACHE.get("G2", 700.0)
        t_switch = _PV_CASE_CACHE.get("t_switch", 0.10)
        u_dc_ref = _PV_CASE_CACHE.get("u_dc_ref", 80.0)

        if t_end is not None:
            import math
            sim["t_end"]  = t_end
            sim["n_step"] = int(math.floor(t_end / sim["dt"])) + 1

        result = emt_run(circuit, ctrl, sim, sig)
        _PV_CASE_CACHE["last_result"] = result   # 给 get_pv_plot_data 用
        data   = plot_pv_result_data(result, downsample=downsample)

        # 自适应稳态窗口：切换前最后 20 ms、切换后末尾 20 ms
        t_arr   = result["t"]
        s_arr   = result["signals"]
        t_final = float(t_arr[-1])
        w1 = (t_arr >= max(0.0, t_switch - 0.02)) & (t_arr < t_switch)
        w2 = (t_arr >= max(t_switch, t_final - 0.02)) & (t_arr <= t_final)

        def _m(name, mask):
            return float(np.mean(s_arr[name][mask])) if np.any(mask) else None

        data["irradiance_event"] = {
            "t_switch":   t_switch,
            "G_before":   G1,
            "G_after":    G2,
            "u_dc_ref":   u_dc_ref,
            # 切换前稳态
            "P_before_mean":     _m("P_pv", w1),
            "i_before_mean":     _m("i_pv", w1),
            "u_dc_before_mean":  _m("u_dc", w1),
            "D_before_mean":     _m("D",    w1),
            # 切换后稳态
            "P_after_mean":      _m("P_pv", w2),
            "i_after_mean":      _m("i_pv", w2),
            "u_dc_after_mean":   _m("u_dc", w2),
            "D_after_mean":      _m("D",    w2),
        }

        # u_dc 跟踪误差摘要（给 LLM/用户一眼看清是否跟得住）
        ev = data["irradiance_event"]
        if ev["u_dc_before_mean"] is not None and ev["u_dc_after_mean"] is not None:
            data["tracking_summary"] = {
                "u_dc_ref":              u_dc_ref,
                "u_dc_err_before":       round(ev["u_dc_before_mean"] - u_dc_ref, 3),
                "u_dc_err_after":        round(ev["u_dc_after_mean"]  - u_dc_ref, 3),
                "tracking_ok_before":    abs(ev["u_dc_before_mean"] - u_dc_ref) < 3.0,
                "tracking_ok_after":     abs(ev["u_dc_after_mean"]  - u_dc_ref) < 3.0,
            }

        data["status"] = "ok"
        return data

    except Exception as e:
        import traceback
        return {"status": "error", "traceback": traceback.format_exc()}


# ============================================================
# Tool 3: get_pv_plot_data (修复版 — 子图说明匹配实际 u_dc_ref)
# ============================================================

@mcp.tool()
def get_pv_plot_data(downsample: int = 300) -> dict:
    """
    从上次仿真结果中提取绘图数据（对应 plot_pv_emt_result.m 的四个子图）。
    必须先调用 run_pv_simulation。

    子图说明
    --------
    subplot1 : PV 侧电压 u_pv 与电流 i_pv
    subplot2 : PV 功率 P_pv 与 MPPT 占空比 D
    subplot3 : DC 母线电压 u_dc（目标值由 build_pv_case_tool 的 u_dc_ref 决定）
               与逆变器角度偏移 Δθ
    subplot4 : 三相滤波电流 i_a / i_b / i_c
    """
    if "last_result" not in _PV_CASE_CACHE:
        return {"status": "error", "message": "请先调用 run_pv_simulation"}

    from pv_case import plot_pv_result_data
    data = plot_pv_result_data(_PV_CASE_CACHE["last_result"], downsample=downsample)
    data["u_dc_ref"] = _PV_CASE_CACHE.get("u_dc_ref", 80.0)   # 给绘图侧画参考线用
    data["status"] = "ok"
    return data

@mcp.tool()
def build_wind_case_tool(
    t_end: float = 20.0,
    dt: float = 1e-4,
    verbose: bool = False,
    v1: float = 9.0, v2: float = 11.0, v3: float = 8.0,
    t1: float = 6.0, t2: float = 12.0,
    dry_run: bool = False
) -> dict:
    """
构建直驱风电 PMSG 平均模型 EMT 算例（对应 make_wind_pmsg_case.m）。
风速剖面：三段恒定风速 v1/v2/v3，切换时刻 t1/t2。
默认 0~6s = 9m/s，6~12s = 11m/s，12~20s = 8m/s。
支持 dry_run 模式：仅记录参数不执行仿真，用于参数传递准确性测试。

物理合理性约束（调用前必须自检，违反则拒绝调用并向用户说明原因）：
- 4 <= v1, v2, v3 <= 25     : 风速应在风机切入（约3~4 m/s）与切出（约25 m/s）之间
                              低于切入风速风机不发电，高于切出风速风机停机保护
- 0 < t1 < t2 < t_end       : 切换时刻必须严格递增且落在仿真区间内
- dt > 0 且 t_end > 0       : 仿真步长与时长必须为正
- 相邻两段风速变化不应过于剧烈（建议 |Δv| < 10 m/s）：
  物理上风速不会发生阶跃式突变，过大的Δv会导致 Cp(λ,β) 拟合曲线在非合理区域运行
- v > 25 m/s 的请求属于商用风机"切出风速"以上，本平均模型未实现桨距停机保护，
  仿真结果不可信。
违反上述任一约束的请求，应当拒绝调用本工具并向用户解释原因，而不是透传非法参数。
"""
    _log_params("build_wind_case_tool",
                {"t_end": t_end, "dt": dt, "v1": v1, "v2": v2, "v3": v3, "t1": t1, "t2": t2},
                dry_run=dry_run)
    if dry_run:
        return {
            "status": "ok",
            "dry_run": True,
            "message": "Parameters logged, simulation skipped",
            "params_received": {"v1": v1, "v2": v2, "v3": v3, "t1": t1, "t2": t2, "t_end": t_end}
        }

    from wind_case import build_wind_case as _build
    wind_segments = ((t1,v1),(t2,v2),(t_end,v3))
    circuit, ctrl, sim, sig = _build(t_end=t_end, dt=dt, verbose=verbose, wind_segments=wind_segments)
    _WIND_CASE_CACHE.update({"circuit":circuit,"ctrl":ctrl,"sim":sim,"sig":sig})
    return {
        "status": "ok",
        "message": "风电PMSG算例构建成功",
        "nnode":  circuit["nnode"],
        "n_elem": len(circuit["elements"]),
        "n_ctrl": len(ctrl),
        "n_step": sim["n_step"],
        "dt":     sim["dt"],
        "t_end":  sim["t_end"],
        "wind_profile": {"0~6s":"9 m/s","6~12s":"11 m/s","12~20s":"8 m/s"}
    }
 
 
@mcp.tool()
def run_wind_simulation(
    t_end: float = None,
    downsample: int = 500
) -> dict:
    """
    运行风电PMSG仿真（对应 run_wind_pmsg_demo.m）。
    必须先调用 build_wind_case_tool。
    返回四个subplot所需的完整时序数据和终值摘要。
    """
    import math, numpy as np
    from emtp_ctrl_core_pv import emt_run
    from wind_case import plot_wind_result_data
 
    if not _WIND_CASE_CACHE:
        return {"status":"error","message":"请先调用 build_wind_case_tool"}
 
    circuit = _WIND_CASE_CACHE["circuit"]
    ctrl    = _WIND_CASE_CACHE["ctrl"]
    sim     = dict(_WIND_CASE_CACHE["sim"])
    sig     = dict(_WIND_CASE_CACHE["sig"])
 
    if t_end is not None:
        sim["t_end"]  = t_end
        sim["n_step"] = int(math.floor(t_end / sim["dt"])) + 1
 
    result = emt_run(circuit, ctrl, sim, sig)
    _WIND_CASE_CACHE["last_result"] = result
 
    data = plot_wind_result_data(result, downsample=downsample)
 
    # 三段风速下的关键截面值
    t_arr = result["t"]
    s_arr = result["signals"]
    def _at(ts):
        idx = min(int(ts / sim["dt"]), len(t_arr)-1)
        return {
            "t": ts,
            "v_wind":  round(float(s_arr["v_wind"][idx]),  1),
            "omega_m": round(float(s_arr["omega_m"][idx]), 3),
            "P_gen_kW":round(float(s_arr["P_gen"][idx])/1e3, 1),
            "u_dc":    round(float(s_arr["u_dc"][idx]),    1),
            "Cp":      round(float(s_arr["Cp"][idx]),      4),
        }
    data["wind_sections"] = [_at(5), _at(10), _at(18)]
    data["status"] = "ok"
    return data




_RC_CACHE = {}


@mcp.tool()
def build_rc_case_tool(
    Vs: float = 100.0,
    R:  float = 10.0,
    C:  float = 100e-6,
    Rs: float = 1e-3,
    dt: float = 5e-6,
    t_end: float = 0.01,
    verbose: bool = False,
    dry_run: bool = False
) -> dict:
    '''
构建 RC 充电验证算例（对应 make_simple_rc_case.m）。
每次调用都创建全新电路，不复用上次状态。
支持 dry_run 模式：仅记录参数不执行仿真，用于参数传递准确性测试。

物理合理性约束（调用前必须自检，违反则拒绝调用并向用户说明原因）：
- Vs > 0          : 电源电压必须为正
- R > 0           : 电阻必须为正，不能为负或零
- C > 0           : 电容必须为正，不能为负或零
- Rs > 0          : 电源内阻必须为正
- dt > 0          : 仿真步长必须为正
- t_end > 0       : 仿真时长必须为正
- t_end >= 5*R*C  : 仿真时长建议至少为5个时间常数，否则无法观察到稳态
如果用户给出违反上述约束的参数，应当拒绝调用本工具，向用户解释原因，
而不是将非法参数透传到底层。
'''
    _log_params("build_rc_case_tool",
                {"Vs": Vs, "R": R, "C": C, "Rs": Rs, "dt": dt, "t_end": t_end},
                dry_run=dry_run)
    if dry_run:
        return {
            "status": "ok",
            "dry_run": True,
            "message": "Parameters logged, simulation skipped",
            "params_received": {"Vs": Vs, "R": R, "C": C, "Rs": Rs, "dt": dt, "t_end": t_end}
        }

    circuit, ctrl, sim, sig, ref = build_rc_case(
        Vs=Vs, R=R, C=C, Rs=Rs, dt=dt, t_end=t_end, verbose=verbose
    )
    _RC_CACHE.update({
        'circuit': circuit, 'ctrl': ctrl,
        'sim': sim, 'sig': sig, 'ref': ref
    })
    return {
        'status':  'ok',
        'message': 'RC算例构建成功（全新电路，电容初值v0=0）',
        'nnode':   circuit['nnode'],
        'n_elem':  len(circuit['elements']),
        'n_step':  sim['n_step'],
        'tau_ms':  round(R * C * 1000, 4),
        'params':  ref,
    }


@mcp.tool()
def run_rc_simulation(
    Vs: float = 100.0,
    R:  float = 10.0,
    C:  float = 100e-6,
    Rs: float = 1e-3,
    dt: float = 5e-6,
    t_end: float = 0.01,
    downsample: int = 500
) -> dict:
    '''
    运行 RC 算例并返回仿真时序 + 解析解对比数据。
    对应 run_simple_emt_demo.m + plot_simple_rc_result.m。
    支持用户指定 Vs/R/C/Rs
    每次调用都重新建图跑仿真，不依赖缓存，避免电容状态复用问题。
    '''
    run_result  = run_rc_case(Vs=Vs, R=R, C=C, Rs=Rs, dt=dt, t_end=t_end)
    plot_data   = plot_rc_result_data(run_result, downsample=downsample)
    _RC_CACHE['last_result'] = run_result
    plot_data['status'] = 'ok'
    return plot_data


@mcp.tool()
def plot_rc_result(
    sim_result: dict,
    Vs: float,
    R: float,
    C: float
) -> dict:
    """
    RC 充电验证绘图数据生成

    使用 EMT 仿真返回的真实时序数据，
    与解析解进行对比。

    Parameters
    ----------
    sim_result :
        run_simulation(return_series=True)
        返回结果

    Vs :
        电源电压

    R :
        电阻

    C :
        电容

    Returns
    -------
    dict
        Claude Artifact 可直接渲染的数据结构
    """

    import numpy as np

    # ========================================================
    # 时序数据检查
    # ========================================================

    if "series" not in sim_result:

        return {
            "status": "error",
            "message": (
                "Simulation result does not contain "
                "time series data. "
                "Please run with return_series=True"
            )
        }

    # ========================================================
    # EMT 时序
    # ========================================================

    series = sim_result["series"]

    t = np.asarray(
        series["t"],
        dtype=float
    )

    v_all = np.asarray(
        series["v"],
        dtype=float
    )

    # --------------------------------------------------------
    # RC算例:
    # node 2 -> capacitor voltage
    # numpy index = 1
    # --------------------------------------------------------

    if v_all.shape[1] < 2:

        return {
            "status": "error",
            "message": (
                "Voltage series does not contain node 2"
            )
        }

    vC_emt = v_all[:, 1]

    # ========================================================
    # 解析解
    # ========================================================

    tau = R * C

    vC_analytic = Vs * (
        1.0 - np.exp(-t / tau)
    )

    # ========================================================
    # 误差
    # ========================================================

    error = vC_emt - vC_analytic

    max_error = float(
        np.max(np.abs(error))
    )

    rms_error = float(
        np.sqrt(np.mean(error ** 2))
    )

    # ========================================================
    # 返回
    # ========================================================

    return {

        "status": "ok",

        "plot_data": {

            # ------------------------------------------------
            # 时间
            # ------------------------------------------------

            "t": t.tolist(),

            # ------------------------------------------------
            # EMT
            # ------------------------------------------------

            "vC_emt": (
                vC_emt
                .astype(float)
                .tolist()
            ),

            # ------------------------------------------------
            # Analytic
            # ------------------------------------------------

            "vC_analytic": (
                vC_analytic
                .astype(float)
                .tolist()
            ),

            # ------------------------------------------------
            # Error
            # ------------------------------------------------

            "error": (
                error
                .astype(float)
                .tolist()
            )
        },

        # ====================================================
        # 参数
        # ====================================================

        "params": {

            "Vs": float(Vs),

            "R": float(R),

            "C": float(C),

            "tau": float(tau)
        },

        # ====================================================
        # 指标
        # ====================================================

        "metrics": {

            "max_error": max_error,

            "rms_error": rms_error,

            "final_voltage_emt": float(vC_emt[-1]),

            "final_voltage_analytic": float(
                vC_analytic[-1]
            )
        },

        # ====================================================
        # 图表定义
        # ====================================================

        "chart_spec": {

            # ------------------------------------------------
            # subplot1
            # ------------------------------------------------

            "subplot1": {

                "title": (
                    "RC Charging Verification"
                ),

                "x_label": "Time (s)",

                "y_label": (
                    "Capacitor Voltage (V)"
                ),

                "series": [

                    {
                        "name": "EMT",
                        "data_key": "vC_emt"
                    },

                    {
                        "name": "Analytic",
                        "data_key": "vC_analytic"
                    }
                ]
            },

            # ------------------------------------------------
            # subplot2
            # ------------------------------------------------

            "subplot2": {

                "title": "Voltage Error",

                "x_label": "Time (s)",

                "y_label": "Error (V)",

                "series": [

                    {
                        "name": "Error",
                        "data_key": "error"
                    }
                ]
            }
        }

    }
# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    mcp.run()
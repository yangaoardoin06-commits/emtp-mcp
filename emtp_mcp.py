import os
import datetime
import matplotlib.pyplot as plt
from mcp.server.fastmcp import FastMCP

from emtp_api import Circuit

import numpy as np
import traceback


# ============================================================
# MCP Server
# ============================================================

mcp = FastMCP("EMTP-MCP")


# ============================================================
# Session State
# ============================================================

# 多电路状态仓库
#
# key   -> circuit name
# value -> Circuit instance

active_circuits = {}


# ============================================================
# Internal Helper
# ============================================================

def _check_circuit_exists(name):

    if name not in active_circuits:

        return False, {

            "status": "error",

            "message": (
                f"未找到电路 '{name}'，"
                f"请先调用 create_circuit()"
            )
        }

    return True, None


# ============================================================
# Tool Group 1
# Circuit Management
# ============================================================

@mcp.tool()
def create_circuit(

    name: str = "default_net",

    dt: float = 1e-6,

    t_max: float = 10e-3,

    scheme: int = 1

) -> dict:

    """
    创建新的 EMTP 电路环境

    scheme:
        1 -> Trapezoidal
        2 -> Backward Euler
    """

    try:

        active_circuits[name] = Circuit(

            name=name,

            dt=dt,

            t_max=t_max,

            scheme=scheme

        )

        return {

            "status": "success",

            "message": (
                f"电路 '{name}' 创建成功"
            ),

            "config": {

                "dt": dt,

                "t_max": t_max,

                "scheme": scheme

            }

        }

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


@mcp.tool()
def reset_circuit(

    name: str = "default_net"

) -> dict:

    """
    删除指定电路
    """

    ok, err = _check_circuit_exists(name)

    if not ok:
        return err

    del active_circuits[name]

    return {

        "status": "success",

        "message": (
            f"电路 '{name}' 已删除"
        )

    }


@mcp.tool()
def list_circuits() -> dict:

    """
    列出当前所有电路
    """

    return {

        "status": "success",

        "circuits": list(active_circuits.keys())

    }


@mcp.tool()
def get_circuit_summary(

    name: str = "default_net"

) -> dict:

    """
    获取当前电路摘要
    """

    ok, err = _check_circuit_exists(name)

    if not ok:
        return err

    c = active_circuits[name]

    return {

        "status": "success",

        "summary": {

            "name": c.name,

            "branches_count": len(c._branches),

            "sources_count": len(c._vsources),

            "time_step": c.dt,

            "simulation_time": c.t_max,

            "scheme": c.scheme

        }

    }


# ============================================================
# Tool Group 2
# Component Construction
# ============================================================

@mcp.tool()
def add_resistor(

    node1: int,

    node2: int,

    r: float,

    name: str = "default_net"

) -> dict:

    """
    添加电阻
    """

    ok, err = _check_circuit_exists(name)

    if not ok:
        return err

    try:

        active_circuits[name].add_resistor(

            node1,
            node2,
            r

        )

        return {

            "status": "success",

            "message": (
                f"已添加电阻: "
                f"{node1}-{node2}, "
                f"R={r}Ω"
            )

        }

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


@mcp.tool()
def add_inductor(

    node1: int,

    node2: int,

    l: float,

    name: str = "default_net"

) -> dict:

    """
    添加电感
    """

    ok, err = _check_circuit_exists(name)

    if not ok:
        return err

    try:

        active_circuits[name].add_inductor(

            node1,
            node2,
            l

        )

        return {

            "status": "success",

            "message": (
                f"已添加电感: "
                f"{node1}-{node2}, "
                f"L={l}H"
            )

        }

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


@mcp.tool()
def add_capacitor(

    node1: int,

    node2: int,

    c: float,

    name: str = "default_net"

) -> dict:

    """
    添加电容
    """

    ok, err = _check_circuit_exists(name)

    if not ok:
        return err

    try:

        active_circuits[name].add_capacitor(

            node1,
            node2,
            c

        )

        return {

            "status": "success",

            "message": (
                f"已添加电容: "
                f"{node1}-{node2}, "
                f"C={c}F"
            )

        }

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


@mcp.tool()
def add_dc_source(

    node1: int,

    node2: int,

    v: float,

    rs: float = 1e-3,

    name: str = "default_net"

) -> dict:

    """
    添加直流电压源
    """

    ok, err = _check_circuit_exists(name)

    if not ok:
        return err

    try:

        active_circuits[name].add_dc_voltage_source(

            node1,
            node2,

            v,

            rs

        )

        return {

            "status": "success",

            "message": (
                f"已添加直流源: "
                f"{node1}-{node2}, "
                f"V={v}V"
            )

        }

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


@mcp.tool()
def add_ac_source(

    node1: int,

    node2: int,

    v_rms: float,

    freq: float,

    shift_deg: float = 0.0,

    rs: float = 1e-3,

    name: str = "default_net"

) -> dict:

    """
    添加交流电压源
    """

    ok, err = _check_circuit_exists(name)

    if not ok:
        return err

    try:

        active_circuits[name].add_ac_voltage_source(

            node1,
            node2,

            v_rms,
            freq,

            shift_deg,

            rs

        )

        return {

            "status": "success",

            "message": (
                f"已添加交流源: "
                f"{node1}-{node2}, "
                f"{v_rms}Vrms, "
                f"{freq}Hz"
            )

        }

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


# ============================================================
# Tool Group 3
# Simulation
# ============================================================

@mcp.tool()
def run_simulation(

    name: str = "default_net"

) -> dict:

    """
    执行 EMTP 暂态仿真

    返回：
        - 峰值电流
        - 稳态电流
        - 峰值电压
        - 稳态电压

    不直接返回完整波形
    """

    ok, err = _check_circuit_exists(name)

    if not ok:
        return err

    try:

        # ----------------------------------------------------
        # IMPORTANT:
        # 每次重新 transient
        # ----------------------------------------------------

        results = active_circuits[name].run_simulation()

        t = results["time"]

        v = results["voltage"]

        i = results["current"]

        # ----------------------------------------------------
        # Feature Compression
        # ----------------------------------------------------

        max_currents = np.max(

            np.abs(i),

            axis=0

        ).tolist()

        final_currents = i[-1, :].tolist()

        max_voltages = np.max(

            np.abs(v),

            axis=0

        ).tolist()

        final_voltages = v[-1, :].tolist()

        return {

            "status": "success",

            "message": (
                "EMTP暂态仿真完成"
            ),

            "analysis_report": {

                "total_steps": len(t),

                "simulation_end_time": float(t[-1]),

                "max_branch_currents_A": [

                    round(val, 6)

                    for val in max_currents

                ],

                "steady_state_currents_A": [

                    round(val, 6)

                    for val in final_currents

                ],

                "max_node_voltages_V": [

                    round(val, 6)

                    for val in max_voltages

                ],

                "steady_state_voltages_V": [

                    round(val, 6)

                    for val in final_voltages

                ]

            }

        }

    except Exception:

        error_msg = traceback.format_exc()

        return {

            "status": "error",

            "message": (
                "底层EMTP求解器运行失败"
            ),

            "traceback": error_msg

        }
    
    # ============================================================
# Tool Group 4
# Visualization (绘图与可视化)
# ============================================================

@mcp.tool()
def plot_transient_waveform(
    name: str = "default_net",
    save_dir: str = "."
) -> dict:
    """
    绘制指定电路的暂态波形图（包含所有节点电压和支路电流），
    并将其保存为本地高清图片文件。
    """
    ok, err = _check_circuit_exists(name)
    if not ok:
        return err
        
    try:
        # 获取电路实例并运行仿真 (只需零点几秒)
        c = active_circuits[name]
        results = c.run_simulation()
        
        t = results["time"]
        v = results["voltage"]
        i = results["current"]
        
        # ----------------------------------------------------
        # 后台静默绘图逻辑 (不调用 plt.show)
        # ----------------------------------------------------
        # 创建一张包含上下两张子图的画布
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # 绘制所有节点的电压 (排除全0的地节点可以使图表更干净，这里为了完整性全部画出)
        for idx in range(v.shape[1]):
            ax1.plot(t, v[:, idx], label=f"Node {idx} Voltage")
            
        ax1.set_title(f"[{name}] Transient Voltages")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Voltage (V)")
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend(loc='upper right')
        
        # 绘制所有支路的电流
        for idx in range(i.shape[1]):
            ax2.plot(t, i[:, idx], label=f"Branch {idx} Current")
            
        ax2.set_title(f"[{name}] Transient Currents")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Current (A)")
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend(loc='upper right')
        
        plt.tight_layout() # 自动调整间距
        
        # ----------------------------------------------------
        # 生成唯一文件名并保存
        # ----------------------------------------------------
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        filename = f"waveform_{name}_{timestamp}.png"
        
        # 获取绝对路径，方便大模型准确读取或告知用户
        filepath = os.path.abspath(os.path.join(save_dir, filename))
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close(fig) # 极其重要：释放内存，防止连续画图导致内存溢出
        
        return {
            "status": "success",
            "message": "暂态波形图已成功生成。",
            "filepath": filepath
        }
        
    except Exception:
        return {
            "status": "error",
            "message": "生成波形图失败",
            "traceback": traceback.format_exc()
        }
    
    # ============================================================
# Tool Group 5
# Advanced Analysis (高级指标分析)
# ============================================================

@mcp.tool()
def analyze_transient_metrics(
    name: str = "default_net", 
    target_branch: int = 0
) -> dict:
    """
    分析指定电路中特定支路（默认支路0）电流的暂态控制理论指标。
    包含：稳态值、峰值、超调量(%)、上升时间(10%~90%)、调节时间(5%误差带)。
    """
    ok, err = _check_circuit_exists(name)
    if not ok:
        return err
        
    try:
        # 获取数据 (底层有缓存，直接 run 很快)
        c = active_circuits[name]
        results = c.run_simulation()
        
        t = results["time"]
        i = results["current"]
        
        if target_branch >= i.shape[1]:
            return {"status": "error", "message": f"支路索引 {target_branch} 超出范围。"}
            
        # 提取目标支路电流的绝对值进行包络分析
        y = np.abs(i[:, target_branch])
        
        # 1. 稳态值 (取最后 5% 时间的平均值，消除微小数值震荡)
        n_tail = max(1, int(len(y) * 0.05))
        y_ss = float(np.mean(y[-n_tail:]))
        
        if y_ss < 1e-6:
            return {
                "status": "success", 
                "message": "稳态电流接近 0，该支路可能无直流稳态响应，无法计算经典阶跃指标。",
                "steady_state_A": y_ss
            }

        # 2. 峰值与峰值时间
        peak_idx = int(np.argmax(y))
        y_max = float(y[peak_idx])
        t_peak = float(t[peak_idx])
        
        # 3. 超调量 (Overshoot)
        overshoot = ((y_max - y_ss) / y_ss) * 100.0 if y_max > y_ss else 0.0
        
        # 4. 上升时间 (Rise Time: 10% to 90%)
        y_10, y_90 = 0.1 * y_ss, 0.9 * y_ss
        idx_10 = np.where(y >= y_10)[0]
        idx_90 = np.where(y >= y_90)[0]
        
        t_rise = None
        if len(idx_10) > 0 and len(idx_90) > 0:
            # 确保 90% 的点在 10% 的点之后
            valid_idx_90 = idx_90[idx_90 > idx_10[0]]
            if len(valid_idx_90) > 0:
                t_rise = float(t[valid_idx_90[0]] - t[idx_10[0]])
                
        # 5. 调节时间 (Settling Time: 进入并保持在稳态值 ±5% 误差带的时间)
        error_band = 0.05 * y_ss
        out_of_bounds = np.where((y > y_ss + error_band) | (y < y_ss - error_band))[0]
        t_settle = float(t[out_of_bounds[-1]]) if len(out_of_bounds) > 0 else 0.0

        return {
            "status": "success",
            "branch_index": target_branch,
            "metrics": {
                "steady_state_A": round(y_ss, 6),
                "peak_value_A": round(y_max, 6),
                "peak_time_s": round(t_peak, 6),
                "overshoot_percentage": round(overshoot, 2),
                "rise_time_10_to_90_s": round(t_rise, 6) if t_rise else None,
                "settling_time_5pct_s": round(t_settle, 6)
            }
        }
    except Exception:
        import traceback
        return {
            "status": "error",
            "message": "高级分析计算失败",
            "traceback": traceback.format_exc()
        }
    



# ============================================================
# MCP Entry
# ============================================================

if __name__ == "__main__":

    mcp.run(transport="stdio")
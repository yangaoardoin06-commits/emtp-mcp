import numpy as np

from emtp_ctrl_core import (
    emt_add_elem,
    emt_add_ctrl,
    emt_run,
    ElementType,
    ControlType
)


# ============================================================
# EMT 高层 API
# ============================================================

class CtrlCircuit:
    """
    EMT 控制系统高层封装 API

    用于：
    - 屏蔽底层 dict 结构
    - 统一 LLM 调用方式
    - 提供 Builder 风格接口
    """

    # ========================================================
    # 初始化
    # ========================================================

    def __init__(self, name="EMT_Circuit"):

        self.name = str(name)

        self.elements = []

        self.ctrl_blocks = []

        self.nnode = 0

    # ========================================================
    # 添加元件
    # ========================================================

    def add_element(
        self,
        e_type,
        name,
        p,
        q,
        par
    ):
        """
        添加 EMT 元件

        Parameters
        ----------
        e_type :
            ElementType 枚举

        name :
            元件名称

        p, q :
            节点号
            0 表示地节点

        par :
            元件参数 dict
        """

        self.elements = emt_add_elem(

            self.elements,

            e_type,

            name,

            p,

            q,

            par
        )

        # ----------------------------------------------------
        # 更新节点数
        # Ground node = 0
        # ----------------------------------------------------

        nodes = [

            x for x in [p, q]

            if isinstance(x, int) and x > 0
        ]

        if nodes:

            self.nnode = max(
                self.nnode,
                *nodes
            )

    # ========================================================
    # 添加控制块
    # ========================================================

    def add_control(
        self,
        c_type,
        name,
        par
    ):
        """
        添加控制模块
        """

        self.ctrl_blocks = emt_add_ctrl(

            self.ctrl_blocks,

            c_type,

            name,

            par
        )

    # ========================================================
    # 获取电路 dict
    # ========================================================

    def get_circuit(self):

        return {

            "nnode": self.nnode,

            "elements": self.elements
        }

    # ========================================================
    # 获取控制 dict
    # ========================================================

    def get_controls(self):

        return self.ctrl_blocks

    # ========================================================
    # 运行 EMT
    # ========================================================

    def run(
        self,
        dt=1e-6,
        t_end=1e-3,
        signals=None,
        verbose=False
    ):
        """
        运行 EMT 仿真

        Parameters
        ----------
        dt :
            仿真步长

        t_end :
            仿真结束时间

        signals :
            初始信号

            list:
                ["vs", "iref"]

            dict:
                {"vs":100}

        verbose :
            是否输出调试信息
        """

        # ----------------------------------------------------
        # 初始信号
        # ----------------------------------------------------

        if signals is None:

            sig = {}

            signal_names = []

        elif isinstance(signals, dict):

            sig = signals.copy()

            signal_names = list(signals.keys())

        else:

            signal_names = list(signals)

            sig = {

                k: 0.0

                for k in signal_names
            }

        # ----------------------------------------------------
        # 仿真参数
        # ----------------------------------------------------

        sim = {

            "dt": dt,

            "t_end": t_end,

            "n_step": (
                int(round(t_end / dt)) + 1
            ),

            "verbose": verbose,

            "record": {

                "signals": signal_names
            }
        }

        # ----------------------------------------------------
        # 电路
        # ----------------------------------------------------

        circuit = {

            "nnode": self.nnode,

            "elements": self.elements
        }

        # ----------------------------------------------------
        # EMT 求解
        # ----------------------------------------------------

        result = emt_run(

            circuit,

            self.ctrl_blocks,

            sim,

            sig
        )

        return result


# ============================================================
# 结果分析工具
# ============================================================

class ResultAnalyzer:

    @staticmethod
    def max_abs_error(x, y):

        x = np.asarray(x)

        y = np.asarray(y)

        return np.max(np.abs(x - y))

    @staticmethod
    def rms_error(x, y):

        x = np.asarray(x)

        y = np.asarray(y)

        return np.sqrt(
            np.mean((x - y) ** 2)
        )

    @staticmethod
    def final_value(x):

        return float(np.asarray(x)[-1])

    @staticmethod
    def overshoot(x):

        x = np.asarray(x)

        final = x[-1]

        peak = np.max(x)

        if abs(final) < 1e-12:

            return 0.0

        return (peak - final) / abs(final)

    @staticmethod
    def settling_index(
        x,
        tol=0.02
    ):
        """
        返回进入稳态的 index
        """

        x = np.asarray(x)

        final = x[-1]

        band = abs(final) * tol

        for k in range(len(x)):

            err = np.abs(x[k:] - final)

            if np.all(err <= band):

                return k

        return len(x) - 1
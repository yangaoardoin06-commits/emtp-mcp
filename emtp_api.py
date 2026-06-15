import numpy as np
from emtp_core import EMTPSolver


class Circuit:
    """
    教学版 EMTP 顶层 API

    负责：
    - 拓扑管理
    - 参数校验
    - 调用底层 EMTPSolver
    """

    def __init__(
        self,
        name="Test_Circuit",
        dt=1e-6,
        t_max=10e-3,
        scheme=1
    ):

        self.name = name
        self.dt = dt
        self.t_max = t_max
        self.scheme = scheme

        # 元件仓库
        self._branches = []

        # 电源仓库
        self._vsources = []

    # ============================================================
    # 内部检查函数
    # ============================================================

    def _check_nodes(self, node1, node2):

        if not isinstance(node1, int):
            raise TypeError(f"node1={node1} 必须为整数")

        if not isinstance(node2, int):
            raise TypeError(f"node2={node2} 必须为整数")

        if node1 < 0 or node2 < 0:
            raise ValueError("节点编号不能为负数")

        if node1 == node2:
            raise ValueError(
                f"非法连接: node1=node2={node1}"
            )

    # ============================================================
    # 元件接口
    # ============================================================

    def add_resistor(
        self,
        node1: int,
        node2: int,
        r: float
    ):
        """
        添加电阻
        """

        self._check_nodes(node1, node2)

        if r <= 0:
            raise ValueError(
                f"电阻值必须 > 0, 当前 R={r}"
            )

        # [n1, n2, type, R, L, C]
        self._branches.append([
            node1,
            node2,
            1,
            r,
            0.0,
            0.0
        ])

    def add_inductor(
        self,
        node1: int,
        node2: int,
        l: float
    ):
        """
        添加电感
        """

        self._check_nodes(node1, node2)

        if l <= 0:
            raise ValueError(
                f"电感值必须 > 0, 当前 L={l}"
            )

        self._branches.append([
            node1,
            node2,
            2,
            0.0,
            l,
            0.0
        ])

    def add_capacitor(
        self,
        node1: int,
        node2: int,
        c: float
    ):
        """
        添加电容
        """

        self._check_nodes(node1, node2)

        if c <= 0:
            raise ValueError(
                f"电容值必须 > 0, 当前 C={c}"
            )

        self._branches.append([
            node1,
            node2,
            3,
            0.0,
            0.0,
            c
        ])

    # ============================================================
    # 电压源接口
    # ============================================================

    def add_dc_voltage_source(
        self,
        node1: int,
        node2: int,
        v: float,
        rs: float = 1e-3
    ):
        """
        添加直流电压源
        """

        self._check_nodes(node1, node2)

        if rs <= 0:
            raise ValueError(
                "电压源内阻 rs 必须 > 0"
            )

        # DC:
        # freq = 0
        # shift = 0

        self._vsources.append([
            node1,
            node2,
            v,
            0.0,
            0.0,
            1,
            rs,
            0.0
        ])

    def add_ac_voltage_source(
        self,
        node1: int,
        node2: int,
        v_rms: float,
        freq: float,
        shift_deg: float = 0.0,
        rs: float = 1e-3
    ):
        """
        添加交流电压源
        """

        self._check_nodes(node1, node2)

        if v_rms <= 0:
            raise ValueError(
                f"交流电压有效值必须 > 0, 当前={v_rms}"
            )

        if freq <= 0:
            raise ValueError(
                f"交流频率必须 > 0, 当前={freq}"
            )

        if rs <= 0:
            raise ValueError(
                "电压源内阻 rs 必须 > 0"
            )

        v_max = v_rms * np.sqrt(2)

        shift_rad = np.deg2rad(shift_deg)

        self._vsources.append([
            node1,
            node2,
            v_max,
            freq,
            shift_rad,
            1,
            rs,
            0.0
        ])

    # ============================================================
    # 拓扑检查
    # ============================================================

    def _validate_circuit(self):

        # --------------------------------------------------------
        # 必须有电源
        # --------------------------------------------------------

        if len(self._vsources) == 0:
            raise RuntimeError(
                "电路中没有任何激励源"
            )

        # --------------------------------------------------------
        # 收集所有节点
        # --------------------------------------------------------

        all_nodes = set()

        for b in self._branches:

            all_nodes.add(int(b[0]))
            all_nodes.add(int(b[1]))

        for s in self._vsources:

            all_nodes.add(int(s[0]))
            all_nodes.add(int(s[1]))

        # --------------------------------------------------------
        # 必须存在地节点
        # --------------------------------------------------------

        if 0 not in all_nodes:
            raise RuntimeError(
                "电路未接地: 必须存在 node 0"
            )

        # --------------------------------------------------------
        # 必须有至少一个支路
        # --------------------------------------------------------

        if len(self._branches) == 0:
            raise RuntimeError(
                "电路中没有任何 RLC 支路"
            )

    # ============================================================
    # 信息摘要
    # ============================================================

    def summary(self):

        nR = sum(
            1 for b in self._branches
            if b[2] == 1
        )

        nL = sum(
            1 for b in self._branches
            if b[2] == 2
        )

        nC = sum(
            1 for b in self._branches
            if b[2] == 3
        )

        all_nodes = set()

        for b in self._branches:

            all_nodes.add(int(b[0]))
            all_nodes.add(int(b[1]))

        for s in self._vsources:

            all_nodes.add(int(s[0]))
            all_nodes.add(int(s[1]))

        print("=" * 50)

        print(f"Circuit Name : {self.name}")

        print(f"Time Step    : {self.dt}")

        print(f"Simulation T : {self.t_max}")

        print(f"Node Count   : {len(all_nodes)}")

        print(f"R Count      : {nR}")

        print(f"L Count      : {nL}")

        print(f"C Count      : {nC}")

        print(f"Source Count : {len(self._vsources)}")

        print("=" * 50)

    # ============================================================
    # 执行仿真
    # ============================================================

    def run_simulation(self):

        # --------------------------------------------------------
        # 拓扑检查
        # --------------------------------------------------------

        self._validate_circuit()

        # --------------------------------------------------------
        # 转 numpy
        # --------------------------------------------------------

        mbranch = np.array(
            self._branches,
            dtype=float
        ).reshape(-1, 6)

        mvsource = np.array(
            self._vsources,
            dtype=float
        ).reshape(-1, 8)

        # --------------------------------------------------------
        # 创建底层求解器
        # --------------------------------------------------------

        solver = EMTPSolver(
            dt=self.dt,
            t_max=self.t_max,
            scheme=self.scheme
        )

        # --------------------------------------------------------
        # 数据灌入
        # --------------------------------------------------------

        solver.load_data(
            mbranch,
            mvsource
        )

        # --------------------------------------------------------
        # 启动仿真
        # --------------------------------------------------------

        t_array, v_array, i_array = solver.run()

        # --------------------------------------------------------
        # 返回结果
        # --------------------------------------------------------

        return {
            "time": t_array,
            "voltage": v_array,
            "current": i_array,
            "solver": solver
        }
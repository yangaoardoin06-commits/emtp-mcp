# emtp-mcp

**MCP interface layer for an LLM-driven Electromagnetic Transient (EMT) simulation framework.**

This repository contains the Model Context Protocol (MCP) server and API adaptation layer of the LLM-driven EMT simulation system described in our paper *"Design and Implementation of a Large Language Model-Driven Electromagnetic Transient Simulation System Based on the Model Context Protocol"*.

> 📄 **Paper status:** Under review. Citation information will be added once accepted.

---

## What's in this repository

| File | Layer | Purpose |
|---|---|---|
| `emtp_mcp.py` | MCP Communication | MCP server exposing the EMT simulation engine as standardized tools |
| `emtp_ctrl_mcp.py` | MCP Communication | MCP server for control modules (PV / wind power control) |
| `emtp_api.py` | API Adaptation | Semantic interface abstraction over the EMTP numerical kernel |
| `emtp_ctrl_api.py` | API Adaptation | Semantic interface for control-related tool calls |

These four files implement the **top two layers** of the four-layer architecture described in the paper:

```
┌─────────────────────────────────────────┐
│   LLM Client  (Claude Sonnet 4.6)       │
├─────────────────────────────────────────┤
│   MCP Communication Layer    ← provided │
├─────────────────────────────────────────┤
│   API Adaptation Layer       ← provided │
├─────────────────────────────────────────┤
│   EMTP Computational Kernel  (not released)
└─────────────────────────────────────────┘
```

> ⚠️ **Note:** The underlying EMTP computational kernel (`emtp_core.py`, `emtp_ctrl_core.py`, case templates, etc.) is **not included** in this release. The files in this repository will not run standalone — they are released for the purpose of demonstrating the MCP-based interface design discussed in the paper.

---

## Requirements

- Python 3.11+
- [`fastmcp`](https://github.com/jlowin/fastmcp) — MCP server framework
- NumPy, SciPy (used by the underlying kernel)
- Claude Desktop, configured to connect to a local MCP server

---

## Architecture

The interface layer implements three key mechanisms described in the paper:

1. **Semantic interface abstraction** — simulation tools are exposed as declarative, physics-aware API calls so that the LLM can invoke them from natural-language instructions without solver-level knowledge.
2. **Hash-based node mapping** — internal node indices are managed transparently, relieving the LLM of bookkeeping responsibility.
3. **Template instantiation** — system-level topologies (RC circuit, grid-connected PV, direct-drive PMSG wind) are encapsulated as parameterized templates, with the LLM acting as a semantic compiler that extracts physical parameters from unstructured user instructions.

---

## Citation

The associated paper is currently under review. Please check back later for the formal citation.

```bibtex
@misc{emtp-mcp-2026,
  title  = {Design and Implementation of a Large Language Model-Driven
            Electromagnetic Transient Simulation System Based on the
            Model Context Protocol},
  author = {Gao, Yan and Xu, Jin},
  year   = {2026},
  note   = {Under review}
}
```

---

## License

This project is released under the [MIT License](LICENSE).

---

## Contact

For questions about the paper or the interface design, please contact:

- Yan Gao — `ardoin06@sjtu.edu.cn`
- Jin Xu — `xujin20506@sjtu.edu.cn`

College of Smart Energy / School of Electrical Engineering
Shanghai Jiao Tong University, Shanghai, China

---

## 中文简介

本仓库包含我们在论文《基于模型上下文协议的大语言模型驱动电磁暂态仿真系统设计与实现》中提出的 LLM 驱动 EMT 仿真框架的 **MCP 通信层与 API 适配层**代码。

四个文件分别对应论文中四层架构的上两层（MCP 服务与 API 抽象），底层的 EMTP 数值核心暂未开源。本仓库主要用于展示论文中讨论的接口设计方案，无法单独运行完整仿真。

论文目前仍在送审中，正式接收后将更新引用信息。

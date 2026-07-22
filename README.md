# Coupled Boolean Network Library (`cbnetwork`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![C++17](https://img.shields.io/badge/C++-17-blue.svg)](https://en.cppreference.com/w/cpp/17)

`cbnetwork` is a high-performance hybrid framework (Python + C++) designed for the creation, simulation, benchmarking, and analysis of **Coupled Boolean Networks (CBNs)**. Developed as part of academic research in Computer Science, it combines the flexibility of Python orchestration with an optimized C++ computing core to ensure scalability and scientific rigor.

The library enables advanced definition of network topologies, local dynamics, and coupling functions, providing a robust environment for researchers in complex systems, computational biology, and artificial intelligence.

---

## 🏛️ Theoretical Background

Coupled Boolean Networks (CBNs) formalize systems composed of interconnected subsystems, where each node is an autonomous Boolean network. The state evolves according to local functions and dynamic signals coming from connected neighbors.

*   **Attractor Fields:** The core objective is to identify stable configurations of the global system (point or cyclic attractors).
*   **Hybrid Architecture:** Intensive state-search and validation tasks are delegated to a native C++ core, dramatically reducing memory footprint (RSS) and execution time compared to purely interpreted implementations.

---

## ⚙️ System Requirements

*   C++17 compatible compiler (`g++` or `clang`)
*   `CMake` (version 3.12 or higher)
*   Python 3.8 or higher

---

## 📦 Installation

Clone the repository and install the base Python dependencies:

```bash
git clone [https://github.com/crptcusco/cbn_core.git](https://github.com/crptcusco/cbn_core.git)
cd cbn_core
pip install -r requirements.txt
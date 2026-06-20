# Audit Report: CBN C++ Core (cbnetwork)

## 1. Inventory of Public Functions (Post-Refactor)

### Class: `cbnetwork::CBN`

| Function | Category | Complexity | Status / Description |
| :--- | :--- | :--- | :--- |
| `find_local_attractors()` | **Unified** | O(N * 2^V) | **Primary Entry Point**. Automatically selects best parallel strategy. |
| `find_compatible_pairs()` | **Unified** | O(E * A^2) | **Primary Entry Point**. Parallel filtering of attractor pairs. |
| `mount_attractor_fields()` | **Unified** | O(Cartesian) | **Primary Entry Point**. Combinatorial field assembly. |
| `find_local_attractors_sequential` | Variant | O(N * 2^V) | Uses Sequential Turbo logic. |
| `find_local_attractors_parallel` | Variant | O(N * 2^V) | Alias for weighted parallel. |
| `find_local_attractors_parallel_with_weights` | Variant | O(N * 2^V) | Bucket balancing logic. |
| `audit_indices` | **Critical** | O(N + E) | Validates topology and variable consistency. |
| `clear_dynamics` | **Critical** | O(N + E) | **Stateless Reset**. Clears all results and internal counters. |
| `clone` | **Critical** | O(N + E) | Deep copy for isolated experiment runs. |
| `process_kind_signal` | **Critical** | O(E * A) | Signal classification (Restricted, Stable, etc.). |
| `order_edges_canonically` | **Critical** | O(E log E) | Deterministic sorting for parity. |

**Eliminated (Legacy/Redundant):**
- `find_local_attractors_brute_force_turbo` (Consolidated into Sequential/Parallel)
- `find_compatible_pairs_turbo` (Alias removed)
- `mount_stable_attractor_fields_turbo` (Alias removed)
- `generate_global_scenes` (Empty/Legacy removed)
- `count_fields_by_global_scenes` (Empty/Legacy removed)

---

## 2. Stateless & Isolation Policy

The core now adheres to a "Disposable" pattern:
- **`clear_dynamics()`**: Fully reset, including `kind_signal` defaults (set to `2: NOT COMPUTE`).
- **Benchmark Isolation**: `scientific_benchmarking.cpp` now performs a fresh `clone()` and explicit `clear_dynamics()` for every strategy run, ensuring Sample 1 cannot pollute Sample 2.
- **Global State**: Minimal and read-only (`allowed_topologies`).

## 3. Audit Mode (`--audit`)

The benchmarking tool now supports an `--audit` flag that reports:
- Node-by-node attractor counts.
- Global compatible pair counts.
- Final global field counts.
This format matches the diagnostic output of the Python solver for bit-for-bit parity verification.

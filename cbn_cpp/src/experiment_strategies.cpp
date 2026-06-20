#include "cbnetwork/experiment_strategies.hpp"
#include <algorithm>
#include <chrono>
#include <functional>
#include <future>
#include <iostream>
#include <numeric>
#include <omp.h>
#include <sys/resource.h>

namespace cbnetwork {

using namespace std::chrono;

static long get_max_rss() {
  struct rusage usage;
  getrusage(RUSAGE_SELF, &usage);
  return usage.ru_maxrss;
}

// Memory-efficient vector merge
static std::vector<int> merge_two_sorted_vectors(const std::vector<int> &v1,
                                                 const std::vector<int> &v2) {
  std::vector<int> res;
  res.reserve(v1.size() + v2.size());
  std::set_union(v1.begin(), v1.end(), v2.begin(), v2.end(),
                 std::back_inserter(res));
  return res;
}

// The local merge_field_lists_sequentially was removed in favor of the correct
// combinatorial implementation in CBN::mount_stable_attractor_fields().

// 1. TRADITIONAL EXPERIMENT
ExperimentResults TraditionalExperiment::run(std::shared_ptr<CBN> cbn) {
  ExperimentResults res;
  res.strategy_name = "Traditional";
  int prev_threads = omp_get_max_threads();
  omp_set_num_threads(1);
  auto start_total = high_resolution_clock::now();

  auto start1 = high_resolution_clock::now();
  cbn->find_local_attractors_sequential();
  auto end1 = high_resolution_clock::now();
  res.p1_ms = duration<double, std::milli>(end1 - start1).count();

  auto start2 = high_resolution_clock::now();
  cbn->find_compatible_pairs(); // Will use sequential path if OMP=1
  auto end2 = high_resolution_clock::now();
  res.p2_ms = duration<double, std::milli>(end2 - start2).count();

  auto start3 = high_resolution_clock::now();
  cbn->mount_attractor_fields();
  auto end3 = high_resolution_clock::now();
  res.p3_ms = duration<double, std::milli>(end3 - start3).count();

  auto end_total = high_resolution_clock::now();
  res.total_ms = duration<double, std::milli>(end_total - start_total).count();
  res.max_rss_kb = get_max_rss();
  res.global_attractors_count = cbn->d_attractor_fields.size();
  res.success = true;
  omp_set_num_threads(prev_threads);
  return res;
}

// 2. SIMPLE PARALLEL EXPERIMENT
ExperimentResults SimpleParallelExperiment::run(std::shared_ptr<CBN> cbn) {
  ExperimentResults res;
  res.strategy_name = "SimpleParallel";
  auto start_total = high_resolution_clock::now();

  auto start1 = high_resolution_clock::now();
  cbn->find_local_attractors_parallel();
  auto end1 = high_resolution_clock::now();
  res.p1_ms = duration<double, std::milli>(end1 - start1).count();

  auto start2 = high_resolution_clock::now();
  cbn->find_compatible_pairs_parallel();
  auto end2 = high_resolution_clock::now();
  res.p2_ms = duration<double, std::milli>(end2 - start2).count();

  auto start3 = high_resolution_clock::now();
  cbn->mount_attractor_fields();
  auto end3 = high_resolution_clock::now();
  res.p3_ms = duration<double, std::milli>(end3 - start3).count();
  auto end_total = high_resolution_clock::now();
  res.total_ms = duration<double, std::milli>(end_total - start_total).count();
  res.max_rss_kb = get_max_rss();
  res.global_attractors_count = cbn->d_attractor_fields.size();
  res.success = true;
  return res;
}

// 3. ADVANCED PARALLEL EXPERIMENT
ExperimentResults AdvancedParallelExperiment::run(std::shared_ptr<CBN> cbn) {
  ExperimentResults res;
  res.strategy_name = "AdvancedParallel";
  auto start_total = high_resolution_clock::now();

  auto start1 = high_resolution_clock::now();
  cbn->find_local_attractors();
  auto end1 = high_resolution_clock::now();
  res.p1_ms = duration<double, std::milli>(end1 - start1).count();

  auto start2 = high_resolution_clock::now();
  cbn->find_compatible_pairs();
  auto end2 = high_resolution_clock::now();
  res.p2_ms = duration<double, std::milli>(end2 - start2).count();

  auto start3 = high_resolution_clock::now();
  cbn->mount_attractor_fields();
  auto end3 = high_resolution_clock::now();
  res.p3_ms = duration<double, std::milli>(end3 - start3).count();
  auto end_total = high_resolution_clock::now();
  res.total_ms = duration<double, std::milli>(end_total - start_total).count();
  res.max_rss_kb = get_max_rss();
  res.global_attractors_count = cbn->d_attractor_fields.size();
  res.success = true;
  return res;
}

} // namespace cbnetwork

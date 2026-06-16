#include "cbnetwork/cbnetwork.hpp"
#include "cbnetwork/experiment_strategies.hpp"
#include "nlohmann/json.hpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>

using namespace cbnetwork;
namespace fs = std::filesystem;
using json = nlohmann::json;

std::string get_filename(int sample_id, const std::string &strategy, const std::string &type) {
  return "cbn_sample_" + std::to_string(sample_id) + "_" + strategy + "_" + type;
}

void log_to_csv(const std::string &filename, const ExperimentResults &res, int sample_id, int topology, int networks, int vars) {
  bool file_exists = fs::exists(filename);
  std::ofstream out(filename, std::ios_base::app);
  if (!out.is_open()) return;
  if (!file_exists) out << "sample_id,strategy,topology,n_networks,n_vars,p1_ms,p2_ms,p3_ms,max_rss_kb,fields\n";
  out << sample_id << "," << res.strategy_name << "," << topology << "," << networks << "," << vars << "," << std::fixed << std::setprecision(4) << res.p1_ms << "," << std::fixed << std::setprecision(4) << res.p2_ms << "," << std::fixed << std::setprecision(4) << res.p3_ms << "," << res.max_rss_kb << "," << res.global_attractors_count << "\n";
}

void export_network_structure_json(int sample_id, std::shared_ptr<CBN> cbn, const std::string &output_dir) {
  std::string filepath = output_dir + "/" + get_filename(sample_id, "base", "network_structure.json");
  cbn->save_network_to_json(filepath);
}

void export_dynamics_json(int sample_id, const std::string &strategy_name, std::shared_ptr<CBN> cbn, const ExperimentResults &res, const std::string &output_dir) {
  std::string filepath = output_dir + "/" + get_filename(sample_id, strategy_name, "dynamics.json");
  json j_dyn;
  j_dyn["simulation_info"] = { {"nodes", (int)cbn->l_local_networks.size()}, {"v_elements", (int)(cbn->get_n_local_variables() * cbn->l_local_networks.size())} };
  json j_attrs = json::array();
  for (auto const& [id, field] : cbn->d_attractor_fields) {
      json j_f; j_f["id"] = id; j_f["length"] = (int)field.size();
      std::vector<int> sorted_field = field; std::sort(sorted_field.begin(), sorted_field.end());
      j_f["states"] = sorted_field; j_attrs.push_back(j_f);
  }
  j_dyn["attractors"] = j_attrs;
  j_dyn["sample_id"] = sample_id; j_dyn["strategy"] = strategy_name;
  j_dyn["performance"] = {{"p1_ms", res.p1_ms}, {"p2_ms", res.p2_ms}, {"p3_ms", res.p3_ms}, {"total_ms", res.total_ms}};
  std::ofstream out(filepath); if (out.is_open()) out << j_dyn.dump(4) << std::endl;
}

int main(int argc, char **argv) {
  int n_samples = 100, n_networks = 12, n_vars = 10, topology = 3;
  std::string custom_output_file = "", custom_output_dir = "", input_json = "";
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--samples" && i + 1 < argc) n_samples = std::stoi(argv[++i]);
    else if ((arg == "--networks" || arg == "--nodes") && i + 1 < argc) n_networks = std::stoi(argv[++i]);
    else if (arg == "--vars" && i + 1 < argc) n_vars = std::stoi(argv[++i]);
    else if (arg == "--topology" && i + 1 < argc) topology = std::stoi(argv[++i]);
    else if (arg == "--output" && i + 1 < argc) custom_output_file = argv[++i];
    else if (arg == "--dir" && i + 1 < argc) custom_output_dir = argv[++i];
    else if (arg == "--input" && i + 1 < argc) { input_json = argv[++i]; n_samples = 1; }
  }
  std::string output_dir = custom_output_dir.empty() ? "../experiments/results" : custom_output_dir;
  fs::create_directories(output_dir);
  std::string output_file = custom_output_file.empty() ? output_dir + "/benchmark_results.csv" : custom_output_file;

  std::vector<std::pair<std::string, std::unique_ptr<ExperimentStrategy>>> strategies;
  strategies.push_back({"Traditional", std::make_unique<TraditionalExperiment>()});
  strategies.push_back({"SimpleParallel", std::make_unique<SimpleParallelExperiment>()});
  strategies.push_back({"AdvancedParallel", std::make_unique<AdvancedParallelExperiment>()});

  for (int s = 0; s < n_samples; ++s) {
    int sample_id = s + 1;
    try {
      std::shared_ptr<CBN> reference_cbn;
      if (!input_json.empty()) reference_cbn = CBN::load_network_from_json(input_json);
      else reference_cbn = CBN::cbn_generator(topology, n_networks, n_vars, 1, 1);
      if (!reference_cbn) throw std::runtime_error("CBN load failed");
      if (input_json.empty()) export_network_structure_json(sample_id, reference_cbn, output_dir);
      for (auto &s_pair : strategies) {
        auto cbn = reference_cbn->clone(); auto results = s_pair.second->run(cbn);
        log_to_csv(output_file, results, sample_id, topology, n_networks, n_vars);
        export_dynamics_json(sample_id, s_pair.first, cbn, results, output_dir);
      }
    } catch (const std::exception &e) { std::cerr << "Error: " << e.what() << std::endl; }
  }
  return 0;
}

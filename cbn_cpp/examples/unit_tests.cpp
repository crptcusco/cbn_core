#include "cbnetwork/coupling.hpp"
#include "cbnetwork/localnetwork.hpp"
#include "cbnetwork/cbnetwork.hpp"
#include <iostream>
#include <cassert>
#include <vector>
#include <map>
#include <stdexcept>

using namespace cbnetwork;

void test_or_coupling() {
    OrCoupling strategy;
    std::vector<int> output_vars = {1, 2, 3};
    int coupling_var = 10;

    std::string func = strategy.generate_coupling_function(output_vars);
    assert(func == " 1 ∨ 2 ∨ 3 ");

    auto cnf = strategy.to_cnf(output_vars, coupling_var);
    std::vector<std::vector<int>> expected = {{-1, 10}, {-2, 10}, {-3, 10}, {1, 2, 3, -10}};
    assert(cnf == expected);
    std::cout << "test_or_coupling passed" << std::endl;
}

void test_and_coupling() {
    AndCoupling strategy;
    std::vector<int> output_vars = {1, 2, 3};
    int coupling_var = 10;

    std::string func = strategy.generate_coupling_function(output_vars);
    assert(func == " 1 ∧ 2 ∧ 3 ");

    auto cnf = strategy.to_cnf(output_vars, coupling_var);
    std::vector<std::vector<int>> expected = {{1, -10}, {2, -10}, {3, -10}, {-1, -2, -3, 10}};
    assert(cnf == expected);
    std::cout << "test_and_coupling passed" << std::endl;
}

void test_threshold_coupling() {
    ThresholdCoupling strategy(2);
    std::vector<int> output_vars = {1, 2, 3};
    int coupling_var = 10;

    auto cnf = strategy.to_cnf(output_vars, coupling_var);
    // Implication 1: (sum >= 2) => C.  Combos of 2 from {1,2,3}: {1,2}, {1,3}, {2,3}. Clauses: {-1,-2,10}, {-1,-3,10}, {-2,-3,10}
    // Implication 2: C => (sum >= 2).  Combos of 3-2+1=2 from {1,2,3}: {1,2}, {1,3}, {2,3}. Clauses: {-10,1,2}, {-10,1,3}, {-10,2,3}

    std::vector<std::vector<int>> expected = {
        {-1, -2, 10}, {-1, -3, 10}, {-2, -3, 10},
        {-10, 1, 2}, {-10, 1, 3}, {-10, 2, 3}
    };
    assert(cnf == expected);
    std::cout << "test_threshold_coupling passed" << std::endl;
}

void test_evaluate_boolean_function() {
    // v1 = v2 OR v3
    // CNF: (-v2 | v1), (-v3 | v1), (v2 | v3 | -v1)
    std::vector<std::vector<int>> cnf = {{-2, 1}, {-3, 1}, {2, 3, -1}};

    std::map<int, int> state = {{1, 1}};
    std::map<int, int> external = {{2, 1}, {3, 0}};
    assert(LocalNetwork::evaluate_boolean_function(cnf, state, external) == 1);

    state[1] = 0;
    assert(LocalNetwork::evaluate_boolean_function(cnf, state, external) == 0);

    external[2] = 0;
    external[3] = 0;
    state[1] = 0;
    assert(LocalNetwork::evaluate_boolean_function(cnf, state, external) == 1);

    std::cout << "test_evaluate_boolean_function passed" << std::endl;
}

void test_complexity_threshold_validation() {
    // We will build a dummy CBN with 11 local networks, each having 4 attractors.
    std::vector<std::shared_ptr<LocalNetwork>> networks;
    for (int i = 1; i <= 11; ++i) {
        auto net = std::make_shared<LocalNetwork>(i, std::vector<int>{i});
        // Add a scene
        auto scene = std::make_shared<LocalScene>(1, std::vector<std::string>{""}, std::vector<int>{});
        // Add 4 dummy attractors
        for (int a = 1; a <= 4; ++a) {
            auto attr = std::make_shared<LocalAttractor>(
                0, a, std::vector<std::shared_ptr<LocalState>>{}, i, std::vector<int>{}, ""
            );
            scene->l_attractors.push_back(attr);
        }
        net->local_scenes.push_back(scene);
        networks.push_back(net);
    }

    // Add 1 dummy edge so directed edges is not empty
    std::vector<std::shared_ptr<DirectedEdge>> edges;
    edges.push_back(std::make_shared<DirectedEdge>(1, 100, 1, 2, std::vector<int>{1}, ""));

    CBN cbn(networks, edges);

    // Call mount_stable_attractor_fields and assert it throws std::runtime_error
    bool threw = false;
    try {
        cbn.mount_stable_attractor_fields();
    } catch (const std::runtime_error& e) {
        std::string msg = e.what();
        if (msg.find("Complexity limit exceeded") != std::string::npos) {
            threw = true;
        }
    }
    assert(threw);
    std::cout << "test_complexity_threshold_validation passed" << std::endl;
}

int main() {
    test_or_coupling();
    test_and_coupling();
    test_threshold_coupling();
    test_evaluate_boolean_function();
    test_complexity_threshold_validation();
    std::cout << "All C++ unit tests passed!" << std::endl;
    return 0;
}

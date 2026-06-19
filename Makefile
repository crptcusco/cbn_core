.PHONY: all build-cpp test-python test-cpp parity clean

all: build-cpp test-python test-cpp parity

build-cpp:
	@echo "Building C++ core..."
	mkdir -p cbn_cpp/build
	cd cbn_cpp/build && cmake .. && make unit_tests scientific_benchmarking

test-python:
	@echo "Running Python unit tests..."
	export PYTHONPATH=$$PYTHONPATH:$$(pwd)/cbn_python/src && python -m pytest cbn_python/tests/test_coupling.py cbn_python/tests/test_localnetwork_logic.py

test-cpp: build-cpp
	@echo "Running C++ unit tests..."
	./cbn_cpp/build/unit_tests

parity: build-cpp
	@echo "Running Property-based Parity Validation..."
	python scripts/parity_validation.py

clean:
	rm -rf cbn_cpp/build
	rm -rf temp_parity
	find . -name "__pycache__" -type d -exec rm -rf {} +

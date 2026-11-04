CXX ?= g++
CXXFLAGS = -std=c++11 -O2 -Wall -Wextra -Werror -Iinclude
SRC = src/saos_core.cpp src/saos_proto.cpp src/saos_calib.cpp src/saos_gateway.cpp
HDR = include/saos_core.h include/saos_proto.h include/saos_calib.h include/saos_gateway.h
all: build/test_core build/test_proto build/test_calib build/test_gateway build/test_gateway_e2e build/dumpframe build/replay build/linkbench build/calibfit
build:
	mkdir -p build
build/test_core: tests/test_core.cpp $(SRC) $(HDR) | build
	$(CXX) $(CXXFLAGS) tests/test_core.cpp src/saos_core.cpp -o $@
build/test_proto: tests/test_proto.cpp $(SRC) $(HDR) | build
	$(CXX) $(CXXFLAGS) tests/test_proto.cpp src/saos_proto.cpp -o $@
build/test_calib: tests/test_calib.cpp $(SRC) $(HDR) | build
	$(CXX) $(CXXFLAGS) tests/test_calib.cpp src/saos_calib.cpp src/saos_proto.cpp -o $@
build/test_gateway: tests/test_gateway.cpp $(SRC) $(HDR) | build
	$(CXX) $(CXXFLAGS) tests/test_gateway.cpp src/saos_gateway.cpp src/saos_proto.cpp src/saos_core.cpp -o $@
build/test_gateway_e2e: tests/test_gateway_e2e.cpp $(SRC) $(HDR) | build
	$(CXX) $(CXXFLAGS) tests/test_gateway_e2e.cpp src/saos_gateway.cpp src/saos_proto.cpp src/saos_core.cpp -o $@
build/dumpframe: tools/dumpframe.cpp $(SRC) $(HDR) | build
	$(CXX) $(CXXFLAGS) tools/dumpframe.cpp src/saos_proto.cpp -o $@
build/calibfit: tools/calibfit.cpp $(SRC) $(HDR) | build
	$(CXX) $(CXXFLAGS) tools/calibfit.cpp src/saos_calib.cpp src/saos_proto.cpp -o $@
build/replay: tools/replay.cpp $(SRC) $(HDR) | build
	$(CXX) $(CXXFLAGS) tools/replay.cpp src/saos_core.cpp -o $@
build/linkbench: tools/linkbench.cpp $(SRC) $(HDR) | build
	$(CXX) $(CXXFLAGS) tools/linkbench.cpp src/saos_proto.cpp -o $@
test: all
	./build/test_core
	./build/test_proto
	./build/test_calib
	./build/test_gateway
	./build/test_gateway_e2e
clean:
	rm -rf build

#!/bin/bash
rm -rf build
mkdir build
cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=$HOME/local --install-prefix=$HOME/local -S . -B build
cmake --build ./build  -j14
cmake --install ./build


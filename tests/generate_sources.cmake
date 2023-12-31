cmake_minimum_required(VERSION 3.19 FATAL_ERROR)
#DEST_DIR
#HEADER
set(header ${HEADER})
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/main.cpp.in ${DEST_DIR}/main.cpp @ONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/test_weak_symbol.cpp.in ${DEST_DIR}/test_weak_symbol.cpp @ONLY)
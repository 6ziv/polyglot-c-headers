project(polyglot_headers)
cmake_minimum_required(VERSION 3.19 FATAL_ERROR)
enable_testing()

add_subdirectory("resources")
add_subdirectory("tests")
add_subdirectory("examples")
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/scripts/ DESTINATION ${CMAKE_INSTALL_PREFIX}/scripts FILES_MATCHING PATTERN "*.py")
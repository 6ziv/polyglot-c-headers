cmake_minimum_required(VERSION 3.19 FATAL_ERROR)
find_program(PYTHON_EXECUTABLE NAMES python python3)

add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/play_mp4/main.cpp"
	COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/play_mp4"
	COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/play_mp4.cpp" "${CMAKE_CURRENT_BINARY_DIR}/play_mp4/main.cpp"
	DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/play_mp4.cpp"
)
add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/play_mp4/badapple.mp4"
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_mp4.py" "${CMAKE_CURRENT_SOURCE_DIR}/../resources/badapple.mp4" "${CMAKE_CURRENT_BINARY_DIR}/play_mp4/badapple.mp4" -p -b
	DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_mp4.py" "${CMAKE_CURRENT_SOURCE_DIR}/../resources/badapple.mp4" "${CMAKE_CURRENT_BINARY_DIR}/play_mp4/main.cpp"
)
add_custom_target(example_mp4 DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/play_mp4/main.cpp" "${CMAKE_CURRENT_BINARY_DIR}/play_mp4/badapple.mp4")

add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/execute_script/main.cpp"
	COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/execute_script"
	COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/execute_script.cpp" "${CMAKE_CURRENT_BINARY_DIR}/execute_script/main.cpp"
	DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/execute_script.cpp"
)
add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/execute_script/play_video.sh"
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" "${CMAKE_CURRENT_SOURCE_DIR}/../resources/badapple.mp4" "${CMAKE_CURRENT_BINARY_DIR}/execute_script/play_video.sh" -s "/bin/env ffplay" -c /bin/env ffplay "@file@"
	DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" "${CMAKE_CURRENT_SOURCE_DIR}/../resources/badapple.mp4" "${CMAKE_CURRENT_BINARY_DIR}/execute_script/main.cpp"
)
add_custom_target(example_script DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/execute_script/main.cpp" "${CMAKE_CURRENT_BINARY_DIR}/execute_script/play_video.sh")

add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/main.cpp"
	COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable"
	COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/run_exe.cpp" "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/main.cpp"
	DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/run_exe.cpp"
)
add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/ymzx.exe"
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_exe.py" "${CMAKE_CURRENT_SOURCE_DIR}/../resources/ymzx.exe" "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/ymzx_raw.exe" -p -b -e
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/concat_files.py" "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/ymzx.exe" "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/ymzx_raw.exe" "${CMAKE_CURRENT_SOURCE_DIR}/../resources/ymzx_tail.patch"
	DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_exe.py" "${CMAKE_CURRENT_SOURCE_DIR}/../resources/ymzx.exe" "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/main.cpp" "${CMAKE_CURRENT_SOURCE_DIR}/../resources/ymzx_tail.patch" "${CMAKE_CURRENT_SOURCE_DIR}/concat_files.py"
)
add_custom_target(example_exe DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/main.cpp" "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/ymzx.exe")

add_custom_target(examples ALL DEPENDS example_mp4 example_script example_exe)

install(
	FILES "${CMAKE_CURRENT_BINARY_DIR}/play_mp4/main.cpp" "${CMAKE_CURRENT_BINARY_DIR}/play_mp4/badapple.mp4"
	DESTINATION ${CMAKE_INSTALL_PREFIX}/examples/play_mp4
)

install(
	FILES "${CMAKE_CURRENT_BINARY_DIR}/execute_script/main.cpp" "${CMAKE_CURRENT_BINARY_DIR}/execute_script/play_video.sh"
	DESTINATION ${CMAKE_INSTALL_PREFIX}/examples/execute_script
)

install(
	FILES "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/main.cpp" "${CMAKE_CURRENT_BINARY_DIR}/run_windows_executable/ymzx.exe"
	DESTINATION ${CMAKE_INSTALL_PREFIX}/examples/run_windows_executable
)
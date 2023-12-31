cmake_minimum_required(VERSION 3.19 FATAL_ERROR)

include(CTest)

find_program(PYTHON_EXECUTABLE NAMES python python3)
find_program(FFMPEG_BIN ffmpeg)

set(SOURCE_MP4_ORIG "${CMAKE_CURRENT_SOURCE_DIR}/../resources/badapple.mp4")
set(SOURCE_MP4 "${CMAKE_CURRENT_BINARY_DIR}/badapple_trimmed.mp4")
set(SOURCE_SCRIPT "${CMAKE_CURRENT_SOURCE_DIR}/print_hello.sh")

macro(setup_fixtures test fixtures)
	set_tests_properties(${test} PROPERTIES FIXTURES_SETUP ${fixtures})
endmacro()

macro(require_fixtures test fixtures)
	set_tests_properties(${test} PROPERTIES FIXTURES_REQUIRED "${fixtures}")
endmacro()

macro(target_as_test name)
	add_test(${name}
		"${CMAKE_COMMAND}"
		--build "${CMAKE_BINARY_DIR}"
		--config "$<CONFIG>"
		--target ${name}
	)
endmacro()

macro(generate_sources header fixture)
	add_custom_command(
		OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${fixture}/main.cpp ${CMAKE_CURRENT_BINARY_DIR}/${fixture}/test_weak_symbol.cpp
		COMMAND "${CMAKE_COMMAND}" -D DEST_DIR=${CMAKE_CURRENT_BINARY_DIR}/${fixture} -D HEADER=${header} -P ${CMAKE_CURRENT_SOURCE_DIR}/generate_sources.cmake
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
	)
	add_test(
		NAME ${fixture}_gen_sources
		COMMAND "${CMAKE_COMMAND}" -D DEST_DIR=${CMAKE_CURRENT_BINARY_DIR}/${fixture} -D HEADER=${header} -P ${CMAKE_CURRENT_SOURCE_DIR}/generate_sources.cmake
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
	)
	setup_fixtures(${fixture}_gen_sources ${fixture}_sources)
	require_fixtures(${fixture}_gen_sources init_${fixture})
endmacro()

macro(init_fixture fixture)
	add_test(
		NAME init_${fixture}
		COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/${fixture}"
		WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
	)
	setup_fixtures(init_${fixture} init_${fixture})
endmacro()

macro(test_add_executable)
	set(sources ${ARGV})
	list(POP_FRONT sources fixture tag postfix)
    
	add_executable(
		executable_${fixture}_${tag}_${postfix} EXCLUDE_FROM_ALL
		${sources}
	)
	set_target_properties(executable_${fixture}_${tag}_${postfix} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}")
	target_include_directories(executable_${fixture}_${tag}_${postfix} BEFORE PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}")
	target_as_test(executable_${fixture}_${tag}_${postfix})
	setup_fixtures(executable_${fixture}_${tag}_${postfix} executable_${fixture}_${tag}_${postfix})
	require_fixtures(executable_${fixture}_${tag}_${postfix} "${fixture}_sources;resource_${fixture}_${tag}")
	#add_dependencies(executable_${fixture}_${tag}_${postfix} ${fixture}_gen_sources)
	
	include("${fixture}_callback.cmake" OPTIONAL)
endmacro()

macro(test)
	set(arguments ${ARGV})
	list(POP_FRONT arguments fixture tag)
    add_test(NAME make_dir_for_${fixture}_${tag} COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}")
	
	include("${fixture}_init.cmake" OPTIONAL)
		
	test_add_executable(${fixture} ${tag} "cpp" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}/main.cpp")
	test_add_executable(${fixture} ${tag} "cpp_weak" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}/main.cpp" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}/test_weak_symbol.cpp")
endmacro()
init_fixture(mp4)
generate_sources(video.mp4 mp4)

add_executable(
    fake_ffplay
    EXCLUDE_FROM_ALL
    ${CMAKE_CURRENT_SOURCE_DIR}/dump_to_file.c
)
add_custom_target(
	make_fake_ffplay_dir
	COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/fake_ffplay_dir"
)
set_target_properties(fake_ffplay PROPERTIES RUNTIME_OUTPUT_NAME "ffplay" RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/fake_ffplay_dir")
add_dependencies(fake_ffplay make_fake_ffplay_dir)
target_as_test(fake_ffplay)
setup_fixtures(fake_ffplay fake_ffplay)

add_test(
	NAME prepare_video_resource
	COMMAND "${FFMPEG_BIN}" "-y" "-i" "${SOURCE_MP4_ORIG}" "-c:v" "copy" "-c:a" "copy" "-ss" "00:00:00" "-t" "00:00:10" "${SOURCE_MP4}"
)
setup_fixtures(prepare_video_resource trimmed_mp4)

add_test(
	NAME prepare_baseline_ts_half
	COMMAND "${FFMPEG_BIN}" "-y" "-fflags" "bitexact" "-i" "${SOURCE_MP4}" "-f" "segment" "-c:v" "copy" "-c:a" "copy" "-segment_list" "${CMAKE_CURRENT_BINARY_DIR}/dummy_m3u8_file.m3u8" "-segment_time" "9223372036854" "${CMAKE_CURRENT_BINARY_DIR}/video_%03d.ts"
)
require_fixtures(prepare_baseline_ts_half trimmed_mp4)
setup_fixtures(prepare_baseline_ts_half ts_1)

add_test(
	NAME prepare_baseline_ts
	COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${CMAKE_CURRENT_BINARY_DIR}/video_000.ts" "${CMAKE_CURRENT_BINARY_DIR}/video.ts"
)
require_fixtures(prepare_baseline_ts ts_1)
setup_fixtures(prepare_baseline_ts baseline_ts)

test(mp4 normal)
#test(mp4 use_pragma -p)
test(mp4 use_base64 -b)
#test(mp4 use_pragma_and_base64 -p -b)

add_executable(
    hello_exe
    EXCLUDE_FROM_ALL
    ${CMAKE_CURRENT_SOURCE_DIR}/hello.c
)

target_as_test(hello_exe)
setup_fixtures(hello_exe hello_exe)

IF (WIN32)
	init_fixture(exe)
	generate_sources(hello.exe exe)
	test(exe normal)
	#test(exe use_pragma -p)
	test(exe use_base64 -b)
	#test(exe use_pragma_and_base64 -p -b)
ELSE()
	init_fixture(script)
	generate_sources(print_hello.sh script)

	test(script normal)
	test(script piping -p)
	test(script shebang -s "/bin/env bash")
	test(script pipeing_shebang -p -s "/bin/env bash")
	test(script cmdline -c /bin/env bash "@file@")
	test(script shebang_cmdline -s "/bin/env bash" -c /bin/env bash "@file@")

	init_fixture(elf)
	generate_sources(hello elf)
	test(elf check_output)

	init_fixture(elf2)
	generate_sources(hello elf2)
	test(elf2 check_exact_binary -s "/bin/env bash ${CMAKE_CURRENT_SOURCE_DIR}/copy_file_rev.sh ${CMAKE_CURRENT_BINARY_DIR}/elf2_check_exact_binary/dumped_elf2" -c "/bin/env" "cp" "-f" "@file@" "${CMAKE_CURRENT_BINARY_DIR}/elf2_check_exact_binary/dumped_elf")
	test(elf2 check_exact_binary_piping -p -s "/bin/env tee ${CMAKE_CURRENT_BINARY_DIR}/elf2_check_exact_binary_piping/dumped_elf2" -c "/bin/env" "cp" "-f" "@file@" "${CMAKE_CURRENT_BINARY_DIR}/elf2_check_exact_binary_piping/dumped_elf")
ENDIF()
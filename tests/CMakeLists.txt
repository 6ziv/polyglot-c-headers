cmake_minimum_required(VERSION 3.19 FATAL_ERROR)

include(CTest)

find_program(PYTHON_EXECUTABLE NAMES python python3)
find_program(FFMPEG_BIN ffmpeg)

set(SOURCE_MP4_ORIG "${CMAKE_CURRENT_SOURCE_DIR}/../resources/badapple.mp4")
set(SOURCE_MP4 "${CMAKE_CURRENT_BINARY_DIR}/badapple_trimmed.mp4")
set(SOURCE_SCRIPT "${CMAKE_CURRENT_SOURCE_DIR}/print_hello.sh")

macro(setup_fixture fixture name)
	add_custom_target(${fixture}_tgt)
	add_test(${name}
		"${CMAKE_COMMAND}"
		--build "${CMAKE_BINARY_DIR}"
		--config "$<CONFIG>"
		--target ${fixture}_tgt
	)
	set_tests_properties(${name} PROPERTIES FIXTURES_SETUP ${fixture})
endmacro()

macro(setup_subfixture fixture subfixture name)
	setup_fixture(${subfixture} ${name})
	set_tests_properties(${name} PROPERTIES FIXTURES_REQUIRED ${fixture})
endmacro()

macro(fixture_depends fixture target)
	add_dependencies(${fixture}_tgt ${target})
endmacro()

macro(require_fixtures test fixtures)
	set_tests_properties(${test} PROPERTIES FIXTURES_REQUIRED ${fixtures})
endmacro()

macro(generate_sources header fixture)
	add_custom_command(
		OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${fixture}/main.cpp ${CMAKE_CURRENT_BINARY_DIR}/${fixture}/test_weak_symbol.cpp
		COMMAND "${CMAKE_COMMAND}" -D DEST_DIR=${CMAKE_CURRENT_BINARY_DIR}/${fixture} -D HEADER=${header} -P ${CMAKE_CURRENT_SOURCE_DIR}/generate_sources.cmake
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
	)
	add_custom_target(${fixture}_gen_sources)
	fixture_depends(${fixture} ${fixture}_gen_sources)
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
	
	setup_subfixture(${fixture}_${tag} compile_${fixture}_${tag}_${postfix} compile_${fixture}_${tag}_${postfix})
	
	fixture_depends(compile_${fixture}_${tag}_${postfix} executable_${fixture}_${tag}_${postfix})
	
	include("${fixture}_callback.cmake" OPTIONAL)
	
	require_fixtures(run_${fixture}_${tag}_${postfix} ${fixture}_${tag};compile_${fixture}_${tag}_${postfix})	
	
endmacro()

macro(test)
	set(arguments ${ARGV})
	list(POP_FRONT arguments fixture tag)
    add_custom_target(make_dir_for_${fixture}_${tag} COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}")
	setup_subfixture(${fixture} ${fixture}_${tag} prepare_${fixture}_${tag}_tests)
	
	include("${fixture}_init.cmake" OPTIONAL)
		
	test_add_executable(${fixture} ${tag} "cpp" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}/main.cpp")
	test_add_executable(${fixture} ${tag} "cpp_weak" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}/main.cpp" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}/test_weak_symbol.cpp")
endmacro()

setup_fixture(mp4 init_mp4_tests)
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
fixture_depends(mp4 fake_ffplay)

add_custom_command(
	OUTPUT "${SOURCE_MP4}"
	COMMAND "${FFMPEG_BIN}" "-y" "-i" "${SOURCE_MP4_ORIG}" "-c:v" "copy" "-c:a" "copy" "-ss" "00:00:00" "-t" "00:00:20" "${SOURCE_MP4}"
	DEPENDS "${SOURCE_MP4_ORIG}"
)

add_custom_command(
    OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/video_000.ts"
    COMMAND "${FFMPEG_BIN}" "-y" "-fflags" "bitexact" "-i" "${SOURCE_MP4}" "-f" "segment" "-c:v" "copy" "-c:a" "copy" "-segment_list" "${CMAKE_CURRENT_BINARY_DIR}/dummy_m3u8_file.m3u8" "-segment_time" "9223372036854" "${CMAKE_CURRENT_BINARY_DIR}/video_%03d.ts"
    DEPENDS "${SOURCE_MP4}"
    BYPRODUCTS "${CMAKE_CURRENT_BINARY_DIR}/dummy_m3u8_file.m3u8"
)
add_custom_command(
    OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/video.ts"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${CMAKE_CURRENT_BINARY_DIR}/video_000.ts" "${CMAKE_CURRENT_BINARY_DIR}/video.ts"
    DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/video_000.ts"
)

add_custom_target(make_ts_baseline DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/video.ts")
fixture_depends(mp4 make_ts_baseline)

test(mp4 normal)
test(mp4 use_pragma -p)
test(mp4 use_base64 -b)
test(mp4 use_pragma_and_base64 -p -b)

IF (WIN32)
add_executable(
    hello_exe
    EXCLUDE_FROM_ALL
    ${CMAKE_CURRENT_SOURCE_DIR}/hello.c
)
setup_fixture(exe init_exe_tests)
generate_sources(hello.exe exe)
test(exe normal)
test(exe use_pragma -p)
test(exe use_base64 -b)
test(exe use_pragma_and_base64 -p -b)

ELSE()
setup_fixture(script init_script_tests)
generate_sources(print_hello.sh script)

test(script normal)
test(script piping -p)
test(script shebang -s "/bin/env bash")
test(script pipeing_shebang -p -s "/bin/env bash")
test(script cmdline -c /bin/env bash "@file@")
test(script shebang_cmdline -s "/bin/env bash" -c /bin/env bash "@file@")


add_executable(
    hello_exe
    EXCLUDE_FROM_ALL
    ${CMAKE_CURRENT_SOURCE_DIR}/hello.c
)
setup_fixture(elf init_elf_tests)
generate_sources(hello elf)
test(elf check_output)

setup_fixture(elf2 init_elf_tests_exact)
generate_sources(hello elf2)
test(elf2 check_exact_binary -s "/bin/env bash ${CMAKE_CURRENT_SOURCE_DIR}/copy_file_rev.sh ${CMAKE_CURRENT_BINARY_DIR}/elf2_check_exact_binary/dumped_elf2" -c "/bin/env" "cp" "-f" "@file@" "${CMAKE_CURRENT_BINARY_DIR}/elf2_check_exact_binary/dumped_elf")
test(elf2 check_exact_binary_piping -p -s "/bin/env tee ${CMAKE_CURRENT_BINARY_DIR}/elf2_check_exact_binary_piping/dumped_elf2" -c "/bin/env" "cp" "-f" "@file@" "${CMAKE_CURRENT_BINARY_DIR}/elf2_check_exact_binary_piping/dumped_elf")

ENDIF()
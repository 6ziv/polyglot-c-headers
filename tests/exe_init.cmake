add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello.exe"
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_exe.py" "$<TARGET_FILE:hello_exe>" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello.exe" ${arguments}
	DEPENDS hello_exe "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_exe.py" make_dir_for_${fixture}_${tag}
)
add_custom_target(make_exe_for_${fixture}_${tag} DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello.exe")
fixture_depends(${fixture}_${tag} make_exe_for_${fixture}_${tag})

add_test(
	NAME validate_exe_${fixture}_${tag}
	COMMAND "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello"
)

set_tests_properties(validate_exe_${fixture}_${tag} PROPERTIES
	PASS_REGULAR_EXPRESSION "Hello from exe"
)

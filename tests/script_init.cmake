add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/print_hello.sh"
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" "${SOURCE_SCRIPT}" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/print_hello.sh" ${arguments}
	DEPENDS "${SOURCE_SCRIPT}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" make_dir_for_${fixture}_${tag}
)
add_custom_target(make_script_for_${fixture}_${tag} DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/print_hello.sh")
fixture_depends(${fixture}_${tag} make_script_for_${fixture}_${tag})

add_test(
	NAME validate_script_${fixture}_${tag}
	COMMAND /bin/env bash "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/print_hello.sh"
)

set_tests_properties(validate_script_${fixture}_${tag} PROPERTIES
	PASS_REGULAR_EXPRESSION "Hello from script"
)

add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello"
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" "$<TARGET_FILE:hello_exe>" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello" ${arguments}
	DEPENDS hello_exe "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" make_dir_for_${fixture}_${tag}
)
add_custom_target(make_elf_for_${fixture}_${tag} DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello")
fixture_depends(${fixture}_${tag} make_elf_for_${fixture}_${tag})

add_test(
	NAME validate_elf_${fixture}_${tag}
	COMMAND "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello"
)

set_tests_properties(validate_elf_${fixture}_${tag} PROPERTIES
	PASS_REGULAR_EXPRESSION "Hello from exe"
)

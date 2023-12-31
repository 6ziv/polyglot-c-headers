add_test(
	NAME make_elf_for_${fixture}_${tag}
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" "$<TARGET_FILE:hello_exe>" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello" ${arguments}
)
require_fixtures(make_elf_for_${fixture}_${tag} "hello_exe;make_dir_for_${fixture}_${tag}")
setup_fixtures(make_elf_for_${fixture}_${tag} resource_${fixture}_${tag}_inaccessible)
add_test(
	NAME chmod_elf_for_${fixture}_${tag}
	COMMAND "${CMAKE_COMMAND}" -DFILE=${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello -P "${CMAKE_CURRENT_SOURCE_DIR}/chmod.cmake"
)
require_fixtures(chmod_elf_for_${fixture}_${tag} resource_${fixture}_${tag}_inaccessible)
setup_fixtures(chmod_elf_for_${fixture}_${tag} resource_${fixture}_${tag})

add_test(
	NAME validate_elf_${fixture}_${tag}
	COMMAND "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello"
)

set_tests_properties(validate_elf_${fixture}_${tag} PROPERTIES
	PASS_REGULAR_EXPRESSION "Hello from exe"
)
require_fixtures(validate_elf_${fixture}_${tag} resource_${fixture}_${tag})
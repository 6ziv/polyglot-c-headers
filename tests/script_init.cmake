add_test(
	NAME make_script_for_${fixture}_${tag}
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" "${SOURCE_SCRIPT}" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/print_hello.sh" ${arguments}
)
require_fixtures(make_script_for_${fixture}_${tag} make_dir_for_${fixture}_${tag})
setup_fixtures(make_script_for_${fixture}_${tag} resource_${fixture}_${tag}_inaccessible)
add_test(
	NAME chmod_script_for_${fixture}_${tag}
	COMMAND "${CMAKE_COMMAND}" -DFILE=${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/print_hello.sh -P "${CMAKE_CURRENT_SOURCE_DIR}/chmod.cmake"
)
require_fixtures(chmod_script_for_${fixture}_${tag} resource_${fixture}_${tag}_inaccessible)
setup_fixtures(chmod_script_for_${fixture}_${tag} resource_${fixture}_${tag})

add_test(
	NAME validate_script_${fixture}_${tag}
	COMMAND /bin/env bash "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/print_hello.sh"
)
set_tests_properties(validate_script_${fixture}_${tag} PROPERTIES
	PASS_REGULAR_EXPRESSION "Hello from script"
)
require_fixtures(validate_script_${fixture}_${tag} resource_${fixture}_${tag})

add_test(
	NAME make_exe_for_${fixture}_${tag}
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_exe.py" "$<TARGET_FILE:hello_exe>" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello.exe" ${arguments}
)
require_fixtures(make_exe_for_${fixture}_${tag} "make_dir_for_${fixture}_${tag};hello_exe")
setup_fixtures(make_exe_for_${fixture}_${tag} resource_${fixture}_${tag})

add_test(
	NAME validate_exe_${fixture}_${tag}
	COMMAND "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello"
)

set_tests_properties(validate_exe_${fixture}_${tag} PROPERTIES
	PASS_REGULAR_EXPRESSION "Hello from exe"
)
require_fixtures(validate_exe_${fixture}_${tag} resource_${fixture}_${tag})
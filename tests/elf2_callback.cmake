add_test(
	NAME run_${fixture}_${tag}_${postfix}
	COMMAND "${CMAKE_COMMAND}" -E env DUMP_FILE=${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/dumped_elf "$<TARGET_FILE:executable_${fixture}_${tag}_${postfix}>"
)
require_fixtures(run_${fixture}_${tag}_${postfix} "executable_${fixture}_${tag}_${postfix};fake_ffplay")
setup_fixtures(run_${fixture}_${tag}_${postfix} executable_${fixture}_${tag}_${postfix}_dumped)

add_test(
	NAME compare_dumped_${fixture}_${tag}_${postfix}
	COMMAND "${CMAKE_COMMAND}" -E compare_files "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/dumped_elf" "$<TARGET_FILE:hello_exe>"
)
require_fixtures(compare_dumped_${fixture}_${tag}_${postfix} executable_${fixture}_${tag}_${postfix}_dumped)

add_dependencies(executable_${fixture}_${tag}_${postfix} make_elf_for_${fixture}_${tag})

add_test(
	NAME run_${fixture}_${tag}_${postfix}
	COMMAND "${CMAKE_COMMAND}" -E env DUMP_FILE=${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/dumped_elf "$<TARGET_FILE:executable_${fixture}_${tag}_${postfix}>"
)
add_test(
	NAME compare_dumped_${fixture}_${tag}_${postfix}
	COMMAND "${CMAKE_COMMAND}" -E compare_files "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/dumped_elf" "$<TARGET_FILE:hello_exe>"
)


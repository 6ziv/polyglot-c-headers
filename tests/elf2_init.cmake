add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello"
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" "$<TARGET_FILE:hello_exe>" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello" ${arguments}
	DEPENDS hello_exe "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_elf.py" make_dir_for_${fixture}_${tag}
)
add_custom_target(make_elf_for_${fixture}_${tag} DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello")
fixture_depends(${fixture}_${tag} make_elf_for_${fixture}_${tag})

add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/dumped_elf2"
	COMMAND "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/hello"
)
add_custom_target(dump_elf_from_script_${fixture}_${tag} DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/dumped_elf2")
add_dependencies(dump_elf_from_script_${fixture}_${tag} make_elf_for_${fixture}_${tag})
setup_subfixture(${fixture} ${fixture}_${tag}_dump1 dump_elf_from_script_${fixture}_${tag})
fixture_depends(${fixture}_${tag}_dump1 dump_elf_from_script_${fixture}_${tag})
require_fixtures(dump_elf_from_script_${fixture}_${tag} ${fixture}_${tag})

add_test(
	NAME validate_elf_${fixture}_${tag}
	COMMAND "${CMAKE_COMMAND}" -E compare_files "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/dumped_elf2" "$<TARGET_FILE:hello_exe>"
)
require_fixtures(validate_elf_${fixture}_${tag} ${fixture}_${tag}_dump1)
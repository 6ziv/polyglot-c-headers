add_dependencies(executable_${fixture}_${tag}_${postfix} make_script_for_${fixture}_${tag})
add_test(
	NAME run_${fixture}_${tag}_${postfix}
	COMMAND "$<TARGET_FILE:executable_${fixture}_${tag}_${postfix}>" 
)

set_tests_properties(run_${fixture}_${tag}_${postfix} PROPERTIES
	PASS_REGULAR_EXPRESSION "Hello from script.*Hello world from main."
)

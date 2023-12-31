add_test(
	NAME run_${fixture}_${tag}_${postfix}
	COMMAND "$<TARGET_FILE:executable_${fixture}_${tag}_${postfix}>" 
)

set_tests_properties(run_${fixture}_${tag}_${postfix} PROPERTIES
	PASS_REGULAR_EXPRESSION "Hello from script.*Hello world from main."
)
require_fixtures(run_${fixture}_${tag}_${postfix} executable_${fixture}_${tag}_${postfix})

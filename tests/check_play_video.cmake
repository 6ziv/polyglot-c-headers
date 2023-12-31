cmake_minimum_required(VERSION 3.19 FATAL_ERROR)

#EXECUTABLE
#BASELINE_TS
#COMPARE_SCRIPT
#DUMP_FILE
#FAKE_PATH
find_program(FFMPEG_BIN ffmpeg)
message(WARNING "${EXECUTABLE}")
message(WARNING "${DUMP_FILE}")
message(WARNING "${FAKE_PATH}")
execute_process(
	COMMAND "${CMAKE_COMMAND}" -E env DUMP_FILE=${DUMP_FILE} ${CMAKE_COMMAND} -E env PATH=${FAKE_PATH} ${EXECUTABLE}
	OUTPUT_VARIABLE ostr
	COMMAND_ERROR_IS_FATAL ANY
)
message(WARNING "${ostr}")
string(FIND "${ostr}" "Hello world from main." main_executed)

if(-1 EQUAL "${main_executed}")
	message(FATAL_ERROR "main function not executed.")
endif()

execute_process(
	COMMAND "${CMAKE_COMMAND}" -DVIDEO1=${DUMP_FILE} -DVIDEO2=${BASELINE_TS} -P ${COMPARE_SCRIPT}
	COMMAND_ECHO STDOUT
	COMMAND_ERROR_IS_FATAL ANY
)

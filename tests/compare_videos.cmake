cmake_minimum_required(VERSION 3.19 FATAL_ERROR)
#VIDEO1
#VIDEO2
find_program(FFMPEG_BIN ffmpeg)
execute_process(COMMAND ${FFMPEG_BIN} "-f" "md5" "-c:v" "copy" "-c:a" "copy" ${VIDEO1} OUTPUT_VARIABLE hash1)
execute_process(COMMAND ${FFMPEG_BIN} "-f" "md5" "-c:v" "copy" "-c:a" "copy" ${VIDEO2} OUTPUT_VARIABLE hash2)
string(COMPARE EQUAL "${hash1}" "${hash2}" hash_eq)
if(NOT ${hash_eq})
	message(SEND_ERROR "Videos not equal")
endif()
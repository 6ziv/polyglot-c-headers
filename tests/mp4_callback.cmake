add_dependencies(executable_${fixture}_${tag}_${postfix} make_mp4_for_${fixture}_${tag})
add_test(
	NAME run_${fixture}_${tag}_${postfix}
	COMMAND "${CMAKE_COMMAND}" -DFAKE_PATH=${CMAKE_CURRENT_BINARY_DIR}/fake_ffplay_dir -DDUMP_FILE=${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/video_dump_${postfix} -DEXECUTABLE=$<TARGET_FILE:executable_${fixture}_${tag}_${postfix}> -DBASELINE_TS=${CMAKE_CURRENT_BINARY_DIR}/video.ts -DCOMPARE_SCRIPT=${CMAKE_CURRENT_SOURCE_DIR}/compare_videos.cmake -P "${CMAKE_CURRENT_SOURCE_DIR}/check_play_video.cmake"
)
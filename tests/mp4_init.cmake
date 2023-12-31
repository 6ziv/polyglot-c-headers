add_custom_command(
	OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/video.mp4"
	COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_mp4.py" "${SOURCE_MP4}" "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/video.mp4" ${arguments}
	DEPENDS "${SOURCE_MP4}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/build_mp4.py" make_dir_for_${fixture}_${tag}
)
add_custom_target(make_mp4_for_${fixture}_${tag} DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/video.mp4")
fixture_depends(${fixture}_${tag} make_mp4_for_${fixture}_${tag})

add_test(
	NAME validate_video_${fixture}_${tag}
	COMMAND "${CMAKE_COMMAND}" -DVIDEO1=${CMAKE_CURRENT_BINARY_DIR}/${fixture}_${tag}/video.mp4 -DVIDEO2=${SOURCE_MP4} -P ${CMAKE_CURRENT_SOURCE_DIR}/compare_videos.cmake
)
require_fixtures(validate_video_${fixture}_${tag} prepare_${fixture}_${tag}_tests)
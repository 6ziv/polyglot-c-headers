cmake_minimum_required(VERSION 3.19 FATAL_ERROR)

set(VIDEO_URL https://raw.githubusercontent.com/chen-qingyu/BadApple/master/BadApple.mp4)
set(VIDEO_SAVEPATH ${CMAKE_CURRENT_SOURCE_DIR}/badapple.mp4)

set(GAME_URL https://down.pc.yyb.qq.com/packing/c8f7975f13c271b55377801ebee54ca7/com.tencent.letsgo_2700200338_installer.exe)
set(GAME_SAVEPATH ${CMAKE_CURRENT_SOURCE_DIR}/ymzx.exe)

if(NOT EXISTS ${VIDEO_SAVEPATH})
  file(DOWNLOAD ${VIDEO_URL} ${VIDEO_SAVEPATH} SHOW_PROGRESS)
  #find_program(FFMPEG_BIN ffmpeg)
  
endif()

if(NOT EXISTS ${GAME_SAVEPATH})
  file(DOWNLOAD ${GAME_URL} ${GAME_SAVEPATH} SHOW_PROGRESS)
  find_program(PYTHON_EXECUTABLE NAMES python python3)
  execute_process(
    COMMAND ${PYTHON_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/patch_gameinstaller.py" "${GAME_SAVEPATH}" "${CMAKE_CURRENT_SOURCE_DIR}/ymzx_tail.patch"
  )
endif()

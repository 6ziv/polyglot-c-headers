cmake_minimum_required(VERSION 3.19 FATAL_ERROR)
#FILE
file(CHMOD "${FILE}" PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ WORLD_READ)
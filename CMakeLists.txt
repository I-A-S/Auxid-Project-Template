cmake_minimum_required(VERSION 3.20)

project(${AUXID_PROJECT_NAME})
enable_testing()

if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
    set(${AUXID_PROJECT_NAME}_IS_TOP_LEVEL ON)
else()
    set(${AUXID_PROJECT_NAME}_IS_TOP_LEVEL OFF)
endif()

set(${AUXID_PROJECT_NAME}_ROOT "${CMAKE_CURRENT_LIST_DIR}" CACHE INTERNAL "")

if(TARGET libauxid)
    message(STATUS "${AUXID_PROJECT_NAME}: Using external LibAuxid provided by parent project")
else()
    message(STATUS "${AUXID_PROJECT_NAME}: Building standalone, using local LibAuxid submodule")
    if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/libauxid/CMakeLists.txt")
        message(FATAL_ERROR "LibAuxid submodule missing! Run: git submodule update --init --recursive")
    endif()
    add_subdirectory(libauxid)
endif()

auxid_setup_project()

option(${AUXID_PROJECT_NAME}_BUILD_TESTS "Build unit tests" ${${AUXID_PROJECT_NAME}_IS_TOP_LEVEL})

include(cmake/find_deps.cmake)

add_subdirectory(src)

if(${AUXID_PROJECT_NAME}_BUILD_TESTS)
    add_subdirectory(tests)
endif()

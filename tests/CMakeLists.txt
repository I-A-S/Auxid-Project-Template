set(SRC_FILES
    "cpp/main.cpp"

    "cpp/sample_test.cpp"
)

add_executable(TestSuite ${SRC_FILES})
target_link_libraries(TestSuite PRIVATE libauxid ${AUXID_PROJECT_NAME})
set_target_properties(TestSuite PROPERTIES CXX_SCAN_FOR_MODULES ON)
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" AND WIN32)
    target_link_libraries(TestSuite PRIVATE stdc++exp)
endif()
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_link_options(TestSuite PRIVATE "LINKER:--allow-multiple-definition")
endif()
add_test(NAME TestSuite COMMAND TestSuite)

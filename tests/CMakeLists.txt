set(SRC_FILES
    "cpp/main.cpp"

    "cpp/sample_test.cpp"
)

add_executable(TestSuite ${SRC_FILES})

target_link_libraries(TestSuite PRIVATE libauxid)

add_test(NAME TestSuite COMMAND TestSuite)

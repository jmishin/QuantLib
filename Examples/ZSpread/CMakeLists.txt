add_executable(ZSpread ZSpread.cpp)
target_link_libraries(ZSpread ql_library ${QL_THREAD_LIBRARIES})
if (QL_INSTALL_EXAMPLES)
    install(TARGETS ZSpread RUNTIME DESTINATION ${QL_INSTALL_EXAMPLESDIR})
endif()


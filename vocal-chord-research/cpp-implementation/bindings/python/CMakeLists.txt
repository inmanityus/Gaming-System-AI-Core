# Python Bindings CMakeLists

find_package(pybind11 REQUIRED)

pybind11_add_module(vocal_synthesis_py
    vocal_synthesis_py.cpp
)

target_link_libraries(vocal_synthesis_py
    PRIVATE
        vocal_synthesis
)

target_include_directories(vocal_synthesis_py
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../../include
)

# Install to Python site-packages
install(TARGETS vocal_synthesis_py
    LIBRARY DESTINATION ${Python_SITEARCH}
)


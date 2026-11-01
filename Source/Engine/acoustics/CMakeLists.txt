cmake_minimum_required(VERSION 3.16)
project(AliceA3DPrototype VERSION 0.1.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_library(alice_acoustics STATIC src/acoustics.cpp src/bsp.cpp)
target_include_directories(alice_acoustics PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
if(MSVC)
  target_compile_options(alice_acoustics PRIVATE /W4)
else()
  target_compile_options(alice_acoustics PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_executable(alice_a3d_demo src/demo.cpp)
target_link_libraries(alice_a3d_demo PRIVATE alice_acoustics)
add_executable(alice_bsp_inspect src/inspect_bsp.cpp)
target_link_libraries(alice_bsp_inspect PRIVATE alice_acoustics)
enable_testing()

# Generated fixtures are synthetic. No game assets are required to run CTest.
find_package(Python3 REQUIRED COMPONENTS Interpreter)
add_custom_command(
  OUTPUT "${CMAKE_CURRENT_SOURCE_DIR}/samples/synthetic_alice_fakk42.bsp"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/build_test_fakk42.py"
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/tools/build_test_fakk42.py"
  VERBATIM)
add_custom_command(
  OUTPUT "${CMAKE_CURRENT_SOURCE_DIR}/samples/synthetic_ibsp46.bsp"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/build_test_bsp.py"
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/tools/build_test_bsp.py"
  VERBATIM)
add_custom_target(generate_synthetic_geometry ALL DEPENDS
  "${CMAKE_CURRENT_SOURCE_DIR}/samples/synthetic_alice_fakk42.bsp"
  "${CMAKE_CURRENT_SOURCE_DIR}/samples/synthetic_ibsp46.bsp")

add_executable(alice_acoustics_tests tests/tests.cpp)
target_link_libraries(alice_acoustics_tests PRIVATE alice_acoustics)
add_test(NAME acoustics_tests COMMAND alice_acoustics_tests)

add_test(NAME fakk42_import COMMAND alice_bsp_inspect ${CMAKE_CURRENT_SOURCE_DIR}/samples/synthetic_alice_fakk42.bsp)
set_tests_properties(fakk42_import PROPERTIES PASS_REGULAR_EXPRESSION "BSP format=FAKK version=42 faces=2 patches=1 triangles=33")
add_test(NAME ibsp46_import COMMAND alice_bsp_inspect ${CMAKE_CURRENT_SOURCE_DIR}/samples/synthetic_ibsp46.bsp)
set_tests_properties(ibsp46_import PROPERTIES PASS_REGULAR_EXPRESSION "BSP format=IBSP version=46 faces=2 patches=1 triangles=33")
add_executable(alice_obj_trace src/obj_trace.cpp)
target_link_libraries(alice_obj_trace PRIVATE alice_acoustics)
add_test(NAME obj_geometry_bridge COMMAND alice_obj_trace ${CMAKE_CURRENT_SOURCE_DIR}/samples/synthetic_wall.geom 2 0 0 0 0 0)
set_tests_properties(obj_geometry_bridge PROPERTIES PASS_REGULAR_EXPRESSION "occluded")

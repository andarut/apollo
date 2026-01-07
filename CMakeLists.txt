cmake_minimum_required(VERSION 3.23)
include(CMakePrintHelpers)
project(apollo)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

message(CMAKE_C_COMPILER="${CMAKE_C_COMPILER}")
message(CMAKE_CXX_COMPILER="${CMAKE_CXX_COMPILER}")

find_package(nlohmann_json REQUIRED)
find_package(Boost REQUIRED)

add_executable(apollo
  src/main.cpp
)
target_compile_features(apollo PRIVATE cxx_std_20)

target_include_directories(apollo PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(apollo PRIVATE
  nlohmann_json::nlohmann_json
  boost::boost
)


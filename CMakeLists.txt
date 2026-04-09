cmake_minimum_required(VERSION 3.20)
project(list_symbols VERSION 0.1.0)

# Find Clang
find_package(Clang CONFIG REQUIRED)

add_executable(list_symbols)
target_sources(
    list_symbols
    PRIVATE
    src/main.c
)
target_include_directories(
    list_symbols
    PRIVATE
    ${CLANG_INCLUDE_DIRS}
)
target_link_libraries(
    list_symbols
    PRIVATE
    libclang
)

cmake_minimum_required(VERSION 3.10)
project(skin_post_process)

set(CMAKE_CXX_STANDARD 14)

find_package(OpenCV REQUIRED)

# 헤더 경로 (당신 환경 정확히 맞춤)
include_directories(/usr/include/hailo/tappas)

include_directories(${OpenCV_INCLUDE_DIRS})

# 라이브러리 (libhailo_common.so는 없어도 됨 → libhailort.so에 다 들어있음)
add_library(skin_post SHARED skin_regression.cpp)

target_link_libraries(skin_post
    /usr/lib/libhailort.so
    # libhailo_common.so는 필요 없음 (최신 HailoRT에서 통합됨)
    ${OpenCV_LIBS}
)

set_target_properties(skin_post PROPERTIES PREFIX "lib" SUFFIX ".so")
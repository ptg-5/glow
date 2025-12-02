/**
 * simple_cls.cpp
 * ResNet50 결과(Softmax)에서 가장 높은 확률의 인덱스를 찾아 Classification 객체로 등록
 */
#include "hailo_objects.hpp"
#include "hailo_common.hpp"

extern "C" {

// 함수명: filter (파이썬 function-name=filter 와 일치해야 함)
void filter(HailoROIPtr roi, void *params_void_ptr) {
    
    // 1. 텐서 가져오기 (이름 몰라도 첫 번째 텐서 가져옴)
    auto tensors = roi->get_tensors();
    if (tensors.empty()) return;
    auto tensor = tensors[0];

    // 2. 데이터 포인터 및 크기
    // (ResNet50은 보통 uint8(Quantized) 또는 float32로 출력됨)
    // 여기서는 안전하게 데이터 크기만큼 돌면서 최댓값을 찾습니다.
    uint8_t *data = tensor->data();
    int size = tensor->size(); // 클래스 개수 (예: 1000개)
    
    // 3. Argmax (최댓값 인덱스 찾기)
    int max_idx = 0;
    float max_val = -1.0f;

    // 데이터가 uint8인지 float인지 확인 (헤일로 텐서는 보통 바이트 단위)
    // 편의상 uint8로 가정하고 비교 (확률 비교에는 문제 없음)
    for (int i = 0; i < size; i++) {
        float val = (float)data[i];
        if (val > max_val) {
            max_val = val;
            max_idx = i;
        }
    }

    // 4. 결과 등록 (라벨을 숫자로 문자열화: "0", "1", ...)
    std::string label = std::to_string(max_idx);
    // confidence는 0.0 ~ 1.0 사이로 정규화 (uint8인 경우 255로 나눔)
    float confidence = max_val / 255.0f; 

    // Hailo Classification 객체 생성 후 ROI에 추가
    auto classification = std::make_shared<HailoClassification>("skin_type", max_idx, label, confidence);
    roi->add_object(classification);
}

}
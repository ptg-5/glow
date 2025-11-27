// skin_regression.cpp
#include <hailo/hailort.h>
#include "hailo_objects.hpp"
#include "hailo_common.hpp"
#include <iostream>
#include <map>
#include "hailomat.hpp"
#include <cmath> // std::exp, std::max 등을 위해 필요
#include <numeric> // std::accumulate 등을 위해 필요

// 로짓(logits) 벡터를 입력받아 확률 벡터로 변환하는 Softmax 함수
std::vector<float> softmax(const std::vector<float>& logits) {
    if (logits.empty()) {
        return {};
    }
    
    // 1. 오버플로우 방지를 위한 최대값 찾기 (안정적인 Softmax)
    float max_logit = -std::numeric_limits<float>::infinity();
    for (float logit : logits) {
        if (logit > max_logit) {
            max_logit = logit;
        }
    }

    // 2. 지수(Exponential) 계산 및 합계
    std::vector<float> exp_values;
    float sum_exp = 0.0f;

    for (float logit : logits) {
        // max_logit을 빼서 값의 범위를 줄여 오버플로우를 방지합니다.
        float exp_val = std::exp(logit - max_logit); 
        exp_values.push_back(exp_val);
        sum_exp += exp_val;
    }

    // 3. 정규화 (Normalization)
    std::vector<float> probabilities;
    for (float exp_val : exp_values) {
        probabilities.push_back(exp_val / sum_exp);
    }

    return probabilities;
}
// ========== FILTER 함수 ==========
extern "C" hailo_status resnet_cls(HailoROIPtr roi)
{
    try
    {
        if (!roi) return HAILO_INVALID_ARGUMENT;
        // 텐서 처리
        HailoTensorPtr tensor;
        try {

            tensor = roi->get_tensor("resnet50_downsample_bias_removed/dense_conv54");


        } catch (...) {
            printf("(텐서 없음)\n");
            fflush(stdout);
            return HAILO_SUCCESS;
        }
        
        if (!tensor || !tensor->data()) {
            printf("(데이터 없음)\n");
            fflush(stdout);
            return HAILO_SUCCESS;
        }
        
        // 결과 계산
        uint8_t* data = tensor->data();
        size_t tensor_size = tensor->size();
        auto q = tensor->quant_info();

        // 디버깅 출력을 유지합니다.
        printf("--- Tensor Info ---\n");
        printf("Tensor Name: resnet50_downsample_bias_removed/dense_conv54\n");
        printf("Scale (qp_scale): %.6f\n", q.qp_scale);
        printf("Zero Point (qp_zp): %d\n", (int)q.qp_zp); 
        printf("Tensor Size (elements): %zu\n", tensor_size);
        
        printf("======== data parsing (uint8_t) ==========\n");
        const size_t MAX_PRINT_ELEMENTS = 30;
        size_t print_limit = (tensor_size > MAX_PRINT_ELEMENTS) ? MAX_PRINT_ELEMENTS : tensor_size;

        for (size_t i = 0; i < print_limit; ++i){
            printf(">>>>%u<<< ", data[i]);
        }
        if (tensor_size > MAX_PRINT_ELEMENTS) {
            printf("... (총 %zu개 중 %zu개만 출력됨)", tensor_size, print_limit);
        }
        printf("\n======== data parsing        end ==========\n");

        
        // ---------- 실제 확률 변환 부분 시작 ----------
        // 텐서의 출력이 3개라고 가정하고, 레이블을 3개로 설정합니다.
        std::vector<std::string> labels = {"dry", "normal", "oily"};
        const size_t MAX_OUTPUTS = labels.size(); // 레이블 수에 맞춰 출력 개수 설정

        if (tensor_size < MAX_OUTPUTS) {
            printf("(텐서 크기가 레이블 수보다 작음)\n");
            return HAILO_SUCCESS;
        }

        // 1. 역양자화 (Dequantization) - 로짓(Logits) 획득
        std::vector<float> logits;
        size_t max_el_index = 0; // 초기값 0
        float max_logit_value = -std::numeric_limits<float>::infinity(); // 최대 로짓 값 추적
        
        printf("======== Dequantized Logits ==========\n");
        for (size_t i = 0; i < MAX_OUTPUTS; i++) {
            // 역양자화 공식: R = (D - Z) * S
            float logit = (data[i] - q.qp_zp) * q.qp_scale;
            
            // 🚨 수정된 부분: 로그잇을 먼저 계산합니다.
            logits.push_back(logit); 

            // 최대값 인덱스 추적 (안전한 로직)
            if (logit > max_logit_value) {
                max_logit_value = logit;
                max_el_index = i;
            }
            
            printf("L%zu: %.2f ", i, logit);
        }
        printf("\n======== Logits end ==========\n");

        // 2. Softmax 적용 - 확률(Probabilities) 획득
        std::vector<float> probabilities = softmax(logits);
        int class_id = static_cast<int>(max_el_index);
        // 3. 결과 문자열 생성
        std::string result =  "";
        float sum_check = 0.0f; // 합계 확인용
        
        printf("======== Softmax Probabilities ==========\n");
        for (size_t i = 0; i < MAX_OUTPUTS; i++) {
            // 확률을 100분율로 변환합니다.
            float val_percent = probabilities[i] * 100.0f;
            sum_check += val_percent;

            if (i > 0) result += ",";
            // 텍스트 레이블과 결과를 포맷합니다.
            result += labels[i] + ":" + std::to_string((int)std::round(val_percent)) + "%";
            printf("%s: %d%% ", labels[i].c_str(), (int)std::round(val_percent));
        }
        printf("\n(Total Sum: %.1f%%)\n", sum_check);
        printf("======== Probabilities end ==========\n");
        
        // ---------- 실제 확률 변환 부분 끝 ----------
        
        printf("→ %s\n", result.c_str());
        fflush(stdout);

        
        // // ---------- 수정된 부분 시작 ----------
        // // 텐서의 출력이 3개라고 가정하고, 레이블을 3개로 설정합니다.
        // // 분류하려는 3가지 텍스트 레이블로 아래 값을 변경하세요.
        // std::vector<std::string> labels = {"dry", "normal", "oily"};
        
        // // 텐서 사이즈가 3개라고 가정하고, 반복 횟수를 3으로 제한합니다.
        // const int MAX_OUTPUTS = 3; 
        // std::string result =  part + ":";
        
        // for (int i = 0; i < MAX_OUTPUTS && i < tensor->size(); i++) {
        //     float val = (data[i] - q.qp_zp) * q.qp_scale * 100.0f;
        //     val = std::max(0.0f, std::min(100.0f, val));
            
        //     if (i > 0) result += ",";
        //     // 텍스트 레이블과 결과를 포맷합니다.
        //     result += labels[i] + ":" + std::to_string((int)val) + "%";
        // }
        // // ---------- 수정된 부분 끝 ----------
        
        // printf("→ %s\n", result.c_str());
        // fflush(stdout);
        
        // Classification 추가
        auto cls = std::make_shared<HailoClassification>("skin",class_id, result, 1.0f);
        roi->add_object(cls);
        
        return HAILO_SUCCESS;
    }
    catch (const std::exception& e)
    {
        printf("[EXCEPTION] %s\n", e.what());
        fflush(stdout);
        return HAILO_SUCCESS;
    }
}
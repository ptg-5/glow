#include "skin_util.hpp"
#include <cmath> // std::exp, std::max 등을 위해 필요
#include <numeric> // std::accumulate 등을 위해 필요
#include <limits>

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
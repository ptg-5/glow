// skin_regression.cpp
#include <hailo/hailort.h>
#include "hailo_objects.hpp"
#include "hailo_common.hpp"
#include <iostream>
#include <map>
#include "hailomat.hpp"

// ========== FILTER 함수 ==========
extern "C" hailo_status skin_regression(HailoROIPtr roi)
{
    try
    {
        if (!roi) return HAILO_INVALID_ARGUMENT;
        HailoBBox real_bbox = roi->get_bbox();
        std::string label = roi->get_stream_id();

        printf("[label:%s][진짜 BBox] x=%.3f, y=%.3f, w=%.3f, h=%.3f\n",
                label.c_str(),
               real_bbox.xmin(), real_bbox.ymin(),
               real_bbox.width(), real_bbox.height());
        // stream_id에서 레이블 가져오기 (create_crops에서 설정한 것)
        std::string part = label;

        // roi->get_stream_id();
        // printf("[get_stream_id] %s#\n", part.c_str()); 
        // stream_id가 비어있으면 detection에서 가져오기
        // if (part.empty()) {
        int class_id = 0;
            try {
                // auto dets = roi->get_objects_typed(HAILO_DETECTION);
                auto dets = hailo_common::get_hailo_detections(roi);
                printf("[detections.size()] %zu\n",dets.size());
                if (!dets.empty()) {
                    std::string s = "";
                    for(auto det : dets){
                        s +=  "(" + det->get_label() + ","  + std::to_string(det->get_confidence()) + "," + std::to_string(det->get_class_id()) + ")";
                        if (label == det->get_label() ){
                            class_id = det->get_class_id();
                        }
                    }
                    printf("detections str: %s\n",s.c_str());
                    auto det = std::dynamic_pointer_cast<HailoDetection>(dets[0]);
                    if (det) {
                        // part += det->get_label();
                    }
                }
            } catch (...) {
                part = "unknown";
            }
        // }
        
        printf("[SKIN] %s ", part.c_str());
        fflush(stdout);
        
        // 텐서 처리
        HailoTensorPtr tensor;
        try {

            tensor = roi->get_tensor("mobile_net_han_kernel_shape/dense_conv42");


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
        auto q = tensor->quant_info();

        
        std::vector<std::string> labels = {"Dry", "Oil", "Acne", "Wrinkle", "Pigment"};
        std::string result =  part + ":";
        
        for (int i = 0; i < 5 && i < tensor->size(); i++) {
            float val = (data[i] - q.qp_zp) * q.qp_scale * 100.0f;
            val = std::max(0.0f, std::min(100.0f, val));
            
            if (i > 0) result += ",";
            result += labels[i] + ":" + std::to_string((int)val) + "%";
        }
        
        printf("→ %s\n", result.c_str());
        fflush(stdout);
        
        // Classification 추가
        // auto result_det = std::make_shared<HailoDetection>(
        //     real_bbox,
        //     class_id,
        //     "skin_result", 
        //     1.0f
        // );
        auto cls = std::make_shared<HailoClassification>("skin",class_id, result, 1.0f);
        // result_det->add_object(cls);
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

extern "C" std::vector<HailoROIPtr> all_detections(std::shared_ptr<HailoMat> image, HailoROIPtr roi)
{
    std::vector<HailoROIPtr> crop_rois;
    std::vector<HailoDetectionPtr> detections_ptrs = hailo_common::get_hailo_detections(roi);

    for (HailoDetectionPtr &detection : detections_ptrs)
    {
        std::string label = detection->get_label();
        
        if (label.empty()) {
            printf("skin_regression.cpp > all_detections > skipping detection with empty label\n");
            continue;
        }

        // 1. HailoDetectionPtr를 HailoROIPtr로 업캐스팅하여 벡터에 추가 (그림 OK 로직 유지)
        // 이 과정에서 메타데이터 연결이 유지된다고 가정합니다.
        crop_rois.emplace_back(detection);

        // 2. 💡 핵심: 벡터에 새로 추가된 객체를 다시 HailoROI 포인터로 가져옵니다.
        // 이 객체는 HailoDetection이므로 HailoROI의 모든 멤버를 가지고 있습니다.
        // std::dynamic_pointer_cast를 사용하여 HailoROIPtr로 안전하게 가져옵니다.
        HailoROIPtr current_roi = crop_rois.back(); 

        // 3. HailoROI 포인터에 라벨(stream_id)을 강제로 설정합니다. (라벨 NG 문제 해결)
        // 이 작업은 원본 detection 객체의 m_stream_id 멤버를 직접 수정하는 효과를 냅니다.
        current_roi->set_stream_id(label); 

        printf("skin_regression.cpp > all_detections > detection: %s, stream_id set: %s<<\n",
               label.c_str(), current_roi->get_stream_id().c_str());
    }
    return crop_rois;
}

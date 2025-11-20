// skin_regression.cpp
#include <hailo/hailort.h>
#include "hailo_objects.hpp"
#include "hailo_common.hpp"
#include <iostream>
#include <map>
#include "hailomat.hpp"
// #include <opencv2/opencv.hpp>
// ========== CROPPER 함수 (안전한 버전) ==========
extern "C" void create_crops(HailoROIPtr roi)
{
    printf("\n[CREATE_CROPS] 시작\n");
    fflush(stdout);
    
    if (!roi) {
        printf("[ERROR] ROI is null\n");
        fflush(stdout);
        return;
    }
    
    try {
        // ★ 핵심: get_objects() 대신 get_objects_typed() 사용
        std::vector<HailoObjectPtr> detection_objects;
        
        try {
            detection_objects = roi->get_objects_typed(HAILO_DETECTION);
        } catch (const std::exception& e) {
            printf("[ERROR] get_objects_typed 실패: %s\n", e.what());
            fflush(stdout);
            return;
        } catch (...) {
            printf("[ERROR] get_objects_typed 알 수 없는 예외\n");
            fflush(stdout);
            return;
        }
        
        printf("[CREATE_CROPS] %zu개 detection 발견\n", detection_objects.size());
        fflush(stdout);
        
        if (detection_objects.empty()) {
            printf("[CREATE_CROPS] detection 없음\n");
            fflush(stdout);
            return;
        }
        
        // 각 detection을 크롭 ROI로 변환
        for (size_t i = 0; i < detection_objects.size(); i++) {
            printf("[CREATE_CROPS] Detection %zu 처리 중...\n", i);
            fflush(stdout);
            
            // Detection으로 캐스팅
            auto detection = std::dynamic_pointer_cast<HailoDetection>(detection_objects[i]);
            
            if (!detection) {
                printf("[WARNING] Detection %zu 캐스팅 실패\n", i);
                fflush(stdout);
                continue;
            }
            
            // Detection 정보 가져오기
            try {
                HailoBBox bbox = detection->get_bbox();  // ← 선언과 동시에 초기화!
                std::string label = detection->get_label();
                
                printf("  [%zu] %s: [%.3f, %.3f, %.3f, %.3f]\n",
                       i, label.c_str(),
                       bbox.xmin(), bbox.ymin(), 
                       bbox.width(), bbox.height());
                fflush(stdout);
                
                // 크롭 ROI 생성
                auto crop_roi = std::make_shared<HailoROI>(bbox, label);
                
                // ★ 중요: 원본 detection을 crop_roi에 추가
                crop_roi->add_object(detection_objects[i]);
                
                // ★ 중요: crop_roi를 메인 ROI에 추가
                roi->add_object(std::dynamic_pointer_cast<HailoObject>(crop_roi));
                
                printf("  [%zu] 크롭 ROI 추가 완료\n", i);
                fflush(stdout);
                
            } catch (const std::exception& e) {
                printf("[ERROR] Detection %zu 처리 실패: %s\n", i, e.what());
                fflush(stdout);
            } catch (...) {
                printf("[ERROR] Detection %zu 알 수 없는 예외\n", i);
                fflush(stdout);
            }
        }
        
        printf("[CREATE_CROPS] 완료 (총 %zu개)\n\n", detection_objects.size());
        fflush(stdout);
    }
    catch (const std::exception& e) {
        printf("[ERROR] create_crops 예외: %s\n", e.what());
        fflush(stdout);
    }
    catch (...) {
        printf("[ERROR] create_crops 알 수 없는 예외\n");
        fflush(stdout);
    }
}

// ========== FILTER 함수 ==========
extern "C" hailo_status skin_regression(HailoROIPtr roi)
{
    try
    {
        if (!roi) return HAILO_INVALID_ARGUMENT;
        HailoBBox real_bbox = roi->get_bbox();

        printf("[진짜 BBox] x=%.3f, y=%.3f, w=%.3f, h=%.3f\n",
               real_bbox.xmin(), real_bbox.ymin(),
               real_bbox.width(), real_bbox.height());
        // stream_id에서 레이블 가져오기 (create_crops에서 설정한 것)
        std::string part = "";
        // roi->get_stream_id();
        // printf("[get_stream_id] %s#\n", part.c_str()); 
        // stream_id가 비어있으면 detection에서 가져오기
        // if (part.empty()) {
            try {
                // auto dets = roi->get_objects_typed(HAILO_DETECTION);
                auto dets = hailo_common::get_hailo_detections(roi);
                printf("[detections.size()] %zu\n",dets.size());
                if (!dets.empty()) {
                    std::string s = "";
                    for(auto det : dets){
                        s +=  det->get_label() + ",";
                    }
                    printf("detections str: %s\n",s);
                    auto det = std::dynamic_pointer_cast<HailoDetection>(dets[0]);
                    if (det) {
                        part += det->get_label();
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
        std::string result = "";
        
        for (int i = 0; i < 5 && i < tensor->size(); i++) {
            float val = (data[i] - q.qp_zp) * q.qp_scale * 100.0f;
            val = std::max(0.0f, std::min(100.0f, val));
            
            if (i > 0) result += ",";
            result += labels[i] + ":" + std::to_string((int)val) + "%";
        }
        
        printf("→ %s\n", result.c_str());
        fflush(stdout);
        
        // Classification 추가
        auto cls = std::make_shared<HailoClassification>("skin", result, 1.0f);
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
    // Get all detections.
    std::vector<HailoDetectionPtr> detections_ptrs = hailo_common::get_hailo_detections(roi);
    printf("skin_regression.cpp > all_detections > stream id :%s<<\n",roi->get_stream_id().c_str());
    for (HailoDetectionPtr &detection : detections_ptrs)
    {
        crop_rois.emplace_back(detection);
        printf("skin_regression.cpp > all_detections > detection: %s<<\n",detection->get_label().c_str());
    }
    return crop_rois;
}
// std::vector<HailoROIPtr> all_detections_copy(std::shared_ptr<HailoMat> image, HailoROIPtr roi)
// {
//     /**
//      * For performance reasons, the cropper is limited to processing only a single detection per frame.
//      * Other detections are ignored but will have an opportunity to be processed in subsequent frames.
//      * However, if detections are always processed in the same order for every frame, 
//      * and processing is restricted to the first detection in the list, 
//      * the same detection may consistently be processed while others are perpetually ignored.
//      * To address this, an aging algorithm based on track IDs is implemented. 
//      * A map of track IDs to their "age" (i.e., the number of frames since they were last processed) is maintained.
//      * This ensures fairness by prioritizing detections with the oldest track IDs for processing over time.
//      */
//     static std::unordered_map<int, int> track_ages; // Map to store track ID and its age
//     std::vector<HailoROIPtr> crop_rois;

//     // Get all detections.
//     std::vector<HailoDetectionPtr> detections_ptrs = hailo_common::get_hailo_detections(roi);
//     printf("all_detections.detections.size : %zu",detections_ptrs.size());
//     for(auto d_p:detections_ptrs){
//         printf("d_p->get_label: %s\n",d_p->get_label());
//     }

//     // Increment the age of all tracks
//     for (auto &entry : track_ages) {
//         entry.second++;
//     }

//     // Sort detections by track age (oldest first)
//     std::sort(detections_ptrs.begin(), detections_ptrs.end(), [&](const HailoDetectionPtr &a, const HailoDetectionPtr &b) {
//         auto tracking_obj_a = get_tracking_id(a);
//         auto tracking_obj_b = get_tracking_id(b);

//         if (tracking_obj_a && tracking_obj_b) {
//             int track_id_a = tracking_obj_a->get_id();
//             int track_id_b = tracking_obj_b->get_id();
//             return track_ages[track_id_a] > track_ages[track_id_b];
//         }
//         return false; // If no tracking ID, do not prioritize
//     });

//     for (HailoDetectionPtr &detection : detections_ptrs)
//     {
//         if (!box_contains_nan(detection->get_bbox()))
//         {
//             crop_rois.emplace_back(detection);
//             printf("all_detections.detection.get_label() : %s",detection->get_label());

//             // Reset the age of the processed track
//             auto tracking_obj = get_tracking_id(detection);
//             if (tracking_obj) {
//                 int track_id = tracking_obj->get_id();
//                 track_ages[track_id] = 0;
//             }

//             // Limit to one detection
//             break;
//         }
//     }

//     // Remove old tracks that are no longer detected
//     for (auto it = track_ages.begin(); it != track_ages.end();) {
//         if (std::none_of(detections_ptrs.begin(), detections_ptrs.end(), [&](const HailoDetectionPtr &detection) {
//                 auto tracking_obj = get_tracking_id(detection);
//                 return tracking_obj && tracking_obj->get_id() == it->first;
//             })) {
//             it = track_ages.erase(it);
//         } else {
//             ++it;
//         }
//     }

//     return crop_rois;
// }

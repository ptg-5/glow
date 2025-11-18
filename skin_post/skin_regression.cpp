// skin_regression.cpp
#include <hailo/hailort.h>
#include "hailo_objects.hpp"
#include "hailo_common.hpp"
#include <iostream>

// extern "C" void create_crops(HailoROIPtr roi)
// {
//     if (!roi)
//     {
//         return;
//     }

//     // 여기서부터가 핵심!
//     // roi를 복사해서 새로운 객체로 만든다 → mutex 분리 → deadlock 방지
//     HailoROIPtr roi_copy = std::make_shared<HailoROI>(*roi);

//     // 이제 안전하게 사용 가능
//     HailoBBox bbox = roi_copy->get_bbox();
//     std::vector<HailoObjectPtr> objects = roi_copy->get_objects();

//     printf("[create_crops] 복사본 사용 → 안전함 (objects: %zu)\n", objects.size());

//     int crop_count = 0;

//     for (const auto &obj : objects)
//     {
//         auto detection = std::dynamic_pointer_cast<HailoDetection>(obj);
//         if (!detection)
//             continue;

//         HailoBBox box = detection->get_bbox();
//         std::string label = detection->get_label();

//         printf("  → Detection: %s\n", label.c_str());

//         // 원본 roi에 crop 추가 (여기선 원본 roi 써도 됨)
//         auto crop_roi = std::make_shared<HailoROI>(box);
//         crop_roi->add_unscaled_object(detection);
//         crop_roi->set_stream_id(label);

//         roi->add_object(crop_roi); // 여기만 원본 roi 사용
//         crop_count++;
//     }

//     // fallback
//     if (crop_count == 0)
//     {
//         auto crop_roi = std::make_shared<HailoROI>(bbox);
//         crop_roi->set_stream_id("face");
//         roi->add_object(crop_roi);
//     }

//     printf("[create_crops] 완료 → %d개 crop 생성\n", crop_count ? crop_count : 1);
// }
// ========== 피부 분석 함수 ==========
extern "C" hailo_status skin_regression(HailoROIPtr roi)
{
    try
    {
        printf("\n========== SKIN REGRESSION START ==========\n");

        if (!roi) {
            printf("[ERROR] ROI is null!\n");
            return HAILO_INVALID_ARGUMENT;
        }

        // 1. 원본 detection이 있는지 확인 (공식 cropper가 넣어준 것)
        auto detections = hailo_common::get_hailo_detections(roi);
        HailoDetectionPtr original_det = nullptr;
        std::string part_name = "face";  // 기본값
        HailoBBox real_bbox = roi->get_bbox();  // fallback: 전체 ROI bbox

        if (!detections.empty()) {
            original_det = detections[0];
            part_name = original_det->get_label();
            real_bbox = original_det->get_bbox();  // 진짜 원본 좌표!
            printf("[INFO] Detection 있음 → 부위: %s\n", part_name.c_str());
        } else {
            printf("[INFO] Detection 없음 → 전체 얼굴(face)로 처리\n");
            // 전체 얼굴 ROI의 bbox를 사용 (이미 roi->get_bbox()가 원본 좌표)
            real_bbox = roi->get_bbox();
        }

        printf("[진짜 좌표] %s → [%.3f, %.3f, %.3f, %.3f]\n",
               part_name.c_str(),
               real_bbox.xmin(), real_bbox.ymin(),
               real_bbox.width(), real_bbox.height());

        // 2. 텐서 가져오기
        HailoTensorPtr tensor = roi->get_tensor("mobile_net_han_kernel_shape/dense_conv42");
        if (!tensor || !tensor->data()) {
            printf("[WARN] 텐서 없음 → 스킵\n");
            return HAILO_SUCCESS;
        }

        uint8_t* data = tensor->data();
        auto q = tensor->quant_info();

        std::vector<std::string> attrs = {"Dryness", "Oiliness", "Acne", "Wrinkles", "Pigmentation"};
        std::string result = "";

        for (int i = 0; i < 5 && i < tensor->size(); i++) {
            float val = (data[i] - q.qp_zp) * q.qp_scale * 100.0f;
            val = std::max(0.0f, std::min(100.0f, val));
            if (i > 0) result += ", ";
            result += attrs[i] + ": " + std::to_string((int)val) + "%";
        }

        printf("[결과] %s → %s\n", part_name.c_str(), result.c_str());

        // 3. 결과 박스 생성 (항상 생성!)
        auto result_det = std::make_shared<HailoDetection>(
            real_bbox,
            0,
            part_name,
            original_det ? original_det->get_confidence() : 1.0f
        );

        auto cls = std::make_shared<HailoClassification>("skin", result, 1.0f);
        result_det->add_object(cls);
        roi->add_object(result_det);

        printf("[완료] %s 결과 화면에 표시됨\n", part_name.c_str());
        printf("========== SKIN REGRESSION END ==========\n\n");

        return HAILO_SUCCESS;
    }
    catch (const std::exception& e)
    {
        printf("[EXCEPTION] %s\n", e.what());
        return HAILO_SUCCESS;
    }
    catch (...)
    {
        printf("[UNKNOWN EXCEPTION]\n");
        return HAILO_SUCCESS;
    }
}
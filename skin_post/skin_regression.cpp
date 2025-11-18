// skin_regression.cpp
#include <hailo/hailort.h>
#include "hailo_objects.hpp"
#include "hailo_common.hpp"
#include <iostream>

extern "C" void create_crops(HailoROIPtr roi)
{
    if (!roi)
    {
        return;
    }

    // 여기서부터가 핵심!
    // roi를 복사해서 새로운 객체로 만든다 → mutex 분리 → deadlock 방지
    HailoROIPtr roi_copy = std::make_shared<HailoROI>(*roi);

    // 이제 안전하게 사용 가능
    HailoBBox bbox = roi_copy->get_bbox();
    std::vector<HailoObjectPtr> objects = roi_copy->get_objects();

    printf("[create_crops] 복사본 사용 → 안전함 (objects: %zu)\n", objects.size());

    int crop_count = 0;

    for (const auto &obj : objects)
    {
        auto detection = std::dynamic_pointer_cast<HailoDetection>(obj);
        if (!detection)
            continue;

        HailoBBox box = detection->get_bbox();
        std::string label = detection->get_label();

        printf("  → Detection: %s\n", label.c_str());

        // 원본 roi에 crop 추가 (여기선 원본 roi 써도 됨)
        auto crop_roi = std::make_shared<HailoROI>(box);
        crop_roi->add_unscaled_object(detection);
        crop_roi->set_stream_id(label);

        roi->add_object(crop_roi); // 여기만 원본 roi 사용
        crop_count++;
    }

    // fallback
    if (crop_count == 0)
    {
        auto crop_roi = std::make_shared<HailoROI>(bbox);
        crop_roi->set_stream_id("face");
        roi->add_object(crop_roi);
    }

    printf("[create_crops] 완료 → %d개 crop 생성\n", crop_count ? crop_count : 1);
}
// ========== 피부 분석 함수 ==========
extern "C" hailo_status skin_regression(HailoROIPtr roi)
{
    try
    {
        printf("\n========== SKIN REGRESSION START ==========\n");

        if (!roi)
        {
            printf("[ERROR] ROI is null!\n");
            return HAILO_INVALID_ARGUMENT;
        }
        // 1. 현재 ROI가 어떤 부위인지 확인
        std::vector<HailoDetectionPtr> detections = hailo_common::get_hailo_detections(roi);
        
        std::string part_name = "";
        int part_index = -1;

        printf("[DEBUG] len of detections %zu\n",detections.size());
        if (!detections.empty()) {
            for(int i = 0 ; i < detections.size() ; ++i){
                auto det = detections[i];  // crop된 ROI는 detection 하나만 있음
                part_name += det->get_label() ;
                break;
            }
            // part_index는 detection이 생성된 순서 → GStreamer에서 순차적으로 처리됨
            // 필요하면 static int counter++ 로 인덱스 부여 가능
        } else {
            // fallback (전체 얼굴)
            part_name = "face";
        }
        printf("[DEBUG] part_name %s\n",part_name.c_str());

        // 1. ROI의 stream_id에서 부위 이름 가져오기
        // std::string part_name = roi->get_stream_id();
        // printf("[DEBUG] stream_id: '%s'\n", part_name.c_str());

        // // 2. stream_id가 비어있다면 detection 객체에서 가져오기
        // // if (part_name.empty()) {
        // printf("[DEBUG] stream_id가 비어있음, detection에서 가져오기 시도\n");
        // auto detections = hailo_common::get_hailo_detections(roi);
        // printf("[DEBUG] Detections count: %zu\n", detections.size());
        // if (!detections.empty() && detections[0])
        // {
        //     part_name = detections[0]->get_label();
        //     printf("[DEBUG] Detection 레이블: '%s'\n", part_name.c_str());
        // }
        // else
        // {
        //     part_name = "unknown";
        //     printf("[DEBUG] Detection 없음, 'unknown' 사용\n");
        // }
        // }

        HailoBBox bbox = roi->get_bbox();
        printf("[분석 부위] %s\n", part_name.c_str());
        printf("[BBox] x=%.3f, y=%.3f, w=%.3f, h=%.3f\n",
               bbox.xmin(), bbox.ymin(), bbox.width(), bbox.height());

        // 3. 텐서 가져오기
        const char *tensor_name = "mobile_net_han_kernel_shape/dense_conv42";
        printf("[DEBUG] 텐서 '%s' 가져오기 시도\n", tensor_name);

        HailoTensorPtr tensor;
        try
        {
            tensor = roi->get_tensor(tensor_name);
        }
        catch (const std::exception &e)
        {
            printf("[ERROR] 텐서 가져오기 실패: %s\n", e.what());
            printf("========== SKIN REGRESSION END ==========\n\n");
            return HAILO_SUCCESS; // 에러를 무시하고 계속 진행
        }

        if (!tensor)
        {
            printf("[ERROR] 텐서가 null입니다\n");
            printf("========== SKIN REGRESSION END ==========\n\n");
            return HAILO_SUCCESS; // 에러를 무시하고 계속 진행
        }

        printf("[SUCCESS] 텐서 가져오기 성공\n");

        // 4. 텐서 정보
        printf("\n[텐서 정보]\n");
        printf("  Name: %s\n", tensor->name().c_str());
        printf("  Shape: [%u, %u, %u]\n",
               tensor->height(), tensor->width(), tensor->features());
        printf("  Size: %u bytes\n", tensor->size());

        // 5. 양자화 정보
        auto quant_info = tensor->quant_info();
        printf("\n[양자화 정보]\n");
        printf("  qp_scale: %.10f\n", quant_info.qp_scale);
        printf("  qp_zp: %.2f\n", quant_info.qp_zp);

        // 6. Raw 데이터
        uint8_t *raw_data = tensor->data();
        if (!raw_data)
        {
            printf("[ERROR] 텐서 데이터가 null입니다\n");
            return HAILO_SUCCESS;
        }

        printf("\n[Raw UINT8 데이터] ");
        for (size_t i = 0; i < tensor->size() && i < 10; i++)
        {
            printf("%d ", raw_data[i]);
        }
        printf("\n");

        // 7. Dequantization 및 결과 생성
        // std::vector<std::string> attributes = {"건조", "유분", "여드름", "주름", "색소"};
        std::vector<std::string> attributes = {"Dryness", "Oiliness", "Acne", "Wrinkles", "Pigmentation"};
        std::string result_text = part_name + ": ";

        printf("\n[Dequantized 결과]\n");
        size_t num_values = std::min(static_cast<size_t>(5), static_cast<size_t>(tensor->size()));

        for (size_t i = 0; i < num_values; i++)
        {
            float dequant_value = tensor->fix_scale(raw_data[i]);
            int percent = static_cast<int>(dequant_value * 100.0f);

            printf("  [%zu] %s: raw=%d → %.6f → %d%%\n",
                   i, attributes[i].c_str(), raw_data[i], dequant_value, percent);

            if (i > 0)
                result_text += ", ";
            result_text += attributes[i] + " " + std::to_string(percent) + "%";
        }

        printf("\n[최종 결과] %s\n", result_text.c_str());

        // 8. Classification 객체 추가
        auto classification = std::make_shared<HailoClassification>(
            part_name + "_analysis",
            result_text,
            1.0f);
        roi->add_object(std::dynamic_pointer_cast<HailoObject>(classification));

        printf("[SUCCESS] Classification 추가 완료\n");
        printf("========== SKIN REGRESSION END ==========\n\n");

        return HAILO_SUCCESS;
    }
    catch (const std::exception &e)
    {
        printf("[ERROR] skin_regression exception: %s\n", e.what());
        return HAILO_INVALID_ARGUMENT;
    }
    catch (...)
    {
        printf("[ERROR] skin_regression unknown exception\n");
        return HAILO_INVALID_ARGUMENT;
    }
}
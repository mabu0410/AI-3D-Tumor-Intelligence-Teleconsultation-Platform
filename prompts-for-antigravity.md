# 🤖 PROMPT BỘ – AI 3D Tumor Platform
> Dùng với Antigravity | Dựa trên file `ai-tumor-platform.md`

---

## ✅ CÁCH SỬ DỤNG

1. Bắt đầu bằng **SYSTEM PROMPT** – dán vào System / Instructions của Antigravity
2. Tiếp theo dùng **PROMPT 0** – để AI lên kế hoạch và xác nhận hiểu đúng
3. Lần lượt chạy **PROMPT 1 → 7** theo từng module
4. Kết thúc bằng **PROMPT FINAL** – tổng hợp và kiểm tra toàn bộ

---

## 🔧 SYSTEM PROMPT
> Dán vào phần System Instructions / Persona của Antigravity

```
You are a senior full-stack AI/ML engineer specializing in medical imaging systems.
You will be given a project specification in Markdown format.
Your job is to implement the project exactly as described, module by module.

Rules you must follow:
- Always read and reference the full spec before writing any code
- Follow the exact tech stack specified: Python, PyTorch, MONAI, FastAPI (backend) and Next.js, Three.js (frontend)
- When implementing a module, output: folder structure → code files → explanation
- Write production-quality code with comments in Vietnamese
- If a decision is ambiguous, state your assumption clearly before proceeding
- Never skip a module or merge two modules into one step
- After each module, output a checklist of what was completed
```

---

## 📋 PROMPT 0 – ĐỌC SPEC & LÊN KẾ HOẠCH

```
Đây là toàn bộ spec dự án của tôi:

[DÁN TOÀN BỘ NỘI DUNG FILE ai-tumor-platform.md VÀO ĐÂY]

Hãy thực hiện các bước sau:
1. Đọc toàn bộ spec trên
2. Liệt kê 7 module cần xây dựng theo đúng thứ tự
3. Với mỗi module, cho tôi biết:
   - Input là gì
   - Output là gì
   - Công nghệ sử dụng
   - Ước tính độ phức tạp (Thấp / Trung bình / Cao)
4. Đề xuất thứ tự triển khai tối ưu (không nhất thiết phải theo số thứ tự)
5. Tạo cấu trúc thư mục đầy đủ cho toàn bộ dự án

Chưa viết code. Chỉ lập kế hoạch.
```

---

## 📁 PROMPT 1 – CẤU TRÚC THƯ MỤC & BOILERPLATE

```
Dựa trên kế hoạch đã lập, hãy tạo toàn bộ cấu trúc thư mục và boilerplate cho dự án.

Yêu cầu cụ thể:
1. Tạo cây thư mục đầy đủ theo dạng:
   ai-tumor-platform/
   ├── backend/
   │   ├── modules/
   │   └── ...
   ├── frontend/
   └── ...

2. Tạo các file cấu hình cơ bản:
   - backend/requirements.txt (Python dependencies: torch, monai, fastapi, uvicorn, pydicom, scikit-learn, xgboost, numpy, nibabel)
   - frontend/package.json (Next.js, Three.js, axios, tailwindcss)
   - docker-compose.yml (backend + frontend + postgres)
   - .env.example

3. Tạo file README.md hướng dẫn cài đặt và chạy dự án

4. Tạo backend/main.py với FastAPI app và đăng ký đầy đủ các router cho 7 module

Sau khi tạo xong, liệt kê checklist những gì đã hoàn thành.
```

---

## 🧠 PROMPT 2 – MODULE 1: SEGMENTATION 3D

```
Bây giờ hãy implement Module 1: Segmentation 3D.

Spec:
- Input: File DICOM (ảnh CT/MRI 3D)
- Mô hình: nnU-Net (ưu tiên), fallback là 3D U-Net
- Loss: Dice Loss + BCE Hybrid
- Output: 3D Binary Mask (.nii.gz)
- Metric: Dice Score, IoU, Hausdorff Distance

Hãy tạo các file sau:
1. backend/modules/segmentation/
   - model.py         → định nghĩa 3D U-Net với PyTorch + MONAI
   - inference.py     → load model, nhận DICOM, trả về mask
   - metrics.py       → tính Dice Score, IoU, Hausdorff Distance
   - router.py        → FastAPI endpoint POST /api/segmentation/predict

2. Endpoint API:
   POST /api/segmentation/predict
   - Input: multipart/form-data chứa file DICOM
   - Output: JSON { mask_path, dice_score, iou, hausdorff, processing_time }

3. Viết unit test cơ bản cho metrics.py

Sau khi viết xong, tóm tắt checklist Module 1.
```

---

## 🎨 PROMPT 3 – MODULE 2: TÁI TẠO & TRỰC QUAN HÓA 3D

```
Implement Module 2: Tái tạo và trực quan hóa 3D.

Spec:
- Input: 3D Binary Mask từ Module 1
- Xử lý: Marching Cubes → tạo mesh 3D
- Tính toán: Volume, Diện tích bề mặt, Sphericity, Độ gồ ghề
- Frontend: Three.js viewer với xoay 360°, cắt lớp, đánh dấu vùng

Hãy tạo:
1. backend/modules/reconstruction/
   - mesh_generator.py  → Marching Cubes với scikit-image, xuất file .obj hoặc .glb
   - geometry.py        → tính Volume, Surface Area, Sphericity, Roughness Index
   - router.py          → FastAPI endpoint POST /api/reconstruction/generate

2. frontend/components/Viewer3D/
   - Viewer3D.tsx        → Three.js scene với OrbitControls
   - TumorMesh.tsx       → load và render file .glb
   - SlicePlane.tsx      → chức năng cắt lớp
   - MarkerTool.tsx      → đánh dấu vùng nghi ngờ
   - CompareView.tsx     → so sánh trước & sau điều trị

3. API endpoint:
   POST /api/reconstruction/generate
   - Input: { mask_path }
   - Output: { mesh_url, volume_cm3, surface_area_cm2, sphericity, roughness_index }

Sau khi viết xong, tóm tắt checklist Module 2.
```

---

## 🔬 PROMPT 4 – MODULE 3 & 4: PHÂN TÍCH HÌNH THÁI + PHÂN LOẠI LÀNH/ÁC

```
Implement Module 3 (Phân tích hình thái 3D) và Module 4 (Phân loại lành/ác) cùng nhau vì chúng dùng chung feature pipeline.

Spec Module 3:
- Trích xuất: Shape features, Radiomics (texture), Surface irregularity, Fractal dimension, Gradient distribution

Spec Module 4:
- Input: feature vector từ Module 3 + dữ liệu lâm sàng (optional)
- Mô hình: XGBoost (trên feature vector) + ResNet3D (trên raw volume)
- Output: Benign/Malignant, Xác suất %, Risk Score

Hãy tạo:
1. backend/modules/analysis/
   - feature_extractor.py   → trích xuất tất cả radiomics features với PyRadiomics
   - shape_features.py      → Shape, Sphericity, Fractal dimension
   - surface_features.py    → Surface irregularity index, Gradient distribution

2. backend/modules/classification/
   - model_xgboost.py       → train và inference XGBoost trên feature vector
   - model_resnet3d.py      → ResNet3D với PyTorch
   - ensemble.py            → kết hợp kết quả 2 mô hình
   - router.py              → FastAPI endpoint POST /api/classification/predict

3. API endpoint:
   POST /api/classification/predict
   - Input: { mask_path, clinical_data (optional) }
   - Output: { label: "Benign"|"Malignant", probability: float, risk_score: float, features: dict }

4. frontend/components/ClassificationResult/
   - RiskGauge.tsx    → hiển thị Risk Score dạng gauge chart
   - FeatureTable.tsx → bảng các đặc trưng đã trích xuất

Sau khi viết xong, tóm tắt checklist Module 3 & 4.
```

---

## 📈 PROMPT 5 – MODULE 5: DỰ ĐOÁN TIẾN TRIỂN

```
Implement Module 5: Dự đoán tiến triển 3–6 tháng.

Spec:
- Input: Chuỗi dữ liệu theo thời gian T0 → T1 → T2 (volume + features mỗi lần chụp)
- Mô hình: LSTM (chính) + Transformer Time-series (nâng cao)
- Output: % tăng/giảm thể tích, khả năng chuyển ác tính, tốc độ xâm lấn

Hãy tạo:
1. backend/modules/prediction/
   - data_prep.py        → chuẩn bị chuỗi thời gian từ nhiều lần scan
   - model_lstm.py       → LSTM model với PyTorch
   - model_transformer.py → Time-series Transformer
   - predictor.py        → inference, trả về dự đoán 3 tháng và 6 tháng
   - router.py           → FastAPI endpoint POST /api/prediction/forecast

2. API endpoint:
   POST /api/prediction/forecast
   - Input: { patient_id, scan_history: [{ date, mask_path, features }] }
   - Output:
     {
       forecast_3m: { volume_change_pct, malignancy_risk, invasion_speed },
       forecast_6m: { volume_change_pct, malignancy_risk, invasion_speed },
       confidence: float
     }

3. frontend/components/ProgressionChart/
   - TimelineChart.tsx   → biểu đồ thể tích theo thời gian (Recharts hoặc Chart.js)
   - ForecastCard.tsx    → hiển thị kết quả dự đoán 3 tháng & 6 tháng

Sau khi viết xong, tóm tắt checklist Module 5.
```

---

## 🏥 PROMPT 6 – MODULE 6 & 7: TELEMEDICINE + QUẢN LÝ LỊCH TÁI KHÁM

```
Implement Module 6 (Telemedicine & Hội chẩn từ xa) và Module 7 (Quản lý lịch tái khám).

Spec Module 6:
- Tuyến dưới: upload case → AI phân tích → gửi hội chẩn
- Tuyến trên: xem 3D, xem phân tích AI, ghi chú, ký duyệt điện tử

Spec Module 7:
- Tự động đề xuất lịch tái khám
- Gửi SMS/Notification
- Lưu trữ lịch sử bệnh án số hóa

Hãy tạo:
1. backend/modules/telemedicine/
   - case_manager.py     → tạo, gửi, nhận case hội chẩn
   - annotation.py       → lưu ghi chú của bác sĩ tuyến trên
   - digital_sign.py     → tạo và xác thực chữ ký điện tử
   - router.py           → các endpoint CRUD cho case hội chẩn

2. backend/modules/scheduler/
   - recommendation.py  → tính toán ngày tái khám dựa trên risk score
   - notification.py    → gửi SMS (Twilio) và push notification
   - router.py          → endpoint quản lý lịch tái khám

3. backend/models/database.py → SQLAlchemy models cho:
   - Patient, ScanRecord, ConsultationCase, Appointment, Notification

4. frontend/pages/
   - dashboard/index.tsx        → trang tổng quan bác sĩ
   - cases/[id].tsx             → chi tiết case hội chẩn
   - patients/[id]/history.tsx  → lịch sử bệnh nhân

Sau khi viết xong, tóm tắt checklist Module 6 & 7.
```

---

## 🔗 PROMPT FINAL – TỔNG HỢP & KIỂM TRA

```
Tất cả 7 module đã được implement. Bây giờ hãy:

1. TÍCH HỢP toàn bộ pipeline end-to-end:
   - Viết backend/pipeline.py gọi lần lượt: segmentation → reconstruction → analysis → classification → prediction
   - Tạo endpoint tổng hợp: POST /api/pipeline/run-full-analysis

2. KIỂM TRA tính nhất quán:
   - Liệt kê tất cả API endpoints đã tạo (method + path + input + output)
   - Xác nhận tất cả import giữa các module đều đúng
   - Kiểm tra không có circular import

3. TẠO tài liệu API:
   - Viết backend/docs/api_reference.md liệt kê đầy đủ tất cả endpoints

4. TẠO script khởi động nhanh:
   - scripts/setup.sh    → cài dependencies, tạo database
   - scripts/run_dev.sh  → chạy backend + frontend cùng lúc
   - scripts/seed_data.py → tạo dữ liệu mẫu để test

5. REVIEW cuối cùng:
   - Liệt kê những gì còn thiếu hoặc cần cải thiện
   - Đề xuất các bước tiếp theo để đưa vào production

Output cuối cùng: Một checklist đầy đủ đánh dấu ✅/❌ cho từng hạng mục của toàn bộ dự án.
```

---

## 💡 MẸO SỬ DỤNG

| Tình huống | Cách xử lý |
|------------|------------|
| AI bị lạc hướng | Nhắc lại: *"Hãy đọc lại spec ở PROMPT 0 và tiếp tục đúng module"* |
| Muốn đi sâu hơn 1 module | Thêm: *"Viết thêm unit test và xử lý edge case cho module này"* |
| AI viết sai tech stack | Nhắc: *"Dùng đúng tech stack: PyTorch + MONAI + FastAPI + Next.js"* |
| Muốn giải thích logic | Thêm vào cuối prompt: *"Sau khi viết code, giải thích ngắn gọn logic chính"* |

# HỆ THỐNG AI PHÁT HIỆN – PHÂN TÍCH – DỰ ĐOÁN KHỐI U 3D
**AI 3D Tumor Intelligence & Teleconsultation Platform**

---

## 1. GIỚI THIỆU DỰ ÁN

### 1.1 Bối cảnh

Trong lĩnh vực chẩn đoán ung thư, việc phát hiện và đánh giá khối u từ ảnh CT/MRI phụ thuộc rất nhiều vào kinh nghiệm của bác sĩ chuyên khoa.

**Các vấn đề hiện tại:**
- Bệnh viện tuyến dưới thiếu bác sĩ chuyên môn sâu
- Đọc ảnh 2D nhiều lát cắt tốn thời gian và dễ sai sót
- Khó theo dõi tiến triển khối u theo thời gian
- Hội chẩn từ xa còn thủ công, thiếu hệ thống đồng bộ

### 1.2 Giải pháp đề xuất

Dự án xây dựng một **hệ thống AI tích hợp** gồm các chức năng:

| STT | Chức năng |
|-----|-----------|
| 1 | Phân đoạn khối u 3D |
| 2 | Tái tạo và trực quan hóa mô hình 3D |
| 3 | Phân tích hình thái bề mặt |
| 4 | Phân loại lành / ác tính |
| 5 | Dự đoán tiến triển 3–6 tháng |
| 6 | Hỗ trợ hội chẩn từ xa |
| 7 | Quản lý & nhắc lịch tái khám |

---

## 2. MỤC TIÊU DỰ ÁN

### 2.1 Mục tiêu tổng quát

Xây dựng một **nền tảng AI y tế** hỗ trợ bác sĩ chẩn đoán và theo dõi khối u dựa trên dữ liệu CT/MRI 3D.

### 2.2 Mục tiêu cụ thể

- [ ] Phân đoạn chính xác khối u từ ảnh DICOM 3D
- [ ] Tái tạo mô hình 3D trực quan
- [ ] Trích xuất đặc trưng hình học và bề mặt
- [ ] Phân loại khối u lành tính / ác tính
- [ ] Dự đoán sự phát triển trong tương lai
- [ ] Tích hợp hệ thống hội chẩn từ xa
- [ ] Tự động nhắc lịch tái khám

---

## 3. TỔNG QUAN KỸ THUẬT

### 3.1 Dữ liệu đầu vào

- **Định dạng:** Ảnh CT hoặc MRI định dạng DICOM
- **Cấu trúc:** Volume 3D gồm nhiều lát cắt

### 3.2 Nguồn dữ liệu tham khảo

- [The Cancer Imaging Archive (TCIA)](https://www.cancerimagingarchive.net/)
- [BraTS Challenge – Brain Tumor Segmentation](https://www.synapse.org/brats)

---

## 4. KIẾN TRÚC HỆ THỐNG

### 4.1 Pipeline tổng thể

```
[1] Upload DICOM
      ↓
[2] Tiền xử lý ảnh
      ↓
[3] Segmentation 3D
      ↓
[4] Tái tạo 3D
      ↓
[5] Phân tích đặc trưng
      ↓
[6] Phân loại lành / ác
      ↓
[7] Dự đoán tiến triển
      ↓
[8] Dashboard & Telemedicine
```

---

## 5. MODULE 1 – SEGMENTATION 3D

### 5.1 Mô hình đề xuất

| Mô hình | Ghi chú |
|---------|---------|
| 3D U-Net | Kiến trúc encoder-decoder 3D chuẩn |
| V-Net | Tối ưu cho dữ liệu y tế volumetric |
| nnU-Net | Tự động cấu hình, SOTA benchmark |

### 5.2 Loss Function

- Dice Loss
- BCE + Dice Hybrid

### 5.3 Output

- **3D Binary Mask** của khối u

### 5.4 Metric đánh giá

| Metric | Mục đích |
|--------|----------|
| Dice Score | Đo độ chồng lấp giữa mask dự đoán và ground truth |
| IoU (Intersection over Union) | Đánh giá độ chính xác vùng phân đoạn |
| Hausdorff Distance | Đo sai lệch biên giới bề mặt |

---

## 6. MODULE 2 – TÁI TẠO & TRỰC QUAN HÓA 3D

### 6.1 Quy trình tái tạo

Sau khi có mask 3D:
1. Áp dụng thuật toán **Marching Cubes** để tạo mesh 3D
2. Tính toán các đặc trưng hình học:
   - Thể tích (Volume)
   - Diện tích bề mặt
   - Độ tròn (Sphericity)
   - Độ gồ ghề bề mặt

### 6.2 Công nghệ trực quan hóa

| Công nghệ | Môi trường |
|-----------|-----------|
| Three.js | Web (frontend) |
| WebGL | Web rendering |
| VTK | Scientific visualization |
| PyVista | Python backend |

### 6.3 Chức năng người dùng

- Xoay 360°
- Cắt lớp (cross-section)
- So sánh trước & sau điều trị
- Đánh dấu vùng nghi ngờ

---

## 7. MODULE 3 – PHÂN TÍCH HÌNH THÁI 3D

### 7.1 Trích xuất đặc trưng

| Nhóm đặc trưng | Chi tiết |
|----------------|----------|
| Shape features | Hình dạng tổng thể của khối u |
| Texture features (Radiomics) | Cấu trúc bề mặt và nội tại |
| Surface irregularity index | Chỉ số gồ ghề bề mặt |
| Fractal dimension | Độ phức tạp hình học |
| Gradient distribution | Phân bố gradient cường độ ảnh |

### 7.2 Mục tiêu phát hiện

Phát hiện các đặc điểm thường thấy ở khối u ác tính:
- Bờ không đều
- Xâm lấn mô lân cận
- Bất đối xứng cao

---

## 8. MODULE 4 – PHÂN LOẠI LÀNH / ÁC

### 8.1 Input

- Đặc trưng 3D (từ Module 3)
- Radiomics features
- Dữ liệu lâm sàng (nếu có)

### 8.2 Mô hình phân loại

| Mô hình | Loại |
|---------|------|
| 3D CNN | Deep learning trực tiếp trên volume |
| ResNet3D | Transfer learning 3D |
| XGBoost | Machine learning trên feature vector |

### 8.3 Output

| Output | Mô tả |
|--------|-------|
| Nhãn phân loại | Benign (lành tính) / Malignant (ác tính) |
| Xác suất | % khả năng ác tính |
| Risk Score | Điểm nguy cơ tổng hợp |

---

## 9. MODULE 5 – DỰ ĐOÁN TIẾN TRIỂN 3–6 THÁNG

### 9.1 Ý tưởng

Sử dụng dữ liệu từ **nhiều lần chụp** theo thời gian:

```
T0 (lần chụp 1) → T1 (lần chụp 2) → T2 (lần chụp 3) → Dự đoán tương lai
```

### 9.2 Mô hình đề xuất

| Mô hình | Ứng dụng |
|---------|----------|
| LSTM | Học chuỗi thời gian |
| Temporal CNN | Trích xuất đặc trưng theo thời gian |
| Transformer Time-series | Attention-based time series prediction |

### 9.3 Output dự đoán

| Output | Ví dụ |
|--------|-------|
| Tăng/giảm thể tích (%) | +10% sau 3 tháng |
| Khả năng chuyển ác tính | 65% nguy cơ |
| Tốc độ xâm lấn | Nhanh / Trung bình / Chậm |

**Ví dụ kết quả:**
- Sau 3 tháng: +10% thể tích
- Sau 6 tháng: nguy cơ cao tiến triển nhanh

---

## 10. MODULE 6 – TELEMEDICINE & HỘI CHẨN TỪ XA

### 10.1 Quy trình cho tuyến dưới (bệnh viện gửi)

1. Upload dữ liệu DICOM lên hệ thống
2. AI phân tích tự động
3. Gửi case hội chẩn lên tuyến trên

### 10.2 Quy trình cho tuyến trên (chuyên gia nhận)

1. Xem mô hình 3D
2. Xem phân tích AI
3. Ghi chú trực tiếp trên hệ thống
4. Ký duyệt điện tử

---

## 11. MODULE 7 – QUẢN LÝ & NHẮC LỊCH TÁI KHÁM

### 11.1 Tính năng hệ thống

- Tự động đề xuất thời gian tái khám dựa trên kết quả phân tích
- Gửi SMS / Push Notification cho bệnh nhân
- Lưu trữ toàn bộ lịch sử bệnh án số hóa

---

## 12. KIẾN TRÚC CÔNG NGHỆ

### 12.1 Tech Stack

| Tầng | Công nghệ |
|------|-----------|
| **Backend** | Python, PyTorch, MONAI, FastAPI |
| **Frontend** | Next.js, Three.js, Web-based 3D Viewer |
| **Database** | PostgreSQL, PACS Integration |
| **Triển khai** | Cloud GPU (AWS / Azure), On-premise Server tại bệnh viện |

### 12.2 Sơ đồ tầng hệ thống

```
┌─────────────────────────────────────────────┐
│              FRONTEND                        │
│         Next.js + Three.js                   │
│         Web 3D Viewer                         │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│              BACKEND                         │
│         FastAPI (Python)                     │
│   PyTorch · MONAI · Segmentation Models      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              DATABASE                        │
│      PostgreSQL + PACS Integration           │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           INFRASTRUCTURE                     │
│    Cloud GPU (AWS/Azure) hoặc On-premise     │
└─────────────────────────────────────────────┘
```

---

## 13. GIÁ TRỊ MANG LẠI

### 13.1 Cho bệnh viện

- Hỗ trợ chẩn đoán chính xác hơn
- Giảm tải cho bác sĩ chuyên khoa
- Chuẩn hóa quy trình đọc ảnh

### 13.2 Cho bác sĩ

- Phân tích định lượng thay vì cảm tính
- Trực quan hóa 3D thay vì chỉ xem 2D slices

### 13.3 Cho bệnh nhân

- Theo dõi tiến triển chính xác theo thời gian
- Phát hiện sớm nguy cơ ác tính
- Giảm chi phí di chuyển nhờ hội chẩn từ xa

---

## 14. TÍNH KHẢ THI

### 14.1 Nền tảng kỹ thuật

| Yếu tố | Trạng thái |
|--------|-----------|
| Deep Learning 3D | Đã được chứng minh hiệu quả trong y tế |
| Dataset | Công khai (TCIA, BraTS) |
| Công nghệ Web 3D | Trưởng thành (Three.js, WebGL) |
| Hạ tầng Cloud GPU | Phổ biến, sẵn sàng (AWS, Azure) |

### 14.2 Kế hoạch triển khai theo giai đoạn

```
Giai đoạn 1:  Segmentation + 3D Viewer
              └─ Upload DICOM → Phân đoạn → Xem 3D

Giai đoạn 2:  Classification + Prediction
              └─ Phân loại lành/ác → Dự đoán tiến triển

Giai đoạn 3:  Telemedicine + Hospital Integration
              └─ Hội chẩn từ xa → Tích hợp hệ thống bệnh viện
```

---

## 15. KẾT LUẬN

Dự án đề xuất xây dựng một **hệ thống AI y tế toàn diện** với các khả năng:

- ✅ Phát hiện và phân đoạn khối u 3D
- ✅ Phân tích hình thái bề mặt chi tiết
- ✅ Phân loại lành tính / ác tính
- ✅ Dự đoán tiến triển theo thời gian
- ✅ Hội chẩn từ xa tích hợp
- ✅ Quản lý và theo dõi bệnh nhân

> **Đây không chỉ là một mô hình AI đơn lẻ, mà là một nền tảng AI y tế thông minh, hỗ trợ quyết định lâm sàng và tăng cường khả năng tiếp cận chuyên môn cao cho các bệnh viện tuyến dưới.**

---

*Tài liệu được tạo từ outline dự án – sẵn sàng để AI thực thi theo từng module.*

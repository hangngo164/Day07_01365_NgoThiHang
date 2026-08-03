# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** PRAI
**Thành viên:** Thành viên 1 — Ngô Thị Hằng; Thành viên 2 — Nguyễn Huy Hoàng; Thành viên 3 — Nguyễn Thị Hoàng Yến\; Thành viên 4 — Quách Xuân Trường
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Quy chế đào tạo, học phí, học bổng

**Phạm vi cụ thể nhóm tập trung:**

> Quy định dành cho sinh viên tại ĐHQGHN/HUS, tập trung vào công tác sinh viên, đánh giá rèn luyện, học phí và học bổng.

### Danh sách tài liệu (Data Inventory)

| #  | Tên tài liệu                                              | Nguồn (Source URL)                                                                     | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán                                                          |
| -- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------- | ------------------------ | ----------- | --------------------------------------------------------------------------- |
| 1  | Quy chế công tác HSSV (Thông tư 10/2016)                | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 37,831      | `audience`, `department`, `category=student-affairs`, `language`    |
| 2  | Quy chế đánh giá điểm rèn luyện (Thông tư 16/2015) | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 16,113      | `audience`, `department`, `category=conduct-evaluation`, `language` |
| 3  | Quy định công tác sinh viên (Thông tư 40/2026)        | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 38,767      | `audience`, `department`, `category=student-affairs`, `language`    |
| 4  | Quy định quản lý và sử dụng học bổng ĐHQGHN        | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 23,457      | `audience`, `department`, `category=scholarship`, `language`        |
| 5  | Nghị định 81 về học phí và hỗ trợ học tập         | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 99,550      | `audience`, `department`, `category=tuition`, `language`            |
| 6  | Nghị định 97/2023 sửa đổi quy định học phí         | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 12,748      | `audience`, `department`, `category=tuition`, `language`            |
| 7  | Quy định học bổng HUS năm học 2023-2024                | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 25,943      | `audience`, `department`, `category=scholarship`, `language`        |
| 8  | Quy chế công tác sinh viên ĐHQGHN năm 2017             | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 62,404      | `audience`, `department`, `category=student-affairs`, `language`    |
| 9  | Quy chế công tác sinh viên ĐHQGHN năm 2014 (bản 1)    | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 49,522      | `audience`, `department`, `category=student-affairs`, `language`    |
| 10 | Quy chế công tác sinh viên ĐHQGHN năm 2014 (bản 2)    | [HUS - Quy chế, quy định](https://hus.vnu.edu.vn/hoc-sinh-sinh-vien/quy-che-quy-dinh) | 2026-08-03 / not-stated  | 49,518      | `audience`, `department`, `category=student-affairs`, `language`    |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [X] Tập tài liệu chỉ chứa quy định công khai từ trang quy chế của HUS, không có dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [X] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version`, `audience` và các trường lọc bổ sung trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata    | Kiểu       | Ví dụ giá trị                                        | Tại sao hữu ích cho truy xuất (retrieval)?                            |
| -------------------- | ----------- | -------------------------------------------------------- | ------------------------------------------------------------------------- |
| `doc_id`           | string      | `97-cpsigned`                                          | Định danh duy nhất, truy vết chunk về văn bản gốc.                |
| `title`            | string      | `Nghị định 97/2023 sửa đổi quy định học phí` | Hiển thị kết quả dễ hiểu cho người dùng.                         |
| `source_url`       | URL string  | `https://hus.vnu.edu.vn/...`                           | Cho phép kiểm chứng nguồn công khai.                                 |
| `retrieved_at`     | date string | `2026-08-03`                                           | Biết thời điểm thu thập dữ liệu.                                   |
| `document_version` | string      | `not-stated`                                           | Phân biệt khi có văn bản thay thế/cập nhật.                       |
| `audience`         | string      | `student`                                              | Giới hạn corpus theo nhóm người dùng.                               |
| `department`       | string      | `student-affairs`                                      | Hỗ trợ truy xuất theo đầu mối quản lý.                            |
| `category`         | string      | `scholarship`                                          | Dùng trong`search_with_filter()` cho học bổng/học phí/rèn luyện. |
| `language`         | string      | `vi`                                                   | Hỗ trợ xử lý truy vấn tiếng Việt.                                  |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu                       | Chiến lược (Strategy)           | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                                        |
| -------------------------------- | ---------------------------------- | ----------------- | --------------------- | ---------------------------------------------------------------------- |
| Thông tư 16/2015 (rèn luyện) | FixedSizeChunker (`fixed_size`)  | 90                | 198.8                 | Trung bình; có overlap nhưng có thể cắt giữa mục.              |
| Thông tư 16/2015 (rèn luyện) | SentenceChunker (`by_sentences`) | 46                | 348.3                 | Tốt khi OCR nhận diện đúng dấu câu.                             |
| Thông tư 16/2015 (rèn luyện) | RecursiveChunker (`recursive`)   | 119               | 131.7                 | Tốt; ưu tiên ngắt theo đoạn/mục nhưng tạo nhiều chunk ngắn. |
| Quy định học bổng ĐHQGHN    | FixedSizeChunker (`fixed_size`)  | 131               | 198.9                 | Trung bình; kích thước ổn định.                                 |
| Quy định học bổng ĐHQGHN    | SentenceChunker (`by_sentences`) | 61                | 381.4                 | Tốt; giữ được nhóm câu mô tả điều kiện học bổng.         |
| Quy định học bổng ĐHQGHN    | RecursiveChunker (`recursive`)   | 141               | 161.4                 | Tốt; giữ tiêu đề, điều khoản và đoạn văn gần nhau.        |
| Nghị định 97/2023 (học phí) | FixedSizeChunker (`fixed_size`)  | 71                | 199.3                 | Trung bình; có thể chia đôi bảng/mức phí.                      |
| Nghị định 97/2023 (học phí) | SentenceChunker (`by_sentences`) | 20                | 636.0                 | Thấp hơn; câu OCR dài làm chunk quá lớn.                        |
| Nghị định 97/2023 (học phí) | RecursiveChunker (`recursive`)   | 88                | 143.4                 | Tốt; tách theo trang/đoạn, phù hợp tài liệu có bảng.         |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Ngô Thị Hằng**

- **Loại chiến lược:** FixedSizeChunker (`chunk_size=500`, `overlap=50`).
- **Mô tả & lý do chọn:** Đây là đường cơ sở dễ tái lập và có overlap để giảm rủi ro mất thông tin ở ranh giới chunk. Chiến lược phù hợp để so sánh công bằng với các cách tách theo cấu trúc.

**Thành viên 2 — Nguyễn Huy Hoàng**

- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`).
- **Mô tả & lý do chọn:** Gom ba câu giúp câu trả lời có đầy đủ chủ ngữ, điều kiện và quy định đi kèm. Điểm yếu là OCR có thể làm sai dấu câu, khiến một số chunk dài bất thường.

**Thành viên 3 — Nguyễn Thị Hoàng Yến**

- **Loại chiến lược:** RecursiveChunker (`chunk_size=500`).
- **Mô tả & lý do chọn:** Tách ưu tiên theo dòng trống, dòng mới rồi đến câu, nên giữ cấu trúc điều/khoản tốt hơn fixed-size. Đây là cấu hình cân bằng giữa độ dài chunk và ngữ cảnh của văn bản quy chế.

**Thành viên 4 — Quách Xuân Trường**

- **Loại chiến lược:** Custom RecursiveChunker (`chunk_size=350`) kết hợp `search_with_filter()` cho câu hỏi theo danh mục.
- **Mô tả & lý do chọn:** Chunk ngắn hơn giúp cô lập điều kiện, mức phí và đối tượng áp dụng. Với câu hỏi chuyên biệt, lọc `category` trước khi xếp hạng làm giảm nhiễu giữa nhóm học bổng, học phí và công tác sinh viên.

### So Sánh Giữa Các Thành Viên

| Thành viên             | Chiến lược (Strategy)   | Điểm truy xuất (/10) | Điểm mạnh                                                      | Điểm yếu                                           |
| ------------------------ | -------------------------- | ----------------------- | ----------------------------------------------------------------- | ----------------------------------------------------- |
| Ngô Thị Hằng          | Fixed-size 500, overlap 50 | 10/10*                  | Số chunk vừa phải, có overlap ở ranh giới.                  | Có thể cắt giữa điều/khoản hoặc bảng.        |
| Nguyễn Huy Hoàng       | 3 câu/chunk               | 10/10*                  | Đoạn trả về có ngữ cảnh câu đầy đủ.                   | Nhạy với lỗi dấu câu do OCR.                     |
| Nguyễn Thị Hoàng Yến | Recursive 500              | 6/10*                   | Giữ cấu trúc đoạn/mục, cân bằng độ dài và ngữ cảnh. | Hai evidence chunk không vào top-3.                 |
| Quách Xuân Trường    | Recursive 350 + filter     | 8/10*                   | Chunk ngắn, lọc đúng chủ đề, chính xác cho câu 5.       | 1,593 chunks, chi phí lưu trữ/tìm kiếm cao hơn. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> FixedSizeChunker 500 với overlap 50 là lựa chọn thực dụng nhất trên bộ benchmark này: đạt 5/5 evidence chunk trong top-3 và chỉ tạo 928 chunks, ít hơn SentenceChunker. SentenceChunker đạt cùng điểm nhưng nhạy với lỗi dấu câu OCR; Recursive 500 giữ cấu trúc tốt về mặt đọc hiểu nhưng hai evidence chunk không vào top-3. `*` Một hit chỉ được tính khi kết quả vừa đúng `doc_id` vừa chứa marker của gold answer; chưa chấm chất lượng câu trả lời tự sinh của LLM.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query)                                                                                                     | Câu trả lời chuẩn (Gold Answer)                                                                                                                                                             | Chunk nào chứa thông tin?                                                                                    |
| - | --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 1 | Sinh viên phải đóng học phí và bảo hiểm y tế như thế nào?                                                | Đóng học phí, bảo hiểm y tế và các lệ phí khác đầy đủ, đúng quy định.                                                                                                       | Quy chế CTSV 2017 hoặc Thông tư 10/2016; marker:`đóng học phí, bảo hiểm y tế`.                     |
| 2 | Khi đánh giá kết quả rèn luyện, quy trình và tiêu chí cần bảo đảm điều gì?                          | Thực hiện nghiêm túc quy trình và tiêu chí; bảo đảm khách quan, công khai, công bằng, chính xác; tôn trọng bình đẳng, dân chủ và phối hợp các đơn vị liên quan. | Thông tư 16/2015; marker:`khách quan, công khai, công bằng, chính xác`.                               |
| 3 | Quy định quản lý và sử dụng học bổng của ĐHQGHN áp dụng đối với ai?                                   | Áp dụng cho học sinh, sinh viên, học viên cao học, nghiên cứu sinh của ĐHQGHN và các đơn vị, bộ phận chức năng liên quan.                                                  | Quy định học bổng ĐHQGHN 2024; marker:`áp dụng đối với học sinh, sinh viên, học viên cao học`. |
| 4 | Học phí từ năm học 2023-2024 của cơ sở chưa tự bảo đảm chi thường xuyên được quy định thế nào? | Giữ ổn định bằng mức thu học phí năm học 2021-2022 do Hội đồng nhân dân tỉnh đã ban hành tại địa phương.                                                                | Nghị định 97/2023; marker:`giữ ổn định mức thu học phí`.                                            |
| 5 | Sinh viên chương trình cử nhân khoa học tài năng nào được xét học bổng hỗ trợ chi phí học tập?   | Sinh viên các chương trình cử nhân khoa học tài năng Toán, Vật lý, Hóa học, Sinh học được xét cấp học bổng hỗ trợ chi phí học tập.                                  | Quy định học bổng HUS 2023-2024; marker:`Vật lý học, Hóa học, Sinh học được xét cấp`.          |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi                                  | Chiến lược tốt nhất cho câu này               | Có chunk liên quan trong top-3? | Ghi chú                                                             |
| - | ------------------------------------------ | ---------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------- |
| 1 | Nghĩa vụ học phí và bảo hiểm y tế  | Fixed-size 500 (đồng hạng Sentence)               | Có                               | Evidence chunk của hai quy chế tương đương xuất hiện top-3. |
| 2 | Nguyên tắc đánh giá rèn luyện       | Fixed-size 500 (đồng hạng Sentence/Recursive 500) | Có                               | Evidence chunk của Thông tư 16/2015 đứng hạng 3.               |
| 3 | Đối tượng áp dụng học bổng ĐHQGHN | Fixed-size 500 (cả bốn cấu hình đều đạt)     | Có                               | Evidence chunk nguồn đứng top-1.                                  |
| 4 | Mức học phí năm 2023-2024              | Fixed-size 500 (đồng hạng Sentence/Recursive 350) | Có                               | Evidence chunk của Nghị định 97/2023 đứng top-1.               |
| 5 | Học bổng hỗ trợ chi phí học tập     | Fixed-size 500 +`category=scholarship`             | Có                               | Lọc metadata giữ kết quả trong nhóm tài liệu học bổng.      |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> Có. Với câu 5, bộ lọc `category=scholarship` loại các văn bản học phí và quy chế công tác sinh viên trước khi xếp hạng, nên cả ba kết quả đều thuộc tài liệu học bổng. Bộ lọc cần dùng vừa đủ chặt; nếu lọc sai danh mục, chunk liên quan có thể bị loại trước khi truy xuất.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

> - OCR biến 8 PDF scan thành Markdown, nhưng lỗi nhận dạng dấu câu và ký tự làm SentenceChunker kém ổn định trên một số tài liệu.
> - RecursiveChunker giữ cấu trúc điều/khoản tốt hơn khi văn bản có nhiều dòng trống, tiêu đề và bảng.
> - Lọc metadata `category=scholarship` giúp câu hỏi học bổng không bị cạnh tranh bởi văn bản học phí hoặc quy chế chung.

**Bài học rút ra khi so sánh trong nhóm:**

> Khi chấm theo evidence chunk thay vì chỉ `doc_id`, Fixed-size và Sentence đều đạt 5/5, Recursive 350 đạt 4/5, còn Recursive 500 đạt 3/5. Kết quả cho thấy chiến lược giữ cấu trúc tốt chưa chắc xếp đúng đoạn trả lời ở top-3 khi embedding hiện tại là từ khóa; sentence chunking cũng phụ thuộc mạnh vào dấu câu OCR. Hai bản quy chế 2014 gần trùng nhau có thể tăng kết quả trùng lặp, vì vậy cần cân nhắc loại bản sao khi mở rộng benchmark.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> Nhóm sẽ lưu URL trực tiếp của từng PDF thay vì chỉ URL trang danh mục, chuẩn hóa `document_version` theo số/ngày ban hành và loại hoặc gắn nhãn các bản trùng lặp. Nhóm cũng sẽ rà soát các đoạn OCR quan trọng, nhất là bảng học phí, trước khi đánh giá để giảm lỗi nhận dạng ảnh hưởng đến truy xuất.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                   | Điểm tự đánh giá |
| -------------------------------------------- | ---------------------- |
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10                 |
| Thiết kế chiến lược (Strategy Design)   | 14 / 15                |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10                |
| Thuyết trình (Demo)                        | 0/ 5                   |
| **Tổng phần nhóm**                  | **33 / 40**      |

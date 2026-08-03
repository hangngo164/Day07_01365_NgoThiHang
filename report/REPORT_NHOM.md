# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**
> *1 câu — ví dụ: thư viện + đăng ký môn học.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sinh viên phải đóng học phí và bảo hiểm y tế như thế nào? | Đóng học phí, bảo hiểm y tế và các lệ phí khác đầy đủ, đúng quy định; hoàn trả vốn vay đúng hạn nếu có. | `quy-che-32...::chunk_19` hoặc `10-2016...::chunk_16` |
| 2 | Khi đánh giá kết quả rèn luyện, quy trình và tiêu chí cần bảo đảm điều gì? | Thực hiện nghiêm túc quy trình và tiêu chí; bảo đảm khách quan, công khai, công bằng, chính xác; tôn trọng bình đẳng, dân chủ và phối hợp các đơn vị liên quan. | `16-2015-tt-bgddt-ve-diem-ren-luyen::chunk_10` |
| 3 | Quy định quản lý và sử dụng học bổng của ĐHQGHN áp dụng đối với ai? | Áp dụng cho học sinh, sinh viên, học viên cao học, nghiên cứu sinh của ĐHQGHN và các đơn vị, bộ phận chức năng liên quan. | `4618-nam-2024-quy-dinh-hoc-bong-vnu::chunk_6-7` |
| 4 | Học phí từ năm học 2023-2024 của cơ sở chưa tự bảo đảm chi thường xuyên được quy định thế nào? | Giữ ổn định bằng mức thu học phí năm học 2021-2022 do Hội đồng nhân dân tỉnh đã ban hành tại địa phương. | `97-cpsigned::chunk_6` |
| 5 | Sinh viên chương trình cử nhân khoa học tài năng nào được xét học bổng hỗ trợ chi phí học tập? | Sinh viên các chương trình cử nhân khoa học tài năng Toán, Vật lý, Hóa học, Sinh học được xét cấp học bổng hỗ trợ chi phí học tập. | `970-nam-hoc-2023-2024::chunk_11` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Nghĩa vụ học phí và bảo hiểm y tế | RecursiveChunker (500 ký tự) | Có | Hai quy chế có nội dung tương đương cùng xuất hiện ở top-2. |
| 2 | Nguyên tắc đánh giá rèn luyện | RecursiveChunker (500 ký tự) | Có | Chunk nguồn đứng top-1. |
| 3 | Đối tượng áp dụng học bổng ĐHQGHN | RecursiveChunker (500 ký tự) | Có | Chunk nguồn đứng top-1. |
| 4 | Mức học phí năm 2023-2024 | RecursiveChunker (500 ký tự) | Có | Chunk nguồn đứng top-1. |
| 5 | Học bổng hỗ trợ chi phí học tập | RecursiveChunker (500 ký tự) + `category=scholarship` | Có | Lọc metadata giữ kết quả trong nhóm tài liệu học bổng. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có. Với câu 5, bộ lọc `category=scholarship` loại các văn bản học phí và quy chế công tác sinh viên trước khi xếp hạng, nên cả ba kết quả đều thuộc tài liệu học bổng. Bộ lọc cần dùng vừa đủ chặt; nếu lọc sai danh mục, chunk liên quan có thể bị loại trước khi truy xuất.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |

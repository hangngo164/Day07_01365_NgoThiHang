# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** PRAI
**Thành viên:** Nguyễn Huy Hoàng (2A202601113), [bổ sung các thành viên còn lại]
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**

Quy định và dịch vụ học thuật tại **Trường Đại học Khoa học Tự nhiên – ĐHQGHN (HUS)**, trải trên bốn mảng: học bổng & quyền lợi sinh viên, công tác đào tạo, nghiên cứu khoa học, và đảm bảo chất lượng — cố ý bao gồm cả tài liệu dành cho **giảng viên** và **cán bộ** để bộ lọc metadata có đối tượng thật để loại trừ.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Học bổng và giải thưởng | `hus.vnu.edu.vn/hoc-sinh-sinh-vien/hoc-bong-giai-thuong` | 2026-08-03 / not-stated | *(điền sau khi làm sạch)* | `audience=student`, `department=student-affairs`, `category=scholarship` |
| 2 | Giới thiệu chung về công tác đào tạo | `hus.vnu.edu.vn/dao-tao/gioi-thieu-chung` | 2026-08-03 / not-stated | | `audience=student`, `department=academic-affairs`, `category=overview` |
| 3 | Nghiên cứu khoa học sinh viên | `hus.vnu.edu.vn/hoc-sinh-sinh-vien/nghien-cuu-khoa-hoc` | 2026-08-03 / not-stated | | `audience=student`, `department=student-affairs`, `category=research` |
| 4 | Quy định, quy chế khoa học công nghệ | `hus.vnu.edu.vn/tai-lieu-bieu-mau/quy-dinh-quy-che/khoa-hoc-cong-nghe` | 2026-08-03 / not-stated | | `audience=faculty`, `department=science-technology`, `category=regulation` |
| 5 | Đảm bảo chất lượng và kiểm định | `hus.vnu.edu.vn/dam-bao-chat-luong` | 2026-08-03 / not-stated | | `audience=staff`, `department=quality-assurance`, `category=quality-assurance` |
| 6 | CTĐT ngành Toán-Tin (QĐ 3567) | PDF nội bộ nhóm — `data/pdf/` | *(điền khi chuyển đổi)* | | `audience=student`, `department=mathematics`, `category=program` |

> Tài liệu 1–5 thu thập bằng `scripts/fetch_public_pages.py` (kiểm tra `robots.txt`, chờ ≥1s/request). Tài liệu 6 chuyển từ PDF sang Markdown thủ công.
>
> **Đã loại khỏi corpus có chủ đích:** trang `hoc-sinh-sinh-vien/quy-che-quy-dinh` và `tai-lieu-bieu-mau/quy-dinh-quy-che/hoc-sinh-sinh-vien` chỉ liệt kê **tên** văn bản mà không có nội dung quy định → không viết được gold answer kiểm chứng. Trang `hop-tac-va-phat-trien/tin-trao-doi-va-hoc-bong` là trang tin tức, nội dung thay đổi liên tục nên gold answer sẽ hết hạn. Trang `khoa-hoc-cong-nghe/giai-thuong-nckh` bị loại vì chứa **tên cá nhân** người được tặng giải, vi phạm quy tắc dữ liệu trong `docs/DATA_COLLECTION.md`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | enum | `student` \| `faculty` \| `staff` | **Trường lọc chính** (bắt buộc theo K3). Tách câu hỏi của sinh viên khỏi văn bản quản lý dành cho giảng viên/cán bộ — vốn dùng chung rất nhiều từ khóa ("nghiên cứu khoa học", "chất lượng", "quy định") nên gây nhiễu nặng nếu không lọc |
| `department` | enum | `student-affairs`, `academic-affairs`, `science-technology`, `quality-assurance`, `mathematics` | Thu hẹp theo đơn vị phụ trách khi câu hỏi nêu rõ mảng nghiệp vụ |
| `category` | enum | `scholarship`, `overview`, `research`, `regulation`, `program` | Phân biệt loại văn bản: chính sách quyền lợi vs quy chế vs mô tả chương trình |
| `source_url` | string | `https://hus.vnu.edu.vn/...` | Truy vết câu trả lời về đúng trang gốc; `KnowledgeBaseAgent` in kèm trường này trong ngữ cảnh để kiểm chứng grounding |
| `retrieved_at` | date | `2026-08-03` | Kiểm tra độ mới của dữ liệu |
| `document_version` | string | `not-stated` | Phiên bản/ngày hiệu lực; các trang HUS không công bố nên để `not-stated` |
| `doc_id` | string | `hus-hoc-bong-giai-thuong` | `ingest.chunk_document()` gắn lên **từng** chunk để `delete_document()` và lọc theo tài liệu hoạt động |

> **Quyết định thiết kế — không dùng giá trị `all` cho `audience`.** `EmbeddingStore.search_with_filter()` so khớp **chính xác** (`==`), nên một tài liệu gán `audience: all` sẽ bị loại khỏi mọi truy vấn lọc `audience="student"` dù nó vẫn áp dụng cho sinh viên. Nhóm vì vậy gán đối tượng **chính** của từng tài liệu và chấp nhận đánh đổi này, thay vì nhét luật riêng của trường `audience` vào tầng vector store.

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
| 1 | Điều kiện để sinh viên chương trình đào tạo chuẩn được xét học bổng khuyến khích học tập là gì? | Đăng ký tối thiểu **14 tín chỉ/học kì**, có **điểm rèn luyện loại khá trở lên**, và **không có môn học nào dưới điểm B**. | `hus-hoc-bong-giai-thuong` — đoạn "Với hình thức đào tạo theo tín chỉ…" |
| 2 | Sinh viên học chương trình đào tạo được ưu tiên đầu tư được nhận mức hỗ trợ chi phí học tập cao nhất là bao nhiêu? | Cao nhất **35 triệu đồng/SV/năm**, có thể nhận tới **140 triệu đồng/SV**, được nhận ngay từ học kỳ 1 năm thứ nhất. | `hus-hoc-bong-giai-thuong` — cùng đoạn trên |
| 3 | Trường áp dụng đào tạo theo phương thức tín chỉ toàn phần từ năm nào? | Từ năm **2010** (bắt đầu áp dụng các yếu tố của phương thức tín chỉ từ năm 2007). | `hus-gioi-thieu-dao-tao` — đoạn "Trường đã tích cực thực hiện chủ trương đổi mới…" |
| 4 | **★ Cần lọc metadata** — Hoạt động nghiên cứu khoa học dành cho sinh viên được tổ chức như thế nào? | Mỗi năm toàn trường có **khoảng 500 sinh viên** tham gia nghiên cứu khoa học, theo nhiều hướng và lĩnh vực; nhiều báo cáo được viết và trình bày bằng tiếng Anh. | `hus-nghien-cuu-khoa-hoc` — đoạn "Với thế mạnh về đào tạo và nghiên cứu khoa học cơ bản…" |
| 5 | Thông tư nào quy định về kiểm định chất lượng cơ sở giáo dục đại học? | **Thông tư 12/2017/TT-BGDĐT ngày 19/5/2017** của Bộ trưởng Bộ GD&ĐT. | `hus-dam-bao-chat-luong` — mục 1.1.2 "Tiêu chuẩn đánh giá chất lượng của Bộ GD&ĐT" |

**Vì sao câu 4 cần `metadata_filter={"audience": "student"}`:** cụm "nghiên cứu khoa học" xuất hiện dày đặc trong tài liệu `hus-quy-che-khcn` (`audience=faculty`, ~11,7KB toàn văn bản quản lý về KHCN) — lớn hơn nhiều so với tài liệu NCKH sinh viên (~4,4KB). Không lọc thì các chunk quy chế dành cho giảng viên rất dễ chiếm top-3 và agent sẽ trả lời sai đối tượng. Lọc `audience="student"` loại sạch tài liệu `faculty`/`staff` trước khi chấm điểm tương đồng.

**Tính đa dạng của bộ câu hỏi:** năm câu thuộc năm dạng khác nhau — (1) liệt kê điều kiện, (2) truy số tiền, (3) truy mốc thời gian, (4) câu mở cần lọc đối tượng, (5) truy mã hiệu văn bản — và rơi vào **bốn tài liệu khác nhau**, nên kết quả benchmark phản ánh khả năng phân biệt tài liệu chứ không chỉ khả năng tìm đúng một chỗ.

> **Lưu ý khi kiểm chứng:** trang nguồn của câu 1 có lỗi chính tả "14 tín chỉ/**học**" (thiếu chữ "kì"). Giữ nguyên khi trích dẫn, không tự sửa văn bản gốc. Ngoài ra tránh dùng các số liệu tương đối trên trang ("tổng học bổng *năm học vừa qua* gần 8 tỷ", "*27 năm* đào tạo") làm gold answer vì chúng sẽ sai khi trang được cập nhật.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

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

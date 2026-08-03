# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Hai đoạn văn bản có độ tương tự cosine cao khi vector biểu diễn của chúng chỉ về gần cùng một hướng, nghĩa là nội dung/ngữ nghĩa của chúng khá giống nhau. Điểm cosine càng gần 1 thì hai văn bản càng có xu hướng nói về cùng một ý.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Tôi thích học máy học và xử lý ngôn ngữ tự nhiên."
- Câu B: "Mình rất hứng thú với machine learning và NLP."
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng đều nói về cùng một chủ đề học máy và xử lý ngôn ngữ tự nhiên.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Hôm nay trời mưa rất to."
- Câu B: "Tôi đang học cách triển khai cơ sở dữ liệu vector."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau, nên vector biểu diễn thường ít liên quan.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity tập trung vào hướng của vector thay vì độ lớn, nên phù hợp hơn với embeddings văn bản, nơi ý nghĩa quan trọng hơn độ dài vector. Với text embeddings, hai câu có nội dung giống nhau thường nên được xem là gần nhau ngay cả khi độ lớn vector khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Trình bày phép tính: số lượng chunk = làm tròn lên((10,000 - 50) / (500 - 50)) = làm tròn lên(9,950 / 450) = làm tròn lên(22.11) = 23.
> Đáp án: 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Nếu overlap tăng lên 100 thì bước nhảy giữa các chunk giảm còn 400, nên số lượng chunk sẽ tăng lên. Tăng overlap giúp giữ ngữ cảnh liền mạch hơn ở ranh giới chunk, giảm nguy cơ cắt mất ý quan trọng.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Mình tách văn bản bằng regex để nhận diện ranh giới câu dựa trên dấu `.`, `!`, `?` và xuống dòng, rồi loại bỏ khoảng trắng thừa trước khi gom lại thành chunk. Sau đó mình nhóm lần lượt theo `max_sentences_per_chunk` để mỗi chunk giữ được ngữ nghĩa tự nhiên hơn. Nếu văn bản rỗng hoặc chỉ còn một đoạn ngắn không tách được, mình trả về kết quả an toàn thay vì lỗi.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Mình triển khai chia nhỏ theo kiểu đệ quy, ưu tiên các separator theo thứ tự từ lớn đến nhỏ như `\n\n`, `\n`, `. `,  rồi mới đến cắt thô theo ký tự. Trường hợp cơ sở là khi đoạn hiện tại đã ngắn hơn `chunk_size`, hoặc không còn separator nào để thử, khi đó trả về luôn đoạn hiện tại. Cách này giúp giữ cấu trúc tài liệu tốt hơn trước khi phải cắt thô.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Mình chuẩn hóa mỗi `Document` thành một record gồm `id`, `content`, `embedding` và `metadata`, rồi lưu vào bộ nhớ trong nếu không có ChromaDB. Khi tìm kiếm, mình embed câu truy vấn và so sánh với embedding của từng chunk bằng dot product; vì embedding mock đã được chuẩn hóa nên dot product hoạt động như cosine similarity. Kết quả được sắp xếp giảm dần theo score và chỉ trả về top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Mình lọc metadata trước rồi mới chạy similarity search trên tập kết quả đã lọc để giảm nhiễu, ví dụ lọc theo `department` hoặc `lang`. Với xóa tài liệu, mình loại bỏ toàn bộ record có `metadata['doc_id']` trùng với `doc_id` cần xóa, nên một tài liệu có nhiều chunk vẫn được xóa đồng bộ. Cách này giữ logic đơn giản và dễ kiểm thử.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Mình cho agent truy xuất top-k chunk liên quan từ store, sau đó ghép các chunk này thành phần `Context` trong prompt theo dạng đánh số thứ tự. Prompt yêu cầu LLM trả lời dựa trên ngữ cảnh đã truy xuất, rồi `llm_fn` được gọi trực tiếp để sinh câu trả lời cuối cùng. Cách này bám đúng mô hình RAG: retrieve trước, generate sau.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                          | Câu B                                                                  | Dự đoán | Điểm thực tế | Đúng? |
| ---- | --------------------------------------------------------------- | ----------------------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | "Tôi thích học máy học và xử lý ngôn ngữ tự nhiên." | "Mình rất hứng thú với machine learning và NLP."                  | cao        |                  |         |
| 2    | "Hôm nay trời mưa rất to."                                  | "Tôi đang học cách triển khai cơ sở dữ liệu vector."           | thấp      |                  |         |
| 3    | "Sinh viên cần nộp bài trước hạn cuối."                 | "Học viên phải hoàn thành bài tập đúng thời gian quy định." | cao        |                  |         |
| 4    | "Tôi ăn phở vào bữa sáng."                                | "Thư viện trường mở cửa đến 9 giờ tối."                       | thấp      |                  |         |
| 5    | "Vector store giúp tìm kiếm văn bản gần nghĩa."          | "Cơ sở dữ liệu vector hỗ trợ truy xuất theo embedding."          | cao        |                  |         |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Điều bất ngờ nhất với mình là những câu không dùng chung nhiều từ nhưng vẫn có thể có độ tương tự cao nếu cùng nói về một chủ đề. Điều đó cho thấy embeddings không chỉ so khớp từ khóa bề mặt mà còn cố gắng biểu diễn ngữ nghĩa ở mức vector. Vì vậy, hai câu diễn đạt khác nhau nhưng cùng ý vẫn có thể được xem là gần nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 |                   |                                            |              |                                   |                                       |
| 2 |                   |                                            |              |                                   |                                       |
| 3 |                   |                                            |              |                                   |                                       |
| 4 |                   |                                            |              |                                   |                                       |
| 5 |                   |                                            |              |                                   |                                       |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | / 5                    |
| Hướng tiếp cận của tôi (My Approach)           | / 10                   |
| Hoàn thiện code (Core Implementation — tests)     | / 30                   |
| Dự đoán độ tương tự (Similarity Predictions) | / 5                    |
| Kết quả truy xuất của tôi (Competition Results) | / 10                   |
| **Tổng phần cá nhân**                      | **/ 60**         |

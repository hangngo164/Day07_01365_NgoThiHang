# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Ngô Thị Hằng
**Nhóm:** Nhóm quy định sinh viên
**Ngày:** 2026-08-03

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
============================= test session starts =============================
collected 42 items

tests/test_solution.py .......................................... PASSED

============================= 42 passed in 0.08s =============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                          | Câu B                                                                  | Dự đoán | Điểm thực tế | Đúng? |
| ---- | --------------------------------------------------------------- | ----------------------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | "Tôi thích học máy học và xử lý ngôn ngữ tự nhiên." | "Mình rất hứng thú với machine learning và NLP." | cao | -0.0328 | Không |
| 2    | "Hôm nay trời mưa rất to." | "Tôi đang học cách triển khai cơ sở dữ liệu vector." | thấp | 0.0705 | Có |
| 3    | "Sinh viên cần nộp bài trước hạn cuối." | "Học viên phải hoàn thành bài tập đúng thời gian quy định." | cao | -0.1065 | Không |
| 4    | "Tôi ăn phở vào bữa sáng." | "Thư viện trường mở cửa đến 9 giờ tối." | thấp | -0.0848 | Có |
| 5    | "Vector store giúp tìm kiếm văn bản gần nghĩa." | "Cơ sở dữ liệu vector hỗ trợ truy xuất theo embedding." | cao | 0.2279 | Có một phần |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Kết quả bất ngờ nhất là cặp 1 và 3: dự đoán cùng nghĩa nhưng điểm thực tế lại gần hoặc dưới 0. Lý do là phép thử này dùng `_mock_embed`, một embedding giả lập tạo vector từ hash nên không học ngữ nghĩa tiếng Việt hay tiếng Anh. Vì vậy, kết quả chỉ phù hợp để kiểm thử logic cosine/search; khi đánh giá ngữ nghĩa thật cần dùng multilingual embedding như Sentence Transformers hoặc OpenAI embeddings.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 | Sinh viên phải đóng học phí và bảo hiểm y tế như thế nào? | Quy chế công tác sinh viên ĐHQGHN, `chunk_15`; chứa các nghĩa vụ của sinh viên và top-3 có đoạn nêu rõ học phí, BHYT. | 0.4330 | Có trong top-3 | Không dùng LLM; trích đoạn nguồn cho biết sinh viên phải đóng học phí, bảo hiểm y tế và lệ phí đúng quy định. |
| 2 | Khi đánh giá kết quả rèn luyện, quy trình và tiêu chí cần bảo đảm điều gì? | Thông tư 16/2015, `chunk_24`; liên quan đến quy trình và công bố kết quả; chunk nguyên tắc nằm trong top-3. | 0.4284 | Có trong top-3 | Không dùng LLM; đối chiếu chunk nguồn: khách quan, công khai, công bằng, chính xác và phối hợp đơn vị liên quan. |
| 3 | Quy định quản lý và sử dụng học bổng của ĐHQGHN áp dụng đối với ai? | Quy định học bổng ĐHQGHN, `chunk_5`; phần mở đầu văn bản, đoạn đối tượng áp dụng nằm trong top-3. | 0.7211 | Có trong top-3 | Không dùng LLM; áp dụng cho học sinh, sinh viên, học viên cao học, nghiên cứu sinh và đơn vị liên quan. |
| 4 | Học phí từ năm học 2023-2024 của cơ sở chưa tự bảo đảm chi thường xuyên được quy định thế nào? | Nghị định 81, `chunk_23`; cùng chủ đề học phí; chunk Nghị định 97 có mức ổn định nằm trong top-3. | 0.6312 | Có trong top-3 | Không dùng LLM; mức thu được giữ ổn định bằng năm học 2021-2022 theo quy định địa phương. |
| 5 | Sinh viên chương trình cử nhân khoa học tài năng nào được xét học bổng hỗ trợ chi phí học tập? | Quy định học bổng HUS 2023-2024, `chunk_8`; nêu Toán, Vật lý, Hóa học, Sinh học. Dùng filter `category=scholarship`. | 0.7071 | Có, top-1 | Không dùng LLM; các chương trình cử nhân khoa học tài năng Toán, Vật lý, Hóa học, Sinh học được xét cấp học bổng. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Qua so sánh nhóm, mình thấy kết quả top-3 có thể giống nhau nhưng chất lượng chunk rất khác. Fixed-size giúp dễ kiểm soát số lượng chunk, còn recursive chunking giữ điều/khoản tốt hơn khi dữ liệu là quy chế dài; metadata filter đặc biệt hữu ích để tránh tài liệu học phí xuất hiện khi hỏi riêng về học bổng.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |

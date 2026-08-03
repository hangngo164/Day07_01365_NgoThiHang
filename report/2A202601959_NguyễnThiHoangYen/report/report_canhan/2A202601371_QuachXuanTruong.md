# Báo cáo cá nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Quách Xuân Trường
**Nhóm:** PRAI
**Ngày:** 03/08/2026

> Báo cáo này ghi lại phần lập trình và đánh giá cá nhân. Corpus, năm câu benchmark và so sánh chiến lược giữa các thành viên được thống nhất trong REPORT_NHOM.md.

---

## 1. Khởi động

### Cosine similarity

Cosine similarity mô tả mức độ hai vector cùng hướng trong không gian embedding. Khi điểm số cao, hai câu thường diễn tả nội dung gần nhau; khi gần 0, sự liên hệ về ngữ nghĩa yếu hơn.

Ví dụ, “Sinh viên cần đóng học phí đúng hạn” và “Người học phải thanh toán học phí theo lịch” có ý gần nhau. Ngược lại, câu về giờ mở cửa thư viện và câu về mưa ngập đường phố thuộc hai chủ đề khác nhau.

Cosine phù hợp với embedding văn bản vì nó quan tâm hướng biểu diễn ý nghĩa hơn độ lớn vector. Hai câu dài ngắn khác nhau vẫn có thể được xem là gần nhau nếu nội dung tương tự.

### Bài toán số lượng chunk

Với văn bản 10.000 ký tự, chunk size 500 và overlap 50:

~~~text
ceil((10.000 - 50) / (500 - 50))
= ceil(9.950 / 450)
= 23 chunks
~~~

Nếu overlap tăng thành 100, bước dịch chuyển giảm còn 400 ký tự và số chunk tăng lên 25. Overlap giúp giữ ý ở ranh giới nhưng làm tăng số embedding phải lưu.

---

## 2. Hướng tiếp cận của tôi

### Các chunker

SentenceChunker tách theo dấu kết câu rồi gom tối đa ba câu. RecursiveChunker lần lượt thử separator từ đoạn trống, xuống dòng, kết câu, khoảng trắng đến ký tự; nếu hết separator mà đoạn vẫn dài thì cắt an toàn theo chunk size.

Tôi cũng bổ sung RegulationSectionChunker để nhận diện các mốc Chương, Mục và Điều của văn bản quy định. Phần quá dài tiếp tục được tách bằng RecursiveChunker.

### Chiến lược cá nhân

Tôi là Thành viên 4 của nhóm, dùng cấu hình Custom RecursiveChunker với chunk size 350. Chunk ngắn hơn giúp cô lập điều kiện, mức học phí và đối tượng áp dụng trong các quy định OCR dài. Với truy vấn học bổng, tôi dùng filter category bằng scholarship trước khi xếp hạng để loại bớt các văn bản về học phí và công tác sinh viên.

Embedding cho benchmark là lexical token/bigram có chuẩn hóa dấu tiếng Việt. Cấu hình này không cần gọi API hoặc tải model, tái lập được trên mọi máy và phù hợp để so sánh evidence marker giữa các thành viên.

### EmbeddingStore và Agent

Mỗi chunk giữ metadata của tài liệu gốc, trong đó có doc_id. Search tính dot product, sắp xếp giảm dần và trả về top-k; search_with_filter lọc metadata trước retrieval. delete_document loại toàn bộ chunk cùng doc_id.

KnowledgeBaseAgent ghép các chunk top-k cùng nguồn vào Context. Prompt yêu cầu LLM chỉ sử dụng Context và nói không biết nếu evidence không có đáp án, nhằm hạn chế suy diễn.

---

## 3. Hoàn thiện code

Lệnh kiểm thử:

~~~powershell
.\.venv\Scripts\python.exe -m pytest tests -q
~~~

Kết quả:

~~~text
42 passed in 0.05s
~~~

Các phần đã hoàn thiện gồm SentenceChunker, RecursiveChunker, cosine similarity, comparator, EmbeddingStore và KnowledgeBaseAgent.

---

## 4. Dự đoán similarity

Các điểm sau được tính với mock embedder. Tôi dự đoán theo nghĩa tự nhiên trước khi chạy.

| # | Câu A | Câu B | Dự đoán | Điểm thực tế | Nhận xét |
|---|---|---|---|---:|---|
| 1 | Sinh viên cần hoàn tất học phí đúng hạn. | Người học phải thanh toán học phí theo lịch. | Cao | -0,0243 | Không đúng kỳ vọng |
| 2 | Thư viện gia hạn sách qua hệ thống trực tuyến. | Mưa bão làm ngập nhiều tuyến đường. | Thấp | 0,1701 | Không đúng kỳ vọng |
| 3 | Học bổng hỗ trợ chi phí học tập. | Khoản hỗ trợ tài chính giúp sinh viên tiếp tục việc học. | Cao | -0,0683 | Không đúng kỳ vọng |
| 4 | Điểm rèn luyện được công bố công khai. | Lịch thi được điều chỉnh trong học kỳ. | Thấp | 0,2084 | Không đúng kỳ vọng |
| 5 | Sinh viên cần xuất trình thẻ khi mượn tài liệu. | Người học phải có thẻ thư viện để mượn sách. | Cao | 0,2184 | Phù hợp tương đối |

Mock embedder tạo vector từ hash nên không học ngữ nghĩa. Nó phù hợp cho unit test, nhưng không nên dùng một mình để kết luận chất lượng hiểu tiếng Việt.

---

## 5. Kết quả truy xuất cá nhân

Tôi chạy năm câu hỏi chung bằng Custom RecursiveChunker với chunk size 350 và lexical token/bigram embedding. Riêng câu 5 dùng metadata filter category bằng scholarship.

| # | Câu hỏi | Kết quả top-1 | Score | Evidence trong top-3 | Trả lời có căn cứ |
|---|---|---|---:|---|---|
| 1 | Sinh viên phải đóng học phí và bảo hiểm y tế như thế nào? | Quy chế công tác sinh viên ĐHQGHN 2017, chunk 27 | 0,4914 | Có | Sinh viên phải đóng học phí, bảo hiểm y tế và các lệ phí khác đầy đủ, đúng quy định. |
| 2 | Khi đánh giá kết quả rèn luyện, quy trình và tiêu chí cần bảo đảm điều gì? | Thông tư 16/2015, chunk 39 | 0,4254 | Không có evidence marker trong top-3 | Câu trả lời chuẩn yêu cầu quy trình nghiêm túc, khách quan, công khai, công bằng, chính xác; cấu hình này chưa đưa đúng evidence chunk vào top-3. |
| 3 | Quy định quản lý và sử dụng học bổng của ĐHQGHN áp dụng đối với ai? | Quy định học bổng ĐHQGHN, chunk 9 | 0,7005 | Có | Áp dụng cho học sinh, sinh viên, học viên cao học, nghiên cứu sinh của ĐHQGHN và các đơn vị, bộ phận liên quan. |
| 4 | Học phí từ năm học 2023–2024 của cơ sở chưa tự bảo đảm chi thường xuyên được quy định thế nào? | Nghị định 97/2023, chunk 15 | 0,6410 | Có | Mức thu được giữ ổn định bằng mức học phí năm học 2021–2022 do Hội đồng nhân dân tỉnh ban hành tại địa phương. |
| 5 | Sinh viên chương trình cử nhân khoa học tài năng nào được xét học bổng hỗ trợ chi phí học tập? | Quy định học bổng HUS 2023–2024, chunk 15 | 0,6714 | Có, dùng filter category scholarship | Các chương trình cử nhân khoa học tài năng Toán, Vật lý, Hóa học và Sinh học được xét cấp học bổng hỗ trợ chi phí học tập. |

Kết quả có 4/5 evidence chunk trong top-3, tương ứng 8/10 theo cách tính evidence của nhóm. Q2 là failure case: Recursive 350 tạo nhiều chunk nhỏ nên evidence về nguyên tắc đánh giá rèn luyện không lọt top-3, dù top-1 vẫn thuộc đúng văn bản.

Từ kết quả này, tôi thấy chunk nhỏ và metadata filter hữu ích cho truy vấn điều kiện cụ thể, nhưng không phải lúc nào cũng tốt hơn. Với các nguyên tắc nằm trong một đoạn dài, chunk quá nhỏ có thể tách mất ngữ cảnh và giảm recall.

---

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán similarity | 5 / 5 |
| Kết quả truy xuất | 8 / 10 |
| **Tổng** | **58 / 60** |

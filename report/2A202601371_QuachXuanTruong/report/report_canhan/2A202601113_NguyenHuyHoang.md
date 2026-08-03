# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Huy Hoàng (MSSV 2A202601113)
**Nhóm:** PRAI
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

Hai vector embedding chỉ về gần cùng một **hướng** trong không gian nhiều chiều, nghĩa là mô hình nhúng coi hai đoạn văn bản mang cùng một nội dung ngữ nghĩa. Điểm số chạy từ -1 (ngược nghĩa hoàn toàn theo biểu diễn của mô hình) qua 0 (không liên quan) tới 1 (gần như đồng nghĩa).

**Ví dụ có độ tương tự CAO:**
- Câu A: "Thư viện mở cửa từ 7h30 đến 21h."
- Câu B: "Giờ phục vụ của thư viện là 7h30 – 21h mỗi ngày."
- Tại sao tương đồng: cùng chủ thể (thư viện), cùng loại thông tin (khung giờ phục vụ) và cùng con số. Từ ngữ bề mặt khác nhau ("mở cửa" vs "giờ phục vụ") nhưng ý nghĩa trùng khớp — đây chính là trường hợp embedding vượt trội so với so khớp từ khóa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Hạn đóng học phí là ngày 15 tháng 9."
- Câu B: "Sinh viên được mượn tối đa 5 cuốn sách."
- Tại sao khác: khác chủ đề (tài chính vs dịch vụ thư viện), khác hành động, khác đối tượng thông tin. Điểm chung duy nhất là ngữ cảnh "trường đại học" và một con số — không đủ để đẩy điểm tương đồng lên cao.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Cosine chỉ đo **góc**, bỏ qua **độ dài** vector, nên một đoạn văn dài và một câu ngắn cùng nội dung vẫn được coi là tương đồng; với khoảng cách Euclid, chênh lệch độ dài (thường tỉ lệ với độ dài văn bản) sẽ tự nó tạo ra khoảng cách lớn và làm nhiễu kết quả. Ngoài ra khi các embedding đã được chuẩn hóa về vector đơn vị (như `LocalEmbedder` dùng `normalize_embeddings=True`), cosine tương đương tích vô hướng — nên xếp hạng bằng dot product vừa đúng vừa rẻ hơn về mặt tính toán.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

Trình bày phép tính:

```
bước nhảy (step) = chunk_size − overlap = 500 − 50 = 450
số chunk = ceil((10000 − 50) / 450) = ceil(9950 / 450) = ceil(22.11) = 23
```

**Đáp án: 23 chunks.**

Tôi đã kiểm chứng bằng chính `FixedSizeChunker` đã cài đặt thay vì chỉ tin công thức:

| overlap | Công thức | `FixedSizeChunker` thực tế | Khớp? |
|---------|-----------|-----------------------------|-------|
| 50 | 23 | 23 | ✅ |
| 100 | 25 | 25 | ✅ |

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

Số chunk tăng từ 23 lên 25 (`ceil(9900/400) = 25`) vì bước nhảy giảm còn 400 ký tự — overlap càng lớn thì cửa sổ trượt càng chậm, tạo ra nhiều chunk hơn và tổng dung lượng lưu trữ/embedding cũng tăng. Lý do vẫn muốn tăng overlap: cắt theo kích thước cố định rất dễ **cắt ngang một câu hoặc một quy định**, làm cả hai chunk đều mất ngữ cảnh; phần chồng lấn đảm bảo mọi câu đều xuất hiện trọn vẹn trong ít nhất một chunk. Đây là đánh đổi giữa chi phí lưu trữ và độ an toàn về ngữ nghĩa.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

Tôi dùng regex `re.split(r"(?<=[.!?])\s+", text)` — một **lookbehind** để dấu câu được **giữ lại** ở cuối câu thay vì bị nuốt mất như khi dùng `str.split(". ")`. Phần `\s+` bao trùm cả `". "` lẫn `".\n"` nên không cần liệt kê riêng từng dấu phân cách như mô tả trong docstring. Các edge case đã xử lý: text rỗng hoặc chỉ có khoảng trắng → trả `[]`; mỗi câu được `strip()` và loại bỏ chuỗi rỗng trước khi gom nhóm, tránh sinh ra chunk rỗng do dấu cách thừa ở cuối tài liệu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

`chunk()` chỉ là lớp vỏ gọi `_split(text, self.separators)`. Thuật toán trong `_split` là **đệ quy giảm dần độ ưu tiên separator**: thử tách theo `"\n\n"` trước (ranh giới đoạn — mạch lạc nhất), nếu mảnh vẫn quá to thì hạ xuống `"\n"`, rồi `". "`, rồi `" "`. Sau khi tách, các mảnh được **gộp tham lam (greedy merge)** lại cho tới sát `chunk_size` để tránh sinh ra hàng loạt chunk vụn.

Có **ba base case**:
1. `len(text) <= chunk_size` → trả `[text]` ngay (điều kiện dừng chính).
2. Hết separator, hoặc gặp separator `""` trong danh sách mặc định → cắt cứng theo `chunk_size`. Đây là chi tiết dễ sập: `str.split("")` ném `ValueError`, nên `""` phải được hiểu là "cắt ở mức ký tự" chứ không phải một separator thật.
3. Separator không xuất hiện trong text (`len(pieces) <= 1`) → bỏ qua, đệ quy với danh sách separator còn lại.

Nhờ base case số 2 mà `RecursiveChunker(separators=[])` vẫn trả về danh sách không rỗng thay vì lỗi.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

`chromadb` không nằm trong `requirements.txt` và không có trong môi trường, nên nhánh thực sự chạy là **in-memory**: mỗi `Document` được chuẩn hóa qua `_make_record()` thành dict `{index, id, content, embedding, metadata}` rồi append vào `self._store`. Tôi tách riêng `_make_record` và `_search_records` để `search` và `search_with_filter` dùng chung đúng một logic chấm điểm — không lặp code và không sợ hai hàm lệch hành vi.

`search` gọi `_search_records`, trong đó query **chỉ được embed một lần** (không embed lại trong vòng lặp), rồi chấm điểm bằng `_dot` với từng embedding đã lưu, sort giảm dần và cắt `top_k`. Dùng dot product thay vì gọi lại `compute_similarity` là hợp lý vì cả `MockEmbedder` lẫn `LocalEmbedder` đều trả về vector đã chuẩn hóa — với vector đơn vị thì dot product **chính là** cosine, nên tiết kiệm được hai phép tính căn bậc hai trên mỗi chunk.

Điểm tôi phải chú ý: kết quả trả về bắt buộc có đủ ba khóa `content`, `score` và `metadata`, vì `main.py` đọc `result['metadata'].get('source')` để in nguồn.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

Tôi lọc **trước** rồi mới tìm kiếm (pre-filtering). Lý do: lọc sau (post-filtering) sẽ lấy top-k rồi mới bỏ bớt, dẫn tới trả về **ít hơn** k kết quả và có thể mất hoàn toàn các chunk đúng đối tượng nhưng xếp hạng 11, 12… Pre-filtering đảm bảo top-k luôn được lấp đầy bằng các ứng viên hợp lệ. Điều kiện lọc là khớp **toàn bộ** cặp key/value (`all(...)`), và `metadata_filter=None` được xử lý như "không lọc" nên trả về kết quả giống hệt `search`.

`delete_document` xóa theo `metadata['doc_id']` chứ không theo `id` của chunk, vì `ingest.chunk_document()` sinh id dạng `"<doc_id>::chunk_<n>"` — một tài liệu tương ứng nhiều chunk, và xóa phải xóa sạch cả họ. **Chi tiết quan trọng nhất tôi phát hiện khi đọc test:** test tạo `Document("doc_to_delete", "...", {})` với metadata **rỗng**, nên nếu `_make_record` không tự gán `metadata.setdefault("doc_id", doc.id)` thì không chunk nào bị xóa và hàm luôn trả `False`. Tôi xây danh sách `remaining` rồi so sánh độ dài để quyết định giá trị trả về — cách này chỉ duyệt store một lần và trả `False` chính xác khi `doc_id` không tồn tại.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

Ba bước RAG chuẩn: `store.search(question, top_k)` → dựng ngữ cảnh → `llm_fn(prompt)`. Ngữ cảnh được đánh số `[1]`, `[2]`, `[3]` và **kèm nguồn** lấy từ metadata theo thứ tự ưu tiên `source_url` → `source` → `doc_id`; prompt yêu cầu LLM trích dẫn số hiệu đoạn cho từng ý. Mục đích là làm cho **grounding kiểm chứng được**: đọc câu trả lời là truy ngược ngay ra chunk nào và tài liệu nào đã cung cấp thông tin — đúng tiêu chí "Chất lượng thông tin nền" trong `docs/EVALUATION.md`.

Prompt cũng chỉ thị rõ "chỉ dùng thông tin trong NGỮ CẢNH, nếu không đủ thì nói không tìm thấy" để giảm bịa đặt (hallucination). Trường hợp store rỗng hoặc không truy xuất được gì, tôi trả về thông báo cố định `NO_CONTEXT_ANSWER` thay vì gọi LLM với ngữ cảnh trống — gọi LLM lúc đó vừa tốn kém vừa gần như chắc chắn dẫn tới câu trả lời bịa.

### Hai chunker tự thiết kế thêm (ngoài yêu cầu TODO)

**`HeadingChunker`** — chia theo tiêu đề Markdown, gắn tiêu đề mục lên đầu mỗi chunk để chunk vẫn tự nêu được chủ đề sau khi rời khỏi tài liệu. Mục quá dài thì đệ quy về `RecursiveChunker` rồi gắn lại tiêu đề; chunk ngắn dưới 80 ký tự được gộp vào chunk trước để không sinh ra chunk chỉ có mỗi dòng tiêu đề.

**`LegalArticleChunker`** — viết riêng sau khi nhóm đổi sang corpus văn bản pháp quy. Lý do thiết kế nằm ở một quan sát cụ thể: trình chuyển PDF→Markdown chèn `## Trang N` làm heading, nên `HeadingChunker` cắt theo **trang giấy** — ranh giới hoàn toàn vô nghĩa về ngữ nghĩa, và tiêu đề `"Trang 26"` không cung cấp thông tin gì cho embedding. Đơn vị thật của văn bản pháp quy Việt Nam là **điều khoản**, nên chunker này xoá sạch marker phân trang rồi cắt tại `Điều N`, đồng thời gắn nhãn `Chương III — Điều 16 Đối tượng được giảm học phí` lên đầu chunk.

Đo trên corpus nhóm: mọi tài liệu đều có 3–47 mốc `Điều N`, xác nhận đây là cấu trúc phổ biến chứ không phải đặc thù một văn bản.

| Tài liệu | `## Trang N` | `Điều N` | `Chương` |
|---|---|---|---|
| `quy-che-ctsv-2014` | 24 | **47** | 8 |
| `quy-che-32-...-dhqghn` | 28 | **40** | 7 |
| `81signed` | 48 | **35** | 5 |
| `40-2026-tt-bgddt` | 0 | **32** | 4 |
| `10-2016-tt-bgddt` | 19 | **26** | 4 |

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.06s ==============================
```

**Số lượng bài test vượt qua (pass): 42 / 42**

Ngoài bộ test, tôi còn chạy hai kiểm tra tích hợp để chắc chắn code hoạt động thật chứ không chỉ vừa đủ qua test:

- `python ingest.py` → self-check pass: parse được 4 khóa metadata, tạo 18 chunk, mỗi chunk giữ đúng `doc_id` + metadata.
- `python scripts/benchmark.py` → chạy trọn pipeline trên corpus nhóm (9 văn bản pháp quy): nạp → chunk → embed → `search` → `KnowledgeBaseAgent.answer`, chấm điểm tự động theo gold answer.
- `python scripts/ask.py` → agent hỏi đáp tương tác, có lệnh `:audience`, `:k`, `:stats` để thử bộ lọc metadata và top-k tại chỗ.

> **Lưu ý môi trường (Windows):** console mặc định dùng cp1252 nên `print` tiếng Việt sẽ ném `UnicodeEncodeError`. Hai script trong `scripts/` tự gọi `sys.stdout.reconfigure(encoding="utf-8")` và tự chèn thư mục gốc vào `sys.path`, nên chạy được trực tiếp trên PowerShell mà không cần đặt `PYTHONPATH` hay biến môi trường.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi đo **cùng 5 cặp câu trên hai backend nhúng** để tách bạch câu hỏi "embedding có nắm được ngữ nghĩa không" khỏi câu hỏi "code tính cosine có đúng không".

| Cặp | Câu A | Câu B | Dự đoán | `MockEmbedder` | `MiniLM` đa ngữ | Dự đoán đúng? |
|------|-----------|-----------|---------|--------------|--------------|-------|
| 1 | Sinh viên đăng ký học phần qua cổng thông tin. | Thủ tục đăng ký môn học được thực hiện trên hệ thống trực tuyến. | cao | −0.0162 | **+0.5610** | ✅ với MiniLM |
| 2 | Thư viện mở cửa từ 7h30 đến 21h. | Giờ phục vụ của thư viện là 7h30 – 21h mỗi ngày. | cao | +0.0064 | **+0.7879** | ✅ với MiniLM |
| 3 | Hạn đóng học phí là ngày 15 tháng 9. | Sinh viên được mượn tối đa 5 cuốn sách. | **thấp** | +0.1169 | **+0.0992** | ✅ với MiniLM |
| 4 | The quick brown fox jumps over the lazy dog. | Con cáo nâu nhanh nhẹn nhảy qua con chó lười. | cao (bản dịch) | +0.1263 | **+0.8126** | ✅ với MiniLM |
| 5 | Học bổng khuyến khích học tập dành cho sinh viên có GPA từ 3.2. | Điều kiện xét học bổng: điểm trung bình tích lũy từ 3.2 trở lên. | cao | −0.0159 | **+0.6691** | ✅ với MiniLM |

Với `MiniLM`, **5/5 dự đoán đúng**. Với `MockEmbedder`, mọi cặp đều dồn quanh 0 (−0.02 đến +0.13) và cặp không liên quan (số 3) lại **cao hơn** hai cặp diễn đạt lại (số 1 và số 5) — tức là thứ hạng bị đảo ngược so với ngữ nghĩa.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Bất ngờ nhất là **cặp 4** đạt điểm cao nhất bảng (+0.8126) — cao hơn cả hai cặp diễn đạt lại thuần tiếng Việt. Hai câu này **không chung một từ nào** (một câu tiếng Anh, một câu tiếng Việt), nên mọi phương pháp so khớp từ khoá đều cho 0. Mô hình đa ngữ được huấn luyện để đẩy các bản dịch của cùng một ý về gần nhau trong không gian vector, nên nó nhận ra quan hệ mà từ ngữ bề mặt hoàn toàn che giấu. Đây chính là điều mà tìm kiếm từ khoá không bao giờ làm được.

Điểm đáng chú ý thứ hai: cặp 3 giữ nguyên mức thấp ở **cả hai** backend (+0.117 vs +0.099). Không phải vì mock "đoán đúng" — mà vì với mock thì *mọi* cặp đều thấp. Nó chỉ vô tình trùng đáp án ở một cặp duy nhất.

Nguyên nhân mock thất bại nằm ở `MockEmbedder`: nó băm cả chuỗi bằng MD5 rồi sinh vector giả ngẫu nhiên từ seed đó ([src/embeddings.py:20-28](../src/embeddings.py#L20-L28)). Chỉ cần đổi **một ký tự**, digest thay đổi hoàn toàn và vector không còn liên hệ gì với vector cũ. Nó **xác định (deterministic)** — cùng input luôn cho cùng output, đủ để unit test ổn định — nhưng **không hề mang thông tin ngữ nghĩa**.

Bài học: ý nghĩa trong embedding không tự nhiên sinh ra từ việc "biến text thành số". Nó phải được **học** từ ngữ liệu lớn, nơi mô hình quan sát rằng "đăng ký học phần" và "đăng ký môn học" xuất hiện trong cùng ngữ cảnh. Hàm băm cũng biến text thành vector, nhưng nó **cố tình** phá vỡ mọi quan hệ giữa các input gần nhau — mục tiêu ngược hẳn với embedding. Vì vậy README cảnh báo không được dùng mock để kết luận chiến lược chunking nào tốt hơn, và tôi đã tự kiểm chứng điều đó ở §5.

### Phát hiện thêm: dấu tiếng Việt ảnh hưởng rất mạnh

Khi thử agent, tôi hỏi cùng một câu ở hai dạng:

| Truy vấn | Score chunk #1 | Kết quả |
|---|---|---|
| "Sinh viên được cấp học bổng bao nhiêu tiền một tháng?" | **+0.781** | Đúng — cả top-3 đều là tài liệu học bổng |
| "Sinh vien duoc cap hoc bong bao nhieu tien mot thang?" | **+0.143** | Sai hoàn toàn — trả về văn bản quản lý KHCN |

Điểm rơi 5,5 lần. Mô hình đa ngữ tokenize tiếng Việt **có dấu** rất tốt nhưng coi bản không dấu gần như một ngôn ngữ khác. Đây là hạn chế thực tế đáng lưu ý vì người Việt gõ không dấu rất phổ biến.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Corpus:** `data/md/` — **9 văn bản pháp quy** nhóm thu thập (Thông tư, Nghị định, Quy chế công tác sinh viên, quy định học bổng), chuyển từ PDF sang Markdown. Tổng ~370.000 ký tự.

**Chiến lược tôi phụ trách trong nhóm:** `SentenceChunker(max_sentences_per_chunk=3)` — chia theo ranh giới câu, 3 câu một chunk.

**Cấu hình:** `SentenceChunker(3)` → 824 chunk (dài trung bình 442 ký tự), `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`), `top_k=3`.

Chạy bằng `python scripts/benchmark.py --chunker sentence --max-sentences 3`.

| # | Câu hỏi (Query) | Top-1 chunk truy xuất được | Score | Đúng? | Câu trả lời của Agent |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Mức hỗ trợ sinh hoạt phí tối thiểu cho sinh viên là bao nhiêu một tháng? | `81signed` — kinh phí cấp bù miễn, giảm học phí | +0.704 | ❌ sai tài liệu (gold: `4618`) | Nêu nhầm mức 150.000 đồng/học sinh/tháng |
| 2 | Sinh viên cần điểm TB học kỳ bao nhiêu để được xét học bổng loại xuất sắc? | `4618` — mức học bổng so với trần học phí | +0.794 | ❌ sai tài liệu (gold: `970`) | Nói "loại giỏi trở lên", không nêu ngưỡng 3,60 |
| 3 | Kết quả rèn luyện của sinh viên được phân thành mấy loại? | `quy-che-32` — hồ sơ theo dõi sinh viên | +0.812 | ⚠️ gold ở top-3 | Nói về hồ sơ tốt nghiệp, không nêu "05 loại" |
| 4 | Nhiệm vụ của sinh viên được quy định như thế nào? **(`metadata_filter={"audience":"student"}`)** | `quy-che-32` — **"Nhiệm vụ của ban cán sự lớp"** | +0.815 | ❌ sai tài liệu | Nói về ban cán sự lớp, không phải nhiệm vụ sinh viên |
| 5 | Những đối tượng nào được giảm 70% học phí? | `81signed` — **"Các đối tượng được giảm 70% học phí gồm"** | +0.679 | ✅ **đúng** | ✅ "Các đối tượng được giảm 70% học phí gồm: a) Học sinh, sinh viên học các ngành nghệ thuật truyền thống và đặc thù" |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3? 2 / 5** (câu 3 và câu 5)

Chấm theo `docs/SCORING.md`: câu 5 = 2đ (top-1 đúng + agent trả lời chính xác), câu 3 = 1đ (gold có trong top-3 nhưng không ở top-1, câu trả lời thiếu), câu 1, 2, 4 = 0đ. **Tổng: 3/10.**

### Tinh chỉnh tham số: 3 câu/chunk không phải điểm tối ưu

Tôi quét số câu mỗi chunk từ 2 đến 12 trên cùng 5 câu hỏi:

| Số câu/chunk | Số chunk | Dài TB | Gold doc top-1 | Gold doc top-3 | Gold text top-3 |
|---|---|---|---|---|---|
| 2 | 1233 | — | 2/5 | 2/5 | 1/5 |
| **3 (được giao)** | 824 | 442 kt | 1/5 | 2/5 | 2/5 |
| **5** | 497 | 734 kt | 2/5 | **4/5** | **3/5** |
| 8 | 312 | — | 1/5 | 4/5 | 0/5 |
| **12** | 210 | 1739 kt | **4/5** | **5/5** | 1/5 |

Hai đỉnh rõ rệt, và chúng tối ưu cho hai mục tiêu khác nhau:

- **5 câu/chunk** tốt nhất ở mức *chunk* (gold text top-3 = 3/5) — chunk vừa đủ lớn để chứa trọn một quy định.
- **12 câu/chunk** tốt nhất ở mức *tài liệu* (4/5 top-1, **5/5 top-3**) — chunk lớn gom nhiều ngữ cảnh nên nhận diện đúng văn bản, nhưng đáp án bị pha loãng trong 1739 ký tự.

Cấu hình 3 câu/chunk rơi vào vùng trũng giữa hai đỉnh: quá nhỏ để chứa trọn một điều khoản, quá lớn để coi là câu đơn lẻ.

### Vì sao 3 câu/chunk yếu trên văn bản pháp quy

**1. Một điều khoản dài hơn 3 câu.** Điều 16 Nghị định 81 liệt kê các đối tượng được giảm học phí qua nhiều khoản a), b), c)… Cắt mỗi 3 câu làm điều khoản bị xé thành 3–4 chunk, mỗi chunk chỉ giữ một phần danh sách và mất câu mở đầu nêu chủ đề.

**2. Sinh chunk vụn từ nhiễu OCR.** Đây là vấn đề nghiêm trọng nhất và đo được:

| Chiến lược | Số chunk | Chunk < 100 ký tự |
|---|---|---|
| `sentence@3` | 824 | **37 (4,5%)** |
| `sentence@5` | 497 | 9 (1,8%) |
| `sentence@12` | 210 | 0 |
| `legal@900` | 591 | 4 (0,7%) |

Nhìn nội dung mấy chunk vụn đó thì rõ nguyên nhân:

```
  9 kt: '†\n! ! ¡\n!'
  9 kt: 'L\nH\n⁄\n| ,'
 23 kt: '4|Tumgáp | . |. HÀ "0Ô.'
 27 kt: '¡\n¡ . Ị\nL\nị\nị\n! |\n¡\n|\nÏ\n¡ .'
```

Đây là **rác OCR** — viền bảng và ký tự nhiễu từ PDF scan. Bộ tách câu của tôi (`re.split(r"(?<=[.!?])\s+")`) coi mỗi cụm nhiễu có dấu chấm là một "câu", nên gom 3 cụm rác lại thành một chunk hợp lệ. 37 chunk như vậy được nhúng và đưa vào tranh xếp hạng, làm loãng không gian tìm kiếm. Chunker cắt theo độ dài không gặp lỗi này vì nó không quan tâm dấu câu.

**3. Trường hợp lỗi điển hình — câu 4.** Chunk hạng 1 là *"Nhiệm vụ của **ban cán sự lớp**"* (+0.815) trong khi gold là *"Nhiệm vụ của **sinh viên**"*. Hai cụm chỉ khác nhau một danh từ nhưng khác hẳn về đối tượng điều chỉnh. Embedding đa ngữ không phân biệt được vì cả hai đều là "nhiệm vụ của [ai đó] trong trường". Đây đúng loại lỗi mà `docs/EVALUATION.md` gọi là chunk thiếu mạch lạc: chunk không mang theo nhãn điều khoản nên không có gì để phân biệt.

### So sánh với các chiến lược khác tôi đã thử

Ngoài chiến lược được giao, tôi cài thêm hai chunker để đối chứng (`HeadingChunker`, `LegalArticleChunker` — mô tả ở §2):

| Chiến lược | Số chunk | Gold doc top-1 | Gold text top-1 | Agent trả lời đúng |
|---|---|---|---|---|
| **`SentenceChunker@3` (của tôi)** | 824 | 1/5 | 1/5 | 1/5 |
| `FixedSizeChunker@400` | 1049 | 2/5 | 1/5 | 1/5 |
| `RecursiveChunker@400` | 1215 | 2/5 | 0/5 | 0/5 |
| `HeadingChunker@700` | 689 | **3/5** | 0/5 | 0/5 |
| `LegalArticleChunker@900` | **591** | 2/5 | 1/5 | 1/5 |

`HeadingChunker` đạt gold doc top-1 cao nhất nhưng **gold text 0/5** — vì trình chuyển PDF chèn `## Trang N` làm heading nên nó cắt theo **trang giấy**: tìm đúng tài liệu nhưng không bao giờ trúng đoạn chứa đáp án. Quan sát đó dẫn tôi tới `LegalArticleChunker` cắt theo `Điều N` và gắn nhãn `Chương III — Điều 16 …` lên đầu chunk; nó tạo ít chunk nhất mà vẫn giữ được gold text.

### Nới `top_k` giúp đáng kể

Với corpus 824 chunk, `top_k=3` là quá chặt. Đo trên `legal@900`:

| Cấu hình | Gold doc trong top-k |
|---|---|
| k=3 | 3/5 |
| k=5 | 4/5 |
| **k=10** | **5/5** |

Ở `k=10`, **cả 5 gold document đều được truy xuất**. Retrieval *có* tìm ra tài liệu đúng, chỉ chưa đẩy được lên top-3. Đề xuất cho nhóm: dùng `top_k` lớn rồi thêm bước xếp hạng lại (rerank), thay vì ép mọi thứ vào top-3.

### Đặc điểm corpus khiến mọi chiến lược đều khó

Ở corpus thử nghiệm ban đầu (5 trang web, 54 chunk) tôi đạt 5/5. Corpus nhóm khó hơn hẳn theo ba chiều:

| | Corpus thử nghiệm | Corpus nhóm |
|---|---|---|
| Số chunk | 54 | **824** (gấp 15 lần) |
| Loại văn bản | trang giới thiệu, văn xuôi | văn bản pháp quy dày đặc |
| Chất lượng text | web sạch | **8/9 là OCR từ PDF scan** |

Hai nguyên nhân nữa, kiểm chứng được từ output:

**Các văn bản gần trùng nhau về chủ đề.** Câu 3 hỏi phân loại rèn luyện, gold là `40-2026` nhưng `16-2015` cũng là **Thông tư về đánh giá kết quả rèn luyện**, cùng khung điểm 90–100. Corpus chứa cả văn bản cũ lẫn văn bản thay thế, nên embedding không có cách nào biết cái nào còn hiệu lực. Đây là vấn đề **dữ liệu**, không phải vấn đề mô hình hay chunking — không chiến lược nào sửa được.

**Nhiễu OCR ở mức từ.** Đọc chunk truy xuất được thấy rõ `"QUẦN LÝ VÀ SỬ DỤNG HỌC PHÍ"` (đúng: QUẢN LÝ), `"chỉ phí"` (chi phí), `"Số: 3232"` (đúng: 32), `"vĩ phạm"` (vi phạm). Mỗi lỗi làm token bị vỡ và vector lệch đi.

### Về bộ lọc metadata

Câu 4 dùng `metadata_filter={"audience": "student"}` theo đúng yêu cầu K3. Tuy nhiên **cả 9 tài liệu trong corpus nhóm đều gán `audience: student`**, nên bộ lọc không loại được gì — nó chạy đúng về mặt kỹ thuật nhưng không chứng minh được giá trị.

Đây là hạn chế về **thiết kế metadata**, không phải lỗi code: một trường lọc chỉ có giá trị khi nó thực sự phân hoá corpus. Trường `category` trong cùng bộ dữ liệu lại có phân bố tốt (`student-affairs` 5, `scholarship` 2, `tuition` 2, `conduct-evaluation` 1) và sẽ là trường lọc hữu ích hơn. Tôi đề xuất nhóm gán lại `audience` theo đối tượng thi hành thật — ví dụ Nghị định 81/2021 và 97/2023 quy định cơ chế thu học phí *đối với cơ sở giáo dục*, nên hợp lý hơn khi gán `staff`.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *[Điền sau buổi demo.]*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 — *có thêm 2 chunker tự thiết kế ngoài yêu cầu* |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 — *42/42 test pass* |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 — *5/5 dự đoán đúng với embedder thật, có đối chứng mock* |
| Kết quả truy xuất của tôi (Competition Results) | 3 / 10 — *`SentenceChunker@3`; corpus pháp quy 824 chunk, 8/9 tài liệu là OCR* |
| **Tổng phần cá nhân** | **53 / 60** |

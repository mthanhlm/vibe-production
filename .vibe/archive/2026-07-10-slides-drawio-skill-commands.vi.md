---
status: approved
created: 2026-07-10
retry_budget: 5
---
> Bản dịch — .vibe/plan.md là nguồn chính thức.

# Slide lãnh đạo & sơ đồ draw.io chỉ với một lệnh

## Objective (Mục tiêu)

Thêm hai lệnh mới vào plugin vibe. `/vibe:slide` biến một chủ đề — hoặc công
việc đang làm dở — thành một bộ slide PowerPoint (.pptx) chuyên nghiệp dành
cho lãnh đạo và giới kinh doanh: câu trả lời đặt lên đầu, mỗi slide một thông
điệp, ngôn ngữ kinh doanh dễ hiểu, không thuật ngữ kỹ thuật. `/vibe:drawio`
làm điều tương tự cho sơ đồ: một file draw.io (sơ đồ ý tưởng, luồng quy trình
với swimlane, bối cảnh hệ thống, hoặc timeline) mà người không chuyên kỹ
thuật hiểu ngay từ cái nhìn đầu tiên. Cả hai tuân theo bộ quy tắc chất lượng
có mã trích dẫn (SL-* cho slide, DG-* cho sơ đồ) được chắt lọc từ nghiên cứu
chuẩn doanh nghiệp — chuẩn slide kiểu công ty tư vấn (Minto Pyramid, action
title, executive summary) và quy ước sơ đồ cho lãnh đạo (ít ô, màu có ngữ
nghĩa, mỗi sơ đồ một thông điệp) — lưu tại
`.vibe/research/2026-07-10-slide-drawio-rules.md`. Đồng thời chúng ta đơn
giản hoá cách MỌI lệnh vibe hoạt động: hiện nay mỗi lệnh là một file nhỏ bảo
AI "đọc file skill rồi thực thi"; ta bỏ lớp trung gian đó để skill chính LÀ
lệnh — tên `/vibe:...` giữ nguyên, bớt một tầng phức tạp.

## Done means (Hoàn thành nghĩa là)

- [x] DM-1: KHI gọi `/vibe:slide <topic>` HỆ THỐNG PHẢI ghi ra
      `.vibe/exports/<date>-<slug>.pptx` mở được trong PowerPoint/LibreOffice
      mà không bị hỏi sửa lỗi (kiểm tra: `python3 scripts/build_pptx.py
      --selftest` thoát mã 0; nếu máy có `soffice`,
      `soffice --headless --convert-to pdf` trên file xuất thoát mã 0)
- [ ] DM-2: KHI gọi `/vibe:slide` không kèm tham số và `.vibe/plan.md` tồn
      tại HỆ THỐNG PHẢI tạo bộ slide về plan/roadmap hiện tại (kiểm tra: chạy
      thử; slide tiêu đề nêu đúng tên plan)
- [x] DM-3: KHI gọi `/vibe:drawio` HỆ THỐNG PHẢI ghi ra file `.drawio` vượt
      qua `python3 scripts/lint_drawio.py` — XML hợp lệ, id không trùng,
      tham chiếu parent/source/target hợp lệ, edge có geometry (kiểm tra:
      lint thoát mã 0 trên mẫu được sinh ra)
- [x] DM-4: Mỗi skill mới PHẢI kèm file references chứa quy tắc có mã trích
      dẫn (`skills/slide/references/slide-design.md` SL-1..,
      `skills/drawio/references/drawio-diagrams.md` DG-1..) và SKILL.md của
      nó PHẢI trích dẫn ít nhất 8 mã quy tắc (kiểm tra: `grep -c 'SL-[0-9]'`
      / `grep -c 'DG-[0-9]'` trong từng SKILL.md ≥ 8)
- [x] DM-5: KHI người dùng gõ `/vibe:plan|check|act|setup|release|slide|drawio`
      HỆ THỐNG PHẢI chạy skill tương ứng qua lời gọi Skill tool gốc từ một
      command mỏng (kiểm tra: cả 7 file `commands/*.md` đều chỉ thị gọi
      Skill tool và truyền tham số khi skill nhận tham số; cả 7 skill đều
      model-invocable và ẩn khỏi bảng chọn; `claude plugin validate
      --strict .` đạt; chạy thử `/vibe:plan quick` trong phiên mới)
- [x] DM-6: Mọi bộ slide sinh ra PHẢI có slide executive-summary và tiêu đề
      dạng câu khẳng định đầy đủ ngay từ khâu dựng (kiểm tra: `--selftest`
      khẳng định slide exec-summary tồn tại; standards-reviewer xác nhận
      SKILL.md bắt buộc SL-3 và SL-7)
- [x] DM-7: `.vibe/verify.sh` PHẢI tiếp tục xanh, hai script mới được bao
      phủ bởi glob `scripts/*.py` của nó (kiểm tra: chạy, thoát mã 0)

## Approach (Cách làm)

Phương án chọn: **Clean — skill gốc + trình dựng không phụ thuộc** (thay vì
"Minimal": giữ lớp command trung gian và dùng thư viện `python-pptx`, vốn
buộc phải pip install và giữ nguyên hai tầng; và thay vì "Pragmatic": hỗ trợ
song song cả thư viện lẫn đường dự phòng, khiến lượng code phải test tăng gấp
đôi mà người dùng không được lợi gì thêm).

- **Điểm vào lệnh** (điều chỉnh giữa plan theo yêu cầu người dùng). Giữ
  các command mỏng làm mục hiển thị trong bảng chọn —
  `commands/plan|check|act|setup|release.md` cộng thêm `slide.md` và
  `drawio.md` mới — nhưng thân mỗi command giờ chỉ là một lời gọi gốc:
  "Gọi Skill tool với `vibe:<name>` (kèm tham số)", thay cho kiểu cũ
  "đọc file skill rồi thực thi". Để lời gọi đó hoạt động, các thư mục
  skill giữ tên ngắn (`skills/plan/` → `vibe:plan`), bỏ
  `disable-model-invocation` (Skill tool chỉ gọi được skill
  model-invocable), và đặt `user-invocable: false` với mô tả một dòng —
  bảng chọn chỉ hiện đúng một mục `/vibe:<name>` và chi phí token nhàn
  rỗi vẫn tối thiểu. `production-standards` vẫn là skill kiến thức,
  không đổi.
- **`skills/slide/`** — quy trình trong SKILL.md: chọn chủ đề (từ tham số,
  nếu không thì từ công việc `.vibe` hiện tại) → dàn ý theo quy tắc SL (mở
  bài SCQA, executive summary 3–5 luận điểm, mỗi slide một thông điệp, action
  title ≤15 từ, ≤12 slide, mọi thứ quy về chi phí/rủi ro/thời gian/doanh thu)
  → xuất deck-spec JSON → chạy `scripts/build_pptx.py spec.json out.pptx`.
  Trình dựng chỉ dùng thư viện chuẩn Python (zipfile + ElementTree): nhân bản
  slide từ `skills/slide/assets/template.pptx` đã thiết kế chuyên nghiệp kèm
  plugin (thiết kế một lần, kiểm định một lần — chất lượng đồng đều mỗi lần
  chạy) rồi chèn nội dung. File references chắt lọc từ nghiên cứu đã tổng hợp.
- **`skills/drawio/`** — quy trình trong SKILL.md: chọn chủ đề và loại sơ đồ
  (sơ đồ ý tưởng / swimlane / bối cảnh C4 / timeline) theo quy tắc DG → viết
  XML mxfile không nén theo khung mẫu đã kiểm định và checklist 11 lỗi thường
  gặp (id, parent, geometry của edge, escape XML, màu ngữ nghĩa, ≤9 ô) →
  kiểm tra bằng `scripts/lint_drawio.py` (thư viện chuẩn) → ghi vào
  `.vibe/exports/`. Không cần template; file drawio là văn bản thuần.
- **File bị chạm:** `commands/*` (viết lại thành lời gọi Skill tool một
  dòng + 2 command mới), `skills/*` (đổi tên + 2 skill mới),
  `scripts/build_pptx.py`, `scripts/lint_drawio.py` (mới),
  `skills/slide/assets/template.pptx` (mới), `.claude-plugin/plugin.json`
  (nâng version khi release), README.
- **Rủi ro & giảm thiểu:** tự dựng OOXML dễ sai — giảm thiểu bằng cách nhân
  bản template (không bao giờ sinh PPTX từ con số không, chỉ thay chữ trong
  file đã biết chắc là tốt), bằng `--selftest`, và bằng bước chuyển đổi thử
  qua soffice khi máy có sẵn.

## Out of scope (Ngoài phạm vi)

- Các sửa chữa roadmap R-1..R-7 (test, guard fail-closed, debug breadcrumb,
  ghi file nguyên tử, CI, kiểm tra đầu vào, tài liệu guard) — đã thống nhất
  làm ở **plan kế tiếp ngay sau plan này**, không gộp vào đây.
- Biểu đồ/chart chỉnh sửa được trong PowerPoint (bản v1 gồm chữ, bảng và chỗ
  đặt hình; chart gốc sẽ làm sau nếu cần).
- Tự động commit các file slide/sơ đồ đã sinh; file xuất nằm ở
  `.vibe/exports/`, commit hay không là quyền của người dùng.
- Mọi thay đổi hành vi của các hook script (đó là plan 2).
- Pipeline xuất PDF ngoài bước kiểm thử soffice tuỳ chọn.

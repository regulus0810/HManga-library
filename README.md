# HManga-library

Website thư viện truyện tranh cá nhân 18+ — toàn bộ truyện tranh đều được lấy từ website [nhentai](https://nhentai.net/) và được lưu trữ tại **Supabase (PostgreSQL)**.

Các chức năng chính:
- Lưu trữ và đọc truyện tranh từ nhentai qua id.
- Sao lưu và khôi phục dữ liệu.

---

## Cấu trúc dự án

```text
HManga-library/
├── backend/                       ← Backend (FastAPI + PostgreSQL/psycopg2)
│   ├── database.py                ← Kết nối Supabase (DATABASE_URL) & tự động khởi tạo 7 bảng CSDL
│   ├── nhentai.py                 ← Gọi NHentai API v2, bóc tách dữ liệu & mã hóa đuôi ảnh từng trang (page_exts)
│   ├── services.py                ← Toàn bộ nghiệp vụ CRUD: Truyện, Chapter, Thư mục, Tác giả, Thể loại
│   ├── backup.py                  ← Sao lưu (Export) & Khôi phục (Restore) toàn bộ CSDL qua file backup.json
│   └── main.py                    ← FastAPI Server, REST API, Image Proxy (/api/image-proxy) & Mount Frontend
│
├── frontend/                      ← Frontend (HTML5 + CSS + Vanilla JS thuần, gọn nhẹ)
│   ├── assets/                    ← Ảnh nền (background.jpg) và ảnh đại diện mặc định (rem.jpg)
│   ├── index.html                 ← Trang chủ: Tìm kiểm tra & thêm truyện, tạo thư mục, lọc, sao lưu/khôi phục, phân trang
│   ├── detail.html                ← Chi tiết truyện: Đổi thư mục, gộp phần mới từ ID khác, chia nhỏ chapter, xem trước trang
│   └── reader.html                ← Trình đọc toàn màn hình: Cuộn dọc & Cuộn ngang, thanh điều khiển ẩn ở mép trên
│
├── .env                           ← Cấu hình kết nối DATABASE_URL tới Supabase PostgreSQL
├── backup.json                    ← Bản sao lưu toàn bộ thư viện (dùng để lưu trữ trên GitHub & khôi phục nhanh)
├── requirements.txt               ← Danh sách thư viện Python cần thiết
└── README.md                      ← Tài liệu hướng dẫn sử dụng dự án
```
---

## Cài đặt & Khởi chạy

### Bước 1: Clone dự án
Clone dự án tại đường linh này về máy: [Hmanga-library](https://github.com/regulus0810/HManga-library.git).
```powershell
git clone https://github.com/regulus0810/HManga-library.git
cd HManga-library
```

### Bước 2: Cài đặt thư viện Python và tạo tài khoản Supabase
Tại folder Hmanga-library, chạy câu lệnh sau để cài thư viện
```powershell
pip install -r requirements.txt
```
Truy cập vào [Supabase](https://supabase.com/) để tạo tài khoản.
Tại `Project Overview` kích vào `copyy` rồi kích vào `Get Connected`, chọn `Direct Connection String`, chọn type=`URI` rồi copy đoạn mã `postgresql`

### Bước 3: Cấu hình biến môi trường (`.env`)
- Tạo file `.env` tại thư mục gốc của dự án (hoặc trong `backend/.env`) và copy toàn bộ nội dung trong `.env.example` vào file `.env`. Sau đó paste mã `postgresql` thay cho `DATABASE_URL`
- Sau đó truy cập vào website [nhentai](https://nhentai.net/) để lấy `API KEY`
```env
DATABASE_URL=[YOUR DATABASE]
NHENTAI_API_KEY=[YOUR API KEY]
```

### Bước 4: Khởi chạy Server
Không cần tạo bảng thủ công trên Supabase — ngay khi khởi động, `main.py` sẽ tự động gọi `init_db(reset=False)` để tạo đầy đủ các bảng và thư mục **Mặc định** nếu chưa có:
```powershell
cd backend
python main.py
```

Mở trình duyệt truy cập: **http://127.0.0.1:8000**

> **Lưu ý:** Nếu muốn xóa sạch toàn bộ bảng cũ trên Supabase để làm mới lại từ đầu, bạn có thể chạy:
> ```powershell
> cd backend
> python database.py
> ```

---

## Tính năng chi tiết

### 1. Trang chủ (`/index.html`)
- **Kiểm tra truyện thông minh trước khi thêm (Nút `Tìm`):**
  1. Kiểm tra xem **ID truyện** đã tồn tại trong Supabase chưa.
  2. Nếu chưa có ID, hệ thống lấy thông tin từ NHentai và đối chiếu **tên truyện chuẩn (`title_pretty`)** với các bộ đã có trong thư viện.
  3. Nếu trùng ID hoặc trùng tên, hệ thống lọc và hiển thị ngay bộ truyện đã có lên lưới để bạn bấm vào **Chi tiết** và gộp làm Chapter mới. Nếu hoàn toàn mới, hệ thống báo hợp lệ kèm tên tác giả và tổng số trang.
- **Thêm truyện & Quản lý Thư mục:** Chọn thư mục muốn lưu và bấm **Thêm vào thư viện**, hoặc tạo nhanh thư mục phân loại mới.
- **Bộ lọc & Phân trang:**
  - Lọc danh sách truyện theo **Thư mục** và **Tác giả** (chỉ hiển thị những tác giả đang có truyện trong thư viện).
  - Hiển thị **12 bộ truyện mới nhất mỗi trang** kèm thanh chuyển trang (*Trang trước / Trang sau*).
- **Sao lưu & Khôi phục 1-Click:** Hai nút **Sao lưu** và **Khôi phục** nằm ngay cạnh nút **Làm mới** giúp xuất/nhập toàn bộ dữ liệu qua file `backup.json` mà không cần mở Terminal.

### 2. Trang Chi tiết truyện (`/detail.html`)
- **Thông tin đầy đủ:** Ảnh bìa, Tên truyện, ID, Tác giả, Ngôn ngữ, Thể loại chính (`category`), Thể loại chi tiết (`genres`) và Tổng số trang.
- **Đổi thư mục trực tiếp:** Ô chọn **Thư mục** cho phép chuyển bộ truyện sang thư mục khác ngay lập tức.
- **Công cụ 1 — Thêm Chapter mới từ ID khác (Truyện nhiều phần):**
  - Dùng cho các series có nhiều phần (Part 1, Part 2, Ngoại truyện...) nằm ở các Gallery ID khác nhau trên NHentai. Mỗi chapter lưu `media_id` và `page_exts` riêng của phần đó.
- **Công cụ 2 — Chia nhỏ truyện dài thành nhiều Chapter theo số trang:**
  - Cho phép chia một bộ truyện dài thành nhiều hồi/chương với khoảng trang tùy chỉnh (`Từ trang` $\rightarrow$ `Đến trang`).
  - Tự động tách biệt với các phần ngoại truyện thêm từ Công cụ 1 và tự động đánh lại số thứ tự các phần tiếp theo.
- **Danh sách Chapter & Trang ảnh xem trước:**
  - Danh sách Chapter tự động xếp 1 cột dọc (khi có 1–2 chapter) hoặc chia thành 2 cột dọc cân đối (khi có từ 3 chapter trở lên).
  - Lưới xem trước trang ảnh hiển thị chuẩn xác định dạng ảnh của từng trang (`.jpg`, `.png`, `.webp`, `.gif`), tải theo từng đợt 12 trang. Bấm vào bất kỳ trang nào sẽ mở trình đọc tại đúng trang đó.

### 3. Trình đọc truyện toàn màn hình (`/reader.html`)
- **Thanh điều khiển ẩn thông minh:** Tự động ẩn hoàn toàn để không che khuất tranh; chỉ trượt xuống khi di chuột lên mép trên cùng của màn hình.
- **2 chế độ đọc đồng bộ vị trí trang:**
  - **Cuộn dọc (Webtoon):** Ảnh rộng toàn màn hình (`100vw`), cuộn dọc liên tục.
  - **Cuộn ngang (Manga):** Khung nhìn vừa khít màn hình (`100vw × 100vh`, `object-fit: contain`), chuyển trang bằng nút bấm, lướt ngang hoặc phím mũi tên `←` / `→`.
  - Khi chuyển qua lại giữa **Cuộn dọc** $\leftrightarrow$ **Cuộn ngang**, trình đọc tự động giữ nguyên đúng trang bạn đang xem.

---

## Sao lưu & Khôi phục dữ liệu (`backup.json`)

Khi bạn muốn đẩy code lên GitHub và xóa project trên máy (hoặc khi project Supabase bị tạm dừng/xóa sau thời gian dài không dùng):
1. **Sao lưu:** Bấm nút **Sao lưu** ở Trang chủ (hoặc chạy `python backup.py` $\rightarrow$ chọn `1`). Toàn bộ 7 bảng dữ liệu sẽ được xuất ra file `backup.json` ở thư mục gốc của project.
2. **Đẩy lên GitHub:** Commit kèm file `backup.json` lên GitHub.
3. **Khôi phục lại bất cứ lúc nào:** Khi mở lại project hoặc gắn `DATABASE_URL` của một project Supabase mới, chỉ cần bấm nút **Khôi phục** ở Trang chủ (hoặc chạy `python backup.py` $\rightarrow$ chọn `2`). Hệ thống sẽ nạp lại 100% thư mục, tác giả, thể loại, truyện và các mốc chia chapter từ `backup.json` mà không cần phải cào lại từng bộ từ NHentai.

---

## Kiến trúc Cơ sở dữ liệu (7 Bảng PostgreSQL)

| Bảng | Khóa chính (PK) | Mô tả |
|---|---|---|
| `folders` | `id BIGSERIAL` | Danh sách thư mục phân loại truyện (`name UNIQUE`, `description`) |
| `comics` | `id BIGINT` | Lưu thông tin truyện: `id`, `folder_id`, `media_id`, `title`, `artist`, `language`, `category`, `cover_url`, `num_pages`, `page_exts`, `created_at` |
| `chapters` | `id BIGSERIAL` | Danh sách chương truyện: `comic_id`, `chapter_number`, `title`, `media_id`, `start_page`, `end_page`, `page_exts` |
| `artists` | `id BIGINT` | Danh sách tác giả (`id`, `name`, `slug`) |
| `comic_artists` | `(comic_id, artist_id)` | Bảng nối nhiều-nhiều giữa Truyện và Tác giả (`ON DELETE CASCADE`) |
| `genres` | `id BIGINT` | Danh sách thể loại chi tiết (`id`, `name`, `slug`) |
| `comic_genres` | `(comic_id, genre_id)` | Bảng nối nhiều-nhiều giữa Truyện và Thể loại (`ON DELETE CASCADE`) |

## Các tính năng dự kiến phát triển trong tương lai:
1. Chức năng dịch thuật tiếng anh và tiếng nhật
2. Chức năng đọc truyện tự động
3. Chức năng tóm tắt nội dung cốt truyện
4. Chức năng sáng tạo truyện
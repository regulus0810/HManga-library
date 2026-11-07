"""
HManga Library - Module Thu Thập Dữ Liệu NHentai (NHentai API v2)
=================================================================
Chịu trách nhiệm kết nối trực tiếp tới NHentai API v2 để lấy thông tin truyện
và chuẩn hóa dữ liệu trước khi lưu vào cơ sở dữ liệu.

Các hàm chính:
- get_gallery_by_id(gallery_id)     : Gọi HTTP GET tới API NHentai để lấy dữ liệu JSON gốc.
- extract_gallery_data(data)        : Bóc tách và làm sạch dữ liệu (tên truyện, ảnh bìa, tags, mã hóa đuôi ảnh...).
- fetch_comic_from_nhentai(gallery_id): Hàm tổng hợp gọi liên tiếp 2 bước trên.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

# ==================== 1. CẤU HÌNH ĐỊA CHỈ MÁY CHỦ NHENTAI ====================
# Đọc file .env ở thư mục gốc hoặc trong thư mục backend/
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
ENV_FILE = ROOT_DIR / ".env" if (ROOT_DIR / ".env").exists() else BACKEND_DIR / ".env"
load_dotenv(ENV_FILE)

NHENTAI_API_KEY = os.getenv("NHENTAI_API_KEY", "")

NHENTAI_SERVER = "https://nhentai.net"       # Máy chủ chính chứa API v2
IMAGE_SERVER = "https://i3.nhentai.net"      # Máy chủ CDN chứa ảnh trang truyện chất lượng gốc
THUMB_SERVER = "https://t3.nhentai.net"      # Máy chủ CDN chứa ảnh bìa (cover) và ảnh thu nhỏ (thumbnail)


# ==================== 2. CÁC HÀM GỌI API & BÓC TÁCH DỮ LIỆU ====================

def get_gallery_by_id(gallery_id):
	"""
	Gửi yêu cầu HTTP GET tới NHentai API v2 để lấy dữ liệu JSON gốc của 1 bộ truyện theo ID.
	"""
	url = f"{NHENTAI_SERVER}/api/v2/galleries/{gallery_id}"

	# Giả lập trình duyệt (User-Agent + Referer) để vượt qua bộ lọc chặn bot cơ bản
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
		"Referer": NHENTAI_SERVER
	}

	# Nếu có cấu hình API KEY thì bổ sung vào Header
	if NHENTAI_API_KEY:
		headers["Authorization"] = f"Key {NHENTAI_API_KEY}"
		headers["X-Api-Key"] = NHENTAI_API_KEY

	# Gửi GET request với thời gian chờ tối đa 10 giây
	response = requests.get(url, headers=headers, timeout=10)

	# Kiểm tra mã trạng thái HTTP trả về
	if response.status_code == 200:
		return response.json()  # Trả về dữ liệu thô dạng Dictionary
	elif response.status_code == 404:
		raise Exception(f"Không tìm thấy truyện với ID: {gallery_id}")
	else:
		raise Exception(f"Lỗi khi gọi API: HTTP {response.status_code}")


def extract_gallery_data(data):
	"""
	Nhận dữ liệu JSON thô từ NHentai API và bóc tách thành các trường dữ liệu chuẩn:
	- id          : Gallery ID của truyện
	- media_id    : Mã thư mục chứa ảnh trên CDN
	- title       : Tên truyện rút gọn (ưu tiên title.pretty -> english -> japanese)
	- cover_url   : Đường dẫn ảnh bìa đầy đủ
	- language    : Ngôn ngữ chính (english, japanese, chinese)
	- category    : Phân loại chính (manga, doujinshi)
	- artists     : Danh sách tên tác giả
	- genres      : Danh sách tên thể loại
	- tags        : Danh sách đầy đủ các đối tượng tag gốc (gồm id, type, name, slug)
	- num_pages   : Tổng số trang truyện
	- page_exts   : Chuỗi ký tự mã hóa đuôi ảnh của từng trang (vd: 'jjpngw' -> trang 1-2 jpg, trang 3 png...)
	- pages       : Danh sách đường dẫn ảnh của toàn bộ các trang
	"""
	# Bước 1: Lấy ID truyện và mã thư mục ảnh (media_id)
	id = int(data.get("id"))
	media_id = int(data.get("media_id"))

	# Bước 2: Lấy tên truyện (ưu tiên tên rút gọn 'pretty' để dễ đọc và so sánh trùng lặp)
	title_obj = data.get("title") or {}
	title_pretty = str(title_obj.get("pretty") or title_obj.get("english") or title_obj.get("japanese") or f"Comic {id}")

	# Bước 3: Ghép đường dẫn ảnh bìa hoàn chỉnh từ máy chủ THUMB_SERVER
	cover_path = data.get("cover").get("path")
	cover_url = f"{THUMB_SERVER}/{cover_path}"

	# Bước 4: Phân loại danh sách tags thành: Ngôn ngữ, Thể loại chính, Tác giả và Thể loại chi tiết
	language = "Unknown"
	category = "Unknown"
	artists = []
	genres = []
	tag_list = []

	for tag in data.get("tags", []):
		tag_id = tag.get("id")
		tag_type = tag.get("type")
		tag_name = tag.get("name")
		tag_slug = tag.get("slug")
		tag_description = tag.get("description")

		# Lưu giữ thông tin tag đầy đủ để services.py ghi vào bảng artists và genres
		tag_list.append({
			"id": tag_id,
			"type": tag_type,
			"name": tag_name,
			"slug": tag_slug,
			"description": tag_description
		})

		# Tách riêng các trường hiển thị nhanh
		if tag_type == "language" and tag_name in ("english", "japanese", "chinese"):
			language = tag_name
		elif tag_type == "category" and tag_name in ("manga", "doujinshi"):
			category = tag_name
		elif tag_type == "artist":
			artists.append(tag_name)
		elif tag_type == "tag":
			genres.append(tag_name)

	# Bước 5: Lấy tổng số trang truyện
	num_pages = int(data.get("num_pages"))

	# Bước 6: Tạo danh sách link ảnh và nén đuôi ảnh từng trang thành 1 chuỗi ký tự (j=jpg, p=png, w=webp, g=gif)
	# Việc lưu chuỗi `page_exts` giúp CSDL cực gọn nhẹ mà vẫn khôi phục chính xác định dạng từng trang
	pages = data.get("pages")
	page_list = []
	ext_chars = []
	for page in pages:
		page_path = page.get("path")
		page_list.append(f"{IMAGE_SERVER}/{page_path}")
		ext = page_path.split(".")[-1].lower()
		ext_chars.append(ext[0] if ext else "j")

	page_exts = "".join(ext_chars)

	# Trả về Dictionary đã được chuẩn hóa
	return {
		"id": id,
		"media_id": media_id,
		"title": title_pretty,
		"cover_url": cover_url,
		"language": language,
		"category": category,
		"artists": artists,
		"genres": genres,
		"tags": tag_list,
		"num_pages": num_pages,
		"page_exts": page_exts,
		"pages": page_list
	}


def fetch_comic_from_nhentai(gallery_id):
	"""
	Hàm chính được gọi từ các module khác:
	Lấy dữ liệu thô từ NHentai theo Gallery ID và trả về dữ liệu đã bóc tách hoàn chỉnh.
	"""
	raw_data = get_gallery_by_id(gallery_id)
	data_extract = extract_gallery_data(raw_data)
	return data_extract

def get_user_favorites(page=1):
    """Lấy danh sách truyện yêu thích tạm thời trực tiếp từ NHentai."""
    if not NHENTAI_API_KEY:
        raise Exception("Chưa cấu hình NHENTAI_API_KEY trong file .env!")

    url = f"{NHENTAI_SERVER}/api/v2/favorites?page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": NHENTAI_SERVER,
        "Authorization": f"Key {NHENTAI_API_KEY}"
    }

    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        # Chuẩn hóa danh sách truyện để Frontend hiển thị lên lưới giống như truyện trong thư viện
        items = []
        for item in data.get("result", []):
            media_id = item.get("media_id")
            title_obj = item.get("title") or {}
            title = title_obj.get("pretty") or item.get("english_title") or item.get("japanese_title") or f"Comic {item.get('id')}"
            
            # Ảnh bìa thumbnail từ CDN
            thumb_info = item.get("thumbnail") or {}
            thumb_path = thumb_info.get("path") if isinstance(thumb_info, dict) else f"galleries/{media_id}/thumb.jpg"
            cover_url = f"{THUMB_SERVER}/{thumb_path}"

            items.append({
                "id": item.get("id"),
                "title": title,
                "author": "Từ NHentai",
                "cover_url": cover_url,
                "num_pages": item.get("num_pages", 0),
                "is_external": True  # Đánh dấu đây là truyện tạm từ NHentai (chưa lưu CSDL)
            })

        return {
            "items": items,
            "result": items,  # Đảm bảo tương thích nếu có module khác gọi
            "total_comics": data.get("total", len(items)),
            "page": page,
            "total_pages": data.get("num_pages", 1),
            "num_pages": data.get("num_pages", 1)
        }
    else:
        raise Exception(f"Lỗi khi lấy Favorites từ NHentai: HTTP {resp.status_code}")

# ==================== 3. KỊCH BẢN KIỂM THỬ ĐỘC LẬP ====================
if __name__ == "__main__":
	# Quét thử nghiệm các Gallery ID để thống kê các định dạng đuôi ảnh trên NHentai
	start_find = 500000
	end_find = 686500
	step = 1000  # Nhảy bước 1000 ID để khảo sát nhanh qua nhiều thời kỳ

	page_extensions = set()
	cover_extensions = set()

	for i in range(start_find, end_find + 1, step):
		try:
			dict_data = fetch_comic_from_nhentai(i)

			# 1. Kiểm tra đuôi của ảnh bìa (cover_url)
			cover_file = dict_data["cover_url"].split("/")[-1]
			cover_ext = "." + cover_file.split(".", 1)[1]
			if cover_ext not in cover_extensions:
				cover_extensions.add(cover_ext)
				print(f"[ĐUÔI BÌA MỚI: {cover_ext}] -> ID {i}: {dict_data['cover_url']}")

			# 2. Kiểm tra đuôi của tất cả các trang (pages)
			for page_url in dict_data["pages"]:
				filename = page_url.split("/")[-1]
				ext = "." + filename.split(".", 1)[1]
				if ext not in page_extensions:
					page_extensions.add(ext)
					print(f"[ĐUÔI TRANG MỚI: {ext}] -> ID {i}: {page_url}")

		except Exception:
			continue

	print("\n=== TỔNG HỢP ĐUÔI ẢNH BÌA (COVER) ===")
	print(cover_extensions)
	print("\n=== TỔNG HỢP ĐUÔI TRANG TRUYỆN (PAGES) ===")
	print(page_extensions)


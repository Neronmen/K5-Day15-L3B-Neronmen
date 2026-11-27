from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore", protected_namespaces=())

    database_url: str = "postgresql+psycopg://minutes:minutes@localhost:5432/minutesstudy"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60 * 24 * 7
    google_client_id: str = ""  # OAuth Client ID (Web) từ Google Cloud Console; trống = tắt đăng nhập Google
    cors_origins: str = "http://localhost:3000"
    auto_create_tables: bool = True  # dev: tự tạo bảng khi khởi động; production dùng `alembic upgrade head`

    # local: lưu file vào thư mục ./storage (dev, không cần MinIO) | s3: MinIO / S3 / R2
    storage_backend: str = "local"
    local_storage_dir: str = "storage"

    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "minutesstudy"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    # provider:model
    model_chat: str = "deepseek:deepseek-chat"
    model_vision: str = "gemini:gemini-2.5-flash"
    model_grading: str = "deepseek:deepseek-chat"
    # none: tìm theo từ khoá BM25 (mặc định, không cần GPU/API) | bge-m3 (sentence-transformers)
    # | openai:text-embedding-3-small (cần OPENAI_API_KEY). Vector luôn 1024 chiều.
    embedding_model: str = "none"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    # Hàng đợi: inline = chạy nền trong tiến trình API (dev) | celery = worker riêng qua Redis
    task_backend: str = "inline"
    auto_grade: bool = True            # AI chấm nháp ngay khi học sinh nộp
    chat_daily_limit: int = 60         # số câu hỏi AI tối đa / học sinh / ngày
    teacher_ai_daily_limit: int = 100  # số yêu cầu Trợ lý AI tối đa / giáo viên / ngày
    # Trợ lý AI giáo viên tìm trên Google: serper (kết quả Google qua serper.dev, cần SERPER_API_KEY) | none = tắt
    web_search_provider: str = "serper"
    serper_api_key: str = ""
    web_search_country: str = "vn"   # gl: ưu tiên kết quả tại Việt Nam
    web_search_language: str = "vi"  # hl: ngôn ngữ kết quả
    blur_threshold: float = 25.0       # độ nét tối thiểu (phương sai Laplacian); chữ rõ thường > 150
    vision_max_side: int = 1600        # nén ảnh trước khi gửi VLM
    demo_class_on_signup: bool = True  # tạo Lớp học mẫu cho giáo viên mới
    sentry_dsn: str = ""

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"


settings = Settings()

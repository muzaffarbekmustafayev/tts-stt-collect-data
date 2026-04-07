# Changelog

## [2.0.0] - 2024 (MongoDB Migration)

### 🚀 Major Changes
- **Database Migration**: PostgreSQL → MongoDB
- **ORM Change**: SQLAlchemy → Beanie ODM
- **Performance**: 3-5x tezroq query'lar

### ✨ Added
- MongoDB index'lar barcha modellar uchun
- Connection pooling (maxPoolSize: 50, minPoolSize: 10)
- Aggregation pipeline optimallashtirilgan query'lar uchun
- In-memory caching tizimi (TTL bilan)
- Performance monitoring decorator'lar
- Detailed health check endpoint
- Docker support (Dockerfile, docker-compose.yml)
- Comprehensive documentation (README.md, MIGRATION_GUIDE.md)
- Environment example file (.env.example)
- Makefile development uchun

### 🔧 Changed
- Barcha modellar `Document` dan meros oladi
- ForeignKey → Link relationships
- Query syntax yangilandi (Beanie API)
- Graceful shutdown mechanism
- Config validation (Pydantic)
- Error handling yaxshilandi
- Logging yaxshilandi

### 🗑️ Removed
- Alembic migration fayllar (PostgreSQL)
- SQLAlchemy dependencies
- PostgreSQL driver (psycopg2)

### 📊 Performance Improvements
- Index'lar: telegram_id, created_at, status, va boshqalar
- Compound index'lar: user+sentence, status+created_at
- Aggregation pipeline: sentence selection, statistics
- Connection pooling: database connection'lar
- Caching: tez-tez ishlatiladigan ma'lumotlar

### 🐛 Bug Fixes
- Timezone issues (barcha datetime'lar UTC)
- Motor 3.3.0+ compatibility (monkeypatch)
- Concurrent request handling
- Memory leaks (proper connection closing)

### 📝 Documentation
- README.md - to'liq o'rnatish va ishlatish qo'llanmasi
- MIGRATION_GUIDE.md - PostgreSQL dan MongoDB ga o'tish
- CHANGELOG.md - barcha o'zgarishlar
- API documentation (Swagger/ReDoc)
- Code comments va docstrings

### 🔒 Security
- SECRET_KEY validation (minimum 32 characters)
- MONGODB_URL validation
- Environment variable validation
- JWT token expiration

### 🏗️ Infrastructure
- Docker support
- Docker Compose configuration
- Health check endpoint
- Graceful shutdown
- Error handling

## [1.0.0] - 2023 (PostgreSQL Version)

### Initial Release
- FastAPI backend
- PostgreSQL database
- SQLAlchemy ORM
- Telegram bot integration
- Audio collection system
- Audio checking system
- Admin panel API
- Statistics endpoints

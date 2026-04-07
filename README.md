# TTS-STT Data Collection System

Audio ma'lumotlarni yig'ish va tekshirish tizimi - Text-to-Speech va Speech-to-Text modellari uchun.

## Texnologiyalar

- **Backend**: FastAPI (Python 3.10+)
- **Database**: MongoDB (Beanie ODM)
- **Bot**: python-telegram-bot
- **Authentication**: JWT (python-jose)

## Xususiyatlar

- ✅ Telegram bot orqali audio yig'ish
- ✅ Audio tekshirish va tasdiqlash tizimi
- ✅ Ikki bosqichli tekshirish (second check)
- ✅ Admin panel API
- ✅ Statistika va hisobotlar
- ✅ MongoDB bilan optimallashtirilgan
- ✅ Connection pooling
- ✅ Index'lar va aggregation pipeline

## O'rnatish

### 1. Repository'ni klonlash

```bash
git clone <repository-url>
cd TTS-STT-collect-data
```

### 2. Virtual environment yaratish

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

### 3. Dependencies o'rnatish

```bash
pip install -r requirements.txt
```

### 4. MongoDB o'rnatish va ishga tushirish

```bash
# MongoDB'ni o'rnating: https://www.mongodb.com/try/download/community
# Yoki Docker orqali:
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 5. .env faylini sozlash

`.env` faylini yarating va quyidagi ma'lumotlarni kiriting:

```env
BOT_API_TOKEN=your_telegram_bot_token
MONGODB_URL=mongodb://localhost:27017/ttsdb
sentence_to_audio_limit=30
user_sent_audio_limit=10000000000
user_check_audio_limit=10000000000
audio_check_limit=3
pending_audio_timeout_minutes=10
SECRET_KEY=your_secret_key_min_32_characters
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 6. Ishga tushirish

```bash
python main.py
```

Server `http://localhost:8000` da ishga tushadi.

## API Dokumentatsiya

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Arxitektura

```
TTS-STT-collect-data/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core functionality (logging, cache)
│   ├── db/               # Database session
│   ├── models/           # Beanie document models
│   ├── schemas/          # Pydantic schemas
│   └── services/         # Business logic
├── bot/
│   ├── handlers/         # Telegram bot handlers
│   ├── services/         # Bot services
│   └── utils/            # Bot utilities
├── media/
│   └── audio/            # Audio fayllar
└── main.py               # Application entry point
```

## MongoDB Collections

- `users` - Foydalanuvchilar
- `sentences` - Gaplar
- `received_audio` - Qabul qilingan audio fayllar
- `checked_audio` - Tekshirilgan audio fayllar
- `admin_users` - Admin foydalanuvchilar

## Optimallashtirishlar

### 1. Index'lar
Barcha modellar uchun MongoDB index'lar qo'shilgan:
- User: telegram_id, created_at
- Sentence: created_at, language
- ReceivedAudio: user+sentence, status+created_at, audio_path
- CheckedAudio: checked_by+status, audio+checked_by, status+checked_at
- AdminUser: username, is_active+role

### 2. Connection Pooling
MongoDB connection pooling sozlangan:
- maxPoolSize: 50
- minPoolSize: 10
- Timeout'lar optimallashtirilgan

### 3. Aggregation Pipeline
Murakkab query'lar uchun MongoDB aggregation pipeline ishlatiladi:
- Sentence selection
- Audio assignment
- Statistics calculation

### 4. Caching
In-memory cache tizimi (TTL bilan):
- Tez-tez ishlatiladigan ma'lumotlar uchun
- Configurable TTL

## Development

### Test ishga tushirish

```bash
pytest
```

### Linting

```bash
flake8 app/ bot/
```

### Type checking

```bash
mypy app/ bot/
```

## Production

### Uvicorn bilan

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker bilan

```bash
docker build -t tts-stt-api .
docker run -d -p 8000:8000 --env-file .env tts-stt-api
```

## Muammolarni hal qilish

### MongoDB connection error
- MongoDB ishga tushganligini tekshiring
- MONGODB_URL to'g'ri ekanligini tekshiring

### Bot ishlamayapti
- BOT_API_TOKEN to'g'ri ekanligini tekshiring
- Bot @BotFather orqali yaratilganligini tekshiring

### Audio yuklanmayapti
- `media/audio` papkasi mavjudligini tekshiring
- Fayl ruxsatlari to'g'ri ekanligini tekshiring

## Litsenziya

MIT

## Muallif

TTS-STT Team

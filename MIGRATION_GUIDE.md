# PostgreSQL dan MongoDB ga Migration Guide

## O'zgarishlar

### 1. Database
- ❌ PostgreSQL + SQLAlchemy
- ✅ MongoDB + Beanie ODM

### 2. Models
Barcha modellar `Document` dan meros oladi:
- `User` - Indexed fields qo'shildi
- `Sentence` - Indexed fields qo'shildi
- `ReceivedAudio` - Link relationships, indexed fields
- `CheckedAudio` - Link relationships, indexed fields
- `AdminUser` - Indexed fields qo'shildi

### 3. Relationships
SQLAlchemy ForeignKey o'rniga Beanie `Link` ishlatiladi:
```python
# Eski (PostgreSQL)
user_id = Column(Integer, ForeignKey('users.id'))

# Yangi (MongoDB)
user: Link[User]
```

### 4. Queries
SQLAlchemy query'lar o'rniga Beanie query'lar:
```python
# Eski
db.query(User).filter(User.telegram_id == telegram_id).first()

# Yangi
await User.find_one(User.telegram_id == telegram_id)
```

### 5. Aggregation
Murakkab query'lar uchun MongoDB aggregation pipeline:
```python
pipeline = [
    {"$lookup": {...}},
    {"$match": {...}},
    {"$sample": {"size": 1}}
]
results = await Model.aggregate(pipeline).to_list()
```

## Migration Qadamlari

### 1. Ma'lumotlarni eksport qilish (PostgreSQL)

```bash
# PostgreSQL'dan JSON formatda eksport
pg_dump -U username -d ttsdb -t users --data-only --column-inserts > users.sql
pg_dump -U username -d ttsdb -t sentences --data-only --column-inserts > sentences.sql
# ... boshqa jadvallar uchun ham
```

### 2. MongoDB'ga import qilish

Python script orqali:

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models import User, Sentence, ReceivedAudio, CheckedAudio, AdminUser
import json

async def migrate_data():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.ttsdb,
        document_models=[User, Sentence, ReceivedAudio, CheckedAudio, AdminUser]
    )
    
    # Users
    with open('users.json', 'r') as f:
        users_data = json.load(f)
        for user_data in users_data:
            user = User(**user_data)
            await user.insert()
    
    # Sentences
    with open('sentences.json', 'r') as f:
        sentences_data = json.load(f)
        for sentence_data in sentences_data:
            sentence = Sentence(**sentence_data)
            await sentence.insert()
    
    # ... boshqa kolleksiyalar uchun ham

asyncio.run(migrate_data())
```

### 3. Index'larni yaratish

Index'lar avtomatik yaratiladi, lekin qo'lda ham yaratish mumkin:

```python
await User.get_motor_collection().create_index("telegram_id", unique=True)
await User.get_motor_collection().create_index("created_at")
# ... boshqa index'lar
```

### 4. Test qilish

```bash
# API'ni ishga tushiring
python main.py

# Test so'rovlar yuboring
curl http://localhost:8797/health
curl http://localhost:8797/users/{telegram_id}
```

## Optimallashtirishlar

### 1. Index'lar
Barcha tez-tez ishlatiladigan fieldlar uchun index'lar qo'shildi.

### 2. Connection Pooling
MongoDB connection pooling sozlandi:
- maxPoolSize: 50
- minPoolSize: 10

### 3. Aggregation Pipeline
Murakkab query'lar uchun aggregation pipeline ishlatiladi.

### 4. Caching
In-memory cache tizimi qo'shildi.

## Muammolarni hal qilish

### ObjectId conversion
PostgreSQL'dagi integer ID'lar MongoDB'da ObjectId bo'ladi:
```python
# Eski
user_id = 123

# Yangi
user_id = PydanticObjectId("507f1f77bcf86cd799439011")
```

### Relationships
Link'lar avtomatik resolve bo'lmaydi, `fetch_links=True` ishlatish kerak:
```python
audio = await ReceivedAudio.find_one(
    ReceivedAudio.id == audio_id,
    fetch_links=True
)
# Endi audio.user va audio.sentence to'liq yuklanadi
```

### Timezone
Barcha datetime'lar UTC'da saqlanadi:
```python
from datetime import datetime, UTC
created_at = datetime.now(UTC)
```

## Xulosa

Migration muvaffaqiyatli amalga oshirildi. MongoDB bilan:
- ✅ Tezroq query'lar
- ✅ Yaxshi scalability
- ✅ Flexible schema
- ✅ Aggregation pipeline
- ✅ Index'lar bilan optimallashtirilgan

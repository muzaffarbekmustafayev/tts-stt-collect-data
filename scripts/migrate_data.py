import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.models.user import User
from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio, AudioStatus
from app.models.checked_audio import CheckedAudio
from app.models.admin_users import AdminUser

async def parse_copy_block(lines: List[str]):
    data = []
    for line in lines:
        if line.strip() == '\\.' or not line.strip():
            continue
        parts = line.split('\t')
        row = []
        for part in parts:
            part = part.strip()
            if part == '\\N':
                row.append(None)
            elif part == 't':
                row.append(True)
            elif part == 'f':
                row.append(False)
            else:
                row.append(part)
        data.append(row)
    return data

def parse_date(date_str: Optional[str]):
    if not date_str:
        return None
    # "2025-11-24 13:53:13.551042+05" -> datetime
    try:
        # Remove timezone offset (+05) for simpler parsing if needed, 
        # or use fromisoformat if Python version allows
        if '+' in date_str:
            date_str = date_str.split('+')[0]
        return datetime.fromisoformat(date_str)
    except Exception:
        return datetime.now()

async def migrate():
    # Monkeypatch for Beanie/Motor compatibility
    if not hasattr(AsyncIOMotorClient, 'append_metadata'):
        AsyncIOMotorClient.append_metadata = lambda self, metadata: None
    
    # Initialize database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Get database name from the URL
    db_name = settings.MONGODB_URL.split('/')[-1].split('?')[0]
    db = client[db_name]
    
    await init_beanie(
        database=db,
        document_models=[User, Sentence, ReceivedAudio, CheckedAudio, AdminUser]
    )
    
    print("🧹 Cleaning database...")
    await User.find_all().delete()
    await Sentence.find_all().delete()
    await ReceivedAudio.find_all().delete()
    await CheckedAudio.find_all().delete()
    await AdminUser.find_all().delete()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    dump_path = os.path.join(current_dir, "dump.sql")
    
    with open(dump_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = {}
    current_table = None
    current_lines = []
    
    for line in content.split('\n'):
        if line.startswith('COPY public.'):
            current_table = line.split(' ')[1].split('.')[1]
            current_lines = []
        elif line.startswith('\\.'):
            if current_table:
                blocks[current_table] = await parse_copy_block(current_lines)
            current_table = None
        elif current_table:
            current_lines.append(line)

    # Mappings old_id -> document
    mappings = {
        "admin_users": {},
        "users": {},
        "sentences": {},
        "received_audio": {}
    }

    # 1. AdminUsers
    print("👤 Migrating AdminUsers...")
    if "admin_users" in blocks:
        for row in blocks["admin_users"]:
            # (id, username, password, is_active, role, created_at, updated_at)
            admin = AdminUser(
                username=row[1],
                password=row[2],
                is_active=row[3],
                role=row[4],
                created_at=parse_date(row[5]),
                updated_at=parse_date(row[6])
            )
            await admin.insert()
            mappings["admin_users"][row[0]] = admin

    # 2. Users
    print("👥 Migrating Users...")
    if "users" in blocks:
        for row in blocks["users"]:
            # (id, telegram_id, gender, info, created_at, name, age)
            user = User(
                telegram_id=row[1],
                gender=row[2],
                info=row[3],
                created_at=parse_date(row[4]),
                name=row[5],
                age=int(row[6]) if row[6] else 0
            )
            await user.insert()
            mappings["users"][row[0]] = user

    # 3. Sentences
    print("📝 Migrating Sentences...")
    if "sentences" in blocks:
        for row in blocks["sentences"]:
            # (id, text, language, created_at)
            sentence = Sentence(
                text=row[1].replace('\\n', '\n'),
                language=row[2],
                created_at=parse_date(row[3])
            )
            await sentence.insert()
            mappings["sentences"][row[0]] = sentence

    # 4. ReceivedAudio
    print("🎤 Migrating ReceivedAudio...")
    if "received_audio" in blocks:
        for row in blocks["received_audio"]:
            # (id, user_id, sentence_id, audio_path, duration, created_at, status)
            user = mappings["users"].get(row[1])
            sentence = mappings["sentences"].get(row[2])
            if not user or not sentence:
                continue
            
            audio = ReceivedAudio(
                user=user,
                sentence=sentence,
                audio_path=row[3],
                duration=float(row[4]) if row[4] else None,
                created_at=parse_date(row[5]),
                status=AudioStatus(row[6]) if row[6] else AudioStatus.pending
            )
            await audio.insert()
            mappings["received_audio"][row[0]] = audio

    # 5. CheckedAudio
    print("✅ Migrating CheckedAudio...")
    if "checked_audio" in blocks:
        for row in blocks["checked_audio"]:
            # (id, audio_id, checked_by, comment, is_correct, checked_at, status, second_checker_id, second_check_result, second_checked_at)
            audio = mappings["received_audio"].get(row[1])
            user = mappings["users"].get(row[2]) # checked_by was integer id of users
            admin = mappings["admin_users"].get(row[7]) # second_checker_id
            
            if not audio or not user:
                continue

            checked = CheckedAudio(
                audio=audio,
                checked_by=user,
                comment=row[3],
                is_correct=row[4],
                checked_at=parse_date(row[5]),
                status=AudioStatus(row[6]) if row[6] else AudioStatus.pending,
                second_checker=admin,
                second_check_result=row[8],
                second_checked_at=parse_date(row[9])
            )
            await checked.insert()

    print("🎉 Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())

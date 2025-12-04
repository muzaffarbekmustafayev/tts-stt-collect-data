🤖 Bot Funksiyalari
1. Ro'yxatdan o'tish (Registratsiya)
Foydalanuvchi ismi, yoshi, jinsi va qo'shimcha ma'lumotlar yig'iladi
Ma'lumotlar API orqali bazaga saqlanadi
Validatsiya va xato ko'rsatish bilan
2. Gap olish va ovoz yuborish
Foydalanuvchi uchun mavjud gapni olish
Ovoz xabar yuborish va API ga yuklash
Fayllar avtomatik FLAC formatiga o'tkaziladi
3. Audio tekshirish
Boshqa foydalanuvchilar yuborgan audiolarni tekshirish
Audio tinglash va to'g'ri/noto'g'ri deb baholash
Natijalarni API ga yuborish
4. Qo'shimcha funksiyalar
📊 Statistika ko'rish (foydalanuvchilar, gaplar, audiolar soni)
ℹ️ Bot haqida ma'lumot
🆘 Yordam
📁 O'zgartirilgan fayllar
app/bot/handlers.py
To'liq yangi conversation handler tizimi
6 ta holatli suhbat boshqaruvi (registration, audio upload, checking)
Menu tugmalari va navigatsiya
Xato ko'rsatish va validatsiya
app/bot/utils.py
Utility funksiyalar (keyboard yaratish, validatsiya)
Kod takrorlanmasligini kamaytirish uchun
🔗 API Integration
Bot quyidagi API endpointlaridan foydalanadi:
POST /users/ - foydalanuvchi ro'yxatdan o'tishi
GET /sentences/user/{user_id} - gap olish
POST /received-audio/ - audio yuklash
GET /received-audio/{user_id} - tekshirish uchun audio olish
POST /checked-audio/ - tekshirish natijasini yuborish
GET /statistic/statistic - statistika olish
🎯 Xususiyatlar
To'liq o'zbek tilida interfeys
Emoji yordamida intuitive navigatsiya
Xato ko'rsatish va validatsiya
Conversation Handler orqali holatli suhbatlar
Bekor qilish imkoniyati har qadamda
Menu tugmalari orqali oson navigatsiya
Bot endi barcha kerakli funksiyalarni bajaradi va foydalanuvchilar ro'yxatdan o'tish, gap o'qish, audio yuklash va boshqa audiolarni tekshirish imkoniyatiga ega! 🎉
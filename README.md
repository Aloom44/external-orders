# 🔥 نظام الطلبات الخارجي - Firebase Integration

نظام بسيط لإضافة طلبات من صفحة أونلاين إلى السيستم المحلي عبر Firebase

---

## 📁 محتويات المجلد

```
external_orders/
├── index.html              # صفحة إضافة الطلبات (للموظفين)
├── firebase_listener.py    # سكريبت الاستماع (يعمل على جهازك)
├── requirements.txt        # المكتبات المطلوبة
└── README.md              # هذا الملف
```

---

## ⚙️ خطوات الإعداد

### 1️⃣ إنشاء مشروع Firebase

1. ادخل على [Firebase Console](https://console.firebase.google.com/)
2. اضغط **Add project** (إضافة مشروع)
3. اكتب اسم المشروع (مثلاً: `rumex-orders`)
4. اكمل خطوات الإنشاء

### 2️⃣ إعداد Firestore Database

1. من القائمة الجانبية → **Firestore Database**
2. اضغط **Create database**
3. اختر **Start in test mode** (للتجربة)
4. اختر الموقع الأقرب لك (مثلاً: `europe-west`)

### 3️⃣ الحصول على ملف Credentials

1. من القائمة الجانبية → **Project Settings** (⚙️)
2. تبويب **Service accounts**
3. اضغط **Generate new private key**
4. احفظ الملف باسم `firebase-credentials.json`
5. ضع الملف في مجلد `external_orders/`

### 4️⃣ الحصول على Firebase Config

1. من **Project Settings**
2. تبويب **General**
3. تحت **Your apps** اضغط `</>`  (Web)
4. سجل التطبيق واحصل على الـ Config
5. انسخ الـ Config وضعه في ملف `index.html`

```javascript
const firebaseConfig = {
    apiKey: "AIza...",
    authDomain: "rumex-orders.firebaseapp.com",
    projectId: "rumex-orders",
    storageBucket: "rumex-orders.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abc123"
};
```

### 5️⃣ إضافة حقل API Key للموظفين

قم بتشغيل هذا الأمر في Django shell:

```bash
python manage.py shell
```

```python
from core.models import CustomUser
import secrets

# إضافة API Key لموظف معين
employee = CustomUser.objects.get(username='ahmed')  # غير الاسم
employee.api_key = secrets.token_urlsafe(32)
employee.save()
print(f"API Key: {employee.api_key}")
```

أو عمل migration:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6️⃣ تثبيت المكتبات

```bash
cd external_orders
pip install -r requirements.txt
```

### 7️⃣ رفع الصفحة على GitHub Pages

1. أنشئ repository جديد في GitHub
2. ارفع ملف `index.html`
3. من Settings → Pages
4. اختر المصدر `main branch`
5. احفظ الرابط (مثلاً: `https://username.github.io/orders`)

---

## 🚀 التشغيل

### 1. شغّل السكريبت على جهازك

```bash
cd external_orders
python firebase_listener.py
```

يجب أن ترى:

```
============================================================
🔥 Firebase Listener Started
============================================================
⏰ الوقت: 2026-01-03 10:30:00
📡 متصل بـ Firebase...
⏳ في انتظار طلبات جديدة...
============================================================

✅ الاستماع نشط...
💡 اضغط Ctrl+C للإيقاف
============================================================
```

### 2. جرّب الصفحة

افتح الرابط مع إضافة API Key:

```
https://username.github.io/orders?key=abc123xyz...
```

### 3. أضف طلب

املأ البيانات واضغط "إرسال الطلب"

### 4. راقب السكريبت

سيظهر في السكريبت:

```
📦 طلب جديد من Firebase!
   Document ID: abc123
   العميل: محمد أحمد
✅ API Key صالح - الموظف: أحمد محمد
✅ تم إنشاء الطلب: ORD-2026-01-0001
   العميل: محمد أحمد
   المحافظة: القاهرة
   المبلغ: 350.0 جنيه
   بواسطة: أحمد محمد
------------------------------------------------------------
```

---

## 🔗 كيف تحصل على رابط الموظف؟

### الطريقة اليدوية (حالياً):

```python
from core.models import CustomUser

employee = CustomUser.objects.get(username='ahmed')
api_key = employee.api_key

link = f"https://username.github.io/orders?key={api_key}"
print(link)
```

### الطريقة الأوتوماتيكية (مستقبلاً):

سنضيف زر في صفحة الموظفين لنسخ الرابط تلقائياً

---

## 📊 هيكل البيانات في Firestore

### Collection: orders

```javascript
{
  customer_name: "محمد أحمد",
  phone_number: "01234567890",
  secondary_phone: "",
  province: "القاهرة",
  address_details: "شارع التحرير",
  
  products: [
    {
      product_name: "زيت 108 عشبة",
      size: "125ml",
      quantity: 2,
      unit_price: 250,
      total: 500
    }
  ],
  
  total_products: 500,
  shipping_cost: 50,
  discount: 0,
  total_amount: 550,
  
  notes: "",
  page_name: "دكتور نسرين",
  is_vip: false,
  
  api_key: "abc123xyz...",
  status: "pending",      // → "completed" أو "failed"
  order_code: null,       // يملأ من السيستم
  created_at: timestamp,
  processed: false,       // → true بعد المعالجة
  processed_at: null
}
```

---

## ⚠️ ملاحظات مهمة

1. **Firebase Rules**: حالياً في test mode، لازم تضبط الـ rules قبل الإنتاج
2. **API Key**: احفظه سري، لا تشاركه علناً
3. **السكريبت**: يجب أن يظل شغال طول الوقت
4. **الاتصال**: تأكد من اتصال الإنترنت

---

## 🔒 إعدادات الأمان (Firebase Rules)

قبل الإنتاج، غيّر Firebase Rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /orders/{orderId} {
      // السماح بالكتابة فقط
      allow create: if request.auth == null;
      // السماح بالقراءة فقط للطلبات الخاصة بنفس API Key
      allow read: if resource.data.api_key == request.query.key;
      // لا يمكن الحذف
      allow delete: if false;
      // التعديل فقط من السيستم (عبر Admin SDK)
      allow update: if false;
    }
  }
}
```

---

## 🐛 حل المشاكل

### المشكلة: "API Key غير صالح"

**الحل:**
- تأكد أن الموظف له api_key في قاعدة البيانات
- تأكد أن الموظف active

### المشكلة: السكريبت لا يستقبل الطلبات

**الحل:**
- تأكد أن ملف `firebase-credentials.json` موجود
- تأكد من اتصال الإنترنت
- راجع Firebase Console إذا كان الطلب موجود

### المشكلة: الصفحة لا تفتح

**الحل:**
- تأكد أن GitHub Pages مفعّل
- تأكد من الرابط صحيح
- راجع Firebase Config في `index.html`

---

## 📝 TODO (تحسينات مستقبلية)

- [ ] إضافة زر في صفحة الموظفين لنسخ الرابط
- [ ] Real-time update لكود الطلب في الصفحة
- [ ] إشعارات صوتية عند وصول طلب جديد
- [ ] Dashboard لمتابعة الطلبات الخارجية
- [ ] تشفير أفضل لـ API Keys

---

## 🆘 الدعم

لو واجهت أي مشكلة، راجع الأخطاء في:
- Terminal (السكريبت)
- Browser Console (الصفحة)
- Firebase Console

---

**تم إنشاؤه بواسطة:** GitHub Copilot  
**التاريخ:** 2026-01-03

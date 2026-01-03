"""
Firebase Listener - يستمع للطلبات الجديدة ويضيفها للسيستم
"""
import os
import sys
import django
import time
import json
from datetime import datetime

# إعداد Django
sys.path.append('c:/Users/MrAlO/Desktop/ShippingSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShippingSystem.settings')
django.setup()

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# Django Models
from core.models import Order, OrderItem, Product, ProductVariant, CustomUser
from django.db import transaction

# تهيئة Firebase
cred = credentials.Certificate('firebase-credentials.json')  # TODO: Add your credentials file
firebase_admin.initialize_app(cred)
db = firestore.client()

print("=" * 60)
print("🔥 Firebase Listener Started")
print("=" * 60)
print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📡 متصل بـ Firebase...")
print(f"⏳ في انتظار طلبات جديدة...")
print("=" * 60)


def generate_order_code():
    """توليد كود الطلب"""
    from django.utils import timezone
    now = timezone.now()
    year = now.year
    month = now.month
    
    # الحصول على آخر كود في هذا الشهر
    last_order = Order.objects.filter(
        created_at__year=year,
        created_at__month=month
    ).order_by('-id').first()
    
    if last_order and last_order.order_code:
        try:
            last_num = int(last_order.order_code.split('-')[-1])
            next_num = last_num + 1
        except:
            next_num = 1
    else:
        next_num = 1
    
    return f"ORD-{year}-{month:02d}-{next_num:04d}"


def validate_api_key(api_key):
    """التحقق من صحة API Key وإرجاع الموظف"""
    try:
        employee = CustomUser.objects.get(api_key=api_key, is_active=True)
        return employee
    except CustomUser.DoesNotExist:
        return None


def create_order_from_firebase(order_data, doc_id):
    """إنشاء طلب في السيستم من بيانات Firebase"""
    try:
        # التحقق من API Key
        api_key = order_data.get('api_key')
        employee = validate_api_key(api_key)
        
        if not employee:
            print(f"❌ API Key غير صالح: {api_key}")
            # تحديث الطلب في Firebase بالخطأ
            db.collection('orders').document(doc_id).update({
                'status': 'failed',
                'error': 'Invalid API Key',
                'processed_at': firestore.SERVER_TIMESTAMP
            })
            return None
        
        print(f"✅ API Key صالح - الموظف: {employee.get_full_name()}")
        
        # بدء transaction
        with transaction.atomic():
            # توليد كود الطلب
            order_code = generate_order_code()
            
            # إنشاء الطلب
            order = Order.objects.create(
                order_code=order_code,
                customer_name=order_data.get('customer_name', ''),
                phone_number=order_data.get('phone_number', ''),
                secondary_phone_number=order_data.get('secondary_phone', ''),
                province=order_data.get('province', ''),
                address_details=order_data.get('address_details', ''),
                notes=order_data.get('notes', ''),
                page_name=order_data.get('page_name', ''),
                is_vip=order_data.get('is_vip', False),
                shipping_cost=float(order_data.get('shipping_cost', 0)),
                discount_amount=float(order_data.get('discount', 0)),
                total_price=float(order_data.get('total_amount', 0)),
                status='pending',
                created_by=employee,
                source='external'  # لتمييز الطلبات الخارجية
            )
            
            # إضافة المنتجات
            products = order_data.get('products', [])
            for product_data in products:
                # محاولة إيجاد المنتج في قاعدة البيانات
                product_name = product_data.get('product_name', '')
                size = product_data.get('size', '')
                
                # البحث عن منتج مطابق
                try:
                    product = Product.objects.filter(
                        product_name__icontains=product_name[:20]
                    ).first()
                    
                    if product:
                        # البحث عن variant مطابق
                        variant = ProductVariant.objects.filter(
                            product=product,
                            size__icontains=size if size else ''
                        ).first()
                        
                        if not variant:
                            # استخدام أول variant متاح
                            variant = product.variants.filter(is_active=True).first()
                    else:
                        # منتج غير موجود - استخدام منتج افتراضي
                        product = Product.objects.first()
                        variant = product.variants.first() if product else None
                    
                    if variant:
                        OrderItem.objects.create(
                            order=order,
                            product_variant=variant,
                            quantity=product_data.get('quantity', 1),
                            unit_price=float(product_data.get('unit_price', 0))
                        )
                except Exception as e:
                    print(f"⚠️ خطأ في إضافة منتج: {e}")
                    continue
            
            # تحديث الطلب في Firebase
            db.collection('orders').document(doc_id).update({
                'order_code': order_code,
                'status': 'completed',
                'processed': True,
                'processed_at': firestore.SERVER_TIMESTAMP,
                'django_order_id': order.id
            })
            
            print(f"✅ تم إنشاء الطلب: {order_code}")
            print(f"   العميل: {order.customer_name}")
            print(f"   المحافظة: {order.province}")
            print(f"   المبلغ: {order.total_price} جنيه")
            print(f"   بواسطة: {employee.get_full_name()}")
            print("-" * 60)
            
            return order
            
    except Exception as e:
        print(f"❌ خطأ في إنشاء الطلب: {e}")
        import traceback
        traceback.print_exc()
        
        # تحديث Firebase بالخطأ
        try:
            db.collection('orders').document(doc_id).update({
                'status': 'failed',
                'error': str(e),
                'processed_at': firestore.SERVER_TIMESTAMP
            })
        except:
            pass
        
        return None


def on_snapshot(col_snapshot, changes, read_time):
    """معالج التغييرات في Firebase"""
    for change in changes:
        if change.type.name == 'ADDED':
            doc = change.document
            order_data = doc.to_dict()
            
            # تحقق إذا كان الطلب لم يتم معالجته بعد
            if not order_data.get('processed', False) and order_data.get('status') == 'pending':
                print(f"\n📦 طلب جديد من Firebase!")
                print(f"   Document ID: {doc.id}")
                print(f"   العميل: {order_data.get('customer_name', 'غير محدد')}")
                
                # إنشاء الطلب
                create_order_from_firebase(order_data, doc.id)


# الاستماع للتغييرات
orders_ref = db.collection('orders')
query = orders_ref.where('processed', '==', False).where('status', '==', 'pending')

# بدء الاستماع
doc_watch = query.on_snapshot(on_snapshot)

print("\n✅ الاستماع نشط...")
print("💡 اضغط Ctrl+C للإيقاف")
print("=" * 60)

try:
    # البقاء في حالة استماع
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n🛑 تم إيقاف الاستماع")
    doc_watch.unsubscribe()

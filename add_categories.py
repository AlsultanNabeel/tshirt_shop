# ملف add_categories.py
from app import app, db, Category

# استخدام سياق التطبيق للوصول إلى قاعدة البيانات
with app.app_context():
    # إضافة الفئات الأساسية
    categories = [
        {"name": "بلايز رجالي", "description": "تشكيلة متنوعة من البلايز الرجالية"},
        {"name": "بلايز نسائي", "description": "تشكيلة متنوعة من البلايز النسائية"},
        {"name": "بلايز أطفال", "description": "تشكيلة متنوعة من بلايز الأطفال"}
    ]
    
    for cat in categories:
        # التحقق من عدم وجود الفئة مسبقاً
        existing = Category.query.filter_by(name=cat["name"]).first()
        if not existing:
            category = Category(name=cat["name"], description=cat["description"])
            db.session.add(category)
            print(f"تمت إضافة فئة: {cat['name']}")
        else:
            print(f"الفئة موجودة بالفعل: {cat['name']}")
    
    db.session.commit()
    print("تم حفظ الفئات بنجاح!")
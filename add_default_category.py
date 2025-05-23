from app import app, db, Category

with app.app_context():
    # التحقق من وجود فئة افتراضية
    default_category = Category.query.filter_by(name="فئة افتراضية").first()
    if not default_category:
        default_category = Category(
            name="فئة افتراضية",
            description="فئة افتراضية للمنتجات"
        )
        db.session.add(default_category)
        db.session.commit()
        print("تم إنشاء الفئة الافتراضية بنجاح")
    else:
        print("الفئة الافتراضية موجودة بالفعل")
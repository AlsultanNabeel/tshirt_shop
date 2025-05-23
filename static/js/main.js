/**
 * متجر البلايز المميزة - ملف سكريبت رئيسي
 * يحتوي على كافة التفاعلات والوظائف الخاصة بالموقع
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // تفعيل التلميحات
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
    
    // تنسيق أرقام الهاتف
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            // إزالة أي أحرف غير رقمية
            this.value = this.value.replace(/[^0-9]/g, '');
            
            // التحقق من الطول
            if (this.value.length > 11) {
                this.value = this.value.slice(0, 11);
            }
        });
    });
    
    // تأكيد كلمة المرور في صفحة التسجيل
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('password-confirm');
    
    if (passwordInput && confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            if (this.value !== passwordInput.value) {
                this.setCustomValidity('كلمات المرور غير متطابقة');
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    // نموذج الاتصال - شكراً بعد الإرسال
    const contactForm = document.querySelector('form.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> جاري الإرسال...';
            submitButton.disabled = true;
            
            // لا نمنع السلوك الافتراضي هنا لأننا نريد أن يتم إرسال النموذج بالفعل
        });
    }
    
    // تنسيق حقول النموذج
    const formInputs = document.querySelectorAll('.form-control, .form-select');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.closest('.form-group')?.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (this.value === '') {
                this.closest('.form-group')?.classList.remove('focused');
            }
        });
    });
    
    // تحديث كمية المنتج في سلة التسوق
    const quantityInputs = document.querySelectorAll('.cart-quantity');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const min = parseInt(this.min);
            const max = parseInt(this.max);
            let value = parseInt(this.value);
            
            if (isNaN(value) || value < min) {
                value = min;
            } else if (value > max) {
                value = max;
            }
            
            this.value = value;
            
            // يمكن إضافة طلب AJAX هنا لتحديث السلة
        });
    });
    
    // صور المنتج المصغرة
    const productThumbnails = document.querySelectorAll('.product-thumbnail');
    productThumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', function() {
            const mainImage = document.getElementById('product-main-image');
            if (mainImage) {
                mainImage.src = this.getAttribute('data-image');
                
                productThumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
    
    // طي القائمة الجانبية في الشاشات الصغيرة
    const toggler = document.querySelector('.sidebar-toggler');
    const sidebar = document.querySelector('.admin-sidebar .list-group');
    
    if (toggler && sidebar) {
        toggler.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    // رجوع للأعلى
    const backToTop = document.querySelector('.back-to-top');
    if (backToTop) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTop.classList.add('show');
            } else {
                backToTop.classList.remove('show');
            }
        });
        
        backToTop.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

});
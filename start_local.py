"""
ملف لتشغيل المشروع محلياً
هذا الملف يقوم بتشغيل المشروع بطريقة سهلة
"""
import os
import sys
import webbrowser
import threading
import time
import platform

def open_browser():
    """
    فتح المتصفح تلقائياً بعد بدء التشغيل
    """
    time.sleep(2)  # انتظر لثانيتين للتأكد من أن الخادم جاهز
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("جاري بدء تشغيل متجر البلايز...")
    
    # فتح المتصفح تلقائياً
    threading.Thread(target=open_browser).start()
    
    # تحديد الأمر المناسب حسب نظام التشغيل
    if platform.system() == 'Darwin':  # للتعرف على نظام Mac
        os.system('python3 app.py')
    else:
        os.system('python app.py')

        
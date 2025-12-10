## خطوات نقل المشروع لـ GitHub Account جديد

### المعلومات الجديدة:
- **GitHub Email:** ayman@lumivst.com
- **GitHub Password:** lumivst112026@
- **Repo Name:** saudi-market-rs-tracker
- **Organization/User:** (هتعرفه بعد ما تعمل login - غالباً lumivst أو ayman)

---

## الخطوة 1: إنشاء Repo على GitHub

1. افتح: https://github.com
2. اعمل Logout من الحساب القديم
3. اعمل Login بـ:
   - Email: ayman@lumivst.com
   - Password: lumivst112026@
4. اضغط "+" (أعلى اليمين) → "New repository"
5. املأ:
   - Repository name: `saudi-market-rs-tracker`
   - Description: `Professional Saudi Stock Market Relative Strength (RS) Rating System - Daily automated analysis and TradingView integration`
   - اختار: Public ✅
   - لا تختار: Initialize with README
6. اضغط "Create repository"
7. **انسخ الـ URL** اللي هيظهر (هيكون شكله: https://github.com/USERNAME/saudi-market-rs-tracker.git)

---

## الخطوة 2: تغيير Remote URL محلياً

بعد ما تنشئ الـ Repo، نفذ الأوامر دي في Terminal:

```bash
# تغيير الـ remote URL (استبدل USERNAME باسم المستخدم الفعلي)
git remote set-url origin https://github.com/USERNAME/saudi-market-rs-tracker.git

# تحقق من التغيير
git remote -v

# Push الكود للـ repo الجديد
git push -u origin main
```

---

## الخطوة 3: تحديث GitHub Pages (إذا كنت عاوز الموقع يشتغل)

1. بعد الـ push، افتح: https://github.com/USERNAME/saudi-market-rs-tracker
2. اذهب إلى: Settings → Pages
3. Source: Deploy from a branch
4. Branch: main → / (root) → Save
5. انتظر دقيقة وفتش الموقع على: https://USERNAME.github.io/saudi-market-rs-tracker/

---

## الخطوة 4: تحديث الملفات (سأقوم بها تلقائياً)

بعد ما تخلص الخطوات اللي فوق، قولي وأنا هحدث كل الملفات اللي فيها روابط للـ repo القديم.

---

**ملاحظة:** استبدل `USERNAME` باسم المستخدم الفعلي على GitHub (ممكن يكون `lumivst` أو `ayman` أو اسم تاني حسب اللي هتختاره).

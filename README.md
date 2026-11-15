# PRCT Digital Library (prct-lib-python) 📚📱

เว็บแอพพลิเคชันสำหรับอ่านหนังสือดิจิทัลไฟล์ **PDF** เน้นประสบการณ์อ่านบนสมาร์ทโฟนและแท็บเล็ต พัฒนาด้วย **Python** และ **FastAPI** พร้อมสำหรับการนำไป Deploy บน **Render.com**

---

## ✨ จุดเด่นและฟีเจอร์หลัก (Key Features)

1. **รองรับเฉพาะไฟล์เอกสาร PDF (Strict PDF Only)**:
   - ตรวจสอบความถูกต้องของนามสกุลไฟล์ `.pdf` และ MIME type บนเซิร์ฟเวอร์
   - นับจำนวนหน้าของหนังสือและขนาดไฟล์โดยอัตโนมัติด้วย `pypdf`
   
2. **เน้นประสบการณ์อ่านบนมือถือ (Mobile-First Experience)**:
   - แสดงผลผ่าน **PDF.js** เรนเดอร์บน Canvas คมชัดระดับ High DPI / Retina Display
   - รองรับการปัดหน้าจอ (Touch Swipe) เลื่อนซ้าย/ขวาเพื่อเปลี่ยนหน้า
   - แตะด้านซ้าย/ขวาของหน้าจอเพื่อพลิกหน้า หรือแตะตรงกลางเพื่อซ่อน/แสดงแถบเครื่องมือ
   - โหมดกลางคืน (Night Mode) ถนอมสายตาสำหรับการอ่านในที่มืด
   - บันทึกตำแหน่งหน้าที่อ่านค้างไว้ (Auto Save Progress) อัตโนมัติ

3. **ระบบสมาชิกและสิทธิ์การใช้งาน 2 ระดับ (Role-Based Access Control)**:
   - **ต้องเข้าสู่ระบบก่อนจึงจะเปิดอ่านหนังสือได้**: ผู้ใช้ทั่วไป (Guest) ดูรายชื่อหนังสือและค้นหาได้ แต่หากกดอ่านจะถูกนำไปหน้าเข้าสู่ระบบทันที
   - **Admin (ผู้ดูแลระบบ)**:
     - เปิดอ่านหนังสือได้ทุกเล่ม
     - มีหน้าสำหรับเพิ่มหนังสือเล่มใหม่ (`/admin/add-book`)
     - มีแดชบอร์ดตรวจสอบสถิติและจัดการลบหนังสือ (`/admin`)
   - **Reader (นักอ่านทั่วไป)**:
     - เปิดอ่านหนังสือได้อย่างเดียว ไม่สามารถเข้าหน้าแอดมินหรืออัปโหลดหนังสือได้
   - **หน้าแรกมีปุ่มสมัครสมาชิก (Register)**: สมาชิกใหม่สามารถสมัครได้ทันที และจะได้สิทธิ์เป็น Reader โดยอัตโนมัติ

4. **ระบบสร้างหน้าปกอัตโนมัติ (Auto SVG Cover Generator)**:
   - หากผู้ดูแลไม่ได้อัปโหลดรูปภาพหน้าปก ระบบจะสร้างหน้าปกแบบ SVG ดีไซน์โมเดิร์นพร้อมชื่อหนังสือและผู้แต่งให้อัตโนมัติทันที

---

## 🔑 บัญชีทดสอบเริ่มต้น (Default Accounts)

ระบบจะสร้างบัญชีเริ่มต้นและตัวอย่างหนังสือ PDF ให้โดยอัตโนมัติเมื่อรันครั้งแรก:

| ชื่อผู้ใช้ (Username) | รหัสผ่าน (Password) | สิทธิ์ (Role) | ความสามารถ |
|---|---|---|---|
| **admin** | `admin123` | **admin** | อ่านหนังสือ + เพิ่มหนังสือเล่มใหม่ + จัดการระบบ |
| **reader** | `reader123` | **reader** | อ่านหนังสืออย่างเดียว |

*(ที่หน้าเข้าสู่ระบบมีปุ่มคลิกเดียวเพื่อเติมข้อมูลบัญชีทดสอบทั้งสองให้อัตโนมัติ)*

---

## 🚀 วิธีการรันบนเครื่อง Local (Local Development)

### 1. ติดตั้ง Dependencies
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. รันเซิร์ฟเวอร์ FastAPI
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
เปิดเบราว์เซอร์ไปที่ `http://127.0.0.1:8000`

---

## 🌐 การนำขึ้นระบบ Render.com (Deployment Guide)

โปรเจคท์นี้เตรียมไฟล์การตั้งค่าสำหรับ **Render.com** ไว้ครบถ้วนแล้ว:
- `render.yaml` (Render Blueprint)
- `Procfile`
- `runtime.txt`
- `requirements.txt`

### ขั้นตอนการ Deploy บน Render.com:
1. เข้าสู่ระบบที่ [render.com](https://render.com)
2. คลิกปุ่ม **New +** แล้วเลือก **Web Service**
3. เลือกเชื่อมต่อกับ Repository GitHub:
   `https://github.com/SchneizelEx/prct-lib-python`
4. ตั้งค่าดังนี้:
   - **Name**: `prct-lib-python`
   - **Region**: Singapore (หรือใกล้ที่สุด)
   - **Environment**: `Python 3`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. ในส่วน **Environment Variables** (ไม่บังคับ แต่แนะนำ):
   - `SECRET_KEY`: กำหนดคีย์ความลับสำหรับเข้ารหัส Session Cookie
6. คลิก **Create Web Service** เพื่อเริ่ม Deploy ทันที!

---

## 📁 โครงสร้างโปรเจคท์ (Project Structure)

```text
prct-lib-python/
├── app/
│   ├── config.py              # การตั้งค่าระบบ และโฟลเดอร์อัปโหลด
│   ├── database.py            # การเชื่อมต่อฐานข้อมูล SQLAlchemy
│   ├── models.py              # Models: User, Book, ReadingProgress
│   ├── auth.py                # ระบบรหัสผ่าน, Cookie Session, สิทธิ์การใช้งาน
│   ├── sample_data.py         # สร้างหนังสือและบัญชีผู้ใช้เริ่มต้น
│   ├── main.py                # จุดเริ่มต้นของ FastAPI Application
│   ├── routes/
│   │   ├── home_routes.py     # หน้าแรก ค้นหาหนังสือ และตัวกรองหมวดหมู่
│   │   ├── auth_routes.py     # หน้าเข้าสู่ระบบ, สมัครสมาชิก, ออกจากระบบ
│   │   ├── book_routes.py     # หน้าอ่านหนังสือบนมือถือ และ API สตรีม PDF
│   │   └── admin_routes.py    # แผงแอดมิน และหน้าเพิ่มหนังสือใหม่
│   ├── static/
│   │   ├── css/custom.css
│   │   └── uploads/           # เก็บไฟล์ PDF และหน้าปก
│   └── templates/
│       ├── base.html          # โครงสร้างพื้นฐาน Mobile Navigation & Tailwind
│       ├── home.html          # หน้าแรก Hero + ปุ่มสมัครสมาชิก + การ์ดหนังสือ
│       ├── login.html         # หน้าเข้าสู่ระบบพร้อมปุ่มเติมข้อมูลด่วน
│       ├── register.html      # หน้าสมัครสมาชิกใหม่
│       ├── read.html          # ตัวอ่าน PDF บนมือถือ (PDF.js + Gestures + Night Mode)
│       └── admin/
│           ├── dashboard.html # แดชบอร์ดสรุปสถิติและจัดการหนังสือ
│           └── add_book.html  # หน้าอัปโหลดหนังสือใหม่ (Admin Only)
├── render.yaml                # ตั้งค่า Blueprint สำหรับ Render
├── Procfile                   # คำสั่งเริ่มเซิร์ฟเวอร์บน Render
├── runtime.txt                # เวอร์ชัน Python
├── requirements.txt           # รายการแพ็กเกจที่ต้องใช้งาน
└── README.md
```

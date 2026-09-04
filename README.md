# EduClassify — Sistem Klasifikasi Pembelajaran Berbasis Deep Learning

Sistem klasifikasi video pembelajaran (CNN EfficientNet-B0) dan deteksi kualitas dokumen (IndoBERT) dengan antarmuka web modern.

---

## 🚀 Cara Menjalankan

### Prasyarat
- Python 3.10+
- Node.js 18+
- pip & npm

---

### 1. Setup Backend

```bash
cd project/backend

# Install dependencies
pip install -r requirements.txt

# Jalankan server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Server berjalan di: http://localhost:8000
Dokumentasi API: http://localhost:8000/docs

**Akun admin default:**
- Username: `admin`
- Password: `admin123`

---

### 2. Setup Frontend

```bash
cd project/frontend

# Install dependencies
npm install

# Jalankan development server
npm run dev
```

Aplikasi berjalan di: http://localhost:5173

---

## 📁 Struktur Proyek

```
project/
├── backend/
│   ├── main.py                  # Entry point FastAPI
│   ├── database.py              # SQLAlchemy setup
│   ├── requirements.txt
│   ├── models/
│   │   └── db_models.py         # 9 tabel database
│   ├── schemas/
│   │   └── schemas.py           # Pydantic schemas
│   ├── routers/
│   │   ├── auth.py              # POST /auth/register|login|logout
│   │   ├── predict.py           # POST /predict, GET /predict/history
│   │   └── admin.py             # Semua endpoint /admin/*
│   ├── services/
│   │   └── auth_service.py      # JWT + bcrypt
│   ├── ai/
│   │   ├── video/
│   │   │   └── cnn_pipeline.py  # EfficientNet-B0
│   │   └── document/
│   │       └── bert_pipeline.py # IndoBERT
│   ├── uploads/
│   │   ├── video/
│   │   └── document/
│   └── saved_models/
│       ├── cnn/                 # .pt files
│       └── bert/                # HuggingFace model dirs
│
└── frontend/
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx              # Router
    │   ├── index.css            # Tailwind + custom
    │   ├── services/
    │   │   └── api.js           # Axios instance
    │   ├── stores/
    │   │   └── authStore.js     # Zustand
    │   ├── components/
    │   │   └── layout/
    │   │       └── AppLayout.jsx # Sidebar + topbar
    │   └── pages/
    │       ├── LoginPage.jsx
    │       ├── RegisterPage.jsx
    │       ├── user/
    │       │   ├── Dashboard.jsx
    │       │   ├── UploadPredict.jsx
    │       │   └── PredictionHistory.jsx
    │       └── admin/
    │           ├── Dashboard.jsx
    │           ├── VideoDataset.jsx
    │           ├── DocumentDataset.jsx
    │           ├── TrainCNN.jsx
    │           ├── TrainBERT.jsx
    │           ├── ModelMonitor.jsx
    │           ├── UserManagement.jsx
    │           ├── ActivityLogs.jsx
    │           └── SystemConfig.jsx
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── postcss.config.js
```

---

## 🎯 Fitur Lengkap

### User
- ✅ Register & Login (JWT)
- ✅ Dashboard statistik prediksi pribadi
- ✅ Upload & Prediksi (drag & drop, progress bar, gauge chart)
- ✅ Riwayat prediksi dengan filter & search

### Admin
- ✅ Dashboard overview (chart, statistik)
- ✅ Manajemen Dataset Video (upload, label, hapus)
- ✅ Manajemen Dataset Dokumen (upload, label, hapus)
- ✅ Training CNN (real-time via WebSocket)
- ✅ Training IndoBERT (real-time via WebSocket)
- ✅ Monitor Model (accuracy, F1, radar chart)
- ✅ Deploy / Rollback versi model
- ✅ Manajemen User (tambah, hapus, ubah role)
- ✅ Log Aktivitas (export CSV)
- ✅ Konfigurasi Sistem (threshold, dll)
- ✅ Export Dataset (.xlsx) & Log (.csv)

---

## 🤖 AI Pipeline

### Video (CNN)
- Model: EfficientNet-B0 (pre-trained ImageNet)
- Input: .mp4 → ekstrak 12 frame merata via OpenCV
- Fine-tune: classifier layer (biner)
- Output: Deep Learning / Bukan Deep Learning + confidence%

### Dokumen (IndoBERT)
- Model: indobenchmark/indobert-base-p1
- Input: .pdf (pdfplumber/PyMuPDF) atau .docx (python-docx)
- Fine-tune: 3-class classification
- Output: Baik / Cukup / Kurang + confidence%

---

## 🛠️ Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, SQLite/PostgreSQL |
| Auth | JWT (python-jose), bcrypt (passlib) |
| AI Video | PyTorch, EfficientNet-B0 (TorchVision), OpenCV |
| AI Dokumen | HuggingFace Transformers, IndoBERT |
| Frontend | React + Vite, Tailwind CSS, Framer Motion |
| Charts | Recharts |
| State | Zustand |
| Forms | React Hook Form |
| HTTP | Axios |

---

## 🔧 Variabel Lingkungan (opsional)

Buat file `.env` di folder `backend/`:

```env
SECRET_KEY=your-super-secret-jwt-key-here
DATABASE_URL=postgresql://user:pass@localhost/educlassify
```

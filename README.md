<div dir="rtl">

# ⚡ نبض المنصات | Platform Pulse

**مرصد ذكي آلي يستدل على حجم القوى العاملة في اقتصاد المنصات عبر الآثار الرقمية العامة**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-red.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-39%20passed-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)]()

</div>

---
## 🚀 رابط الحل المباشر (Live Demo)

### 🔗 [https://platformpulse.streamlit.app/](https://platformpulse.streamlit.app/)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://platformpulse.streamlit.app/)

---

## 📺 الفيديو التوضيحي

> 🎬 **[رابط الفيديو — https://youtu.be/7onyMmLung4](https://youtu.be/7onyMmLung4)**

---
## 📌 المشكلة

لا يوجد مصدر بيانات رسمي واحد يرصد **العاملين في اقتصاد المنصات** (سائقو أوبر وكريم، موصّلو هنقرستيشن وجاهز ومرسول، العمال المستقلون) في الوقت الفعلي. إحصاءات الجهات الرسمية تصدر متأخرة، ولا تُفرّق بين العامل الرسمي والعامل في المنصة.

## 💡 الحل

**نبض المنصات** يُجمّع خمسة مصادر بيانات عامة وغير تقليدية، ويحوّلها إلى **مؤشر مركّب** يُقدّر حجم القوى العاملة في اقتصاد المنصات شهرياً — دون الحاجة إلى أي بيانات خاصة أو مسح ميداني.

---

## 🗂️ مصادر البيانات الخمسة

| # | المصدر | ما يُقيسه |
|---|--------|-----------|
| 1 | **تقييمات التطبيقات** (Google Play + App Store) | تكرار التقييمات = نشاط العمّال |
| 2 | **Google Trends** | اتجاهات البحث عن وظائف المنصات |
| 3 | **OpenStreetMap** | كثافة نقاط الاستلام/التسليم جغرافياً |
| 4 | **Telegram + X (Twitter)** | مشاعر قنوات السائقين والعمال |
| 5 | **GASTAT + GOSI** | خط أساسي للمقارنة والتحقق |

---

## 🔬 المنهجية

### المؤشر المركّب

$$\text{Index}_t = \sum_{s=1}^{5} w_s \cdot \text{Signal}_{s,t}$$

حيث تُحسب الأوزان $w_s$ بـ:
1. **ElasticNetCV** إذا توفرت ≥6 نقاط بيانات تاريخية
2. **IVW (Inverse Variance Weighting)** كاحتياط

فترات الثقة تُحسب بـ **Rolling Bootstrap** (1000 عينة، نافذة 6 أشهر).

---

### تقدير العمالة

$$\text{Workers}_{est} = N_{total} \times \left[\alpha_{low} + (\alpha_{high} - \alpha_{low}) \times \frac{Index}{100}\right]$$

حيث:
- $\alpha_{low}$ = 0.4%، $\alpha_{high}$ = 1.8% — نطاق ILO لاقتصاد المنصات في الشرق الأوسط

---

### 📐 اشتقاق $N_{total}$ — إجمالي القوى العاملة

> ⚠️ **ملاحظة منهجية:** لا تنشر الهيئة العامة للإحصاء رقماً مطلقاً لإجمالي قوة العمل في بياناتها المتاحة (تحتوي على معدلات ونسب فقط). لذا يُشتق هذا الرقم رياضياً من **مصدرين رسميين** وفق المعادلة:

$$N_{total} = \text{السكان (15+)} \times \text{معدل المشاركة}$$

**المصدر 1 — السكان في سن العمل:**

| البند | القيمة | المصدر |
|---|---|---|
| إجمالي سكان المملكة 2024 | 35,300,000 | [نشرة التقديرات السكانية 2024 — GASTAT](https://www.stats.gov.sa/documents/20117/2435273/Population+Estimates+Publication+2024+EN.pdf/7d123c57-1626-7d2f-ba7f-8a719f928f28) |
| الفئة 15–64 سنة (74.7%) | 26,369,100 | المصدر نفسه |
| الفئة 65+ سنة (2.8%) | 988,400 | المصدر نفسه |
| **السكان في سن العمل (15+)** | **27,357,500** | المجموع |

**المصدر 2 — معدل المشاركة في القوى العاملة:**

| البند | القيمة | المصدر |
|---|---|---|
| معدل المشاركة الإجمالي Q4-2024 | 66.4% | [نشرة سوق العمل Q4-2024، جدول (1) — GASTAT](https://www.stats.gov.sa/documents/d/guest/lms-q4_2024_pr_ar-press-release-pdf) |

**الحساب:**

$$N_{total} = 27{,}357{,}500 \times 66.4\% \approx \mathbf{18{,}165{,}000}$$

**الخط الأساسي للمقارنة:**
- 175,000 عامل رسمي في قطاعَي النقل والتوصيل — GASTAT Q4-2023 (السجلات الإدارية)

---

## 🏗️ هيكل المشروع

```
platform_pulse/
├── src/
│   ├── collectors/          # جمع البيانات من المصادر الخمسة
│   │   ├── appstore_collector.py
│   │   ├── trends_collector.py
│   │   ├── spatial_collector.py
│   │   ├── social_collector.py
│   │   ├── official_collector.py
│   │   └── run_all_collectors.py
│   ├── processing/          # تنظيف وتوحيد البيانات
│   │   ├── cleaner.py
│   │   ├── normalizer.py
│   │   └── validator.py
│   ├── models/              # النماذج التحليلية
│   │   ├── composite_index.py   # المؤشر المركّب (ElasticNet + IVW + Bootstrap CI)
│   │   ├── sentiment_marbert.py # تحليل المشاعر العربية (CAMeL-BERT)
│   │   ├── spatial_dbscan.py    # تجميع المدن (DBSCAN)
│   │   ├── anomaly_detection.py # كشف الشذوذ (Isolation Forest)
│   │   └── prophet_forecast.py  # التنبؤ الزمني (Prophet)
│   ├── database/            # قاعدة البيانات
│   │   ├── schema.py
│   │   └── db_manager.py
│   └── dashboard/           # لوحة التحكم التفاعلية
│       ├── app.py
│       └── components/
│           ├── monthly_index.py    # المؤشر الشهري
│           ├── sector_breakdown.py # التفصيل القطاعي
│           ├── heatmap.py          # الخريطة الحرارية
│           ├── forecast.py         # التنبؤات
│           ├── gap_analysis.py     # فجوة الرصد
│           └── social_pulse.py     # النبض الاجتماعي
├── data/
│   ├── sample/              # بيانات عينة توضيحية
│   └── processed/           # بيانات معالجة
├── tests/                   # 39 اختبار وحدة
├── config/settings.yaml
├── Dockerfile
├── docker-compose.yml
├── setup.sh
└── run.sh
```


---
## 🚀 تشغيل المشروع

### الطريقة 1: تثبيت محلي

```bash
# 1. تثبيت المتطلبات
bash setup.sh

# 2. تشغيل كامل (جمع + معالجة + نماذج + لوحة تحكم)
bash run.sh

# 3. أو تشغيل اللوحة مباشرة (بيانات العينة)
source venv/bin/activate
streamlit run src/dashboard/app.py
```

### الطريقة 2: Docker

```bash
# بناء وتشغيل
docker compose up --build

# أو تشغيل الأجزاء منفصلة
docker compose run platform-pulse python -m src.collectors.run_all_collectors
docker compose run platform-pulse python run_models.py
docker compose run platform-pulse streamlit run src/dashboard/app.py
```

### الطريقة 3: خطوة بخطوة

```bash
# جمع البيانات
python -m src.collectors.run_all_collectors

# تنظيف ومعالجة
python -m src.processing.cleaner
python -m src.processing.normalizer
python -m src.processing.validator

# تشغيل النماذج
python run_models.py

# تشغيل اللوحة
streamlit run src/dashboard/app.py
```
---
💡 تنبيه خاص للجنة التحكيم (Evaluation Note)
ملاحظة منهجية: لتسهيل عملية التقييم وضمان عمل "النبض الاجتماعي" (Social Pulse) بشكل فوري وتفاعلي، قمنا بتضمين ملف .env يحتوي على مفاتيح الوصول وجلسة العمل (API Session) اللازمة لسحب البيانات من المصادر المفتوحة.

الغرض: تمكين اللجنة من تجربة الحل كاملاً دون الحاجة لإعداد مفاتيح خاصة أو واجهات برمجية إضافية.

الأمان: هذا الإجراء مخصص حصراً لبيئة الهاكاثون ولفترة التقييم، مع الالتزام التام بسياسات خصوصية البيانات الموضحة في دليل المتسابق.

---
## 🤖 الذكاء الاصطناعي والتقنيات المستخدمة

| التقنية | الاستخدام |
|---|---|
| **MARBERT** | تحليل المشاعر العربية |
| **Prophet** | التنبؤ الاستشرافي مع موسمية سعودية |
| **ElasticNet** | بناء المؤشر المركّب |
| **DBSCAN** | تجميع المدن جغرافياً |
| **Isolation Forest** | كشف الشذوذ |
| **Bootstrap CI** | فترات الثقة الإحصائية (95%) |

---
## 🧪 الاختبارات

```bash
python -m pytest tests/ -v
```

**39 اختبار وحدة** تغطي:
- منطق المؤشر المركّب (التدرج، الثقة، الشذوذ)
- تطبيع المدن والتواريخ
- صحة بيانات العينة (الحدود الجغرافية، نطاقات القيم)
- استرداد بيانات المجتمع والمنصات

---

## 👥 الفريق

هاكاثون الابتكار في البيانات — المسار الأول | **فريق أثر (Athar)**
- بدر العتيبي — قائد الفريق
- مسفر القحطاني — عضو
- عبدالكريم الشمري — عضو

---

## ⚖️ الملكية الفكرية وحقوق النشر

تؤول جميع حقوق الملكية الفكرية لهذا المشروع إلى **الهيئة العامة للإحصاء (GASTAT)**، وذلك وفقاً للشروط والأحكام المنظمة لـ **"هاكاثون الابتكار في البيانات"**.


# 🚀 RAG Embedding Models Benchmark (Text-to-SQL)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)
![FAISS](https://img.shields.io/badge/Vector_DB-FAISS-red.svg)
![HuggingFace](https://img.shields.io/badge/Models-HuggingFace-yellow.svg)

RAG (Retrieval-Augmented Generation) mimarilerinde veya Text-to-SQL projelerinde doğru "Embedding" modelini seçmek her zaman zorlu bir denge meselesidir. En zeki lokal modeli kullanmak istersiniz ama sunucunuzun RAM'i yetmez; Cloud API kullanırsınız bu sefer de limitlere, maliyetlere ve veri gizliliği sorunlarına takılırsınız.

Bu proje, tam olarak bu sorunu çözmek için geliştirildi. 1525 satırlık gerçek bir kurumsal veritabanı üzerinde; 6 farklı modelin (Lokal ve Cloud) hem **anlamsal eşleştirme doğruluğunu** hem de **gerçek zamanlı donanım tüketimini (CPU/RAM)** ve **hızını (Latency)** anlık olarak test edip kıyaslayabileceğiniz bir platformdur.

---

## ✨ Öne Çıkan Mühendislik Çözümleri

Sistemi sadece "çalışan" bir kod bloğu olarak bırakmadık, canlı ortama (Production) uygun mimari eklemeler yaptık:

* 💾 **FAISS Disk Caching:** Lokal modeller devasa olduğu için her model değişiminde yaşanan ~150 saniyelik o meşhur "Cold Start" darboğazını çözdük. İşlenen vektör havuzu `.index` dosyası olarak diske kaydedilir. Böylece sonraki tüm aramalarda sistem saniyeler içinde ayağa kalkar ve **0.05 saniye** hızında yanıt verir.
* 📊 **Gerçek Zamanlı Donanım İzleme:** Modeller gerçekten donanımı ne kadar yoruyor? Bunu tahmini bırakmadık. `psutil` kütüphanesi ile her sorguda bilgisayarın **anlık RAM (MB)** ve **CPU (%)** sıçramalarını UI üzerindeki log tablosuna yansıtıyoruz.
* 🛡️ **API Rate Limit Koruması:** Cloud (Gemini) testlerinde Google'ın "Dakikada 100 İstek" sınırlarına (HTTP 429) çarpıp sistemi çökertmemek için güvenli bir bekleme (sleep/retry) akışı kurguladık.

---

## 🤖 Test Edilen Modeller

Arayüz üzerinden anında geçiş yapıp birbiriyle yarıştırdığımız modeller:

1. `intfloat/multilingual-e5-large` *(Referans / En Zeki ama En Ağır)*
2. `intfloat/multilingual-e5-base` *(Optimum Performans / Favori)*
3. `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` *(Dengeli)*
4. `intfloat/multilingual-e5-small` *(En Hızlı / Hafif)*
5. `sentence-transformers/distiluse-base-multilingual-cased-v2` *(Alternatif)*
6. `gemini-embedding-001` *(Cloud / Google API)*

---

## 🛠️ Kurulum ve Çalıştırma

Projeyi kendi bilgisayarınızda denemek çok basit. Sadece Google Gemini API anahtarınızı eklemeyi unutmayın!

**1. Repoyu klonlayın ve klasöre girin:**
```bash
git clone https://github.com/KULLANICI_ADIN/embedding-model-comparison.git
cd embedding-model-comparison

**2. Gerekli kütüphaneleri kurun:**
```bash

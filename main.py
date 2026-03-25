from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sentence_transformers import SentenceTransformer
from google import genai
import faiss
import numpy as np
import json
import time
import os
import psutil

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# JSON Verisini Yükle (Tüm veriler okunuyor)
with open('golden_queries.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)
questions = [item['question'] for item in json_data]

# Cache Mekanizması
current_model_name = None
current_local_model = None
current_faiss_index = None

# Gemini İstemcisi
client = genai.Client(api_key="sizin_gemini_api_keyiniz")

# Gemini vektörlerini kalıcı olarak kaydedeceğimiz dosyanın adı
GEMINI_INDEX_FILE = "gemini_vektorleri.index"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/search")
async def search(query: str = Form(...), model_choice: str = Form(...)):
    global current_model_name, current_local_model, current_faiss_index
    
    start_time = time.time()
    
    # EĞER FARKLI BİR MODEL SEÇİLDİYSE VEKTÖR HAVUZUNU (FAISS) HAZIRLA
    if current_model_name != model_choice:
        print(f"\n[{model_choice}] yükleniyor ve vektör havuzu kontrol ediliyor...")
        
        # 1. DURUM: GEMINI SEÇİLDİYSE (DISK CACHING)
       
        if model_choice == "gemini-embedding-001":
            if os.path.exists(GEMINI_INDEX_FILE):
                print(f"Diskte '{GEMINI_INDEX_FILE}' bulundu! RAM'e yükleniyor...")
                current_faiss_index = faiss.read_index(GEMINI_INDEX_FILE)
                current_model_name = model_choice
                print("FAISS index başarıyla yüklendi, sistem aramaya hazır!")
            else:
                print("Kayıtlı dosya bulunamadı. Veriler API'ye gönderiliyor...")
                all_gemini_embeddings = []
                
                for i, q in enumerate(questions):
                    response = client.models.embed_content(
                        model=model_choice,
                        contents=q
                    )
                    all_gemini_embeddings.append(response.embeddings[0].values)
                    
                    if (i + 1) % 10 == 0 or (i + 1) == len(questions):
                        print(f"Gemini: {i + 1} / {len(questions)} soru işlendi...")
                    
                    # Google Rate Limit koruması
                    time.sleep(0.8) 
                    
                question_embeddings = np.array(all_gemini_embeddings, dtype=np.float32)
                
                faiss.normalize_L2(question_embeddings)
                dimension = question_embeddings.shape[1]
                current_faiss_index = faiss.IndexFlatIP(dimension)
                current_faiss_index.add(question_embeddings)
                
                faiss.write_index(current_faiss_index, GEMINI_INDEX_FILE)
                current_model_name = model_choice
                print(f"MUHTEŞEM! Veriler başarıyla işlendi ve '{GEMINI_INDEX_FILE}' diske kaydedildi.")

        # 2. DURUM: LOKAL (HUGGINGFACE) MODEL SEÇİLDİYSE
        
        else:
            print(f"{model_choice} RAM'e yükleniyor...")
            current_local_model = SentenceTransformer(model_choice)
            
            # Model ismindeki '/' gibi dosya sistemini bozacak karakterleri temizle
            safe_model_name = model_choice.replace("/", "_")
            LOCAL_INDEX_FILE = f"{safe_model_name}_vektorleri.index"
            
            # ADIM A: Bu modelin FAISS dosyası daha önce oluşturulmuş mu?
            if os.path.exists(LOCAL_INDEX_FILE):
                print(f"Diskte '{LOCAL_INDEX_FILE}' bulundu! 150 saniye beklemeden RAM'e yükleniyor...")
                current_faiss_index = faiss.read_index(LOCAL_INDEX_FILE)
            
            # ADIM B: Dosya yoksa sıfırdan oluştur ve DİSKE KAYDET
            else:
                print(f"{model_choice} için veriler işleniyor (İlk sefere mahsus uzun sürecek)...")
                question_embeddings = current_local_model.encode(questions)
                question_embeddings = np.array(question_embeddings, dtype=np.float32)

                faiss.normalize_L2(question_embeddings)
                dimension = question_embeddings.shape[1]
                current_faiss_index = faiss.IndexFlatIP(dimension)
                current_faiss_index.add(question_embeddings)
                
                # Gelecekte beklememek için diske kaydet
                faiss.write_index(current_faiss_index, LOCAL_INDEX_FILE)
                print(f"İşlem bitti ve '{LOCAL_INDEX_FILE}' diske kaydedildi.")

            current_model_name = model_choice
            print("Lokal model FAISS index'i başarıyla hazırlandı!")

    # KULLANICI SORGUSUNU (QUERY) ARAMA VE KAYNAK ÖLÇÜMÜ
    
    # CPU/RAM Ölçümünü başlat
    process = psutil.Process(os.getpid())
    process.cpu_percent(interval=None) # Sayacı sıfırla
    
    if model_choice == "gemini-embedding-001":
        query_response = client.models.embed_content(
            model=model_choice,
            contents=query
        )
        query_embedding = np.array([query_response.embeddings[0].values], dtype=np.float32)
    else:
        query_embedding = current_local_model.encode([query])
        query_embedding = np.array(query_embedding, dtype=np.float32)

    faiss.normalize_L2(query_embedding)
    scores, indices = current_faiss_index.search(query_embedding, 1)
    
    # CPU/RAM Ölçümünü bitir
    cpu_usage = process.cpu_percent(interval=None)
    ram_usage_mb = process.memory_info().rss / (1024 * 1024)
    
    best_match_index = int(indices[0][0])
    best_score = float(scores[0][0])
    similarity_percentage = round(best_score * 100, 2)

    latency = time.time() - start_time
    
    resource_info = f"{ram_usage_mb:.1f} MB RAM / %{cpu_usage:.1f} CPU"
    if model_choice == "gemini-embedding-001":
        resource_info += " (Cloud İşlemi)"
    
    return {
        "similarity_percentage": f"%{similarity_percentage}",
        "latency_seconds": round(latency, 4),
        "resource_usage": resource_info,
        "matched_data": json_data[best_match_index]
    }
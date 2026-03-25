RAG Embedding Models Benchmark (Text-to-SQL)
RAG (Retrieval-Augmented Generation) mimarilerinde veya Text-to-SQL projelerinde doğru "Embedding" modelini seçmek her zaman zorlu bir denge meselesidir. 
En zeki lokal modeli kullanmak istersiniz ama sunucunuzun RAM'i yetmez; Cloud API kullanırsınız bu sefer de limitlere, maliyetlere ve veri gizliliği sorunlarına takılırsınız.

Bu proje, tam olarak bu sorunu çözmek için geliştirildi. 1525 satırlık gerçek bir kurumsal veritabanı üzerinde; 6 farklı modelin (Lokal ve Cloud) hem anlamsal eşleştirme doğruluğunu hem de gerçek zamanlı donanım tüketimini (CPU/RAM) ve hızını (Latency) anlık olarak test edip kıyaslayabileceğiniz bir platformdur.

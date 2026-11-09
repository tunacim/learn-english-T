# English coach · İngilizce koçu (Claude Code skill)

🇬🇧 A Claude Code skill for Turkish-speaking developers who want to learn English while they work. You read bilingual answers and short tips during work, and you practise with questions in a separate session. Your progress is saved, and you can see it as charts.

🇹🇷 Çalışırken İngilizce öğrenmek isteyen Türk yazılımcılar için bir Claude Code skill'i. İş sırasında iki dilli cevaplar ve kısa hap bilgiler okursun. Ayrı bir oturumda sorularla pratik yaparsın. İlerlemen kaydedilir ve grafik olarak görebilirsin.

## Nasıl çalışır? / How does it work?

| | 💼 İş oturumu / Work session | 🎓 `/english` oturumu / Study session |
| --- | --- | --- |
| Cevaplar | İki dilde (önce İngilizce, sonra Türkçe) | İki dilde |
| Hap bilgi | Agent'lar çalışırken ara sıra, mesajın en altında. **Soru yok.** | Var, sonunda küçük bir kontrol sorusuyla |
| Soru-cevap | ❌ İş karışmasın diye yok | ✅ Seviye testi, tekrar, cümle kurma, kelime |
| Kayıt | Verilen hap bilgi kaydedilir | Her cevap kaydedilir |

İki oturum aynı ilerleme dosyasını kullanır. İş sırasında verilen hap bilgi, 2 gün sonra `/english` oturumunda "anladın mı?" diye sorulur.

## Neler var? / What's inside?

- **📚 Müfredat (`curriculum.md`):** A1–A2, 6 ünite, 45 konu (Zaman, Cümle, Gramer, Kelime); her konuda Türk öğrencinin tipik hatası
- **📘 Kelime yolları:** Temel (sık kelimeler), Günlük (az bilinen günlük kelimeler), Angular mülakat; her oturumda 4 kelime maddesi, hap bilgiler gramer ve kelime arasında sırayla
- **✍️ Yazım:** sadece kısa bir notla belirtilir, puanı etkilemez
- **🔁 Ders döngüsü:** ön soru → kısa ders → 6 soruluk quiz (tanıma → kontrollü üretim → serbest cümle) → sonuç → aralıklı tekrar; ünite sonu sınavı (10 soru)
- **🚦 Konu durumu:** ⚪ başlanmadı · 🔵 öğreniliyor · 🔴 zayıf · 🟠 gelişiyor · 🟢 iyi · 🔁 tekrar zamanı (✅ = 1, 🟡 = 0,5, ❌ = 0)
- **🏷️ Hata etiketleri:** yazım, article, -s, yardımcı fiil, kelime sırası, zaman, edat, kelime seçimi, fiil biçimi, eksik kelime; iş oturumundaki Better English düzeltmeleri de sayılır
- **Seviyeler:** A2 (günlük temel) → B1 (iş hayatı) → B2 (yazılımcı İngilizcesi) → C1 (doğal konuşma)
- **4 alan:** günlük konuşma, gramer, kelime ve kalıplar, yazılımcı İngilizcesi
- **Soru türleri:** çeviri, boşluk doldurma, seçmeli, düzeltme, kendi cümlen, sırala, kelime kutusuyla kur
- **💊 Hap bilgi:** sık karıştırılan basit konular (do/does, -s, didn't + fiil, since/for, make/do, actually ≠ aslında…)
- **🧱 Cümle kurma:** 5 adımlı sabit yöntem (Kim? → Ne yaptı? → Neyi? → Nerede/ne zaman? → Olumsuz/soru?), 4 basamak ve 10 güvenli cümle başlangıcı
- **📘 Kelime:** en sık kullanılan B1 kelimeleri, tek başına değil kalıp içinde
- **Aralıklı tekrar:** yanlışlar 1, 3, 7 gün sonra, sonra SM-2 algoritmasıyla
- %60–70 başarı hedefi ve her 20 soruda bir rapor
- **📊 İstatistik sayfası:** öğretmen notu, "iyisin / gelişiyorsun / zayıfsın / tekrar zamanı" özeti, A1/A2 seviye ilerlemesi, ünite ünite konu tablosu (puan, son 10, trend), en sık hatalar, sınav sonuçları, günlük grafikler. İnternet gerekmez.

## Kurulum / Setup

**Gerekenler / Requirements:** Claude Code, Python 3 (sadece grafik sayfası için; ek paket gerekmez).

1. Bu klasörü şuraya kopyala:
   ```
   ~/.claude/skills/english/
   ```
   İçinde `SKILL.md`, `README.md`, `curriculum.md` ve `scripts/dashboard.py` olmalı.
2. Claude Code'da **yeni bir oturum** aç ve şunu yaz:
   ```
   /english
   ```
   İlk oturum 5 soruluk seviye testidir.
3. **İsteğe bağlı, iş sırasında hap bilgi için:** `~/.claude/CLAUDE.md` dosyana şu satırları ekle:
   ```
   - Sohbet yanıtları iki dilli: önce İngilizce, sonra Türkçe. İngilizce kısmı kısa ve sade (B1–B2).
   - Kullanıcı İngilizce yazarsa ve hata varsa, cevabın sonuna 1–2 satırlık "Better English" notu ekle.
   - İş oturumunda agent'lar çalışırken ara sıra (iş başına en fazla 1) english skill'ini "tip" argümanıyla yükle: sadece hap bilgi ver, soru sorma. Soru-cevap sadece /english oturumunda.
   ```

## Kullanım / Usage

**`/english` oturumunda yazabileceklerin:**

| Komut | Ne yapar |
| --- | --- |
| `/english` | Oturumu başlatır: önce zamanı gelen tekrarlar, sonra karışık pratik |
| `review` / `tekrar` | Sadece zamanı gelen tekrarlar |
| `konu <ad>` / `topic <ad>` | O konu için ders + quiz |
| `sınav` / `exam` | Ünite sınavı (10 soru) |
| `hap` / `tip` | Bir hap bilgi |
| `cümle` / `sentence` | Cümle kurma pratiği |
| `kelime` / `vocab` | Kelime çalışması |
| `writing` / `yazma` | Serbest yazma |
| `reading` / `okuma` | Kısa bir metin ve 2 soru |
| `stats` / `istatistik` | Grafik sayfasını yeniler, 3 ana rakamı verir |
| `bitti` / `stop` | Oturumu bitirir, kısa özet verir |

**İş oturumunda:** `english off` (ya da `ingilizce dur`) hap bilgileri durdurur. `english on` ile tekrar başlar.

## Dosyalar / Files

İlerlemen `~/English-Learning/` klasöründe tutulur. Klasör ilk kullanımda kendiliğinden oluşur.

| Dosya | Ne işe yarar |
| --- | --- |
| `progress.md` | Seviye, tekrar listesi, kelimeler, hap bilgiler, günlük kayıt (okunabilir) |
| `answers.csv` | Her cevap bir satır; istatistik için |
| `dashboard.html` | Grafik sayfası; çift tıkla, tarayıcıda açılır |

Grafik sayfasını elle yenilemek için:
```
python3 ~/.claude/skills/english/scripts/dashboard.py
```

## Notlar / Notes

- Skill, ana dili Türkçe olan bir yazılımcı için yazıldı. Örnekler iş hayatından ve yazılımdan.
- Verilerin sadece senin bilgisayarında durur. Dış servis yok.
- Teşekkür: aralıklı tekrar (SM-2), kalite puanı ve %60–70 başarı hedefi [m98/fluent](https://github.com/m98/fluent) projesinden (MIT) uyarlandı.

# English coach · İngilizce koçu (Claude Code skill)

🇬🇧 A Claude Code skill for Turkish-speaking developers who want to learn English while they work. You read bilingual answers and short tips during work, and you practise with questions in a separate session. Every answer is saved, and you can see your progress as charts.

🇹🇷 Çalışırken İngilizce öğrenmek isteyen Türk yazılımcılar için bir Claude Code skill'i. İş sırasında iki dilli cevaplar ve kısa hap bilgiler okursun. Ayrı bir oturumda sorularla pratik yaparsın. Her cevap kaydedilir ve ilerlemeni grafik olarak görürsün.

## İçindekiler / Contents

1. [Nasıl çalışır? / How does it work?](#1-nasıl-çalışır--how-does-it-work)
2. [Kurulum / Setup](#2-kurulum--setup)
3. [Kullanım / Usage](#3-kullanım--usage)
4. [İstatistik nasıl tutulur? / How are the stats kept?](#4-i̇statistik-nasıl-tutulur--how-are-the-stats-kept)
5. [Nerede ne yazıyor? / What is written where?](#5-nerede-ne-yazıyor--what-is-written-where)
6. [Grafik sayfası / The dashboard](#6-grafik-sayfası--the-dashboard)
7. [Konu durumu nasıl hesaplanır? / How is topic status computed?](#7-konu-durumu-nasıl-hesaplanır--how-is-topic-status-computed)
8. [Nasıl gelişirim? / How do I improve?](#8-nasıl-gelişirim--how-do-i-improve)
9. [Nasıl takip ederim? / How do I track my progress?](#9-nasıl-takip-ederim--how-do-i-track-my-progress)
10. [Neler var? / What's inside?](#10-neler-var--whats-inside)
11. [Notlar / Notes](#11-notlar--notes)

## 1. Nasıl çalışır? / How does it work?

🇬🇧 There are two kinds of sessions. Both use the same progress files.

🇹🇷 İki tür oturum var. İkisi de aynı ilerleme dosyalarını kullanır.

| | 💼 İş oturumu / Work session | 🎓 `/english` oturumu / Study session |
| --- | --- | --- |
| Ne zaman | Normal kod işi yaparken | İngilizce için ayrı açtığın oturumda |
| Cevaplar | İki dilde (önce İngilizce, sonra Türkçe) | İki dilde |
| Hap bilgi | Agent'lar çalışırken ara sıra, mesajın en altında. **Soru yok.** | Var, sonunda küçük bir kontrol sorusuyla |
| Better English | İngilizce yazarsan ve hata varsa, cevabın sonunda 1–2 satır düzeltme | Her cevaba geri bildirim |
| Soru-cevap | ❌ İş karışmasın diye yok | ✅ Seviye testi, ders, quiz, sınav, tekrar, cümle kurma, kelime |
| Kayıt | Hap bilgi ve Better English düzeltmeleri | Her cevap |

**İki oturum birbirine bağlı:**

1. İş oturumunda bir hap bilgi alırsın (ör. `since vs for`).
2. Skill bunu `progress.md` dosyasına bir tekrar kartı olarak yazar: `Hap: since vs for`, 2 gün sonra.
3. 2 gün sonra `/english` açarsan, Claude bu konuda yeni bir "anladın mı?" sorusu sorar.
4. Cevabına göre kart ileri tarihe gider (doğru) veya ertesi güne döner (yanlış).

İş oturumundaki Better English düzeltmeleri de kaydedilir. Bunlar puanını etkilemez, ama "En sık hatalar" listesine girer. Böylece günlük yazışmada en çok nerede hata yaptığını görürsün.

## 2. Kurulum / Setup

**Gerekenler / Requirements:** Claude Code, Python 3 (sadece grafik sayfası için; ek paket gerekmez).

1. Bu repoyu şuraya klonla:
   ```
   git clone <repo-url> ~/.claude/skills/english
   ```
   İçinde `SKILL.md`, `README.md`, `curriculum.md` ve `scripts/dashboard.py` olmalı.
2. Claude Code'da **yeni bir oturum** aç ve şunu yaz:
   ```
   /english
   ```
   İlk oturum 5 soruluk seviye testidir. `~/English-Learning/` klasörü bu sırada kendiliğinden oluşur.
3. **İsteğe bağlı, iş sırasında hap bilgi için:** `~/.claude/CLAUDE.md` dosyana şu satırları ekle:
   ```
   - Sohbet yanıtları iki dilli: önce İngilizce, sonra Türkçe. İngilizce kısmı kısa ve sade (B1–B2).
   - Kullanıcı İngilizce yazarsa ve hata varsa, cevabın sonuna 1–2 satırlık "Better English" notu ekle.
   - Better English notu yazınca ~/English-Learning/answers.csv'ye sessizce bir satır ekle: kind=work-note, result = close | wrong, topic_id ve errors (id'ler ~/.claude/skills/english/curriculum.md'de), topic = "yanlış → doğru". Python csv modülüyle yaz.
   - İş oturumunda agent'lar çalışırken ara sıra (iş başına en fazla 1) english skill'ini "tip" argümanıyla yükle: sadece hap bilgi ver, soru sorma. Soru-cevap sadece /english oturumunda.
   ```

## 3. Kullanım / Usage

**`/english` oturumunda yazabileceklerin:**

| Komut | Ne yapar |
| --- | --- |
| `/english` | Oturumu başlatır: önce zamanı gelen tekrarlar, sonra konu, cümle kurma ve kelime |
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

**Normal bir `/english` oturumunun sırası:**

1. Claude `progress.md` ve `curriculum.md` dosyalarını okur.
2. Grafik sayfasını yeniler ve sıradaki konuyu bulur.
3. **Karışık tekrar:** zamanı gelen kartlardan ve zayıf konulardan 5 soru.
4. **Konu bloğu:** tek konu için ön soru → kısa ders → 6 soruluk quiz.
5. **Cümle kurma:** 1 soru.
6. **Kelime:** 4 madde (2 tekrar, 2 yeni kelime).
7. `bitti` yazınca: günün özeti ve yarın zamanı gelecek kartlar.

**İş oturumunda:** `english off` (ya da `ingilizce dur`) hap bilgileri durdurur. `english on` ile tekrar başlar.

## 4. İstatistik nasıl tutulur? / How are the stats kept?

🇬🇧 Every answer becomes one line in a CSV file. A Python script reads this file and draws the charts. Nothing goes to the internet.

🇹🇷 Her cevap bir CSV dosyasında bir satır olur. Bir Python script'i bu dosyayı okur ve grafikleri çizer. Hiçbir şey internete gitmez.

```
Sen cevap verirsin
      │
      ▼
Claude puanlar: ✅ doğru · 🟡 yakın · ❌ yanlış  (+ hata etiketi)
      │
      ├──► answers.csv   → her cevap 1 satır (ham veri)
      ├──► progress.md   → durum, tekrar kartları, kelimeler, günlük kayıt
      │
      ▼
scripts/dashboard.py   (answers.csv + progress.md + curriculum.md okur)
      │
      ▼
dashboard.html         → grafik sayfası, tarayıcıda açılır
```

**Puanlama:** ✅ = 1 puan, 🟡 = 0,5 puan, ❌ = 0 puan. Küçük yazım hataları (büyük harf, nokta, kesme işareti) ✅'yi 🟡 yapmaz. Sadece `yazim` etiketi alır.

**Hata etiketi:** her hatanın bir etiketi olur. Liste `curriculum.md` § Error tags içinde:

| Etiket | Ne demek | Örnek hata |
| --- | --- | --- |
| `yazim` | Yazım ve noktalama | i, doesnt |
| `article` | a / an / the | on frontend |
| `s-eki` | he/she/it -s eksik veya fazla | he work |
| `yardimci-fiil` | do / does / did / be eksik veya fazla | Where you work? |
| `kelime-sirasi` | Kelime sırası | fiil sonda |
| `zaman-secimi` | Yanlış zaman | alışkanlıkta -ing |
| `edat` | in / on / at / to / for | go to home |
| `kelime-secimi` | Yanlış kelime | meet (meeting yerine) |
| `fiil-bicimi` | -s/-es, -ed, düzensiz fiil, -ing/to | sended |
| `eksik-kelime` | Eksik kelime veya cümle parçası | 2. fiil yok |

**Grafik sayfası ne zaman yenilenir:** her `/english` oturumunun başında ve sonunda, bir de `stats` yazınca. Elle de yenileyebilirsin:

```
python3 ~/.claude/skills/english/scripts/dashboard.py
```

## 5. Nerede ne yazıyor? / What is written where?

🇬🇧 Your data is in `~/English-Learning/`, not in this repo. The repo has only the skill.

🇹🇷 Verilerin `~/English-Learning/` klasöründe. Bu repoda değil. Repoda sadece skill var.

| Dosya | Yer | Ne işe yarar |
| --- | --- | --- |
| `SKILL.md` | bu repo | Claude için kurallar: oturum akışı, puanlama, tekrar, kayıt |
| `curriculum.md` | bu repo | 45 konu (6 ünite) ve hata etiketleri |
| `scripts/dashboard.py` | bu repo | İstatistik sayfasını üretir |
| `answers.csv` | `~/English-Learning/` | Her cevap bir satır; istatistiğin ham verisi |
| `progress.md` | `~/English-Learning/` | Okunabilir durum dosyası |
| `dashboard.html` | `~/English-Learning/` | Grafik sayfası; çift tıkla, tarayıcıda açılır |

### `answers.csv` sütunları

| Sütun | Ne yazar | Örnek |
| --- | --- | --- |
| `date`, `time` | Cevap zamanı | `2026-10-20`, `10:05` |
| `kind` | Ne tür madde | `quiz`, `review`, `exam`, `tip`, `work-note` … |
| `area` | Alan | `Gramer`, `Yazılımcı İngilizcesi` |
| `level` | Sorunun seviyesi | `A2`, `B1` |
| `result` | Sonuç | `ok` (✅), `close` (🟡), `wrong` (❌); ders ve hap bilgide boş |
| `q` | Kalite puanı 0–5 (aralıklı tekrar için) | `4` |
| `topic` | Kısa Türkçe not | `past simple; sended → sent` |
| `topic_id` | Müfredattaki konu id'si | `past-simple-irregular` |
| `qtype` | Soru tipi | `gap`, `translate`, `free` … |
| `errors` | Hata etiketleri, `;` ile | `zaman-secimi;edat` |

**`kind` değerleri:**

- `placement` seviye testi · `pretest` ön soru / hızlı test · `lesson` ders · `quiz` konu quiz'i · `exam` ünite sınavı
- `review` tekrar · `sentence` cümle kurma · `vocab` kelime · `question` diğer sorular
- `tip` hap bilgi · `tip-check` hap bilgi kontrol sorusu
- `work-note` iş oturumundaki Better English düzeltmesi (puana girmez, sadece hata istatistiğine girer)

### `progress.md` bölümleri

| Bölüm | Ne yazar |
| --- | --- |
| **Durum** | Seviye, toplam soru, doğru sayısı, son 10 cevap, güncel konu, sonraki oturum planı |
| **Tekrar listesi** | Tekrar kartları: konu, doğru hali, sonraki tekrar tarihi, aralık, EF |
| **Yeni kelimeler ve kalıplar** | Öğrendiğin kelimeler: English — Türkçe — tarih — grup |
| **Hap bilgiler** | Verilen hap bilgiler ve tarihleri (aynı hap 14 gün tekrar verilmez) |
| **Cümle kalıpları** | Çalıştığın kalıplar ve senin örneklerin |
| **Günlük kayıt** | Her gün bir satır: soru sayısı, doğru, alanlar |
| **Raporlar** | Her 20 soruda bir ve her sınavdan sonra kısa rapor |

**Tekrar kartı nasıl ilerler (aralıklı tekrar):**

1. Yanlış veya yakın her cevap, her yeni kelime ve her hap bilgi bir kart olur.
2. İlk üç tekrar: 1, 3 ve 7 gün sonra. Hap bilgi kartı 2 gün sonra başlar.
3. Sonra SM-2 algoritması: aralık her doğru cevapta uzar. Kolay kartlar daha seyrek gelir.
4. Bir tekrarda yanlış yaparsan (q < 3) kart 1 güne döner.
5. 21+ günlük aralıkta doğru cevap verirsen kart **öğrenildi** olur ve listeden çıkar.

## 6. Grafik sayfası / The dashboard

🇬🇧 Open `~/English-Learning/dashboard.html` in your browser. It works without the internet.

🇹🇷 `~/English-Learning/dashboard.html` dosyasını tarayıcıda aç. İnternet gerekmez.

| Bölüm | Ne gösterir |
| --- | --- |
| **Öğretmen notu** | Birkaç cümlelik kişisel yorum: neyi iyi yapıyorsun, neye odaklanmalısın |
| **Durumun** | Konular grup grup: 🟢 iyi · 🟠 gelişiyor · 🔴 zayıf · 🔁 tekrar zamanı |
| **Seviye ilerlemesi** | A1 ve A2 konularının yüzde kaçı 🟢 |
| **Kelimeler** | Kelime yolları ve öğrenilen kelime sayısı |
| **Konular** | Ünite ünite konu tablosu: durum, puan, son 10 cevap (✅🟡❌), trend (↑ → ↓) |
| **En sık hatalar** | Hata etiketleri: toplam ve son zamanlardaki sayı |
| **Sınavlar** | Her ünite sınavının sonucu |
| **Gruplar / Alanlar** | Zaman, Cümle, Gramer, Kelime grupları ve 4 alan için başarı |
| **Günlük cevaplar** | Her gün kaç ✅ / 🟡 / ❌ verdin |
| **Puan, son 10 cevap** | Puanının zaman içindeki çizgisi |
| **Öğrenilen kelime ve kalıp** | Toplam kelime sayısının artışı |

Script konsola da kısa bir özet yazar: her durumdaki konular ve `sıradaki:` konu.

## 7. Konu durumu nasıl hesaplanır? / How is topic status computed?

🇬🇧 The script looks at all graded answers for a topic and checks these rules from top to bottom.

🇹🇷 Script bir konunun puanlı bütün cevaplarına bakar ve kuralları yukarıdan aşağı kontrol eder.

| Durum | Kural |
| --- | --- |
| ⚪ Başlanmadı | Hiç kayıt yok |
| 🔵 Öğreniliyor | 4'ten az puanlı cevap (sadece ders veya hap bilgi de buraya girer) |
| 🔴 Zayıf | Son 5 cevap %50'nin altında |
| 🟢 İyi | Son 10 cevap ≥ %80, en az 2 farklı günde, en az 2 doğru **üretim** cevabı |
| 🔁 Tekrar zamanı | 🟢 kuralı tutuyor ama 14 günden fazla pratik yok |
| 🟠 Gelişiyor | Diğer her durum |

- **Üretim cevabı:** kendin cümle kurduğun sorular (`translate`, `wordbox`, `transform`, `free`). Sadece seçerek 🟢 olamazsın.
- **Trend:** son 5 cevap ile önceki 5 cevap karşılaştırılır. +15 puan ve üstü ↑, −15 ve altı ↓, arası →.
- Durum düşebilir. 🟢 bir konuda tekrar hataları başlarsa konu 🟠 veya 🔴 olur.
- `work-note` satırları (Better English) konu durumunu değiştirmez.

## 8. Nasıl gelişirim? / How do I improve?

🇬🇧 Short and often is better than long and rare. Do a little every day, and let the review cards do the planning.

🇹🇷 Kısa ve sık çalışmak, uzun ve seyrek çalışmaktan iyidir. Her gün biraz çalış. Planı tekrar kartlarına bırak.

**Günlük rutin (15–20 dakika):**

1. Yeni bir Claude Code oturumu aç ve `/english` yaz.
2. Önce zamanı gelen tekrarları bitir. Kartları biriktirme.
3. Bir konu bloğu yap. Claude zayıf konuyu veya sıradaki konuyu seçer.
4. Cümle kurma ve kelime bloklarını atlama.
5. `bitti` yaz ve özeti oku.

**İş sırasında:**

1. Claude ile mümkün olduğunca İngilizce yaz. Her Better English notu bir veri satırıdır.
2. Hap bilgileri oku. 2 gün sonra `/english` sana bunları sorar.
3. Cevabın İngilizce kısmını önce oku, sonra Türkçe kısmıyla karşılaştır.

**İpuçları:**

- **Cümle kurmakta zorlanırsan** 5 adımı kullan: Kim? → Ne yaptı (hangi zaman)? → Neyi? → Nerede / ne zaman? → Olumsuz / soru mu?
- **Hangi kelimeyle başlayacağını bilmiyorsan** güvenli başlangıçları kullan: *I think… / I'm working on… / Could you…? / The problem is… / Let me check…*
- **Başarın %80'in üstündeyse** sorular zorlaşır. **%50'nin altındaysa** kolaylaşır. Hedef %60–70: biraz zorlanmak öğrenmenin işaretidir.
- **🔴 bir konu görürsen** `konu <ad>` yazıp o konunun dersini tekrar al.
- **Bir ünitenin bütün konuları 🟠 veya üstüyse** `sınav` yaz.
- **En sık hatan** her hafta değişmiyorsa o etikete ait hap bilgiyi iste: `hap <konu>`.

## 9. Nasıl takip ederim? / How do I track my progress?

🇬🇧 Look at the dashboard once a week. Check a few numbers and compare them with last week.

🇹🇷 Grafik sayfasına haftada bir bak. Birkaç rakamı kontrol et ve geçen haftayla karşılaştır.

**Haftalık kontrol listesi:**

1. `/english` oturumunda `stats` yaz, ya da script'i elle çalıştır.
2. `~/English-Learning/dashboard.html` dosyasını aç.
3. **Seviye ilerlemesi:** A1 ve A2'de 🟢 konuların yüzdesi arttı mı?
4. **Konular:** 🔴 konu sayısı azaldı mı? Trend sütununda ↓ olan konu var mı?
5. **En sık hatalar:** ilk 3 etiket hangileri? "Son zamanlarda" sayısı toplamdan düşük mü?
6. **Puan, son 10 cevap:** çizgi %60–70 civarında mı?
7. **Günlük cevaplar:** haftada kaç gün çalıştın? Boş gün sayısı az mı?
8. **Öğrenilen kelime:** sayı her hafta arttı mı?

**Neye bakarak gelişmeyi anlarsın:**

| İşaret | Anlamı |
| --- | --- |
| 🔵 → 🟠 → 🟢 | Konuyu öğreniyorsun |
| ↑ trend | Son cevapların öncekilerden iyi |
| Bir hata etiketinin "son zamanlarda" sayısı düşüyor | O hatayı yapmayı bırakıyorsun |
| Tekrar kartları listeden çıkıyor | Kalıcı öğrenme oldu |
| Better English notları azalıyor | Gündelik yazışmada daha az hata yapıyorsun |

**Uzun vadeli hedef:** A1 ve A2 konularının hepsi 🟢. Seviye, sadece o seviyedeki bütün ünite sınavlarında %80+ alınca değişir.

**Elle bakmak istersen:**

- `progress.md` → **Raporlar** bölümü: her 20 soruda bir yazılan kısa rapor.
- `progress.md` → **Günlük kayıt**: gün gün soru ve doğru sayısı.
- `answers.csv`: Excel, Numbers veya Google Sheets ile açılır. `errors` sütununa göre filtrele.

## 10. Neler var? / What's inside?

- **📚 Müfredat (`curriculum.md`):** A1–A2, 6 ünite, 45 konu (Zaman, Cümle, Gramer, Kelime); her konuda Türk öğrencinin tipik hatası
- **📘 Kelime yolları:** Temel (sık kelimeler), Günlük (az bilinen günlük kelimeler), Angular mülakat; her oturumda 4 kelime maddesi, hap bilgiler gramer ve kelime arasında sırayla
- **✍️ Yazım:** sadece kısa bir notla belirtilir, puanı etkilemez
- **🔁 Ders döngüsü:** ön soru → kısa ders → 6 soruluk quiz (tanıma → kontrollü üretim → serbest cümle) → sonuç → aralıklı tekrar; ünite sonu sınavı (10 soru)
- **🚦 Konu durumu:** ⚪ başlanmadı · 🔵 öğreniliyor · 🔴 zayıf · 🟠 gelişiyor · 🟢 iyi · 🔁 tekrar zamanı
- **🏷️ Hata etiketleri:** 10 etiket; iş oturumundaki Better English düzeltmeleri de sayılır
- **Seviyeler:** A2 (günlük temel) → B1 (iş hayatı) → B2 (yazılımcı İngilizcesi) → C1 (doğal konuşma)
- **4 alan:** günlük konuşma, gramer, kelime ve kalıplar, yazılımcı İngilizcesi
- **Soru türleri:** çeviri, boşluk doldurma, seçmeli, düzeltme, dönüştürme, kendi cümlen, sırala, kelime kutusuyla kur
- **💊 Hap bilgi:** sık karıştırılan basit konular (do/does, -s, didn't + fiil, since/for, make/do, actually ≠ aslında…)
- **🧱 Cümle kurma:** 5 adımlı sabit yöntem, 4 basamak ve 10 güvenli cümle başlangıcı
- **Aralıklı tekrar:** 1, 3, 7 gün, sonra SM-2
- **📊 İstatistik sayfası:** tek HTML dosyası, internet gerekmez

## 11. Notlar / Notes

- Skill, ana dili Türkçe olan bir yazılımcı için yazıldı. Örnekler iş hayatından ve yazılımdan.
- Verilerin sadece senin bilgisayarında durur. Dış servis yok. `~/English-Learning/` bu repoya girmez.
- Teşekkür: aralıklı tekrar (SM-2), kalite puanı ve %60–70 başarı hedefi [m98/fluent](https://github.com/m98/fluent) projesinden (MIT) uyarlandı.

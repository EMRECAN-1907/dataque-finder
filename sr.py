"""
Sembolik regresyon demosu (genetik programlama, kütüphanesiz).

Gizli formül:  ucret = (tutar * 0.001 + adet * 2) * 1.05
Program bu formülü bilmiyor; sadece 150 örnek satır görüyor
ve formülü kendisi bulmaya çalışıyor.

Çalıştır:  python sr_demo.py
"""
import random
import math

random.seed(1)

# ---------------------------------------------------------------
# 1) VERİ: gizli formülle 150 satır üret (120 eğitim + 30 sınav)
# ---------------------------------------------------------------
def gizli_formul(tutar, adet):
    return (tutar * 0.001 + adet * 2) * 1.05

satirlar = []
for _ in range(150):
    tutar = random.randint(100, 10000)
    adet = random.randint(1, 50)
    satirlar.append(({"tutar": tutar, "adet": adet}, gizli_formul(tutar, adet)))

egitim, sinav = satirlar[:120], satirlar[120:]
DEGISKENLER = ["tutar", "adet"]

# ---------------------------------------------------------------
# 2) FORMÜL = AĞAÇ.  ("+", sol, sag) | ("x", "tutar") | ("c", 2.0)
# ---------------------------------------------------------------
ISLEMLER = ["+", "-", "*"]

def rastgele_yaprak():
    if random.random() < 0.6:
        return ("x", random.choice(DEGISKENLER))
    # sabitler logaritmik ölçekte: 0.001 ... 10 (finansal oranlar küçük olur)
    deger = 10 ** random.uniform(-3, 1)
    return ("c", float(f"{deger:.3g}"))

def rastgele_agac(derinlik):
    if derinlik == 0 or random.random() < 0.3:
        return rastgele_yaprak()
    return (random.choice(ISLEMLER),
            rastgele_agac(derinlik - 1),
            rastgele_agac(derinlik - 1))

def hesapla(agac, satir):
    tip = agac[0]
    if tip == "x":
        return satir[agac[1]]
    if tip == "c":
        return agac[1]
    a, b = hesapla(agac[1], satir), hesapla(agac[2], satir)
    if tip == "+": return a + b
    if tip == "-": return a - b
    return a * b

def yazdir(agac):
    if agac[0] == "x": return agac[1]
    if agac[0] == "c": return f"{agac[1]:.6g}"
    return f"({yazdir(agac[1])} {agac[0]} {yazdir(agac[2])})"

def boyut(agac):
    return 1 if agac[0] in ("x", "c") else 1 + boyut(agac[1]) + boyut(agac[2])

# ---------------------------------------------------------------
# 3) UYGUNLUK: ortalama göreli hata + karmaşıklık cezası
#    (küçük formül tercih edilir -> Occam'ın usturası)
# ---------------------------------------------------------------
def hata(agac, veri):
    toplam = 0.0
    for satir, y in veri:
        try:
            tahmin = hesapla(agac, satir)
        except OverflowError:
            return math.inf
        toplam += abs(tahmin - y) / abs(y)
    return toplam / len(veri)

def uygunluk(agac):
    return hata(agac, egitim) + 0.0005 * boyut(agac)

# ---------------------------------------------------------------
# 4) GENETİK OPERATÖRLER
# ---------------------------------------------------------------
def alt_agaclar(agac, yol=()):
    yield yol, agac
    if agac[0] not in ("x", "c"):
        yield from alt_agaclar(agac[1], yol + (1,))
        yield from alt_agaclar(agac[2], yol + (2,))

def degistir(agac, yol, yeni):
    if not yol:
        return yeni
    parca = list(agac)
    parca[yol[0]] = degistir(agac[yol[0]], yol[1:], yeni)
    return tuple(parca)

def caprazla(anne, baba):
    """Annenin rastgele bir dalını babanın rastgele bir dalıyla değiştir."""
    yol, _ = random.choice(list(alt_agaclar(anne)))
    _, dal = random.choice(list(alt_agaclar(baba)))
    cocuk = degistir(anne, yol, dal)
    return cocuk if boyut(cocuk) <= 25 else anne

def mutasyon(agac):
    yol, dal = random.choice(list(alt_agaclar(agac)))
    if dal[0] == "c" and random.random() < 0.7:
        # sabiti hafifçe oynat (ince ayar)
        return degistir(agac, yol, ("c", float(f"{dal[1] * random.uniform(0.9, 1.1):.5g}")))
    return degistir(agac, yol, rastgele_agac(2))

def turnuva(nufus, puanlar, k=5):
    adaylar = random.sample(range(len(nufus)), k)
    return nufus[min(adaylar, key=lambda i: puanlar[i])]

def ince_ayar(agac, deneme=60):
    """Formülün YAPISINI sabit tut, sadece SABİTLERİNİ iyileştir (tepe tırmanma)."""
    en_iyi, en_iyi_puan = agac, uygunluk(agac)
    for _ in range(deneme):
        sabitler = [(y, d) for y, d in alt_agaclar(en_iyi) if d[0] == "c"]
        if not sabitler:
            break
        yol, dal = random.choice(sabitler)
        aday = degistir(en_iyi, yol, ("c", dal[1] * random.uniform(0.97, 1.03)))
        p = uygunluk(aday)
        if p < en_iyi_puan:
            en_iyi, en_iyi_puan = aday, p
    return en_iyi

# ---------------------------------------------------------------
# 5) EVRİM DÖNGÜSÜ
# ---------------------------------------------------------------
NUFUS, NESIL = 400, 60
nufus = [rastgele_agac(4) for _ in range(NUFUS)]

for nesil in range(NESIL + 1):
    puanlar = [uygunluk(a) for a in nufus]
    en_iyi_i = min(range(NUFUS), key=lambda i: puanlar[i])
    en_iyi = nufus[en_iyi_i]

    if nesil % 5 == 0:
        print(f"Nesil {nesil:3d} | hata %{hata(en_iyi, egitim)*100:8.3f} | {yazdir(en_iyi)}")

    en_iyi = ince_ayar(en_iyi)           # en iyinin sabitlerini parlat
    yeni = [en_iyi]                      # elitizm: en iyiyi koru
    while len(yeni) < NUFUS:
        r = random.random()
        if r < 0.7:
            yeni.append(caprazla(turnuva(nufus, puanlar), turnuva(nufus, puanlar)))
        else:
            yeni.append(mutasyon(turnuva(nufus, puanlar)))
    nufus = yeni

# ---------------------------------------------------------------
# 6) SINAV: hiç görmediği 30 satır
# ---------------------------------------------------------------
print("\nBulunan formül :", yazdir(en_iyi))
print("Gizli formül   : ((tutar * 0.001) + (adet * 2)) * 1.05")
print(f"Sınav hatası   : %{hata(en_iyi, sinav)*100:.4f}  (30 görülmemiş satır)")
print("\nİlk 5 sınav satırı:")
for satir, y in sinav[:5]:
    print(f"  tutar={satir['tutar']:5d} adet={satir['adet']:2d} | gerçek={y:10.4f} | tahmin={hesapla(en_iyi, satir):10.4f}")
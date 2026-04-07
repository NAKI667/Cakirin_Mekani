# Çakır'ın Mekanı

Çakır'ın Mekanı, klasik yazı-tura ödevini daha ciddi bir Python paketine çeviren tematik bir CLI casino projesidir. Kullanıcı kaydı, admin yönetimi, SQLite tabanlı veri saklama, oyun geçmişi ve üç farklı oyun içerir:

- Yazı tura
- Rulet
- Blackjack

Uygulama `Typer` ve `Rich` kullanır; metinlerde Çakır ve Polat havasını taşıyan kısa replikler yer alır.

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .[dev]
```

## EXE Üretimi

Windows üzerinde tek dosya çalıştırılabilir almak için:

```powershell
.\build_exe.ps1
```

Üretilen dosya:

```text
dist\Cakirin_Mekani.exe
```

Bu `.exe` çift tıklanınca doğrudan interaktif menüyle açılır. Komut satırından çalıştırırsan mevcut CLI komutlarını da kullanabilirsin.

## Hızlı Başlangıç

```bash
cakir-casino init-db
cakir-casino auth register --username polat --password derinmasa
cakir-casino auth login --username polat --password derinmasa
cakir-casino profile show
cakir-casino play coinflip --bet 100 --side yazi
cakir-casino play roulette --bet 50 --bet-type color --value red
cakir-casino play blackjack --bet 200
cakir-casino history --limit 10
```

Varsayılan admin hesabı:

- Kullanıcı adı: `cakir`
- Şifre: `istanbul`

## Özellikler

- Hash'lenmiş parola saklama
- Yerel SQLite veritabanı
- Oturum dosyası üzerinden aktif kullanıcı takibi
- Admin komutları ile kullanıcı yönetimi, log görüntüleme ve bakiye güncelleme
- Oyun geçmişi ve chip bakiyesi takibi

## Proje Yapısı

```text
cakir_casino/
  cli.py
  auth.py
  db.py
  services.py
  session.py
  ui/theme.py
  games/
tests/
```

## Notlar

- Uygulama varsayılan olarak çalışma dizininde `.cakir_casino/` klasörü açar.
- Blackjack doğal kazancında `3:2` ödeme kesirli çıkarsa oyuncu lehine yukarı yuvarlanır.
- Testler `pytest` ile yazılmıştır.

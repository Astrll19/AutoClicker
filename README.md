
🎯 RECORD & PLAYBACK
- Rekam **klik mouse** (kiri/kanan/tengah) + **press/release**
- Rekam **gerakan mouse** penuh (jalur diputar ulang persis, bukan teleport)
- Rekam **keyboard** press + release
- Rekam **scroll**
- Throttle rekaman gerakan (default 16ms ≈ 60fps, bisa diatur)
- Toggle on/off rekam gerakan mouse

 ✏ ACTION EDITOR
- Log rekaman jadi **Treeview interaktif** (bukan plain text)
- **Edit per-action**: type, delay ms, speed multiplier, posisi x/y, button/key
- **Move To**: pindah action dari urutan A ke B langsung
- **Delete** action terpilih
- **⬆ ⬇** geser satu posisi
- Double-click row = edit langsung

🔁 PLAYBACK OPTIONS (ada di semua mode)
- **Repeat count** — set berapa kali loop
- **Repeat Until Stop** — loop sampai F7/Stop ditekan
- **Speed multiplier** — percepat/perlambat playback
- **Per-action speed** — tiap action bisa punya speed sendiri
- **Jitter ms** — random delay biar timing ga robotik
- **Hold ms** — tahan klik/tombol sebelum release
- **Relative Position** — posisi klik relatif ke posisi mouse saat play
- **Scheduled Start** — auto-start jam tertentu (format HH:MM)

🎯 MULTI-TARGET
- List target dengan kolom: X, Y, Delay ms, Action, Button/Key, Type, Label
- **Action per target**: mouse click ATAU keyboard shortcut
- **Button**: left / right / middle
- **Click type**: single / double click
- **Edit target** (dialog + double-click)
- **Reorder** — input "dari nomor X ke nomor Y" langsung
- **⬆ ⬇** geser urutan
- **Pick on screen** — minimize 3 detik, capture posisi mouse otomatis

 🔵 INTERVAL CLICKER
- Klik satu titik berulang dengan interval tetap
- Pilih button (left/right/middle)
- Pick posisi dari screen (3 detik)
- Support semua playback options (jitter, until stop, dll)

🧠 HUMANIZED MODE
- **Mouse movement**: kurva Bezier natural dengan arc + micro-tremor
- **Click timing**: variable hold duration 40–140ms, pre-click pause
- **Keyboard**: variasi timing antar ketukan, sesekali jeda panjang
- Toggle on/off dari header (berlaku ke semua mode)
- Setting: **Mouse Speed** slider + **Key Variance** slider di Settings tab

🟣 OVERLAY DRAG TARGETS
- Lingkaran berwarna muncul di layar persis di posisi tiap target
- **Drag langsung** → koordinat update otomatis ke tabel
- Tiap target beda warna, ada badge delay di sampingnya
- **Klik kanan** lingkaran → hapus target
- Toggle show/hide dari header atau tab Multi-Target

---

## 👁 IMAGE RECOGNITION
- Watch layar, auto klik kalau gambar tertentu muncul
- **Snip screen** — seleksi area layar langsung buat jadi template
- Setting confidence level
- Pilih click type: single / double / right click
- Terintegrasi Humanized Mode

🎨 COLOR TRIGGER
- Watch pixel di koordinat tertentu
- Auto klik kalau warna pixel cocok dengan target color
- Setting tolerance (±N)
- **Color picker** dari dialog
- Pick posisi watch + posisi klik dari screen (3 detik)
- Terintegrasi Humanized Mode

🔗 MACRO CHAINS
- Gabungin beberapa recording jadi satu sequence
- Nama + repeat count + notes per chain
- Run chain langsung dari list

💾 PROFILES
- Save/load seluruh konfigurasi (actions + targets + chains) sebagai profil
- Nama profil bebas
- List profil dengan kolom jumlah actions/targets/chains

 💿 SAVE / LOAD
- Format file `.axd` (Astryxl Desk), kompatibel dengan `.nclick` dan `.json` lama
- Save/load recording + targets + chains sekaligus

🖥 HUD OVERLAY
- Window kecil always-on-top transparan
- Tampilkan status: IDLE / RECORDING / PLAYING
- Bisa di-drag ke mana saja
- Toggle dari header

🌙 DARK / LIGHT MODE
- Full theme switch semua komponen
- Toggle dari header atau Settings tab
- Dark: neon green on dark navy
- Light: hijau/biru tua on putih/abu muda

 ⌨ HOTKEYS GLOBAL
| Key |        fungsi       |
|-----|---------------------|
| F5  | Play / Stop         |
| F6  | Record / Stop       |
| F7  | Emergency Stop semua|

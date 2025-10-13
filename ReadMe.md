
# 🧠 CerebrumLux V8 Build Automation (MinGW Compatible)
**Version:** 6.0    
**License:**  
- **CerebrumLux Build Script:** MIT License © 2025 algoritma  
- **Google V8 Engine:** BSD-3-Clause License © The Chromium Authors
**Repository:** [github.com/algoritma/CerebrumLux_V8_Build](https://github.com/algoritma/CerebrumLux_V8_Build)

---

## 🇹🇷 Türkçe Açıklama

### 🎯 Amaç
Bu betik, Google V8 JavaScript motorunu **Windows + MinGW** ortamında tamamen otomatik olarak derlemek, yapılandırmak ve **vcpkg** ile bütünleştirmek amacıyla geliştirilmiştir.  
Normalde V8 yalnızca Visual Studio + Clang ortamında derlenebilir; bu betik, MinGW desteğini kazandırarak **Visual Studio gereksinimini ortadan kaldırır**.

---

### 🚀 Özellikler
- **Tam Otomatik Derleme Süreci:** V8 kaynaklarını indirir, bağımlılıkları çözer, derler ve sonuçları vcpkg’ye kopyalar.  
- **MinGW Toolchain Entegrasyonu:** `DEPOT_TOOLS_WIN_TOOLCHAIN=0` ortam değişkeni ile MinGW derleyicilerini kullanır.  
- **Visual Studio Gereksinimi Yok:** `vs_toolchain.py` betiğini otomatik yamalayarak VS tespiti adımlarını atlar.  
- **Güçlü Hata Kurtarma:** `gclient sync` ve `git` işlemleri yeniden deneme, proxy fallback ve hata toleransı ile yürütülür.  
- **vcpkg Entegrasyonu:** Derlenen kütüphaneleri ve başlık dosyalarını otomatik olarak `installed/x64-mingw-static` dizinine yerleştirir.  
- **Portfile Güncelleme:** `ports/v8` içindeki `portfile.cmake` ve `vcpkg.json` dosyalarını dinamik olarak üretir.  
- **Tamamen Loglanmış Süreç:** Her adım `logs/` dizininde ayrıntılı olarak kaydedilir.  
- **Ağ Engellerine Dayanıklı:** `chromium.googlesource` erişimi başarısız olursa GitHub mirror’larını kullanır.  

---

### ⚙️ Gereksinimler
| Bileşen            | Yol Örneği                                                      | Açıklama              |
| ------------------ | ----------------------------------------------------------------| --------------------- |
| **Python 3.10+**   | `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python.exe`| Ana çalıştırma ortamı |
| **Git**            | `C:\Program Files\Git\bin`                                      | Kaynak yönetimi       |
| **MinGW (x86_64)** | `C:\Qt\Tools\mingw1310_64\bin`                                  | Derleyici             |
| **depot_tools**    | `C:\depot_tools`                                                | V8 kaynak yöneticisi  |
| **vcpkg**          | `C:\vcpkg`                                                      | C++ paket yöneticisi  |

---

### 🧩 Kullanım
1. Tüm gereksinimlerin sistem PATH’inde olduğundan emin olun.  
2. Bu depoyu klonlayın:
   ```bash
   git clone https://github.com/algoritma/CerebrumLux_V8_Build.git
   cd CerebrumLux_V8_Build
````

3. Betiği çalıştırın:

   ```bash
   python build_v8.py
   ```
4. Betik tamamlandığında derlenmiş `libv8_monolith.a` ve `include/` dosyaları otomatik olarak:

   ```
   C:\vcpkg\installed\x64-mingw-static\
   ```

   altına yerleştirilir.
5. Artık `vcpkg integrate install` ile sistem genelinde kullanılabilir.

---

### 📂 Çıktılar

* **Derlenmiş Kütüphane:** `libv8_monolith.a`
* **Başlık Dosyaları:** `include/v8/`
* **Loglar:** `C:\v8build\logs\CerebrumLux-V8-Build-<version>.log`
* **vcpkg Port:** `C:\vcpkg\ports\v8\`

---

### ⚠️ Notlar

* İlk çalıştırmada `C:\v8-mingw` klasörü tamamen temizlenir.
* `build/vs_toolchain.py` dosyası otomatik yamalanır.
* Betik başarısız olursa, en son log dosyasına (`logs/`) bakmanız yeterlidir.
* Tüm işlem genellikle 30–60 dakika sürer (bağlantı hızına bağlı olarak).

---

## 🇬🇧 English Description

### 🎯 Purpose

This script automates the **complete build process of Google’s V8 JavaScript engine** under **Windows + MinGW**, integrating it directly into **vcpkg**.
Normally V8 requires Visual Studio and Clang; this script **eliminates that dependency**, enabling native MinGW builds.

---

### 🚀 Features

* **Full Automatic Build:** Fetches, syncs, builds, and integrates V8 with vcpkg automatically.
* **MinGW Toolchain Integration:** Uses `DEPOT_TOOLS_WIN_TOOLCHAIN=0` to enforce MinGW toolchain usage.
* **No Visual Studio Required:** Automatically patches `vs_toolchain.py` to bypass VS detection.
* **Resilient Error Handling:** Retries and proxy fallbacks for unstable networks and sync failures.
* **vcpkg Integration:** Copies headers and built libraries into the correct vcpkg installation tree.
* **Portfile Generator:** Dynamically creates and updates `ports/v8/portfile.cmake` and `vcpkg.json`.
* **Complete Logging:** Detailed build logs stored in `logs/` directory.
* **Mirror Fallbacks:** Uses GitHub mirrors when Chromium’s source servers throttle or block access.

---

### ⚙️ Requirements

| Component          | Example Path                                                     | Description           |
| ------------------ | ---------------------------------------------------------------- | --------------------- |
| **Python 3.10+**   | `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python.exe` | Runtime               |
| **Git**            | `C:\Program Files\Git\bin`                                       | Version control       |
| **MinGW (x86_64)** | `C:\Qt\Tools\mingw1310_64\bin`                                   | Compiler              |
| **depot_tools**    | `C:\depot_tools`                                                 | V8 dependency manager |
| **vcpkg**          | `C:\vcpkg`                                                       | C++ package manager   |

---

### 🧩 Usage

1. Ensure all requirements are installed and available in your PATH.
2. Clone this repository:

   ```bash
   git clone https://github.com/algoritma/CerebrumLux_V8_Build.git
   cd CerebrumLux_V8_Build
   ```
3. Run the build:

   ```bash
   python build_v8.py
   ```
4. After the build, precompiled `libv8_monolith.a` and headers will be copied to:

   ```
   C:\vcpkg\installed\x64-mingw-static\
   ```
5. Optionally integrate vcpkg globally:

   ```bash
   vcpkg integrate install
   ```

---

### 📂 Outputs

* **Compiled Library:** `libv8_monolith.a`
* **Headers:** `include/v8/`
* **Logs:** `C:\v8build\logs\CerebrumLux-V8-Build-<version>.log`
* **vcpkg Port:** `C:\vcpkg\ports\v8\`

---

### ⚠️ Notes

* On first run, the entire `C:\v8-mingw` directory will be deleted and recreated.
* `build/vs_toolchain.py` is automatically patched for MinGW compatibility.
* Check the `logs/` directory for detailed error traces if something fails.
* The whole process may take 30–60 minutes depending on network speed.

---

## 📜 License
- **CerebrumLux Build Script:** MIT License © 2025 algoritma  
- **Google V8 Engine:** BSD-3-Clause License © The Chromium Authors

---

**CerebrumLux V8 Builder** — turning complex Chromium infrastructure into a one-command MinGW solution. 🧠⚙️


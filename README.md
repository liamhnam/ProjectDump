# 🚀 ProjectDump

**ProjectDump** là công cụ giúp bạn gom toàn bộ mã nguồn của một dự án thành một file duy nhất (`source_dump.txt`) hoặc sao chép thẳng vào Clipboard. Chỉ với 1 thao tác, bạn đã có ngay toàn bộ context (ngữ cảnh) của project để dán vào ChatGPT, Claude, Gemini hoặc bất kỳ AI/LLM nào.

Tạm biệt việc phải copy-paste từng file một cách thủ công!

---

## 🔥 [MỚI] Phiên bản VS Code Extension (Khuyên dùng)

Chúng tôi đã phát hành tiện ích mở rộng (Extension) chính thức trên VS Code. Đây là cách nhanh nhất và tiện lợi nhất để gom mã nguồn ngay trong lúc code.

### 📥 Hướng dẫn cài đặt Extension

**Cách 1: Trực tiếp từ VS Code Marketplace**
1. Mở thanh **Extensions** trong VS Code (`Ctrl + Shift + X` hoặc `Cmd + Shift + X`).
2. Tìm kiếm **`ProjectDump`** (tác giả: `canhhungit`).
3. Nhấn **Install**.

**Cách 2: Cài đặt thủ công bằng file `.vsix`**
1. Tải file `projectdump-x.x.x.vsix` từ dự án.
2. Mở thanh **Extensions** trong VS Code, nhấn vào dấu **`...`** (góc trên bên phải).
3. Chọn **Install from VSIX...** và tìm đến file vừa tải về.

### 💡 Hướng dẫn sử dụng Extension
- **Cách 1 (Nhanh nhất):** Nhìn xuống góc dưới bên phải (thanh Status Bar) của VS Code, bấm vào nút **`{} Dump`**.
- **Cách 2:** Nhấn `Ctrl + Shift + P` (hoặc `Cmd + Shift + P`), gõ `ProjectDump` và chọn:
  - `ProjectDump: Generate Source Dump` (Lưu ra file `source_dump.txt`).
  - `ProjectDump: Dump & Copy to Clipboard` (Copy thẳng vào bộ nhớ tạm để paste vào AI).
- **Cách 3:** Click chuột phải vào một thư mục bất kỳ ở thanh Explorer bên trái, chọn **`ProjectDump: Dump This Folder`** để chỉ gom code của riêng thư mục đó.

---

## 🖥️ Phiên bản Python GUI (Standalone)

Nếu bạn cần gom dự án ở môi trường ngoài VS Code, bạn có thể sử dụng phiên bản giao diện (GUI) độc lập được viết bằng Python/Tkinter.

### 1. Chạy trực tiếp bằng Python
Yêu cầu hệ thống: **Python 3.8+**
```bash
python __main__.py
```

### 2. Build thành file chạy độc lập (.exe / .app)
Cài đặt thư viện PyInstaller:
```bash
pip install pyinstaller
```

**Dành cho Windows (.exe):**
```bash
pyinstaller --onefile --windowed --icon=icon.ico __main__.py -n ProjectDumpGUI
```
*(File kết quả sẽ nằm trong thư mục `dist/ProjectDumpGUI.exe`)*

**Dành cho macOS (.app):**
```bash
pyinstaller --onefile --windowed --icon=icon.icns __main__.py -n ProjectDumpGUI
```
*(File kết quả sẽ nằm trong thư mục `dist/ProjectDumpGUI.app`)*

---

## ✨ Các tính năng cốt lõi
- 🔍 **Nhận diện thông minh:** Tự động phát hiện công nghệ của dự án (Python, Node.js, Java, Go, v.v.).
- 🚫 **Tự động lọc rác:** Mặc định bỏ qua các thư mục nặng (`node_modules`, `build`, `dist`, `cache`...) và các file nhị phân.
- 📝 **Tôn trọng `.gitignore`:** Tự động đọc và bỏ qua các file nằm trong `.gitignore`.
- 📁 **Tạo sơ đồ cây (ASCII Tree):** Sinh ra cây cấu trúc thư mục ở đầu file giúp AI dễ hình dung kiến trúc project.
- 🌐 **Hỗ trợ đa ngôn ngữ:** Giao diện hỗ trợ cả Tiếng Việt và Tiếng Anh.

---

## 📜 License
MIT License.

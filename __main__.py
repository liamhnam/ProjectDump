import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from aggregator import aggregate_code
from constants import TEXT_VI, TEXT_EN
from filters import (
    get_essential_files,
    get_exclude_patterns,
    should_exclude_path,
    should_exclude_file,
)
import io
import contextlib
import subprocess
import platform
import json
from appdirs import user_data_dir

APP_NAME = "ProjectDump"
CONFIG_FILE = os.path.join(user_data_dir(APP_NAME), "last_path.json")

def save_last_path(path: str):
    """Lưu đường dẫn gần nhất vào thư mục người dùng (cross-platform)"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_path": path}, f)
    except Exception as e:
        print("Không thể lưu last_path:", e)

def load_last_path() -> str | None:
    """Tải lại đường dẫn gần nhất"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_path")
        except Exception:
            return None
    return None


class ProjectDumpGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 ProjectDump")
        self.root.geometry("950x700")

        self.output_path = None
        self.exclude_vars = {}   # {full_path: tk.BooleanVar()}

        # Language selection
        tk.Label(root, text="🌐 Ngôn ngữ / Language:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.lang_var = tk.StringVar(value="en")
        lang_menu = ttk.Combobox(root, textvariable=self.lang_var, values=["vi", "en"], state="readonly", width=10)
        lang_menu.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Project path selection
        tk.Label(root, text="📂 Thư mục dự án:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.path_var = tk.StringVar()
        self.path_entry = tk.Entry(root, textvariable=self.path_var, width=70)
        self.path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")
        tk.Button(root, text="Browse", command=self.choose_folder).grid(row=1, column=2, padx=5, pady=5)

        # Exclude folders (checkbox list)
        tk.Label(root, text="🚫 Thư mục cần bỏ qua:").grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        self.exclude_frame = tk.Frame(root)
        self.exclude_frame.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="nsew")

        # Run + Open buttons
        tk.Button(root, text="▶️ Chạy ProjectDump", command=self.run_projectdump).grid(
            row=3, column=0, pady=10, padx=10, sticky="w"
        )
        self.open_btn = tk.Button(root, text="📂 Mở thư mục output", command=self.open_output_folder, state="disabled")
        self.open_btn.grid(row=3, column=1, pady=10, sticky="w")

        # Log output area
        tk.Label(root, text="📜 Log output:").grid(row=4, column=0, padx=10, pady=5, sticky="nw")
        self.log_text = tk.Text(root, wrap="word", height=25)
        self.log_text.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="nsew")

        scrollbar = tk.Scrollbar(root, command=self.log_text.yview)
        scrollbar.grid(row=4, column=3, sticky="nsew")
        self.log_text.config(yscrollcommand=scrollbar.set)

        root.grid_rowconfigure(4, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # Load last project path
        last_path = load_last_path()
        if last_path:
            self.path_var.set(last_path)
            self.show_subfolders(last_path)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)
            save_last_path(folder)
            self.show_subfolders(folder)

    def show_subfolders(self, project_path):
        # Clear old checkboxes
        for widget in self.exclude_frame.winfo_children():
            widget.destroy()
        self.exclude_vars = {}

        try:
            for item in os.listdir(project_path):
                full_path = os.path.join(project_path, item)
                exclude_dirs, exclude_files = get_exclude_patterns()
                if os.path.isdir(full_path) and item not in exclude_dirs:
                    var = tk.BooleanVar(value=False)
                    chk = tk.Checkbutton(self.exclude_frame, text=item, variable=var)
                    chk.pack(anchor="w")
                    self.exclude_vars[full_path] = var
        except Exception as e:
            print("Không thể quét subfolders:", e)

    def run_projectdump(self):
        project_path = self.path_var.get().strip() or os.getcwd()
        lang = self.lang_var.get().lower()
        text = TEXT_EN if lang == "en" else TEXT_VI
        project_path = os.path.abspath(project_path)

        save_last_path(project_path)

        self.open_btn.config(state="disabled")
        self.output_path = None

        exclude_list = [os.path.basename(path) for path, var in self.exclude_vars.items() if var.get()]
        exclude_dirs, exclude_files = get_exclude_patterns()
        exclude_dirs = set(exclude_dirs).union(set(exclude_list))

        log_buffer = io.StringIO()
        with contextlib.redirect_stdout(log_buffer), contextlib.redirect_stderr(log_buffer):
            code_content = aggregate_code(project_path, text, exclude_dirs, exclude_files)

        success = bool(code_content)
        self.log_text.insert(tk.END, log_buffer.getvalue() + "\n")
        self.log_text.see(tk.END)

        if success:
            self.output_path = os.path.join(project_path, "source_dump.txt")
            self.open_btn.config(state="normal")
            messagebox.showinfo("✅ Success", text["done"])
        else:
            messagebox.showerror("❌ Error", text["error"])

    def open_output_folder(self):
        if self.output_path and os.path.exists(self.output_path):
            folder = os.path.dirname(self.output_path)
            try:
                if platform.system() == "Windows":
                    os.startfile(folder)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", folder])
                else:
                    subprocess.run(["xdg-open", folder])
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở folder: {e}")
        else:
            messagebox.showwarning("⚠️", "Không tìm thấy file output!")


def main():
    root = tk.Tk()
    app = ProjectDumpGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

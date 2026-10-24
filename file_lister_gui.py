import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

class FileListerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("檔案名稱列表工具")
        self.root.geometry("700x550")
        self.root.minsize(500, 400)

        # 頂部資訊
        self.path_var = tk.StringVar(value="目前資料夾: ./source")
        path_label = tk.Label(root, textvariable=self.path_var, anchor="w", fg="#333")
        path_label.pack(fill=tk.X, padx=10, pady=(10, 0))

        # 按鈕區
        button_frame = tk.Frame(root)
        button_frame.pack(pady=8)

        tk.Button(button_frame, text="選擇資料夾", command=self.select_folder, width=12).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="重新整理", command=self.list_files, width=12).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="複製全部", command=self.copy_all, width=12).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="儲存到文字檔", command=self.save_to_file, width=14).pack(side=tk.LEFT, padx=4)

        # 文字顯示區（可選取、複製）
        self.text_area = scrolledtext.ScrolledText(
            root,
            wrap=tk.NONE,
            font=("Consolas", 11),
            selectbackground="#4a90e2",
            selectforeground="white"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 狀態列
        self.status_var = tk.StringVar(value="就緒")
        status_bar = tk.Label(root, textvariable=self.status_var, anchor="w", relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # 預設資料夾
        self.folder_path = "./source"
        self.list_files()

    def select_folder(self):
        path = filedialog.askdirectory(title="選擇要列出檔案名稱的資料夾")
        if path:
            self.folder_path = path
            self.list_files()

    def list_files(self):
        self.text_area.delete(1.0, tk.END)
        self.path_var.set(f"目前資料夾: {self.folder_path}")

        if not os.path.isdir(self.folder_path):
            self.text_area.insert(tk.END, f"【錯誤】資料夾不存在或無法存取：\n{self.folder_path}\n")
            self.status_var.set("資料夾不存在")
            return

        try:
            items = sorted(os.listdir(self.folder_path), key=lambda x: x.lower())
            if not items:
                self.text_area.insert(tk.END, "（此資料夾是空的）\n")
                self.status_var.set("0 個項目")
            else:
                for name in items:
                    self.text_area.insert(tk.END, name + "\n")
                self.status_var.set(f"共 {len(items)} 個項目")
                self.root.title(f"檔案名稱列表 - {os.path.basename(self.folder_path) or self.folder_path}")
        except Exception as e:
            self.text_area.insert(tk.END, f"讀取失敗：{e}\n")
            self.status_var.set("讀取錯誤")

    def copy_all(self):
        content = self.text_area.get(1.0, tk.END).strip()
        if not content or content.startswith("【錯誤】") or content.startswith("（此資料夾"):
            messagebox.showwarning("提示", "沒有可複製的檔案名稱")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_var.set("已複製全部檔案名稱到剪貼簿")
        messagebox.showinfo("完成", "已將所有檔案名稱複製到剪貼簿\n可直接貼上使用")

    def save_to_file(self):
        content = self.text_area.get(1.0, tk.END).strip()
        if not content or content.startswith("【錯誤】") or content.startswith("（此資料夾"):
            messagebox.showwarning("提示", "沒有內容可儲存")
            return

        default_name = "sourcedir1.txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("文字檔", "*.txt"), ("所有檔案", "*.*")],
            title="儲存檔案名稱列表"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.status_var.set(f"已儲存至 {os.path.basename(file_path)}")
                messagebox.showinfo("完成", f"已成功儲存到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("儲存失敗", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = FileListerGUI(root)
    root.mainloop()

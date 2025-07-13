import os
import customtkinter as ctk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

class CodeExplorerFrame(ctk.CTkFrame):
    """
    Простой файловый браузер + встроенный текстовый просмотрщик.
    Сканирует папки проекта и по двойному клику открывает файлы.
    """
    def __init__(self, parent, project_root, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.project_root = project_root

        # слева — дерево
        self.tree = ttk.Treeview(self)
        self.tree.heading("#0", text="Project Files", anchor="w")
        self.tree.bind("<Double-1>", self._on_open)
        self.tree.pack(side="left", fill="y")

        # справа — редактор
        self.editor = ScrolledText(self, wrap="none", font=("Consolas", 11))
        self.editor.pack(side="right", fill="both", expand=True)
        self.editor.configure(bg="#000000", fg="#FFFFFF", insertbackground="#FFFFFF")

        self._build_tree()

    def _build_tree(self):
        def recurse(parent, path):
            for name in sorted(os.listdir(path)):
                full = os.path.join(path, name)
                node = self.tree.insert(parent, "end", text=name, open=False)
                if os.path.isdir(full):
                    recurse(node, full)
        recurse("", self.project_root)

    def _on_open(self, event):
        item = self.tree.focus()
        # собираем относительный путь
        parts = []
        cur = item
        while cur:
            parts.append(self.tree.item(cur, "text"))
            cur = self.tree.parent(cur)
        path = os.path.join(self.project_root, *reversed(parts))
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    txt = f.read()
            except UnicodeDecodeError:
                txt = "<!> This file cannot be opened (binary or unsupported encoding)"
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", txt)

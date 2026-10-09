import ast
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class  MetricsCalculator(ast.NodeVisitor):
    def __init__(self):
        self.cl = 0  # Абсолютная сложность
        self.statements_count = 0  # Количество исполняемых операторов
        self.max_nesting = 0  # Максимальная глубина вложенности
        self.current_nesting = 0
        self.log_items = []  # Лог для отладки и проверки на защите

    def log_stmt(self, node, desc):
        line = getattr(node, 'lineno', '?')
        self.statements_count += 1
        self.log_items.append(f"[СТРОКА {line:>2}] ОПЕРАТОР: {desc}")

    def log_cond(self, node, desc, depth):
        line = getattr(node, 'lineno', '?')
        self.cl += 1
        self.log_items.append(f"[СТРОКА {line:>2}] ПРЕДИКАТ: {desc} (Глубина: {depth})")

    def handle_condition_block(self, node, cond_name, body, orelse=None):
        self.statements_count += 1
        line = getattr(node, 'lineno', '?')
        self.log_items.append(f"[СТРОКА {line:>2}] ОПЕРАТОР ВЕТВЛЕНИЯ/ЦИКЛА: {cond_name}")

        self.current_nesting += 1
        if self.current_nesting > self.max_nesting:
            self.max_nesting = self.current_nesting

        self.log_cond(node, cond_name, self.current_nesting)

        for item in body:
            self.visit(item)

        self.current_nesting -= 1

        if orelse:
            for item in orelse:
                self.visit(item)

    def visit_If(self, node):
        self.handle_condition_block(node, "if / elif", node.body, node.orelse)

    def visit_IfExp(self, node):
        # Тернарный оператор внутри выражения: x if cond else y
        self.log_cond(node, "тернарный if-else", self.current_nesting)
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)

    def visit_While(self, node):
        self.handle_condition_block(node, "цикл while", node.body, node.orelse)

    def visit_For(self, node):
        self.handle_condition_block(node, "цикл for", node.body, node.orelse)

    def visit_Match(self, node):
        self.statements_count += 1
        line = getattr(node, 'lineno', '?')
        self.log_items.append(f"[СТРОКА {line:>2}] ОПЕРАТОР: match")

        # Отсекаем default ветку (case _)
        explicit_cases = [
            c for c in node.cases
            if not (isinstance(c.pattern, ast.MatchAs) and c.pattern.name is None and c.pattern.pattern is None)
        ]

        n_cases = len(explicit_cases)
        added_depth = 0

        # Модель вложенных if-else для switch по требованию преподавателя
        for i, case in enumerate(explicit_cases):
            if i > 0 and added_depth < (n_cases - 1):
                added_depth += 1
                self.current_nesting += 1

            if self.current_nesting > self.max_nesting:
                self.max_nesting = self.current_nesting

            self.log_cond(case, f"case (альтернатива {i + 1})", self.current_nesting)

            for stmt in case.body:
                self.visit(stmt)

        self.current_nesting -= added_depth

        # Обход тела дефолтной ветки
        for c in node.cases:
            if c not in explicit_cases:
                for stmt in c.body:
                    self.visit(stmt)

    def visit_FunctionDef(self, node):
        # Определение функций НЕ считаем оператором по требованию
        self.generic_visit(node)

    def visit_Assign(self, node):
        self.log_stmt(node, "присваивание (=)")
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self.log_stmt(node, "составное присваивание (+=, -=)")
        self.generic_visit(node)

    def visit_Expr(self, node):
        # Игнорируем строки документации (docstrings)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        self.log_stmt(node, "выражение / вызов функции")
        self.generic_visit(node)

    def visit_Return(self, node):
        self.log_stmt(node, "return")
        self.generic_visit(node)

    def visit_Break(self, node):
        self.log_stmt(node, "break")

    def visit_Continue(self, node):
        self.log_stmt(node, "continue")


class ParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор метрик Джилба")
        self.root.geometry("820x680")

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        btn_load = ttk.Button(frame, text="Выбрать файл .py для анализа", command=self.load_file)
        btn_load.pack(fill=tk.X, pady=(0, 10))

        # Разделение окна на код и подробный лог подсчёта
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        frame_left = ttk.Labelframe(paned, text=" Исходный код ", padding=5)
        self.txt_preview = tk.Text(frame_left, wrap=tk.NONE, width=45)
        self.txt_preview.pack(fill=tk.BOTH, expand=True)
        paned.add(frame_left, weight=1)

        frame_right = ttk.Labelframe(paned, text=" Построчный реестр операторов и условий ", padding=5)
        self.txt_log = tk.Text(frame_right, wrap=tk.NONE, width=50)
        self.txt_log.pack(fill=tk.BOTH, expand=True)
        paned.add(frame_right, weight=1)

        results_frame = ttk.LabelFrame(frame, text=" Результаты расчёта метрик Джилба ", padding=10)
        results_frame.pack(fill=tk.X)

        self.lbl_cl = ttk.Label(results_frame, text="Абсолютная сложность (CL): —", font=("Arial", 11, "bold"))
        self.lbl_cl.pack(anchor=tk.W, pady=2)

        self.lbl_nesting = ttk.Label(results_frame, text="Максимальный уровень вложенности (CLI): —",
                                     font=("Arial", 11, "bold"))
        self.lbl_nesting.pack(anchor=tk.W, pady=2)

        self.lbl_rel = ttk.Label(results_frame, text="Относительная сложность (cl = CL / N_op): —",
                                 font=("Arial", 11, "bold"))
        self.lbl_rel.pack(anchor=tk.W, pady=2)

        self.lbl_ops = ttk.Label(results_frame, text="Всего операторов (N_op): —", font=("Arial", 9))
        self.lbl_ops.pack(anchor=tk.W, pady=2)

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if not filepath:
            return

        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        self.txt_preview.delete("1.0", tk.END)
        self.txt_preview.insert(tk.END, code)

        self.txt_log.delete("1.0", tk.END)

        try:
            tree = ast.parse(code)
            calc = MetricsCalculator()
            calc.visit(tree)

            rel_cl = (calc.cl / calc.statements_count) if calc.statements_count > 0 else 0

            self.lbl_cl.config(text=f"Абсолютная сложность (CL): {calc.cl}")
            self.lbl_nesting.config(text=f"Максимальный уровень вложенности (CLI): {calc.max_nesting}")
            self.lbl_rel.config(text=f"Относительная сложность (cl = CL / N_op): {rel_cl:.4f} ({rel_cl * 100:.2f}%)")
            self.lbl_ops.config(text=f"Всего операторов (N_op): {calc.statements_count}")

            for line in calc.log_items:
                self.txt_log.insert(tk.END, line + "\n")

        except SyntaxError as e:
            messagebox.showerror("Ошибка синтаксиса", f"Ошибка при разборе кода:\n{e}")


if __name__ == "__main__":
    app_window = tk.Tk()
    app = ParserApp(app_window)
    app_window.mainloop()
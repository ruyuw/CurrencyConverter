import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

API_KEY = "18ce20439aafc0a14f2a9a77"  # Замените на реальный ключ
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/"

HISTORY_FILE = "history.json"

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        # Доступные валюты
        self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "CHF", "CAD", "AUD", "TRY"]

        # Загрузка истории
        self.history = self.load_history()

        # Создание интерфейса
        self.create_widgets()
        self.update_history_table()

    def create_widgets(self):
        # Рамка ввода
        input_frame = ttk.LabelFrame(self.root, text="Конвертация", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5)
        self.amount_entry = ttk.Entry(input_frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Из валюты:").grid(row=0, column=2, padx=5, pady=5)
        self.from_currency = ttk.Combobox(input_frame, values=self.currencies, width=7, state="readonly")
        self.from_currency.set("USD")
        self.from_currency.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="В валюту:").grid(row=0, column=4, padx=5, pady=5)
        self.to_currency = ttk.Combobox(input_frame, values=self.currencies, width=7, state="readonly")
        self.to_currency.set("EUR")
        self.to_currency.grid(row=0, column=5, padx=5, pady=5)

        self.convert_btn = ttk.Button(input_frame, text="Конвертировать", command=self.convert)
        self.convert_btn.grid(row=0, column=6, padx=10, pady=5)

        # Результат
        self.result_label = ttk.Label(input_frame, text="Результат: ---", font=("Arial", 10, "bold"))
        self.result_label.grid(row=1, column=0, columnspan=7, pady=10)

        # Таблица истории
        history_frame = ttk.LabelFrame(self.root, text="История конвертаций", padding=10)
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("Дата", "Сумма", "Из", "В", "Результат")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Кнопка очистки
        self.clear_btn = ttk.Button(self.root, text="Очистить историю", command=self.clear_history)
        self.clear_btn.pack(pady=5)

    def validate_amount(self, amount_str):
        """Валидация ввода суммы"""
        try:
            amount = float(amount_str)
            if amount <= 0:
                return None, "Сумма должна быть больше нуля"
            return amount, None
        except ValueError:
            return None, "Введите корректное число"

    def convert(self):
        amount_str = self.amount_entry.get().strip()
        amount, error = self.validate_amount(amount_str)
        if error:
            messagebox.showerror("Ошибка ввода", error)
            return

        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()

        if from_curr == to_curr:
            result = amount
            result_str = f"{result:.4f} {to_curr}"
            self.result_label.config(text=f"Результат: {result_str}")
            self.add_to_history(amount, from_curr, to_curr, result)
            return

        # Запрос к API
        try:
            url = BASE_URL + from_curr
            response = requests.get(url, verify=False, timeout=5)
            data = response.json()

            if data["result"] == "success":
                rate = data["conversion_rates"].get(to_curr)
                if rate:
                    result = amount * rate
                    result_str = f"{result:.4f} {to_curr}"
                    self.result_label.config(text=f"Результат: {result_str}")
                    self.add_to_history(amount, from_curr, to_curr, result)
                else:
                    messagebox.showerror("Ошибка", f"Валюта {to_curr} не найдена")
            else:
                messagebox.showerror("Ошибка API", "Не удалось получить курс")
        except requests.RequestException:
            messagebox.showerror("Ошибка сети", "Проверьте подключение к интернету и API-ключ")

    def add_to_history(self, amount, from_curr, to_curr, result):
        record = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "from": from_curr,
            "to": to_curr,
            "result": round(result, 4)
        }
        self.history.insert(0, record)  # новые сверху
        if len(self.history) > 20:  # храним последние 20 записей
            self.history.pop()
        self.save_history()
        self.update_history_table()

    def update_history_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for record in self.history:
            self.tree.insert("", "end", values=(
                record["datetime"],
                f"{record['amount']} {record['from']}",
                record["from"],
                record["to"],
                f"{record['result']} {record['to']}"
            ))

    def clear_history(self):
        if messagebox.askyesno("Подтверждение", "Очистить всю историю?"):
            self.history = []
            self.save_history()
            self.update_history_table()
            self.result_label.config(text="Результат: ---")

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_history(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()

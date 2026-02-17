import tkinter as tk
from tkinter import ttk
import requests
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import json

COLORS = {
    'bg': '#0A0A0A',
    'card': '#111111',
    'green': '#00FF88',
    'green_dark': '#00AA55',
    'white': '#FFFFFF',
    'gray': '#888888',
    'input_bg': '#1A1A1A',
    'blue': '#0088FF',
    'red': '#FF4444',
    'yellow': '#FFD700'
}

SOURCES = {
    "ЦБ РФ": {
        "url": "https://www.cbr-xml-daily.ru/daily_json.js",
        "base_currency": "RUB"
    },
    "ExchangeRate-API": {
        "url": "https://api.exchangerate-api.com/v4/latest/USD",
        "base_currency": "USD"
    },
    "Frankfurter": {
        "url": "https://api.frankfurter.app/latest",
        "base_currency": "EUR"
    },
    "Криптовалюты": {
        "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",
        "base_currency": "USD"
    }
}

current_source = "ЦБ РФ"
rates = {}
currency_names = {}
currencies = {}
conversion_history = []
MAX_HISTORY_ITEMS = 10

def add_to_history(amount, from_curr, result, to_curr):
    timestamp = datetime.now().strftime("%H:%M:%S")
    conversion = {
        'timestamp': timestamp,
        'amount': amount,
        'from_curr': from_curr,
        'result': result,
        'to_curr': to_curr
    }
    conversion_history.insert(0, conversion)
    if len(conversion_history) > MAX_HISTORY_ITEMS:
        conversion_history.pop()
    update_history_display()

def update_history_display():
    history_text = ""
    for item in conversion_history:
        history_text += f"{item['timestamp']}  {item['amount']} {item['from_curr']} → {item['result']} {item['to_curr']}\n"
    
    if hasattr(app, 'history_text'):
        app.history_text.config(state='normal')
        app.history_text.delete('1.0', tk.END)
        app.history_text.insert('1.0', history_text if history_text else "История пуста")
        app.history_text.config(state='disabled')

def clear_history():
    conversion_history.clear()
    update_history_display()
    app.status_var.set("История очищена")

def get_currency_name(code):
    return currencies.get(code, code)

def update_currency_names(from_var, to_var, from_name_var, to_name_var):
    from_name_var.set(get_currency_name(from_var.get()))
    to_name_var.set(get_currency_name(to_var.get()))

def parse_cbr_data(data):
    global rates, currency_names
    rates = data['Valute']
    rates['RUB'] = {'Value': 1, 'Nominal': 1, 'Name': 'Российский рубль'}
    for code, info in rates.items():
        currency_names[code] = info.get('Name', code)
    return list(rates.keys())

def parse_exchangerate_data(data):
    global rates, currency_names
    rates = data['rates']
    rates['USD'] = 1.0
    currency_names['USD'] = 'Доллар США'
    for code in rates.keys():
        if code not in currency_names:
            currency_names[code] = code
    return list(rates.keys())

def parse_frankfurter_data(data):
    global rates, currency_names
    rates = data['rates']
    rates['EUR'] = 1.0
    currency_names['EUR'] = 'Евро'
    for code in rates.keys():
        if code not in currency_names:
            currency_names[code] = code
    return list(rates.keys())

def parse_crypto_data(data):
    global rates, currency_names
    rates = {}
    currency_names = {}
    if 'bitcoin' in data:
        rates['BTC'] = data['bitcoin']['usd']
        currency_names['BTC'] = 'Биткойн'
    if 'ethereum' in data:
        rates['ETH'] = data['ethereum']['usd']
        currency_names['ETH'] = 'Эфириум'
    rates['USD'] = 1.0
    currency_names['USD'] = 'Доллар США'
    rates['EUR'] = 0.92
    currency_names['EUR'] = 'Евро'
    rates['RUB'] = 90.0
    currency_names['RUB'] = 'Российский рубль'
    return list(rates.keys())

def update_rates():
    global current_source
    current_source = app.source_var.get()
    app.status_var.set("Обновление курсов...")
    try:
        source_info = SOURCES[current_source]
        data = requests.get(source_info["url"], timeout=10).json()
        
        if current_source == "ЦБ РФ":
            currencies_list = parse_cbr_data(data)
        elif current_source == "ExchangeRate-API":
            currencies_list = parse_exchangerate_data(data)
        elif current_source == "Frankfurter":
            currencies_list = parse_frankfurter_data(data)
        elif current_source == "Криптовалюты":
            currencies_list = parse_crypto_data(data)
            
        app.from_combo['values'] = sorted(currencies_list)
        app.to_combo['values'] = sorted(currencies_list)
        base_currency = source_info["base_currency"]
        
        if app.from_var.get() not in currencies_list:
            app.from_var.set(base_currency)
        if app.to_var.get() not in currencies_list:
            app.to_var.set("RUB" if "RUB" in currencies_list else list(currencies_list)[0] if currencies_list else base_currency)
            
        update_currency_names(app.from_var, app.to_var, app.from_name_var, app.to_name_var)
        now = datetime.now().strftime("%H:%M:%S")
        app.status_var.set(f"{current_source} | Обновлено в {now}")
        convert()
        
    except requests.exceptions.ConnectionError:
        app.status_var.set("Ошибка: Нет подключения к интернету")
        app.result_var.set("Проверьте подключение")
    except requests.exceptions.Timeout:
        app.status_var.set("Ошибка: Таймаут соединения")
        app.result_var.set("Попробуйте позже")
    except Exception as e:
        app.status_var.set(f"Ошибка: {str(e)[:30]}")
        app.result_var.set("Ошибка загрузки данных")

def get_rate(currency):
    if current_source == "ЦБ РФ":
        if currency == 'RUB':
            return Decimal(1)
        rate_info = rates.get(currency)
        if rate_info:
            return Decimal(rate_info['Value']) / Decimal(rate_info['Nominal'])
    else:
        rate = rates.get(currency)
        if rate is not None:
            return Decimal(str(rate))
    return None

def convert():
    try:
        amount_str = app.amount_var.get().replace(',', '.')
        if not amount_str or amount_str in ['.', ',']:
            app.result_var.set("Введите сумму")
            return
            
        amount = Decimal(amount_str)
        if amount <= 0:
            app.result_var.set("Введите сумму > 0")
            return
            
        from_curr = app.from_var.get()
        to_curr = app.to_var.get()
        
        if from_curr == to_curr:
            result = amount
        else:
            from_rate = get_rate(from_curr)
            to_rate = get_rate(to_curr)
            if from_rate is None or to_rate is None:
                app.result_var.set("Нет данных по валюте")
                return
                
            result = amount * from_rate / to_rate if current_source == "ЦБ РФ" else amount * to_rate / from_rate
            
        result = result.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        amount_formatted = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
        result_formatted = f"{result:,.4f}".replace(',', ' ').replace('.', ',')
        result_string = f"{amount_formatted} {from_curr} = {result_formatted} {to_curr}"
        app.result_var.set(result_string)
        
        add_to_history(amount_formatted, from_curr, result_formatted, to_curr)
        
        update_currency_names(app.from_var, app.to_var, app.from_name_var, app.to_name_var)
        
    except ValueError:
        app.result_var.set("Введите число")
    except Exception as e:
        app.result_var.set("Ошибка расчета")

def swap_currencies():
    from_curr = app.from_var.get()
    to_curr = app.to_var.get()
    app.from_var.set(to_curr)
    app.to_var.set(from_curr)
    convert()

class CurrencyConverterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Конвертер валют by Sqwerel")
        self.root.geometry("550x650")
        self.root.configure(bg=COLORS['bg'])
        self.root.resizable(False, False)
        
        self.setup_styles()
        self.create_variables()
        self.create_widgets()
        self.bind_events()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLORS['card'])
        style.configure('TLabel', background=COLORS['card'], foreground=COLORS['gray'])
        style.configure('Title.TLabel', background=COLORS['bg'], foreground=COLORS['green'],
                        font=('Arial', 16, 'bold'))
        style.configure('Result.TLabel', background=COLORS['card'], foreground=COLORS['green'],
                        font=('Arial', 14, 'bold'))
        style.configure('Status.TLabel', background=COLORS['bg'], foreground=COLORS['gray'])
        style.configure('CurrencyName.TLabel', background=COLORS['card'], foreground=COLORS['blue'],
                        font=('Arial', 9))
        style.configure('History.TLabel', background=COLORS['bg'], foreground=COLORS['yellow'],
                        font=('Arial', 10, 'bold'))
        style.configure('TEntry', fieldbackground=COLORS['input_bg'], foreground=COLORS['white'],
                        borderwidth=2, insertcolor=COLORS['green'], padding=5)
        style.configure('TCombobox', fieldbackground=COLORS['input_bg'], foreground=COLORS['white'],
                        borderwidth=2)
        style.map('TCombobox',
                  fieldbackground=[('readonly', COLORS['input_bg'])],
                  selectbackground=[('readonly', COLORS['green'])],
                  selectforeground=[('readonly', COLORS['bg'])])

    def create_variables(self):
        self.amount_var = tk.StringVar(value="100")
        self.source_var = tk.StringVar(value=current_source)
        self.from_var = tk.StringVar(value="USD")
        self.to_var = tk.StringVar(value="RUB")
        self.result_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Загрузка...")
        self.from_name_var = tk.StringVar()
        self.to_name_var = tk.StringVar()

    def create_widgets(self):
        ttk.Label(self.root, text="Конвертер валют by Sqwerel", style='Title.TLabel').pack(pady=15)
        
        source_frame = ttk.Frame(self.root)
        source_frame.pack(pady=10, padx=25, fill='x')
        ttk.Label(source_frame, text="Источник данных:").grid(row=0, column=0, sticky='w')
        self.source_combo = ttk.Combobox(source_frame, textvariable=self.source_var,
                                       values=list(SOURCES.keys()), state="readonly", width=25)
        self.source_combo.grid(row=0, column=1, sticky='e')
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=10, padx=25, fill='x')
        
        ttk.Label(main_frame, text="Сумма:").grid(row=0, column=0, sticky='w', pady=8)
        self.amount_entry = ttk.Entry(main_frame, textvariable=self.amount_var, width=25)
        self.amount_entry.grid(row=0, column=1, columnspan=2, sticky='e', pady=8, padx=5)
        
        ttk.Label(main_frame, text="Из валюты:").grid(row=1, column=0, sticky='w', pady=5)
        from_frame = ttk.Frame(main_frame)
        from_frame.grid(row=1, column=1, sticky='w', pady=5)
        self.from_combo = ttk.Combobox(from_frame, textvariable=self.from_var, width=10)
        self.from_combo.pack(side='left')
        ttk.Label(from_frame, textvariable=self.from_name_var, style='CurrencyName.TLabel').pack(side='left', padx=5)
        
        self.swap_btn = tk.Button(main_frame, text="⇄", bg=COLORS['green'], fg=COLORS['bg'],
                                 font=('Arial', 10, 'bold'), bd=0, padx=8, cursor="hand2")
        self.swap_btn.grid(row=1, column=2, pady=5)
        
        ttk.Label(main_frame, text="В валюту:").grid(row=2, column=0, sticky='w', pady=5)
        to_frame = ttk.Frame(main_frame)
        to_frame.grid(row=2, column=1, sticky='w', pady=5)
        self.to_combo = ttk.Combobox(to_frame, textvariable=self.to_var, width=10)
        self.to_combo.pack(side='left')
        ttk.Label(to_frame, textvariable=self.to_name_var, style='CurrencyName.TLabel').pack(side='left', padx=5)
        
        result_frame = ttk.Frame(self.root)
        result_frame.pack(pady=15, padx=25, fill='x')
        ttk.Label(result_frame, textvariable=self.result_var, style='Result.TLabel').pack()
        
        history_frame = ttk.Frame(self.root)
        history_frame.pack(pady=10, padx=25, fill='both', expand=True)
        
        history_header = ttk.Frame(history_frame)
        history_header.pack(fill='x', pady=5)
        ttk.Label(history_header, text="Последние конвертации", style='History.TLabel').pack(side='left')
        
        clear_history_btn = tk.Button(history_header, text="Очистить", bg=COLORS['red'], fg=COLORS['white'],
                                     font=('Arial', 8), bd=0, padx=10, cursor="hand2", command=clear_history)
        clear_history_btn.pack(side='right')
        
        history_text_frame = ttk.Frame(history_frame)
        history_text_frame.pack(fill='both', expand=True)
        
        self.history_text = tk.Text(history_text_frame, height=8, bg=COLORS['input_bg'], fg=COLORS['white'],
                                   font=('Courier', 9), wrap='word', bd=2, relief='flat')
        self.history_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(history_text_frame, orient='vertical', command=self.history_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.history_text.configure(yscrollcommand=scrollbar.set)
        self.history_text.insert('1.0', "История пуста")
        self.history_text.config(state='disabled')
        
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side='bottom', fill='x', pady=10)
        ttk.Label(status_frame, textvariable=self.status_var, style='Status.TLabel').pack()
        
        self.refresh_btn = tk.Button(self.root, text="🔄 Обновить", bg=COLORS['blue'], fg=COLORS['white'],
                                   font=('Arial', 9), bd=0, padx=15, pady=5, cursor="hand2")
        self.refresh_btn.pack(pady=5)

    def bind_events(self):
        self.source_combo.bind('<<ComboboxSelected>>', lambda e: update_rates())
        self.swap_btn.config(command=swap_currencies)
        self.refresh_btn.config(command=update_rates)
        
        self.amount_var.trace_add('write', lambda *args: convert())
        self.from_var.trace_add('write', lambda *args: convert())
        self.to_var.trace_add('write', lambda *args: convert())
        self.from_combo.bind('<<ComboboxSelected>>', lambda e: convert())
        self.to_combo.bind('<<ComboboxSelected>>', lambda e: convert())

    def run(self):
        with open("currencies.json", "r", encoding='utf-8') as f:
            global currencies
            currencies = json.JSONDecoder().decode(f.read())
        update_rates()
        self.amount_entry.focus_set()
        self.amount_entry.select_range(0, tk.END)
        self.root.mainloop()

app = CurrencyConverterApp()

if __name__ == "__main__":
    app.run()
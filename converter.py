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
            currencies = parse_crypto_data(data)
        from_combo['values'] = sorted(currencies)
        to_combo['values'] = sorted(currencies)
        base_currency = source_info["base_currency"]
        if from_var.get() not in currencies:
            from_var.set(base_currency)
        if to_var.get() not in currencies:
            to_var.set("RUB" if "RUB" in currencies else list(currencies)[0] if currencies else base_currency)
        update_currency_names(from_var, to_var, from_name_var, to_name_var)
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
        result_var.set(f"{amount_formatted} {from_curr} = {result_formatted} {to_curr}")
        update_currency_names(from_var, to_var, from_name_var, to_name_var)
    except ValueError:
        result_var.set("Введите число")
    except Exception as e:
        result_var.set("Ошибка расчета")

def on_amount_change_wrapper(*args, amount_var, from_var, to_var, result_var, from_name_var, to_name_var):
    convert_wrapper(amount_var, from_var, to_var, result_var, from_name_var, to_name_var)

def on_currency_change_wrapper(*args, amount_var, from_var, to_var, result_var, from_name_var, to_name_var):
    convert_wrapper(amount_var, from_var, to_var, result_var, from_name_var, to_name_var)

def change_source_wrapper(event, source_var, status_var, from_combo, to_combo, 
                         from_var, to_var, from_name_var, to_name_var, result_var):
    update_rates_wrapper(source_var, status_var, from_combo, to_combo,
                        from_var, to_var, from_name_var, to_name_var, result_var)

def swap_currencies_wrapper(from_var, to_var, amount_var, result_var, from_name_var, to_name_var):
    from_curr = from_var.get()
    to_curr = to_var.get()
    from_var.set(to_curr)
    to_var.set(from_curr)
    convert_wrapper(amount_var, from_var, to_var, result_var, from_name_var, to_name_var)

def create_window():
    root = tk.Tk()
    root.title("Конвертер валют")
    root.geometry("450x500")
    root.configure(bg=COLORS['bg'])
    root.resizable(False, False)
    return root

def setup_styles():
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
    style.configure('TEntry',
                    fieldbackground=COLORS['input_bg'],
                    foreground=COLORS['white'],
                    borderwidth=2,
                    insertcolor=COLORS['green'],
                    padding=5)
    style.configure('TCombobox',
                    fieldbackground=COLORS['input_bg'],
                    foreground=COLORS['white'],
                    borderwidth=2)
    style.map('TCombobox',
              fieldbackground=[('readonly', COLORS['input_bg'])],
              selectbackground=[('readonly', COLORS['green'])],
              selectforeground=[('readonly', COLORS['bg'])])
    return style

def create_title_section(root):
    title_frame = ttk.Frame(root)
    title_frame.pack(pady=15)
    ttk.Label(title_frame, text="КОНВЕРТЕР ВАЛЮТ by Sqwerel", style='Title.TLabel').pack()
    return title_frame

def create_source_section(root, source_var):
    source_frame = ttk.Frame(root)
    source_frame.pack(pady=10, padx=25, fill='x')
    ttk.Label(source_frame, text="Источник данных:").grid(row=0, column=0, sticky='w')
    source_combo = ttk.Combobox(source_frame, textvariable=source_var,
                                values=list(SOURCES.keys()), state="readonly", width=25)
    source_combo.grid(row=0, column=1, sticky='e')
    return source_frame, source_combo

def create_main_section(root, amount_var, from_var, to_var, from_name_var, to_name_var):
    main_frame = ttk.Frame(root)
    main_frame.pack(pady=10, padx=25, fill='x')
    ttk.Label(main_frame, text="Сумма:").grid(row=0, column=0, sticky='w', pady=8)
    amount_entry = ttk.Entry(main_frame, textvariable=amount_var, width=25)
    amount_entry.grid(row=0, column=1, columnspan=2, sticky='e', pady=8, padx=5)
    ttk.Label(main_frame, text="Из валюты:").grid(row=1, column=0, sticky='w', pady=5)
    from_frame = ttk.Frame(main_frame)
    from_frame.grid(row=1, column=1, sticky='w', pady=5)
    from_combo = ttk.Combobox(from_frame, textvariable=from_var, width=10)
    from_combo.pack(side='left')
    ttk.Label(from_frame, textvariable=from_name_var, style='CurrencyName.TLabel').pack(side='left', padx=5)
    swap_btn = tk.Button(main_frame, text="⇄", 
                        bg=COLORS['green'], fg=COLORS['bg'],
                        font=('Arial', 10, 'bold'), bd=0, padx=8,
                        cursor="hand2")
    swap_btn.grid(row=1, column=2, pady=5)
    ttk.Label(main_frame, text="В валюту:").grid(row=2, column=0, sticky='w', pady=5)
    to_frame = ttk.Frame(main_frame)
    to_frame.grid(row=2, column=1, sticky='w', pady=5)
    to_combo = ttk.Combobox(to_frame, textvariable=to_var, width=10)
    to_combo.pack(side='left')
    ttk.Label(to_frame, textvariable=to_name_var, style='CurrencyName.TLabel').pack(side='left', padx=5)
    return main_frame, amount_entry, from_combo, to_combo, swap_btn

def create_result_section(root, result_var):
    result_frame = ttk.Frame(root)
    result_frame.pack(pady=15, padx=25, fill='x')
    result_label = ttk.Label(result_frame, textvariable=result_var, style='Result.TLabel')
    result_label.pack()
    return result_frame

def create_status_section(root, status_var):
    status_frame = ttk.Frame(root)
    status_frame.pack(side='bottom', fill='x', pady=10)
    status_label = ttk.Label(status_frame, textvariable=status_var, style='Status.TLabel')
    status_label.pack()
    return status_frame

def create_refresh_button(root):
    refresh_btn = tk.Button(root, text="🔄 Обновить",
                           bg=COLORS['blue'], fg=COLORS['white'],
                           font=('Arial', 9), bd=0, padx=15, pady=5,
                           cursor="hand2")
    refresh_btn.pack(pady=5)
    return refresh_btn

def main():
    global amount_var
    root = create_window()
    setup_styles()
    amount_var = tk.StringVar(value="100")
    source_var = tk.StringVar(value=current_source)
    from_var = tk.StringVar(value="USD")
    to_var = tk.StringVar(value="RUB")
    result_var = tk.StringVar(value="")
    status_var = tk.StringVar(value="Загрузка...")
    from_name_var = tk.StringVar(value="")
    to_name_var = tk.StringVar(value="")
    create_title_section(root)
    source_frame, source_combo = create_source_section(root, source_var)
    main_frame, amount_entry, from_combo, to_combo, swap_btn = create_main_section(
        root, amount_var, from_var, to_var, from_name_var, to_name_var
    )
    create_result_section(root, result_var)
    create_status_section(root, status_var)
    refresh_btn = create_refresh_button(root)
    def change_source_handler(event=None):
        change_source_wrapper(event, source_var, status_var, from_combo, to_combo,
                            from_var, to_var, from_name_var, to_name_var, result_var)
    def swap_currencies_handler():
        swap_currencies_wrapper(from_var, to_var, amount_var, result_var, from_name_var, to_name_var)
    def on_amount_change_handler(*args):
        on_amount_change_wrapper(amount_var=amount_var, from_var=from_var, to_var=to_var,
                               result_var=result_var, from_name_var=from_name_var,
                               to_name_var=to_name_var)
    def on_currency_change_handler(*args):
        on_currency_change_wrapper(amount_var=amount_var, from_var=from_var, to_var=to_var,
                                 result_var=result_var, from_name_var=from_name_var,
                                 to_name_var=to_name_var)
    def update_rates_handler():
        update_rates_wrapper(source_var, status_var, from_combo, to_combo,
                           from_var, to_var, from_name_var, to_name_var, result_var)
    source_combo.bind('<<ComboboxSelected>>', change_source_handler)
    swap_btn.config(command=swap_currencies_handler)
    refresh_btn.config(command=update_rates_handler)
    amount_var.trace_add('write', on_amount_change_handler)
    from_var.trace_add('write', on_currency_change_handler)
    to_var.trace_add('write', on_currency_change_handler)
    from_combo.bind('<<ComboboxSelected>>', lambda e: on_currency_change_handler())
    to_combo.bind('<<ComboboxSelected>>', lambda e: on_currency_change_handler())
    update_rates_handler()
    amount_entry.focus_set()
    amount_entry.select_range(0, tk.END)
    root.mainloop()

if __name__ == "__main__":
    app.run()
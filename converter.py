import tkinter as tk
from tkinter import ttk
import requests
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

root = tk.Tk()
root.title("Конвертер валют")
root.geometry("450x500")
root.configure(bg='#0A0A0A')
root.resizable(False, False)

COLORS = {
    'bg': '#0A0A0A',
    'card': '#111111',
    'green': '#00FF88',
    'green_dark': '#00AA55',
    'white': '#FFFFFF',
    'gray': '#888888',
    'input_bg': '#1A1A1A',
    'blue': '#0088FF',
    'red': '#FF4444'
}

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

sources = {
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

current_source = "ExchangeRate-API"
rates = {}
currency_names = {}

source_var = tk.StringVar(value=current_source)
amount_var = tk.StringVar(value="100")
from_var = tk.StringVar(value="USD")
to_var = tk.StringVar(value="EUR")
result_var = tk.StringVar(value="")
status_var = tk.StringVar(value="Загрузка...")
from_name_var = tk.StringVar(value="")
to_name_var = tk.StringVar(value="")


def get_currency_name(code):
    currency_names_dict = {
        "USD": "Доллар США",
        "EUR": "Евро",
        "GBP": "Фунт стерлингов",
        "JPY": "Японская йена",
        "CNY": "Китайский юань",
        "CHF": "Швейцарский франк",
        "CAD": "Канадский доллар",
        "AUD": "Австралийский доллар",
        "BTC": "Биткойн",
        "ETH": "Эфириум",
        "RUB": "Российский рубль",
        "KZT": "Казахстанский тенге",
        "BYN": "Белорусский рубль",
        "UAH": "Украинская гривна",
        "TRY": "Турецкая лира",
        "INR": "Индийская рупия",
        "BRL": "Бразильский реал",
        "KRW": "Южнокорейская вона",
        "SGD": "Сингапурский доллар",
        "HKD": "Гонконгский доллар",
        "NZD": "Новозеландский доллар",
        "MXN": "Мексиканский песо",
        "SEK": "Шведская крона",
        "NOK": "Норвежская крона",
        "DKK": "Датская крона",
        "PLN": "Польский злотый",
        "THB": "Тайский бат",
        "IDR": "Индонезийская рупия",
        "MYR": "Малайзийский ринггит",
        "PHP": "Филиппинское песо",
        "ZAR": "Южноафриканский рэнд",
        "AED": "Дирхам ОАЭ",
        "SAR": "Саудовский риял",
        "ILS": "Израильский шекель",
        "CZK": "Чешская крона",
        "HUF": "Венгерский форинт",
        "RON": "Румынский лей",
        "BGN": "Болгарский лев",
        "HRK": "Хорватская куна",
        "ISK": "Исландская крона",
        "ARS": "Аргентинское песо",
        "CLP": "Чилийское песо",
        "COP": "Колумбийское песо",
        "PEN": "Перуанский соль",
        "VND": "Вьетнамский донг",
        "EGP": "Египетский фунт",
        "PKR": "Пакистанская рупия",
        "BDT": "Бангладешская така",
        "NGN": "Нигерийская найра",
        "KES": "Кенийский шиллинг",
        "XAU": "Золото (унция)",
        "XAG": "Серебро (унция)"
    }
    return currency_names_dict.get(code, code)


def update_currency_names():
    from_name_var.set(get_currency_name(from_var.get()))
    to_name_var.set(get_currency_name(to_var.get()))


def change_source(event=None):
    global current_source
    current_source = source_var.get()
    update_rates()


def update_rates():
    status_var.set("Обновление курсов...")
    root.update()

    try:
        source_info = sources[current_source]
        url = source_info["url"]
        base_currency = source_info["base_currency"]

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        global rates, currency_names

        if current_source == "ExchangeRate-API":
            rates = data['rates']
            rates['USD'] = 1.0
            currency_names['USD'] = 'Доллар США'

            for code in rates.keys():
                if code not in currency_names:
                    currency_names[code] = get_currency_name(code)

            currencies = list(rates.keys())

        elif current_source == "Frankfurter":
            rates = data['rates']
            rates['EUR'] = 1.0
            currency_names['EUR'] = 'Евро'

            for code in rates.keys():
                if code not in currency_names:
                    currency_names[code] = get_currency_name(code)

            currencies = list(rates.keys())

        elif current_source == "Криптовалюты":
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

            currencies = list(rates.keys())

        from_combo['values'] = sorted(currencies)
        to_combo['values'] = sorted(currencies)

        if from_var.get() not in currencies:
            from_var.set(base_currency)
        if to_var.get() not in currencies:
            to_var.set("EUR" if "EUR" in currencies else list(currencies)[0] if currencies else base_currency)

        update_currency_names()

        now = datetime.now().strftime("%H:%M:%S")
        status_var.set(f"{current_source} | Обновлено в {now}")
        convert()

    except requests.exceptions.ConnectionError:
        status_var.set("Ошибка: Нет подключения к интернету")
        result_var.set("Проверьте подключение")
    except requests.exceptions.Timeout:
        status_var.set("Ошибка: Таймаут соединения")
        result_var.set("Попробуйте позже")
    except Exception as e:
        status_var.set(f"Ошибка: {str(e)[:30]}")
        result_var.set("Ошибка загрузки данных")
        print(f"Ошибка при обновлении курсов: {e}")


def get_rate(currency):
    rate = rates.get(currency)
    if rate is not None:
        return Decimal(str(rate))
    return None


def convert():
    try:
        amount_str = amount_var.get().replace(',', '.')
        if not amount_str or amount_str == '.' or amount_str == ',':
            result_var.set("Введите сумму")
            return

        amount = Decimal(amount_str)
        if amount <= 0:
            result_var.set("Введите сумму > 0")
            return

        from_curr = from_var.get()
        to_curr = to_var.get()

        if from_curr == to_curr:
            result = amount
        else:
            from_rate = get_rate(from_curr)
            to_rate = get_rate(to_curr)

            if from_rate is None or to_rate is None:
                result_var.set("Нет данных по валюте")
                return

            result = amount * to_rate / from_rate

        result = result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        amount_formatted = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
        result_formatted = f"{result:,.2f}".replace(',', ' ').replace('.', ',')

        result_var.set(f"{amount_formatted} {from_curr} = {result_formatted} {to_curr}")
        update_currency_names()

    except ValueError:
        result_var.set("Введите число")
    except Exception as e:
        result_var.set("Ошибка расчета")
        print(f"Ошибка при конвертации: {e}")


def swap_currencies():
    from_curr = from_var.get()
    to_curr = to_var.get()
    from_var.set(to_curr)
    to_var.set(from_curr)
    convert()


def on_amount_change(*args):
    convert()


def on_currency_change(*args):
    convert()


title_frame = ttk.Frame(root)
title_frame.pack(pady=15)

ttk.Label(title_frame, text="КОНВЕРТЕР ВАЛЮТ by Sqwerel", style='Title.TLabel').pack()

source_frame = ttk.Frame(root)
source_frame.pack(pady=10, padx=25, fill='x')

ttk.Label(source_frame, text="Источник данных:").grid(row=0, column=0, sticky='w')
source_combo = ttk.Combobox(source_frame, textvariable=source_var,
                            values=list(sources.keys()), state="readonly", width=25)
source_combo.grid(row=0, column=1, sticky='e')
source_combo.bind('<<ComboboxSelected>>', change_source)

main_frame = ttk.Frame(root)
main_frame.pack(pady=10, padx=25, fill='x')

ttk.Label(main_frame, text="Сумма:").grid(row=0, column=0, sticky='w', pady=8)
amount_entry = ttk.Entry(main_frame, textvariable=amount_var, width=25)
amount_entry.grid(row=0, column=1, columnspan=2, sticky='e', pady=8, padx=5)
amount_var.trace_add('write', on_amount_change)

ttk.Label(main_frame, text="Из валюты:").grid(row=1, column=0, sticky='w', pady=5)
from_frame = ttk.Frame(main_frame)
from_frame.grid(row=1, column=1, sticky='w', pady=5)

from_combo = ttk.Combobox(from_frame, textvariable=from_var, width=10)
from_combo.pack(side='left')
from_combo.bind('<<ComboboxSelected>>', on_currency_change)

ttk.Label(from_frame, textvariable=from_name_var, style='CurrencyName.TLabel').pack(side='left', padx=5)

swap_btn = tk.Button(main_frame, text="⇄", command=swap_currencies,
                     bg=COLORS['green'], fg=COLORS['bg'],
                     font=('Arial', 10, 'bold'), bd=0, padx=8,
                     cursor="hand2")
swap_btn.grid(row=1, column=2, pady=5)

ttk.Label(main_frame, text="В валюту:").grid(row=2, column=0, sticky='w', pady=5)
to_frame = ttk.Frame(main_frame)
to_frame.grid(row=2, column=1, sticky='w', pady=5)

to_combo = ttk.Combobox(to_frame, textvariable=to_var, width=10)
to_combo.pack(side='left')
to_combo.bind('<<ComboboxSelected>>', on_currency_change)

ttk.Label(to_frame, textvariable=to_name_var, style='CurrencyName.TLabel').pack(side='left', padx=5)

result_frame = ttk.Frame(root)
result_frame.pack(pady=15, padx=25, fill='x')

result_label = ttk.Label(result_frame, textvariable=result_var, style='Result.TLabel')
result_label.pack()

status_frame = ttk.Frame(root)
status_frame.pack(side='bottom', fill='x', pady=10)

status_label = ttk.Label(status_frame, textvariable=status_var, style='Status.TLabel')
status_label.pack()

info_frame = ttk.Frame(root)
info_frame.pack(side='bottom', fill='x', pady=5)


refresh_btn = tk.Button(root, text="🔄 Обновить", command=update_rates,
                        bg=COLORS['blue'], fg=COLORS['white'],
                        font=('Arial', 9), bd=0, padx=15, pady=5,
                        cursor="hand2")
refresh_btn.pack(pady=5)

update_rates()
amount_entry.focus_set()
amount_entry.select_range(0, tk.END)

from_var.trace_add('write', on_currency_change)
to_var.trace_add('write', on_currency_change)

root.mainloop()
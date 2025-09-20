import locale
currency_mapping = [
    ("INR", "🇮🇳 Indian Rupee (₹)"),
    ("USD", "🇺🇸 US Dollar ($)"),
    ("EUR", "🇪🇺 Euro (€)"),
    ("GBP", "🇬🇧 British Pound (£)"),
    ("JPY", "🇯🇵 Japanese Yen (¥)"),
    ("CAD", "🇨🇦 Canadian Dollar (C$)"),
    ("AUD", "🇦🇺 Australian Dollar (A$)"),
    ("CHF", "🇨🇭 Swiss Franc (CHF)"),
    ("BRL", "🇧🇷 Brazilian Real (R$)"),
    ("MXN", "🇲🇽 Mexican Peso ($)"),
    ("SGD", "🇸🇬 Singapore Dollar (S$)"),
    ("HKD", "🇭🇰 Hong Kong Dollar (HK$)"),
    ("NZD", "🇳🇿 New Zealand Dollar (NZ$)"),
    ("CNY", "🇨🇳 Chinese Yuan (¥)"),
    ("KRW", "🇰🇷 South Korean Won (₩)"),
    ("THB", "🇹🇭 Thai Baht (฿)"),
    ("MYR", "🇲🇾 Malaysian Ringgit (RM)"),
    ("IDR", "🇮🇩 Indonesian Rupiah (Rp)"),
    ("PHP", "🇵🇭 Philippine Peso (₱)"),
    ("VND", "🇻🇳 Vietnamese Dong (₫)"),
    ("TRY", "🇹🇷 Turkish Lira (₺)"),
    ("AED", "🇦🇪 UAE Dirham (د.إ)"),
    ("SAR", "🇸🇦 Saudi Riyal (ر.س)"),
    ("ILS", "🇮🇱 Israeli Shekel (₪)"),
    ("PKR", "🇵🇰 Pakistani Rupee (₨)"),
    ("BDT", "🇧🇩 Bangladeshi Taka (৳)"),
    ("LKR", "🇱🇰 Sri Lankan Rupee (₨)"),
    ("NPR", "🇳🇵 Nepalese Rupee (₨)")
]

def get_currency_options():
    """Get list of popular currencies with their symbols and codes"""
    return {
            "USD": {"symbol": "$", "name": "US Dollar"},
            "EUR": {"symbol": "€", "name": "Euro"},
            "GBP": {"symbol": "£", "name": "British Pound"},
            "JPY": {"symbol": "¥", "name": "Japanese Yen"},
            "CAD": {"symbol": "C$", "name": "Canadian Dollar"},
            "AUD": {"symbol": "A$", "name": "Australian Dollar"},
            "CHF": {"symbol": "CHF", "name": "Swiss Franc"},
            "CNY": {"symbol": "¥", "name": "Chinese Yuan"},
            "INR": {"symbol": "₹", "name": "Indian Rupee"},
            "BRL": {"symbol": "R$", "name": "Brazilian Real"},
            "MXN": {"symbol": "$", "name": "Mexican Peso"},
            "SGD": {"symbol": "S$", "name": "Singapore Dollar"},
            "HKD": {"symbol": "HK$", "name": "Hong Kong Dollar"},
            "NZD": {"symbol": "NZ$", "name": "New Zealand Dollar"},
            "SEK": {"symbol": "kr", "name": "Swedish Krona"},
            "NOK": {"symbol": "kr", "name": "Norwegian Krone"},
            "DKK": {"symbol": "kr", "name": "Danish Krone"},
            "PLN": {"symbol": "zł", "name": "Polish Zloty"},
            "HUF": {"symbol": "Ft", "name": "Hungarian Forint"},
            "RUB": {"symbol": "₽", "name": "Russian Ruble"},
            "ZAR": {"symbol": "R", "name": "South African Rand"},
            "KRW": {"symbol": "₩", "name": "South Korean Won"},
            "THB": {"symbol": "฿", "name": "Thai Baht"},
            "MYR": {"symbol": "RM", "name": "Malaysian Ringgit"},
            "IDR": {"symbol": "Rp", "name": "Indonesian Rupiah"},
            "PHP": {"symbol": "₱", "name": "Philippine Peso"},
            "VND": {"symbol": "₫", "name": "Vietnamese Dong"},
            "TRY": {"symbol": "₺", "name": "Turkish Lira"},
            "AED": {"symbol": "د.إ", "name": "UAE Dirham"},
            "SAR": {"symbol": "﷼", "name": "Saudi Riyal"},
            "ILS": {"symbol": "₪", "name": "Israeli Shekel"},
            "PKR": {"symbol": "₨", "name": "Pakistani Rupee"},
            "BDT": {"symbol": "৳", "name": "Bangladeshi Taka"},
            "LKR": {"symbol": "₨", "name": "Sri Lankan Rupee"},
            "NPR": {"symbol": "₨", "name": "Nepalese Rupee"}
        }



# Map currency symbols → default locales
CURRENCY_LOCALE_MAP = {
    "₹": "en_IN",   # Indian Rupee
    "$": "en_US",   # US Dollar (also MXN, but default to US)
    "€": "de_DE",   # Euro (Germany style)
    "£": "en_GB",   # British Pound
    "¥": "ja_JP",   # Japanese Yen (also CNY, but default to JP)
    "C$": "en_CA",  # Canadian Dollar
    "A$": "en_AU",  # Australian Dollar
    "CHF": "de_CH", # Swiss Franc (Swiss German locale)
    "R$": "pt_BR",  # Brazilian Real
    "S$": "en_SG",  # Singapore Dollar
    "HK$": "zh_HK", # Hong Kong Dollar
    "NZ$": "en_NZ", # New Zealand Dollar
    "₩": "ko_KR",   # South Korean Won
    "฿": "th_TH",   # Thai Baht
    "RM": "ms_MY",  # Malaysian Ringgit
    "Rp": "id_ID",  # Indonesian Rupiah
    "₱": "fil_PH",  # Philippine Peso
    "₫": "vi_VN",   # Vietnamese Dong
    "₺": "tr_TR",   # Turkish Lira
    "د.إ": "ar_AE", # UAE Dirham
    "ر.س": "ar_SA", # Saudi Riyal
    "₪": "he_IL",   # Israeli Shekel
    "₨": "en_PK",   # Pakistani Rupee (also LKR, NPR)
    "৳": "bn_BD",   # Bangladeshi Taka
}


def format_budget(symbol: str, amount: float) -> str:
    """
    Format a number as currency using locale based on symbol.
    Removes decimals.
    """
    loc = CURRENCY_LOCALE_MAP.get(symbol, "en_IN")  # fallback to en_IN
    try:
        locale.setlocale(locale.LC_ALL, loc)
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')  # fallback to system default

    formatted_number = locale.format_string("%d", int(amount), grouping=True)
    return f"{symbol}{formatted_number}"

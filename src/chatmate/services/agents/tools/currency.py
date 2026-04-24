from __future__ import annotations

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from .geocoding import geocode

# ISO 3166-1 alpha-2 → ISO 4217 currency code
_COUNTRY_CURRENCY: dict[str, str] = {
    "AD": "EUR", "AE": "AED", "AF": "AFN", "AL": "ALL", "AM": "AMD",
    "AO": "AOA", "AR": "ARS", "AT": "EUR", "AU": "AUD", "AZ": "AZN",
    "BA": "BAM", "BD": "BDT", "BE": "EUR", "BF": "XOF", "BG": "BGN",
    "BH": "BHD", "BI": "BIF", "BJ": "XOF", "BN": "BND", "BO": "BOB",
    "BR": "BRL", "BT": "BTN", "BW": "BWP", "BY": "BYN", "BZ": "BZD",
    "CA": "CAD", "CD": "CDF", "CF": "XAF", "CG": "XAF", "CH": "CHF",
    "CI": "XOF", "CL": "CLP", "CM": "XAF", "CN": "CNY", "CO": "COP",
    "CR": "CRC", "CU": "CUP", "CV": "CVE", "CY": "EUR", "CZ": "CZK",
    "DE": "EUR", "DJ": "DJF", "DK": "DKK", "DO": "DOP", "DZ": "DZD",
    "EC": "USD", "EE": "EUR", "EG": "EGP", "ER": "ERN", "ES": "EUR",
    "ET": "ETB", "FI": "EUR", "FJ": "FJD", "FR": "EUR", "GA": "XAF",
    "GB": "GBP", "GE": "GEL", "GH": "GHS", "GM": "GMD", "GN": "GNF",
    "GQ": "XAF", "GR": "EUR", "GT": "GTQ", "GW": "XOF", "GY": "GYD",
    "HK": "HKD", "HN": "HNL", "HR": "EUR", "HT": "HTG", "HU": "HUF",
    "ID": "IDR", "IE": "EUR", "IL": "ILS", "IN": "INR", "IQ": "IQD",
    "IR": "IRR", "IS": "ISK", "IT": "EUR", "JM": "JMD", "JO": "JOD",
    "JP": "JPY", "KE": "KES", "KG": "KGS", "KH": "KHR", "KM": "KMF",
    "KP": "KPW", "KR": "KRW", "KW": "KWD", "KZ": "KZT", "LA": "LAK",
    "LB": "LBP", "LK": "LKR", "LR": "LRD", "LS": "LSL", "LT": "EUR",
    "LU": "EUR", "LV": "EUR", "LY": "LYD", "MA": "MAD", "MD": "MDL",
    "ME": "EUR", "MG": "MGA", "MK": "MKD", "ML": "XOF", "MM": "MMK",
    "MN": "MNT", "MR": "MRU", "MT": "EUR", "MU": "MUR", "MV": "MVR",
    "MW": "MWK", "MX": "MXN", "MY": "MYR", "MZ": "MZN", "NA": "NAD",
    "NE": "XOF", "NG": "NGN", "NI": "NIO", "NL": "EUR", "NO": "NOK",
    "NP": "NPR", "NZ": "NZD", "OM": "OMR", "PA": "PAB", "PE": "PEN",
    "PG": "PGK", "PH": "PHP", "PK": "PKR", "PL": "PLN", "PT": "EUR",
    "PY": "PYG", "QA": "QAR", "RO": "RON", "RS": "RSD", "RU": "RUB",
    "RW": "RWF", "SA": "SAR", "SC": "SCR", "SD": "SDG", "SE": "SEK",
    "SG": "SGD", "SI": "EUR", "SK": "EUR", "SL": "SLL", "SN": "XOF",
    "SO": "SOS", "SR": "SRD", "SS": "SSP", "ST": "STN", "SV": "USD",
    "SY": "SYP", "SZ": "SZL", "TD": "XAF", "TG": "XOF", "TH": "THB",
    "TJ": "TJS", "TL": "USD", "TM": "TMT", "TN": "TND", "TO": "TOP",
    "TR": "TRY", "TT": "TTD", "TW": "TWD", "TZ": "TZS", "UA": "UAH",
    "UG": "UGX", "US": "USD", "UY": "UYU", "UZ": "UZS", "VE": "VES",
    "VN": "VND", "VU": "VUV", "WS": "WST", "YE": "YER", "ZA": "ZAR",
    "ZM": "ZMW", "ZW": "ZWL",
}

_SYMBOLS = {"GBP": "£", "EUR": "€", "USD": "$"}


def _fetch_rate(base: str, target: str) -> float | None:
    url = f"https://open.er-api.com/v6/latest/{base}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())
    return data.get("rates", {}).get(target)


def get_exchange_rates(location: str) -> str:
    geo = geocode(location)
    if not geo:
        return f"Could not geocode location: {location}"

    currency = _COUNTRY_CURRENCY.get(geo["country_code"])
    if not currency:
        return f"Unknown currency for country code: {geo['country_code']}"

    bases = [b for b in ("GBP", "EUR", "USD") if b != currency]
    if not bases:
        return f"{geo['name']} uses {currency}, which is one of the base currencies."

    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {base: ex.submit(_fetch_rate, base, currency) for base in bases}

    lines = [f"Exchange rates into {currency} ({geo['name']}, {geo['country']}):"]
    for base, fut in futures.items():
        rate = fut.result()
        sym = _SYMBOLS.get(base, "")
        if rate:
            lines.append(f"  {sym}1 {base} = {rate:,.2f} {currency}")
        else:
            lines.append(f"  {base}: rate unavailable")
    return "\n".join(lines)

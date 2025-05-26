from kafka import KafkaConsumer
import json
import random
import string
from collections import Counter
import psycopg2
from datetime import datetime

# --- Konfiguracje ---
SERVER = "localhost:9092"
TOPIC = "air-data"
AIRLINE_FILTER = "DL"
VOUCHER_LOCATION = "hala A, bramka 4"
MAX_DASHBOARD = 30

# --- Połączenie do PostgreSQL ---
conn = psycopg2.connect(
    dbname="air_data",
    user="user",
    password="password",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# --- Dane dla dashboardu opóźnień ---
delayed_flights = []
reason_counter = Counter()

# --- Funkcje ogólne ---
def generate_voucher_code():
    prefix = random.choice(["DL", "UA", "AF", "LO"])
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefix}-{suffix}"

def generate_voucher_amount():
    return random.choice(range(25, 56, 5))

# --- Logika odwołań ---
def build_cancellation_message(flight, code, voucher_code, voucher_amount):
    reason_map = {
        "A": "z powodu decyzji operacyjnej linii lotniczej.",
        "B": "ze względu na niesprzyjające warunki pogodowe.",
        "C": "z powodu ograniczeń w ruchu lotniczym.",
        "D": "z powodów bezpieczeństwa."
    }
    reason = reason_map.get(code, "z nieznanego powodu.")
    base = (
        f"Szanowna Pasażerko,\n"
        f"Twój lot nr {flight['FL_NUMBER']} z {flight['ORIGIN']} do {flight['DEST']} "
        f"w dniu {flight['FL_DATE']} został odwołany {reason}\n\n"
    )
    actions = {
        "A": "🛫 Zaproponujemy Ci alternatywne połączenie tak szybko, jak to możliwe.\n💰 Możesz być uprawniona do odszkodowania — sprawdź szczegóły w aplikacji lub u personelu.\n",
        "B": "⚠️ Twoje bezpieczeństwo jest dla nas najważniejsze.\n🔁 Alternatywne połączenie może zostać zaproponowane po poprawie pogody.\n",
        "C": "🔄 Trwa reorganizacja tras przelotu — prosimy o cierpliwość.\n📲 Śledź aplikację, by otrzymać informacje o nowym połączeniu.\n",
        "D": "🚨 Służby lotniskowe pracują nad zapewnieniem bezpieczeństwa.\n📩 Prosimy o śledzenie komunikatów w aplikacji lub kontakt z punktem informacji.\n"
    }
    action = actions.get(code, "📞 Prosimy o kontakt z obsługą klienta w celu uzyskania szczegółów.\n")
    voucher = (
        f"🍽️ Otrzymujesz voucher na posiłek o wartości {voucher_amount} zł — odbiór w {VOUCHER_LOCATION}.\n"
        f"📄 Kod vouchera: **{voucher_code}**\n"
    )
    return base + action + voucher

# --- Logika opóźnień ---
def extract_delay_reasons(flight):
    keys = [
        'DELAY_DUE_CARRIER', 'DELAY_DUE_WEATHER',
        'DELAY_DUE_NAS', 'DELAY_DUE_SECURITY',
        'DELAY_DUE_LATE_AIRCRAFT'
    ]
    return [k for k in keys if float(flight.get(k, 0) or 0) > 0]

def calculate_compensation_details(reasons, delay_minutes):
    hours = round(delay_minutes / 60, 2)
    voucher_eligible = hours > 3
    compensation_eligible = False
    compensation_amount = "0$"
    if reasons and set(reasons) != {'DELAY_DUE_WEATHER'}:
        if 3 < hours <= 5:
            compensation_eligible, compensation_amount = True, "200$"
        elif 5 < hours <= 8:
            compensation_eligible, compensation_amount = True, "400$"
        elif hours > 8:
            compensation_eligible, compensation_amount = True, "600$"
    return voucher_eligible, compensation_eligible, compensation_amount, hours

def generate_delay_message(hours, desc, voucher, comp, amount):
    msg = f"Opóźnienie samolotu wynosi {hours} godziny. Powodem opóźnienia jest: {desc}. "
    if voucher:
        msg += "Zgodnie z obowiązującymi przepisami, pasażerowi przysługuje voucher na posiłek na lotnisku. "
    if comp:
        msg += f"Pasażerowi przysługuje również odszkodowanie w wysokości {amount}. "
    if not voucher and not comp:
        msg += "Z uwagi na rodzaj przyczyny oraz czas opóźnienia, nie przysługuje prawo do rekompensaty."
    return msg

def generate_voucher_note(flight, voucher_code, voucher_amount):
    return (
        f"Szanowna Pasażerko / Szanowny Pasażerze,\n"
        f"Twój lot nr {flight['FL_NUMBER']} z {flight['ORIGIN']} do {flight['DEST']} "
        f"w dniu {flight['FL_DATE']} kwalifikuje się do otrzymania vouchera.\n"
        f"🍽️ Voucher na posiłek o wartości {voucher_amount} zł do odbioru w {VOUCHER_LOCATION}.\n"
        f"📄 Kod vouchera: **{voucher_code}**\n"
        "Życzymy miłego lotu!\n"
    )

def write_dashboard():
    sorted_flights = sorted(delayed_flights, key=lambda x: x["delay_minutes"], reverse=True)
    data = {
        "delayed_flights": sorted_flights[:MAX_DASHBOARD],
        "stats": {
            "total_delayed": len(delayed_flights),
            "delayed_by_reason": dict(reason_counter)
        }
    }
    with open("outputs/dashboard_delays.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("dashboard_delays.json zaktualizowany.")

# --- Inicjalizacja KafkaConsumer ---
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[SERVER],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='combined-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

with open("outputs/cancelled_messages.txt", "a", encoding="utf-8") as cancel_log, \
     open("outputs/vouchers.txt", "a", encoding="utf-8") as voucher_log:

    for msg in consumer:
        flight = msg.value
        try:
            # 1) Obsługa odwołań
            if flight.get("CANCELLED") == "1.0":
                code = flight.get("CANCELLATION_CODE", "").strip()
                vc = generate_voucher_code()
                va = generate_voucher_amount()
                cancel_msg = build_cancellation_message(flight, code, vc, va)

                print("📩 WIADOMOŚĆ DLA PASAŻERA (odwołanie):")
                print(cancel_msg)
                cancel_log.write(cancel_msg + "\n")

                cursor.execute("""
                    INSERT INTO cancellations (
                        fl_number, origin, dest, fl_date,
                        cancellation_code, voucher_code, voucher_amount, message
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    flight.get("FL_NUMBER"),
                    flight.get("ORIGIN"),
                    flight.get("DEST"),
                    flight.get("FL_DATE"),
                    code, vc, va, cancel_msg
                ))
                conn.commit()

            # 2) Obsługa opóźnień
            if flight.get("AIRLINE_CODE") == AIRLINE_FILTER:
                delay = float(flight.get("DEP_DELAY", "0") or 0)
                if delay > 0:
                    reasons = extract_delay_reasons(flight)
                    desc_map = {
                        'DELAY_DUE_CARRIER': "decyzja linii lotniczej",
                        'DELAY_DUE_WEATHER': "złe warunki pogodowe",
                        'DELAY_DUE_NAS': "problemy w ruchu lotniczym",
                        'DELAY_DUE_SECURITY': "problemy z bezpieczeństwem",
                        'DELAY_DUE_LATE_AIRCRAFT': "opóźnienie spowodowane wcześniejszym lotem"
                    }
                    desc = ", ".join(desc_map.get(r, r) for r in reasons) or "Nieznany powód opóźnienia"

                    voucher_ok, comp_ok, comp_amt, hours = calculate_compensation_details(reasons, delay)
                    delay_msg = generate_delay_message(hours, desc, voucher_ok, comp_ok, comp_amt)

                    vc2, va2, note = "", 0, ""
                    if voucher_ok:
                        vc2 = generate_voucher_code()
                        va2 = generate_voucher_amount()
                        note = generate_voucher_note(flight, vc2, va2)
                        voucher_log.write(note + "\n")

                    # zapis do tabeli delays
                    cursor.execute("""
                        INSERT INTO delays (
                            flight_number, origin, destination, fl_date,
                            delay_minutes, reason, reason_description,
                            voucher_eligible, voucher_code, voucher_amount,
                            compensation_eligible, compensation_amount, message, delay_reasons_list
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        flight.get("FL_NUMBER"),
                        flight.get("ORIGIN"),
                        flight.get("DEST"),
                        flight.get("FL_DATE"),
                        int(delay),
                        "|".join(reasons),
                        desc,
                        voucher_ok,
                        vc2,
                        va2,
                        comp_ok,
                        comp_amt,
                        delay_msg,
                        reasons
                    ))
                    conn.commit()

                    # aktualizacja dashboardu
                    record = {
                        "flight_number": flight.get("FL_NUMBER"),
                        "origin": flight.get("ORIGIN"),
                        "destination": flight.get("DEST"),
                        "date": flight.get("FL_DATE"),
                        "delay_minutes": delay,
                        "reason": "|".join(reasons),
                        "reason_description": desc,
                        "voucher_eligible": "Yes" if voucher_ok else "No",
                        "voucher_code": vc2,
                        "voucher_amount": va2,
                        "compensation_eligible": "Yes" if comp_ok else "No",
                        "compensation_amount": comp_amt,
                        "message": delay_msg,
                        "delay_reasons_list": reasons
                    }
                    delayed_flights.append(record)
                    reason_counter["|".join(reasons)] += 1
                    write_dashboard()

        except Exception as e:
            print("❌ Błąd przetwarzania:", e)
            conn.rollback()

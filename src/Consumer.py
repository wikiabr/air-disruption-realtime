from kafka import KafkaConsumer
import json
import random
import string
import psycopg2
from datetime import datetime

SERVER = "localhost:9092"
TOPIC = "air-data"

# Miejsce odbioru vouchera
voucher_location = "hala A, bramka 4"

# Funkcja generująca kod vouchera
def generate_voucher_code():
    prefix = random.choice(["DL", "UA", "AF", "LO"])
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefix}-{suffix}"

# Funkcja generująca kwotę (25–55 zł, co 5 zł)
def generate_voucher_amount():
    return random.choice(range(25, 56, 5))

# Funkcja budująca komunikat
def build_message(flight, code, voucher_code, voucher_amount):
    reason = {
        "A": "z powodu decyzji operacyjnej linii lotniczej.",
        "B": "ze względu na niesprzyjające warunki pogodowe.",
        "C": "z powodu ograniczeń w ruchu lotniczym.",
        "D": "z powodów bezpieczeństwa."
    }.get(code, "z nieznanego powodu.")

    base_info = (
        f"Szanowna Pasażerko,\n"
        f"Twój lot nr {flight['FL_NUMBER']} z {flight['ORIGIN']} do {flight['DEST']} "
        f"w dniu {flight['FL_DATE']} został odwołany {reason}\n\n"
    )

    if code == "A":
        action = "🛫 Zaproponujemy Ci alternatywne połączenie tak szybko, jak to możliwe.\n💰 Możesz być uprawniona do odszkodowania — sprawdź szczegóły w aplikacji lub u personelu.\n"
    elif code == "B":
        action = "⚠️ Twoje bezpieczeństwo jest dla nas najważniejsze.\n🔁 Alternatywne połączenie może zostać zaproponowane po poprawie pogody.\n"
    elif code == "C":
        action = "🔄 Trwa reorganizacja tras przelotu — prosimy o cierpliwość.\n📲 Śledź aplikację, by otrzymać informacje o nowym połączeniu.\n"
    elif code == "D":
        action = "🚨 Służby lotniskowe pracują nad zapewnieniem bezpieczeństwa.\n📩 Prosimy o śledzenie komunikatów w aplikacji lub kontakt z punktem informacji.\n"
    else:
        action = "📞 Prosimy o kontakt z obsługą klienta w celu uzyskania szczegółów.\n"

    voucher_info = (
        f"🍽️ Otrzymujesz voucher na posiłek o wartości {voucher_amount} zł — odbiór w {voucher_location}.\n"
        f"📄 Kod vouchera: **{voucher_code}**\n"
    )

    return base_info + action + voucher_info

# Połączenie z bazą PostgreSQL
conn = psycopg2.connect(
    dbname="air_data",
    user="user",
    password="password",
    host="localhost",  # Jeśli uruchamiasz z systemu gospodarza (Windows/macOS)
    port="5432"
)
cursor = conn.cursor()

# Konfiguracja konsumenta Kafka
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[SERVER],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='cancel-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Główna pętla przetwarzania
with open("outputs/cancelled_messages.txt", "a", encoding="utf-8") as log_file:
    for msg in consumer:
        flight = msg.value

        if flight.get("CANCELLED") == "1.0":
            code = flight.get("CANCELLATION_CODE", "").strip()
            voucher_code = generate_voucher_code()
            voucher_amount = generate_voucher_amount()
            message = build_message(flight, code, voucher_code, voucher_amount)

            print("📩 TO OTRZYMAŁBY PASAŻER:")
            print(message)
            log_file.write(message + "\n")

            # Zapis do bazy danych
            try:
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
                    code,
                    voucher_code,
                    voucher_amount,
                    message
                ))
                conn.commit()
            except Exception as e:
                print("❌ Błąd przy zapisie do bazy:", e)
                conn.rollback()

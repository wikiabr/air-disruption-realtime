from kafka import KafkaConsumer
import json
from collections import defaultdict, Counter

SERVER = "localhost:9092"
TOPIC = "air-data"

# Inicjalizacja danych
cancelled_flights = []
reason_counter = Counter()
origin_counter = Counter()

# Ustaw maksymalną liczbę lotów do pokazania na dashboardzie
MAX_FLIGHTS = 30

# Słownik opisów powodów
cancellation_descriptions = {
    "A": "decyzja linii lotniczej",
    "B": "złe warunki pogodowe",
    "C": "problemy w ruchu lotniczym",
    "D": "problemy bezpieczeństwa"
}

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[SERVER],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='dashboard-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

def write_dashboard():
    # Top 3 miejsca z największą liczbą odwołań
    top_origins = dict(origin_counter.most_common(3))

    # Dane do dashboardu
    dashboard_data = {
        "cancelled_flights": cancelled_flights[-MAX_FLIGHTS:],  # tylko ostatnie N
        "stats": {
            "total_cancelled": len(cancelled_flights),
            "cancelled_by_reason": dict(reason_counter),
            "top_origins": top_origins
        }
    }

    with open("outputs/dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)

    print("📊 dashboard_data.json zaktualizowany.")

# Główna pętla
for msg in consumer:
    flight = msg.value

    if flight.get("CANCELLED") == "1.0":
        code = flight.get("CANCELLATION_CODE", "").strip()
        desc = cancellation_descriptions.get(code, "nieznany powód")

        record = {
            "flight_number": flight.get("FL_NUMBER"),
            "origin": flight.get("ORIGIN"),
            "destination": flight.get("DEST"),
            "date": flight.get("FL_DATE"),
            "reason": code,
            "reason_description": desc
        }

        cancelled_flights.append(record)
        reason_counter[code] += 1
        origin_counter[flight.get("ORIGIN", "???")] += 1

        write_dashboard()
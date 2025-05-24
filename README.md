# ✈️ Projekt: Obsługa opóźnionych i odwołanych lotów – Apache Kafka + Python + PostgreSQL

Projekt realizowany w ramach przedmiotu **Analiza danych w czasie rzeczywistym**.

Celem jest stworzenie systemu, który:
- przetwarza dane o lotach w czasie rzeczywistym,
- wykrywa opóźnione i odwołane loty,
- automatycznie generuje komunikaty dla pasażerów (np. vouchery, alternatywne połączenia),
- zapisuje dane do bazy PostgreSQL jako źródło dla Power BI lub dashboardu.

---

## 💡 Decyzja biznesowa

**Automatyzacja obsługi pasażerów w sytuacjach zakłóceń**, aby:
- zmniejszyć obciążenie operacyjne obsługi klienta,
- zwiększyć satysfakcję i komfort pasażerów.

---

## 📦 Zawartość repozytorium

| Plik / folder | Opis |
|---------------|------|
| `src/Producer.py` | Odczytuje dane z pliku CSV i wysyła do Apache Kafka (topic `air-data`) |
| `src/Consumer.py` | Odbiera dane z Kafka, generuje komunikaty, zapisuje do pliku i PostgreSQL |
| `src/dashboard_writer.py` | Tworzy plik JSON z danymi statystycznymi do dashboardu |
| `docker-compose.yml` | Uruchamia Kafka, Zookeeper, PostgreSQL i pgAdmin |
| `data/dashboard_sample.csv` | Przykładowe dane wejściowe |
| `data/sample_flights.csv` | Alternatywny plik CSV z danymi lotów |
| `outputs/dashboard_data.json` | ✨ Generowany plik z danymi do dashboardu |
| `outputs/cancelled_messages.txt` | ✨ Generowane wiadomości dla pasażerów |
| `odwolania-test.ipynb` | Notebook do tworzenia testowych danych |
| `.env`, `.gitignore` | Pliki konfiguracyjne (np. ignorowanie dużych plików) |

---

## ▶️ Jak uruchomić projekt

### 1. Uruchom wszystkie usługi w tle (Kafka, Zookeeper, PostgreSQL, pgAdmin):
```bash
docker-compose up -d
`````
### 2. Uruchom terminal z konsumentem:
W terminalu:
```bash
python Consumer.py
`````
### 3. (Ewentualnie) Uruchom terminal z writerem dashboardu:
W terminalu:
```bash
python dashboard_writer.py
`````
### 4. Uruchom terminal z producentem:
W terminalu:
```bash
python Producer.py
`````

⚠️UWAGA!

Plik _ALL_FLIGHTS_30m.csc nie jest dołączony do repozytorium, jest ignorowany przez .gitignore

Upewnij się, że podłączasz się pod odpowiedni port

Sprawdź, czy istnieje topic air-data w twoim środowisku

Zobacz, czy podpięty jest odpowiedni plik w Producer.py

🔐 Dane dostępowe do PostgreSQL
Parametr	Wartość
Host	localhost
Port	5432
Baza	air_data
Użytkownik	user
Hasło	password

🌐 Interfejs webowy pgAdmin
Dostępny pod adresem:
👉 http://localhost:8080

Login: admin@admin.com
Hasło: admin

Po zalogowaniu się do pgAdmin:
Kliknij "Add New Server"

W zakładce Connection użyj:
Host name: postgres
Username: user
Password: password

📊 Power BI jako warstwa wizualizacyjna
System generuje dane w bazie PostgreSQL (tabela cancellations), które mogą być załadowane do Power BI jako źródło danych.

Jak dodać w Power BI:
Wybierz Pobierz dane → Baza danych → PostgreSQL

Wypełnij:
Serwer: localhost
Baza danych: air_data
Login: user
Hasło: password

Wybierz tabelę public.cancellations
# ✈️ Projekt: Obsługa opóźnionych i odwołanych lotów – Apache Kafka + Python

Projekt realizowany w ramach przedmiotu **Analiza danych w czasie rzeczywistym**. 

Celem jest stworzenie systemu, który przetwarza dane o lotach w czasie rzeczywistym, wykrywa opóźnione i odwołane loty oraz W przypadku opóźnienia system automatycznie wysyła pasażerom, którzy oczekują na samolot spersonalizowane powiadomienia (SMS, e-mail, aplikacja) z aktualnym statusem i dalszymi instrukcjami. W przypadku odwołania lotu, pasażerowie mogą otrzymać gotowe wiadomości z propozycją alternatywnego połączenia, informacją o prawie do odszkodowania lub natychmiastowy dostęp do voucherów na posiłek czy zniżek.

**Podejmowana decyzja biznesowa:**
Automatyzacja obsługi pasażerów w sytuacjach zakłóceń, aby zmniejszyć obciążenie operacyjne i poprawić doświadczenie klienta

---

## 📦 Zawartość repozytorium

| Plik | Opis |
|------|------|
| `Producer.py` | Odczytuje dane z pliku `.csv` i wysyła wiadomości do Kafki (topic `air-data`) |
| `Consumer.py` | Odbiera wiadomości z Kafki i generuje komunikaty dla pasażerów |
| `dashboard_writer.py` | Tworzy dane do dashboardu na podstawie wiadomości z Kafki |
| `docker-compose.yml` | Plik uruchamiający Apache Kafka i Zookeeper w Dockerze |
| `sample_flights.csv` | Przykładowy plik z danymi o lotach, zawierający odwołane loty |
| `dashboard_sample.csv` | Alternatywny zestaw danych dla dashboardu |
| `dashboard_data.json` | ✨ Plik generowany – zawiera statystyki do dashboardu |
| `cancelled_messages.txt` | ✨ Plik generowany – zapis komunikatów dla pasażerów |
| `odwolania-test.ipynb` | Notebook do tworzenia próbki danych z większą liczbą odwołań |

---

## ▶️ Jak uruchomić projekt

### 1. Uruchom Kafkę i Zookeepera:
W terminalu:
```bash
docker-compose up -d
`````
### 2. Uruchom terminal z konsumentem:
W terminalu:
```bash
python Consumer.py
`````
### 3. Uruchom terminal z writerem dashboardu:
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

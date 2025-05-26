from kafka import KafkaProducer
import json
from time import sleep
import csv

SERVER = "localhost:9092"
TOPIC = "air-data"


if __name__ =="__main__":
    producer = KafkaProducer(
        bootstrap_servers=[SERVER],
        value_serializer = lambda x: json.dumps(x).encode('utf-8')
        )
    try:
        while True:
            for i in range(2):
                print("Próba otwarcia pliku")
                with open("data/ALL_FLIGHTS_30m.csv", "r", encoding="utf-8-sig") as f:
                    message={}
                    line_reader = csv.reader(f, delimiter=',')
                    col_names = next(line_reader)
                    print(col_names)
                    print(len(col_names))
                    for i in range(40):
                        col_values = next(line_reader)
                        print(col_values)
                        print(len(col_values))
                        message = dict(zip(col_names, col_values))
                        producer.send(TOPIC,value=message)
                        producer.flush()
                        print(message)
                        message={}
                        sleep(5)
                sleep(5)
    except KeyboardInterrupt:
        producer.close()
    except FileNotFoundError:
        print(f"BŁĄD: Plik {"ALL_FLIGHTS_30m.csv"} nie istnieje!")
    except Exception as e:
        print(f"BŁĄD przy otwieraniu pliku: {str(e)}")
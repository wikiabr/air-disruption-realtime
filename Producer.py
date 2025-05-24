from kafka import KafkaProducer
import json
from time import sleep
import csv

SERVER = "kafka:9092"
TOPIC = "air-data"


if __name__ =="__main__":
    producer = KafkaProducer(
        bootstrap_servers=[SERVER],
        value_serializer = lambda x: json.dumps(x).encode('utf-8')
        )
    try:
        for i in range(10):
            with open("dashboard_sample.csv", "r", encoding="utf-8-sig") as f:
                message={}
                line_reader = csv.reader(f, delimiter=',')
                col_names = next(line_reader)
                print(col_names)
                print(len(col_names))
                for i in range(10):
                    col_values = next(line_reader)
                    print(col_values)
                    print(len(col_values))
                    message = dict(zip(col_names, col_values))
                    producer.send(TOPIC,value=message)
                    producer.flush()
                    print(message)
                    message={}
                    sleep(2)
            sleep(2)
    except KeyboardInterrupt:
        producer.close()

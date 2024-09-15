FROM bitnami/spark:latest
COPY consumer_kafka_to_csv.py /app/consumer_kafka_to_csv.py
WORKDIR /app
RUN pip install kafka-python
CMD ["spark-submit", "--master", "spark://spark-master:7077", "consumer_kafka_to_csv.py"]

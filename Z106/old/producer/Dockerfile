FROM bitnami/spark:latest
COPY api_to_parquet_kafka.py /app/api_to_parquet_kafka.py
WORKDIR /app
RUN pip install kafka-python requests
CMD ["spark-submit", "--master", "spark://spark-master:7077", "api_to_parquet_kafka.py"]

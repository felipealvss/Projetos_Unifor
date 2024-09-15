from pyspark.sql import SparkSession
from kafka import KafkaConsumer
import time
import os

# Configuração do Spark
spark = SparkSession.builder \
    .appName("ParquetToCSV") \
    .getOrCreate()

# Consumer Kafka
consumer = KafkaConsumer(
    'parquet-files',
    bootstrap_servers='kafka:9092',  # "kafka" refere-se ao nome do serviço no docker-compose.yml
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='my-group')

def process_parquet_to_csv(spark, parquet_file, output_csv):
    # Lendo o arquivo Parquet com PySpark
    df = spark.read.parquet(parquet_file)
    # Convertendo para CSV
    df.write.csv(output_csv, header=True)
    print(f"Arquivo CSV gerado: {output_csv}")

if __name__ == "__main__":
    output_folder = '/output/'  # Diretório mapeado no Docker
    
    while True:
        # Verificar novos arquivos no tópico Kafka
        for message in consumer:
            parquet_file = message.value.decode('utf-8')
            print(f"Novo arquivo Parquet detectado: {parquet_file}")
            
            # Definir o nome do CSV de saída
            output_csv = os.path.join(output_folder, os.path.basename(parquet_file).replace('.parquet', '.csv'))
            
            # Processar o arquivo Parquet e gerar CSV
            process_parquet_to_csv(spark, parquet_file, output_csv)
            
        # Esperar 2 segundos antes de checar novos arquivos
        time.sleep(2)

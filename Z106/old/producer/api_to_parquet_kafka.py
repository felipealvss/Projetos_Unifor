import requests as req
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pyspark.sql import SparkSession
from kafka import KafkaProducer
import os

# Configurando o Spark
spark = SparkSession.builder \
    .appName("APIToParquet") \
    .getOrCreate()

# Configuração do Kafka Producer
producer = KafkaProducer(bootstrap_servers='kafka:9092')  # "kafka" refere-se ao nome do serviço no docker-compose.yml
topic = 'parquet-files'

# URL base da API e parâmetros
base_url = 'https://dadosabertos.aneel.gov.br/api/3/action/datastore_search'
resource_id = '49fa9ca0-f609-4ae3-a6f7-b97bd0945a3a'
query = 'GD.CE'
limit = 100  # Número de registros por página

# Função para obter o total de registros
def get_total_records():
    url = f'{base_url}?resource_id={resource_id}&q={query}&limit=1'
    retries = 3
    delay = 2
    for attempt in range(retries):
        try:
            response = req.get(url)
            if response.status_code == 200:
                data = response.json()
                return data['result']['total']
            else:
                print(f'Erro na requisição: {response.status_code}. Tentativa {attempt + 1} de {retries}')
                time.sleep(delay)
        except Exception as e:
            print(f'Erro na requisição: {e}. Tentativa {attempt + 1} de {retries}')
            time.sleep(delay)
    raise Exception('Falha ao obter o total de registros.')

# Função para obter dados de uma URL
def fetch_data(offset):
    url = f'{base_url}?resource_id={resource_id}&q={query}&limit={limit}&offset={offset}'
    retries = 3
    delay = 5
    for attempt in range(retries):
        try:
            response = req.get(url, timeout=10)  # Aumentar o timeout
            if response.status_code == 200:
                return response.json()
            else:
                print(f'Erro na requisição: {response.status_code}. Tentativa {attempt + 1} de {retries}')
                time.sleep(delay)
        except Exception as e:
            print(f'Erro na requisição: {e}. Tentativa {attempt + 1} de {retries}')
            time.sleep(delay)
    return None  # Retorna None se falhar após tentativas

# Função para salvar dados em Parquet e enviar para Kafka
def save_to_parquet(spark, data, batch_number):
    # Criar DataFrame do PySpark a partir dos dados
    df = spark.createDataFrame(data)
    # Gerar o nome do arquivo Parquet
    parquet_file = f'/output/data_batch_{batch_number}.parquet'  # Caminho do arquivo Parquet no volume mapeado
    # Salvar como arquivo Parquet
    df.write.mode("overwrite").parquet(parquet_file)
    print(f'Arquivo parquet salvo: {parquet_file}')
    # Enviar o caminho do arquivo Parquet para o Kafka
    try:
        producer.send(topic, parquet_file.encode('utf-8'))
        producer.flush()
        print(f'Arquivo {parquet_file} enviado para Kafka.')
    except Exception as e:
        print(f'Erro ao enviar o arquivo {parquet_file} para o Kafka: {e}')

# Função para buscar e processar dados da API
def fetch_all_data(total_records, limit):
    offsets = range(0, total_records, limit)
    batch_number = 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_data, offset): offset for offset in offsets}

        for future in as_completed(futures):
            try:
                data = future.result()
                if data:
                    records = data['result']['records']
                    save_to_parquet(spark, records, batch_number)
                    batch_number += 1
                else:
                    print(f'Nenhum dado retornado para o offset {futures[future]}')
            except Exception as e:
                print(f'Erro ao processar o futuro para o offset {futures[future]}: {e}')

# Função principal para iniciar o processo
if __name__ == "__main__":
    # Obter o total de registros da API
    total_records = get_total_records()
    print(f'Total de registros disponíveis: {total_records}')

    # Obter todos os dados e processar
    fetch_all_data(total_records, limit)

    # Fechar o producer do Kafka
    producer.close()

    print('Processamento completo!')

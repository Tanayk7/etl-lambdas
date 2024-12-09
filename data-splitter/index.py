import boto3
import requests
import json
import os
import concurrent.futures
import pandas as pd
import traceback
import logging 
import numpy

from data_processing import DataProcessor
from io import StringIO
from dotenv import load_dotenv
from psycopg2.extensions import register_adapter, AsIs

load_dotenv()

def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)

def addapt_numpy_int64(numpy_int64):
    return AsIs(numpy_int64)

register_adapter(numpy.float64, addapt_numpy_float64)
register_adapter(numpy.int64, addapt_numpy_int64)

def process_requests_concurrently(requests, execution_handler, num_workers=10):
    results = []
    # Using ThreadPoolExecutor to handle multiple requests concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submitting process_gpt with the prompt, system_msg, and (image_path / cv2_image /url)
        results = list(executor.map(lambda params: execution_handler(**params), requests))
    return results

def send_processing_request(chunk): 
    url = os.getenv('DATA_PROCESSOR_URL')
    response = requests.post(url, json={ 'chunk': chunk })
    return response.json()

def handler(event, context):
    print(f"event: {event}")
    record = event["Records"][0]
    receipt_handle = record["receiptHandle"]
    message_body = json.loads(record["body"])  # Parse JSON string into Python dictionary
    bucket_name = message_body["bucket_name"]
    s3_key = message_body["s3_key"]
    queue_url = os.getenv('ETL_JOB_QUEUE_URL')  # ARN can be used as the QueueUrl for FIFO queues
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    region = 'ap-south-1'
    session = boto3.session.Session(
        region_name=region
    )
    s3 = session.client('s3')
    sqs = session.client("sqs")
    
    print(f"Processing message: {message_body}")
    
    try:
        # Retrieve the message body
        print("downloading file from s3...")
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        print("Downloaded file from s3 successfully!")
        # Read the content and load into pandas DataFrame
        csv_content = response['Body'].read().decode('utf-8')
        reader = pd.read_csv(StringIO(csv_content), chunksize=20000)
        request_batch = [{ 'chunk': chunk.to_csv(index=False) } for chunk in reader]
        print("batch size: ", len(request_batch))
        results = process_requests_concurrently(
            requests=request_batch, 
            execution_handler=send_processing_request,
            num_workers=20
        )
        print("Done processing all chunks!")

        processed_chunks = []
        for result in results:  
            print("Chunk processing result: ", result['message'])
            if 'chunk' in result: 
                chunk_df = pd.read_csv(StringIO(result['chunk']))
                processed_chunks.append(chunk_df)
            else: 
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
                return json.dumps({ 
                    "result": f"Error occured during ETL pipeline: {result['message']}" 
                }), 500

        print("Saving chunks to database...")
        session = DataProcessor.create_session()
        processor = DataProcessor(session)
        processor.save_all_to_db(processed_chunks)
        print("Saved chunk to database successfully!")

        # Acknowledge (delete) the message
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        print(f"Message {record['messageId']} deleted successfully.")
        return json.dumps({ "result": "Data processed successfully!" }), 200
    except Exception as e:
        print(f"Error processing message {record['messageId']}: {str(e)}")
        traceback.print_exc()
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        return json.dumps({ 
            "result": f"Error occured during ETL pipeline: {traceback.print_exc()}" 
        }), 500

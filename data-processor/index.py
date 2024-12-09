import json 
import pandas as pd
import numpy
import traceback
from data_processing import DataProcessor
from io import StringIO

# Wrapper for processing chunks
def process_chunk_wrapper(chunk) -> pd.DataFrame:
    processor = DataProcessor(None)  # No session needed for processing
    return processor.process_chunk(chunk)

def handler(event, context):
    print(f"event: {event}")
    chunk_str = '' 

    if 'body' in event: 
        body = json.loads(event['body'])
        chunk_str = body['chunk']
        print("Chunk received by processor!")
    else: 
        chunk_str = event['chunk']
        print("Chunk received by processor: ", chunk_str)

    print("processing chunk...")
    try:
        # Read and process the chunk
        chunk = pd.read_csv(StringIO(chunk_str))
        processed_chunk = process_chunk_wrapper(chunk)
        print("Done processing chunk...")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Chunk processed successfully!",
                "chunk": processed_chunk.to_csv(index=False)
            })
        }
    except Exception as e:
        print(f"ETL pipeline failed: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Error occurred while processing chunk.",
                "details": traceback.format_exc()
            })
        }

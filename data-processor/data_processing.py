import pandas as pd
import numpy as np
import os
import io
from math import radians, cos, sin, asin, sqrt

class DataProcessor:
    def __init__(self, session):
        self.session = session

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of Earth in kilometers
        return c * r

    def process_chunk(self, chunk):
        print("processing chunk...")
        
        # Convert datetime columns to proper types
        chunk['pickup_datetime'] = pd.to_datetime(chunk['pickup_datetime'])
        chunk['dropoff_datetime'] = pd.to_datetime(chunk['dropoff_datetime'])
        # print("Converted datetime columns!")

        # Calculate trip distance   
        chunk['trip_distance'] = chunk.apply(
            lambda row: self.haversine(
                row['pickup_latitude'], row['pickup_longitude'],
                row['dropoff_latitude'], row['dropoff_longitude']
            ), axis=1
        )
        # print("Calculated trip distances!")

        # Clean invalid data
        chunk = chunk.dropna(subset=['pickup_latitude', 'pickup_longitude', 'dropoff_latitude', 'dropoff_longitude'])
        chunk = chunk[chunk['trip_duration'] > 0]  # Remove non-positive durations
        # print("Cleaned invalid data!")

        # Convert all numpy types to native Python types
        chunk = chunk.applymap(lambda x: int(x) if isinstance(x, (np.int64, np.int32)) else x)
        chunk = chunk.applymap(lambda x: float(x) if isinstance(x, (np.float64, np.float32)) else x)
        # print("Converted all numpy types to native python types!")
        print("Done processing chunk!")
        return chunk
    
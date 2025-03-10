import pandas as pd
import numpy as np
import os
import io

from math import radians, cos, sin, asin, sqrt
from models import Vendor, Trip
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import exc

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

    @staticmethod
    def create_session():
        # Use environment variables to store credentials
        DATABASE_URL = os.getenv("DATABASE_URL")  # Example: postgresql://username:password@host:port/dbname
        engine = create_engine(DATABASE_URL)
        session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return scoped_session(session_factory)
    
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
    
    def save_to_db(self, chunk):
        print("Saving chunk to DB...")
        try:
            # Insert unique vendors
            unique_vendors = chunk['vendor_id'].unique()
            existing_vendors = {v.vendor_id for v in self.session.query(Vendor.vendor_id).all()}
            new_vendors = [Vendor(vendor_id=vendor_id) for vendor_id in unique_vendors if vendor_id not in existing_vendors]

            if new_vendors:
                try:
                    self.session.bulk_save_objects(new_vendors)
                    self.session.commit()
                    print("Inserted new vendors!")
                except exc.IntegrityError as e:
                    print("Unique constraint violation while inserting vendors:", e)
                    self.session.rollback()  # Rollback the failed transaction

            # Map vendor_id to database ID
            vendor_map = {v.vendor_id: v.id for v in self.session.query(Vendor).all()}
            chunk['vendor_id'] = chunk['vendor_id'].map(vendor_map)

            # Use COPY for trip records
            output = io.StringIO()
            chunk.to_csv(output, sep='\t', index=False, header=False)
            output.seek(0)

            connection = self.session.connection()
            cursor = connection.connection.cursor()
            cursor.copy_from(output, 'trips', sep='\t', null="")
            connection.commit()
            print("Bulk inserted trip records in DB using COPY!")
        except Exception as e:
            print("Error occurred!: ", e)
            raise
    
    def save_all_to_db(self, all_chunks, batch_size=50000):
        """
        Save all processed chunks to the database using COPY for bulk insertion.
        Args:
            all_chunks (list[pd.DataFrame]): List of processed chunks.
        """
        print("Saving all chunks to DB...")

        try:
            # Combine all chunks into a single DataFrame
            full_data = pd.concat(all_chunks, ignore_index=True)
            print(f"Combined full dataset: {len(full_data)} rows")

            # Insert unique vendors
            unique_vendors = full_data['vendor_id'].unique()
            existing_vendors = {v.vendor_id for v in self.session.query(Vendor.vendor_id).all()}
            new_vendors = [Vendor(vendor_id=vendor_id) for vendor_id in unique_vendors if vendor_id not in existing_vendors]
            
            if new_vendors:
                try:
                    self.session.bulk_save_objects(new_vendors)
                    self.session.commit()
                    print("Inserted new vendors!")
                except exc.IntegrityError as e:
                    print("Unique constraint violation while inserting vendors:", e)
                    self.session.rollback()  # Rollback the failed transaction

            # Map vendor_id to database ID
            vendor_map = {v.vendor_id: v.id for v in self.session.query(Vendor).all()}
            full_data['vendor_id'] = full_data['vendor_id'].map(vendor_map)
            
            connection = self.session.connection()
            cursor = connection.connection.cursor()
            
            # Insert trip records in batches
            for start in range(0, len(full_data), batch_size):
                batch = full_data.iloc[start:start + batch_size]
                print(f"Inserting batch {start // batch_size + 1} with {len(batch)} rows")

                output = io.StringIO()
                batch.to_csv(output, sep='\t', index=False, header=False)
                output.seek(0)
           
                cursor.copy_from(output, 'trips', sep='\t', null="")
                connection.commit()
                print("Wrote batch successfully!")
                
            print("All batches inserted successfully!")
        except Exception as e:
            self.session.rollback()
            print("Error occurred while saving all chunks: ", e)
            raise
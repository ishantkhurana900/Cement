# data_uploader.py - Excel to Firebase Real-time Data Stream

import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import time
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import sys

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_upload.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CementPlantDataUploader:
    def __init__(self, service_account_path, database_url, excel_file_path):
        """
        Initialize the data uploader
        
        Args:
            service_account_path (str): Path to Firebase service account key
            database_url (str): Firebase Realtime Database URL
            excel_file_path (str): Path to Excel file with cement plant data
        """
        self.excel_file_path = excel_file_path
        self.database_url = database_url
        self.data_records = []
        self.current_index = 0
        
        # Initialize Firebase
        try:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
            logger.info("✅ Firebase initialized successfully")
        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {e}")
            raise
        
        # Load Excel data
        self.load_excel_data()
    
    def load_excel_data(self):
        """Load and prepare Excel data for streaming"""
        try:
            logger.info(f"📊 Loading Excel data from: {self.excel_file_path}")
            
            # Read Excel file
            df = pd.read_excel(self.excel_file_path)
            
            # Clean column names (remove spaces, make consistent)
            df.columns = df.columns.str.strip()
            
            # Convert to list of dictionaries
            self.data_records = df.to_dict('records')
            
            logger.info(f"✅ Loaded {len(self.data_records)} data records")
            logger.info(f"📋 Columns: {list(df.columns)}")
            
            # Validate required columns
            required_columns = [
                'Clinker_Inlet_Temp', 'Clinker_Outlet_Temp', 'Cooling_Air_Flow',
                'Secondary_Air_Temp_Cooler', 'Grate_Speed', 'Clinker_Production_Rate'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"⚠️ Missing columns: {missing_columns}")
            
        except Exception as e:
            logger.error(f"❌ Error loading Excel data: {e}")
            raise
    
    def clean_data_record(self, record):
        """Clean and prepare a single data record"""
        cleaned_record = {}
        
        for key, value in record.items():
            # Skip Time column if it exists
            if key.lower() in ['time', 'timestamp']:
                continue
                
            # Handle NaN values
            if pd.isna(value):
                cleaned_record[key] = 0.0
            elif isinstance(value, (int, float)):
                cleaned_record[key] = float(value)
            else:
                cleaned_record[key] = str(value)
        
        # Add timestamp
        cleaned_record['timestamp'] = datetime.now().isoformat()
        cleaned_record['upload_time'] = int(time.time() * 1000)  # Milliseconds
        
        return cleaned_record
    
    def upload_current_data(self, data_record):
        """Upload current data point to Firebase"""
        try:
            ref = db.reference('cement_plant_data/current')
            ref.set(data_record)
            
            # Also store in history (but limit to last 1000 records to save space)
            history_ref = db.reference('cement_plant_data/history')
            history_ref.push(data_record)
            
            # Clean old history records (keep only recent ones)
            self.cleanup_history()
            
            logger.info(f"📡 Uploaded data point - Clinker Inlet: {data_record.get('Clinker_Inlet_Temp', 'N/A')}°C")
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
    
    def cleanup_history(self):
        """Keep only recent history records to manage database size"""
        try:
            history_ref = db.reference('cement_plant_data/history')
            
            # Get all history records
            history_data = history_ref.get()
            
            if history_data and len(history_data) > 1000:  # Keep last 1000 records
                # Sort by timestamp and keep only recent ones
                sorted_keys = sorted(history_data.keys(), 
                                   key=lambda x: history_data[x].get('upload_time', 0))
                
                # Delete oldest records
                keys_to_delete = sorted_keys[:-1000]  # Keep last 1000
                
                for key in keys_to_delete:
                    history_ref.child(key).delete()
                
                logger.info(f"🧹 Cleaned {len(keys_to_delete)} old records from history")
                
        except Exception as e:
            logger.warning(f"⚠️ History cleanup failed: {e}")
    
    def simulate_real_time_streaming(self, loop_data=True):
        """
        Simulate real-time data streaming every 5 seconds
        
        Args:
            loop_data (bool): Whether to loop the data when reaching the end
        """
        logger.info("🚀 Starting real-time data streaming (5-second intervals)")
        logger.info(f"📊 Total records available: {len(self.data_records)}")
        
        try:
            while True:
                # Get current record
                if self.current_index >= len(self.data_records):
                    if loop_data:
                        logger.info("🔄 Reached end of data, looping back to start")
                        self.current_index = 0
                    else:
                        logger.info("✅ Finished uploading all data records")
                        break
                
                record = self.data_records[self.current_index]
                cleaned_record = self.clean_data_record(record)
                
                # Upload to Firebase
                self.upload_current_data(cleaned_record)
                
                # Update progress
                progress = ((self.current_index + 1) / len(self.data_records)) * 100
                logger.info(f"📈 Progress: {progress:.1f}% ({self.current_index + 1}/{len(self.data_records)})")
                
                # Update metadata
                self.update_metadata()
                
                self.current_index += 1
                
                # Wait 5 seconds before next update
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Streaming stopped by user")
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
            raise
    
    def update_metadata(self):
        """Update system metadata"""
        try:
            metadata = {
                'last_update': datetime.now().isoformat(),
                'current_index': self.current_index,
                'total_records': len(self.data_records),
                'update_interval_seconds': 5,
                'status': 'active'
            }
            
            db.reference('cement_plant_data/metadata').set(metadata)
            
        except Exception as e:
            logger.warning(f"⚠️ Metadata update failed: {e}")
    
    def upload_single_record(self, index=0):
        """Upload a single record for testing"""
        if 0 <= index < len(self.data_records):
            record = self.data_records[index]
            cleaned_record = self.clean_data_record(record)
            self.upload_current_data(cleaned_record)
            logger.info(f"✅ Single record uploaded: Index {index}")
        else:
            logger.error(f"❌ Invalid index: {index}")

def main():
    """Main execution function"""
    print("🏭 Cement Plant Real-time Data Uploader")
    print("=" * 50)
    
    # Configuration
    SERVICE_ACCOUNT_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'service-account-key.json')
    DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', 'https://your-project-id-default-rtdb.firebaseio.com')
    EXCEL_FILE_PATH = os.getenv('EXCEL_FILE_PATH', 'cement_plant_data.xlsx')
    
    # Validate files exist
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        logger.error(f"❌ Service account key not found: {SERVICE_ACCOUNT_PATH}")
        print("Please ensure your Firebase service account key is in the correct location.")
        return
    
    if not os.path.exists(EXCEL_FILE_PATH):
        logger.error(f"❌ Excel file not found: {EXCEL_FILE_PATH}")
        print("Please ensure your Excel file is in the correct location.")
        return
    
    try:
        # Initialize uploader
        uploader = CementPlantDataUploader(
            service_account_path=SERVICE_ACCOUNT_PATH,
            database_url=DATABASE_URL,
            excel_file_path=EXCEL_FILE_PATH
        )
        
        # Ask user for operation mode
        print("\nChoose operation mode:")
        print("1. Real-time streaming (continuous, 5-second intervals)")
        print("2. Upload single record (for testing)")
        print("3. Upload all records once (no looping)")
        
        try:
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == "1":
                print("\n🚀 Starting continuous real-time streaming...")
                print("Press Ctrl+C to stop")
                uploader.simulate_real_time_streaming(loop_data=True)
                
            elif choice == "2":
                try:
                    index = int(input("Enter record index to upload (0-based): "))
                    uploader.upload_single_record(index)
                except ValueError:
                    logger.error("❌ Invalid index provided")
                    
            elif choice == "3":
                print("\n📊 Uploading all records once...")
                uploader.simulate_real_time_streaming(loop_data=False)
                
            else:
                logger.error("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n⏹️ Operation stopped by user")
    
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        raise

if __name__ == "__main__":
    main()
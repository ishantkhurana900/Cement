import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create sample data matching your structure
print("Creating sample Excel file...")

# Generate sample data (100 records, 5-second intervals)
num_records = 100
start_time = datetime.now()

data = {
    'Time': [start_time + timedelta(seconds=i*5) for i in range(num_records)],
    'Clinker_Inlet_Temp': np.random.normal(1300, 50, num_records),
    'Clinker_Outlet_Temp': np.random.normal(100, 20, num_records),
    'Cooling_Air_Flow': np.random.normal(500, 50, num_records),
    'Secondary_Air_Temp_Cooler': np.random.normal(900, 50, num_records),
    'Grate_Speed': np.random.normal(12, 3, num_records),
    'Clinker_Production_Rate': np.random.normal(130, 10, num_records),
    'Cement_Mill_Feed_Rate': np.random.normal(135, 15, num_records),
    'Gypsum_Addition': np.random.normal(3.8, 0.3, num_records),
    'Cement_Mill_Power': np.random.normal(2250, 150, num_records),
    'Cement_Fineness_Blaine': np.random.normal(350, 30, num_records),
    'Cement_Fineness_45um': np.random.normal(11, 2, num_records),
    'Separator_Efficiency': np.random.normal(81, 2, num_records)
}

df = pd.DataFrame(data)
df.to_excel('cement_plant_data1.xlsx', index=False)
print(f"✅ Sample Excel file created with {num_records} records")

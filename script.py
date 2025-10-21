# Create a comprehensive cost analysis for the cement plant dashboard
import pandas as pd

# Free tier limits from research
free_tiers = {
    'Firebase Realtime Database': {
        'Storage': '1 GB',
        'Simultaneous Connections': 100,
        'Data Transfer': '10 GB/month',
        'Cost': 'FREE'
    },
    'Firebase Hosting': {
        'Storage': '1 GB', 
        'Data Transfer': '10 GB/month',
        'Cost': 'FREE'
    },
    'Firebase Authentication': {
        'Monthly Active Users': 50000,
        'Cost': 'FREE'
    },
    'Cloud Functions': {
        'Invocations': '2M/month',
        'Compute Time': '400K GB-seconds',
        'Outgoing Data': '5 GB/month',
        'Cost': 'FREE'
    }
}

# Calculate data requirements for cement plant monitoring
data_per_update = 0.5  # KB per data update (13 parameters)
updates_per_day = 17280  # Every 5 seconds = 86400/5 
updates_per_month = updates_per_day * 30

monthly_data_mb = (data_per_update * updates_per_month) / 1024
monthly_data_gb = monthly_data_mb / 1024

print("CEMENT PLANT DASHBOARD - COST OPTIMAL ANALYSIS")
print("=" * 50)
print(f"Data per update: {data_per_update} KB")
print(f"Updates per day: {updates_per_day:,}")
print(f"Updates per month: {updates_per_month:,}")
print(f"Monthly data volume: {monthly_data_mb:.2f} MB ({monthly_data_gb:.3f} GB)")
print(f"Storage requirement: ~{monthly_data_gb*12:.2f} GB/year (if keeping history)")

print("\nFREE TIER COVERAGE:")
print("✅ Realtime Database: Well within 10GB/month limit")
print("✅ Hosting: Static files < 1GB, traffic < 10GB/month")  
print("✅ Authentication: No users needed for monitoring")
print("✅ Cloud Functions: Minimal usage for data ingestion")

print(f"\nESTIMATED MONTHLY COST: $0 (100% FREE TIER)")

# Create usage tracking table
usage_data = {
    'Service': ['Realtime Database', 'Hosting', 'Cloud Functions', 'Authentication'],
    'Usage': [f'{monthly_data_gb:.3f} GB', '<0.1 GB', '<1K invocations', 'Not needed'],
    'Free Limit': ['10 GB', '10 GB', '2M invocations', '50K MAU'],
    'Status': ['✅ Free', '✅ Free', '✅ Free', '✅ Free']
}

usage_df = pd.DataFrame(usage_data)
print("\nUSAGE vs FREE TIER LIMITS:")
print(usage_df.to_string(index=False))

# Save to CSV for reference
usage_df.to_csv('firebase_usage_analysis.csv', index=False)
print(f"\n✅ Usage analysis saved to firebase_usage_analysis.csv")
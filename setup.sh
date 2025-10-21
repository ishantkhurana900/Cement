#!/bin/bash
# setup.sh - Automated setup script for Cement Plant Dashboard

set -e  # Exit on any error

echo "🏭 Cement Plant Dashboard Setup Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running on Ubuntu/Debian
if [[ -f /etc/debian_version ]]; then
    print_info "Detected Debian/Ubuntu system"
    PACKAGE_MANAGER="apt"
else
    print_warning "This script is optimized for Ubuntu/Debian. Adjust commands for your OS."
fi

# Step 1: Install Node.js and npm (if not already installed)
echo -e "\n${BLUE}Step 1: Installing Node.js and npm...${NC}"
if command -v node >/dev/null 2>&1; then
    print_status "Node.js already installed: $(node --version)"
else
    print_info "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    print_status "Node.js installed: $(node --version)"
fi

# Step 2: Install Firebase CLI
echo -e "\n${BLUE}Step 2: Installing Firebase CLI...${NC}"
if command -v firebase >/dev/null 2>&1; then
    print_status "Firebase CLI already installed: $(firebase --version)"
else
    print_info "Installing Firebase CLI..."
    sudo npm install -g firebase-tools
    print_status "Firebase CLI installed"
fi

# Step 3: Install Python dependencies
echo -e "\n${BLUE}Step 3: Installing Python dependencies...${NC}"
if command -v python3 >/dev/null 2>&1; then
    print_status "Python3 found: $(python3 --version)"
else
    print_error "Python3 not found. Please install Python3 first."
    exit 1
fi

if command -v pip3 >/dev/null 2>&1; then
    print_status "pip3 found: $(pip3 --version)"
else
    print_info "Installing pip3..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# Install Python requirements
if [[ -f "data-ingestion/requirements.txt" ]]; then
    print_info "Installing Python requirements..."
    pip3 install -r data-ingestion/requirements.txt
    print_status "Python dependencies installed"
else
    print_warning "requirements.txt not found in data-ingestion/ directory"
fi

# Step 4: Create project structure
echo -e "\n${BLUE}Step 4: Creating project structure...${NC}"

# Create directories
mkdir -p public
mkdir -p functions
mkdir -p data-ingestion
mkdir -p sample-data

print_status "Project directories created"

# Step 5: Firebase project setup
echo -e "\n${BLUE}Step 5: Firebase project setup...${NC}"
print_info "You'll need to login to Firebase and select/create a project"

# Check if already logged in
if firebase projects:list >/dev/null 2>&1; then
    print_status "Already logged in to Firebase"
else
    print_info "Please login to Firebase..."
    firebase login
fi

# Initialize Firebase project
if [[ ! -f "firebase.json" ]]; then
    print_info "Initializing Firebase project..."
    echo "Please select the following when prompted:"
    echo "  - Realtime Database"
    echo "  - Functions"
    echo "  - Hosting"
    echo ""
    firebase init
    print_status "Firebase project initialized"
else
    print_status "Firebase project already initialized"
fi

# Step 6: Create sample Excel file with your data structure
echo -e "\n${BLUE}Step 6: Creating sample data file...${NC}"

cat > sample-data/create_sample_data.py << 'EOF'
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create sample data matching your structure
print("Creating sample Excel file...")

# Generate sample data (500 records, 5-second intervals)
num_records = 500
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

# Save to Excel
df.to_excel('sample-data/cement_plant_data.xlsx', index=False)
print("✅ Sample Excel file created: sample-data/cement_plant_data.xlsx")
print(f"📊 Generated {num_records} sample records")
EOF

python3 sample-data/create_sample_data.py
print_status "Sample data file created"

# Step 7: Environment file setup
echo -e "\n${BLUE}Step 7: Environment configuration...${NC}"

if [[ ! -f "data-ingestion/.env" ]]; then
    print_info "Creating environment configuration file..."
    
    # Get Firebase project ID
    PROJECT_ID=$(firebase use --json 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['projectId'])" 2>/dev/null || echo "your-project-id")
    
    cat > data-ingestion/.env << EOF
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=service-account-key.json
FIREBASE_DATABASE_URL=https://${PROJECT_ID}-default-rtdb.firebaseio.com

# Data Configuration
EXCEL_FILE_PATH=../sample-data/cement_plant_data.xlsx

# Logging Configuration
LOG_LEVEL=INFO
EOF
    
    print_status "Environment file created: data-ingestion/.env"
    print_warning "Don't forget to download your Firebase service account key!"
else
    print_status "Environment file already exists"
fi

# Step 8: Create basic Firebase functions package.json
echo -e "\n${BLUE}Step 8: Firebase Functions setup...${NC}"

if [[ ! -f "functions/package.json" ]]; then
    cat > functions/package.json << 'EOF'
{
  "name": "cement-plant-functions",
  "description": "Cloud Functions for Cement Plant Dashboard",
  "scripts": {
    "build": "tsc",
    "serve": "npm run build && firebase emulators:start --only functions",
    "shell": "npm run build && firebase functions:shell",
    "start": "npm run shell",
    "deploy": "firebase deploy --only functions",
    "logs": "firebase functions:log"
  },
  "engines": {
    "node": "18"
  },
  "main": "lib/index.js",
  "dependencies": {
    "firebase-admin": "^11.8.0",
    "firebase-functions": "^4.3.1"
  },
  "devDependencies": {
    "typescript": "^4.9.0",
    "@types/node": "^18.15.0"
  },
  "private": true
}
EOF
    print_status "Functions package.json created"
fi

# Step 9: Set up Firebase Hosting files (copy your HTML, CSS, JS)
echo -e "\n${BLUE}Step 9: Setting up hosting files...${NC}"
print_info "You need to copy your HTML, CSS, and JS files to the public/ directory"
print_info "Files needed:"
echo "  - public/index.html"
echo "  - public/styles.css"
echo "  - public/dashboard.js"

# Step 10: Final instructions
echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Download your Firebase service account key:"
echo "   - Go to Firebase Console > Project Settings > Service Accounts"
echo "   - Click 'Generate new private key'"
echo "   - Save as 'data-ingestion/service-account-key.json'"
echo ""
echo "2. Copy your project files:"
echo "   - Copy index.html to public/"
echo "   - Copy styles.css to public/"
echo "   - Copy dashboard.js to public/"
echo "   - Update Firebase config in dashboard.js"
echo ""
echo "3. Replace sample data with your Excel file:"
echo "   - Replace sample-data/cement_plant_data.xlsx with your actual data"
echo ""
echo "4. Test the data uploader:"
echo "   cd data-ingestion"
echo "   python3 data_uploader.py"
echo ""
echo "5. Deploy to Firebase:"
echo "   firebase deploy"
echo ""
print_status "Your cement plant dashboard is ready for deployment!"

# Create a quick start guide
cat > QUICK_START.md << 'EOF'
# Quick Start Guide

## 1. Setup Complete ✅
Your development environment is ready!

## 2. Required Files to Add
- `data-ingestion/service-account-key.json` (Download from Firebase Console)
- `public/index.html` (Your dashboard HTML)
- `public/styles.css` (Your dashboard styles)
- `public/dashboard.js` (Your dashboard JavaScript)

## 3. Update Firebase Config
Edit `public/dashboard.js` and update the Firebase configuration with your project details.

## 4. Test Data Upload
```bash
cd data-ingestion
python3 data_uploader.py
```

## 5. Deploy Dashboard
```bash
firebase deploy
```

## 6. View Live Dashboard
Your dashboard will be available at: https://your-project-id.web.app

## Monthly Cost: $0 (Free Tier) 💰
EOF

print_status "Quick start guide created: QUICK_START.md"
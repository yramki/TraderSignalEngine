#!/bin/bash
# Start Discord Trading Signal Scraper

# Set text colors for better feedback
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}[INFO]${NC} Activating virtual environment..."
source venv/bin/activate

# Verify key dependencies
echo -e "${GREEN}[INFO]${NC} Verifying dependencies..."
python3 -c "import pyautogui" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} PyAutoGUI not installed. Please run install.sh again."
    echo -e "${YELLOW}[TIP]${NC} You can also try: source venv/bin/activate && pip install pyautogui"
    exit 1
fi

# Run application
echo -e "${GREEN}[INFO]${NC} Starting Discord Trading Signal Scraper..."
python3 src/main.py "$@"

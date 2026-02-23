# 🚀 AWS EFS Analyze

r: Cost Optimization ToolAWS EFS Analyzer is a high-performance command-line tool built to help AWS users identify massive cost-saving opportunities within their Elastic File System (EFS) environments.
# ✨ Key Features:
# ⚡ Parallel Processing: Scans massive file systems efficiently using multi-core processing (customizable thread count).
# 📊 Smart Categorization: Groups files by age based on last access time (7, 14, 30, 60, 90 days, 1 year, and 2+ years).
# 💰 Cost Projection: Real-time estimation of savings if data is moved to EFS Infrequent Access or Archive tiers.
# 🛡️ Safety First: * Automatically excludes system directories (/proc, /sys, /dev).Detects and prevents symbolic link loops.Warns about high CPU usage before resource-intensive scans.
# 📈 Rich Reporting: Generates detailed reports in both Interactive HTML (with visualizations) and Plain Text.
# ⏱️ Real-time Progress: Integrated progress bar with completion percentage, file count, and ETA.

# 🛠 Installation Prerequisites:
Python 3.8 or higher 
An active AWS EFS mount point on your Linux/Unix system.
# Setup: Clone the repository:Bash git clone https://github.com/kpratikshak/aws-efs-analyzer.git
# cd aws-efs-analyzer
 # Install dependencies:pip install -r requirements.txt
 #  🚀 Usage: Run the analyzer by pointing it to your EFS mount :
 path:Bashpython3 efs_analyzer.py --path /mnt/efs_data --threads 4 --output-dir ./reports
Options:FlagDescriptionDefault--path(Required) 
Path to the EFS mount pointN/A--threadsNumber of parallel threads for scanningCPU Implements robust permission checks to ensure the scan completes even when encountering restricted files.

 # Contributions are welcome! 
 If you have ideas for new features (like automated lifecycle policy generation), feel free to:Fork the Project: 
 Create your Feature Branch (git checkout -b feature/AmazingFeature)Commit your Changes (git commit -m 'Add some AmazingFeature')
 Push to the Branch (git push origin feature/AmazingFeature)
 Open a Pull Request
 📄 License: Distributed under the MIT License. See LICENSE for more information

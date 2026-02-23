🚀 AWS EFS Analyzer

AWS EFS Analyzer is a Python-based tool that scans an Amazon EFS (Elastic File System) mount point to identify cost optimization opportunities.

It categorizes files based on last access time and calculates potential cost savings across different EFS storage tiers — helping you make informed lifecycle policy decisions.

⚠️ IMPORTANT:
This tool performs READ-ONLY operations.
It does NOT modify files or change your EFS configuration.
It only analyzes file metadata to recommend potential cost savings.

✨ Key Features
⚡ Parallel Processing

Efficiently scans large file systems using multi-core processing (customizable thread count).

📊 Smart Categorization

Groups files based on last access time:

0–7 days

8–14 days

15–30 days

31–60 days

61–90 days

91–365 days

1–2 years

2+ years

💰 Cost Projection

Estimates potential savings when transitioning data to:

EFS Standard

EFS Infrequent Access (IA)

EFS Archive

🛡️ Safety First

Automatically excludes system directories (/proc, /sys, /dev, etc.)

Detects and prevents symbolic link loops

Warns about high CPU usage before intensive scans

Implements robust permission handling to continue scanning even if restricted files are encountered

📈 Rich Reporting

Generates detailed reports in:

📄 Plain Text

🌐 Interactive HTML (with visualizations)

⏱️ Real-Time Progress Tracking

Displays:

Progress bar

File count

Completion percentage

ETA

🛠 Installation
Prerequisites

Python 3.8+

An active AWS EFS mount point on a Linux/Unix system

Clone the Repository
git clone https://github.com/kpratikshak/aws-efs-analyzer.git
cd aws-efs-analyzer
Install Dependencies
pip install -r requirements.txt
🚀 Usage

Run the analyzer by pointing it to your EFS mount:

python3 efs_analyzer.py --path /mnt/efs_data --threads 4 --output-dir ./reports
⚙️ Available Options
Flag	Description	Default
--path	(Required) Path to the EFS mount point	N/A
--threads	Number of parallel threads for scanning	CPU core count
--output-dir	Directory to store reports	./reports
📊 Example Output

After completion, the tool generates:

📄 efs_report_<timestamp>.txt

🌐 efs_report_<timestamp>.html

These reports include:

Storage distribution by access time

Tier recommendations

Estimated monthly savings

Optimization insights

🤝 Contributing

Contributions are welcome!

# Fork the project
git checkout -b feature/AmazingFeature
git commit -m "Add some AmazingFeature"
git push origin feature/AmazingFeature


📄 License

Distributed under the MIT License.
See the LICENSE file for more information.

#! /bin/bash
export USER_EMAIL="gosugrag@gmail.com"
sudo apt update
sudo apt install -y python3 python3-pip
cd /opt/findminiapp
find ./logs -type f -name "*.log" -mtime +30 -exec rm {} \;
pip install -r requirements.txt
/usr/bin/python3 -m findminiapp_spider.py
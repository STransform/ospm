# OSPM(Oromia Steel Pipe )

This system consists of multiple modules. Initially, it is launched with the HRMS module, which includes user management. Additional modules, such as CRM,Payroll, will be integrated at a later stage.
  
## Technology stack
- Python: Programming language
- JS: Client-side interactions and dynamic functionalities
- owl: Odoo Web library (framework)
- Werkzeug: Web Server
- QWeb: templating engine(generating HTML and XML views)
- Bootstrap: CSS framework
- XML-RPC: API and Integration
   
## Introduction
```bash
The OTES project consists of multiple modules, including HRMS, CRM, Project Management, and Inventory.
 ```
## Features
```bash
- List of key features or functionalities of each modules
- Highlight any unique aspects of OTES project
 ```
## Installation
### Prerequisites
 ```bash
- Prerequisites or dependencies (Python, PostgreSQL ,XML,JS,OWL,OS)
 ```
### Installation Steps

1. **Update The System:**  
```bash
sudo apt update
```
2. **Add System User:**
```bash
sudo useradd -m -d /opt/odoo16 -U -r -s /bin/bash odoo16
```
2. **Install Dependencies:**
```bash
   sudo apt install build-essential wget git python3-pip python3-dev python3-venv python3-wheel libfreetype6-dev libxml2-dev libzip-dev libsasl2-dev python3-setuptools libjpeg-dev zlib1g-dev libpq-dev libxslt1-dev libldap2-dev libtiff5-dev libopenjp2-7-dev
```
3. **Install dependencies:**
```bash
sudo apt install postgresql
```
4. **add a new postgresql use:**
```bash
sudo su - postgres -c "createuser -s odoo16"
```
3. **Install dependencies:**
 ```bash
 sudo apt install postgresql
```
4. **add a new postgresql use:**
```bash
sudo su - postgres -c "createuser -s odoo16"
```
5. **Install Wkhtmltopdf:**
```bash
sudo apt install wkhtmltopdf
```
6. **wkhtmltopdf --version:**
```bash
 pip install -r requirements.txt
```
7. **install Odoo under that username:**
 ```bash
 sudo su - odoo16
```
8. **clone the repository:**
```bash
 pgit clone https://github.com/STransform/otes.git
```
9. **clone the repository:**
```bash
pgit clone https://github.com/STransform/otes.git
```
10. **create a new python virtual environment:**
```bash
    python3 -m venv odoo16-venv
```
11. **activate:**
    ```bash
    source odoo16-venv/bin/activate
    ```
12. **install Odoo:**
```bash
    pip3 install wheel
    pip3 install -r odoo16/requirements.txt
    deactivate
    mkdir /opt/odoo16/odoo16/custom-addons
    exit
```
13. **Create database systemd unit file**
```bash 
sudo nano /etc/odoo16.conf
```
14. **Copy and save :**
```bash 
   [options]
admin_passwd = .....
db_host = False
db_port = False
db_user = odoo16
db_password = False
addons_path = /opt/odoo16/odoo16/addons,/opt/odoo16/odoo16/custom-addons
xmlrpc_port = 8069
```
15. **Create Odoo Systemd Unit file:**
```bash
sudo nano /etc/systemd/system/odoo16.service
```
16. **Copy and save :**
```bash
 [Unit]
Description=Odoo16
Requires=postgresql.service
After=network.target postgresql.service
[Service]
Type=simple
SyslogIdentifier=odoo16
PermissionsStartOnly=true
User=odoo16
Group=odoo16
ExecStart=/opt/odoo16/odoo16-venv/bin/python3 /opt/odoo16/odoo16/odoo-bin -c /etc/odoo16.conf
StandardOutput=journal+console
[Install]
WantedBy=multi-user.target
```
17. **Reload:**
```bash
sudo systemctl daemon-reload
```
18. **Start service:**
```bash
sudo systemctl start odoo16
```
    
10. **Check status:**
```bash
sudo systemctl status odoo16
```


10. **Author:**
```bash
S Transform
```



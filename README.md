# QoeDataReport

Automated creating of CSV report using QoE data from FT QoE module.
---

Installation:
---
- git clone https://github.com/swifty94/QoeDataReport.git or download it as is via https://github.com/swifty94/QoeDataReport/archive/refs/heads/master.zip
- unzip on target location
- run ./install, E.g:

<pre>
[server-01.com:~/QoeDataReport_v1]# ./install
Created folders: log/ reports/
Installing dependencies
Processing ./clickhouse_driver-0.2.1-cp36-cp36m-manylinux1_x86_64.whl
Processing ./mysql_connector_python-8.0.25-cp36-cp36m-manylinux1_x86_64.whl
Processing ./protobuf-3.17.3-cp36-cp36m-manylinux_2_5_x86_64.manylinux1_x86_64.whl
Processing ./pytz-2021.1-py2.py3-none-any.whl
Processing ./six-1.16.0-py2.py3-none-any.whl
Processing ./tzlocal-2.1-py2.py3-none-any.whl
Installing collected packages: pytz, tzlocal, clickhouse-driver, six, protobuf, mysql-connector-python
Successfully installed clickhouse-driver-0.2.1 mysql-connector-python-8.0.25 protobuf-3.17.3 pytz-2021.1 six-1.16.0 tzlocal-2.1
Done!
</pre>


Usage:
---
- Make sure your QoE monitoring in the CPEAdmin is actively running!
- copy or rename settings-sample.json to settings.json
- put your own details in each respective tag, example:
<pre>
{
    "qoeMonitoringName": "YourQoeMonitoringName",           // name of the QoE monitoring fro CPEAdmin
    "trDbString": {                                         // connection string to FT DB (MySQL)
        "host": "localhost",
        "user": "ftacs",
        "password": "ftacs",
        "database": "ftacs"
    },
    "collectDateRange": false,                              // if collectDateRange=true -> dateRange must be specified
                                                                otherwise data will be collected only for the current day

    "dateRange": [                                          // Array of date/time range for data collection
                                                            // ['begin_date_time', 'end_date_time']
        "YYYY-MM-DD HH:MM:SS",
        "YYYY-MM-DD HH:MM:SS"
    ],
    
    "qoeDbString": "clickhouse://localhost",                // connection string to ClickHouse DB
    "qoeDbSchema": "ftacs_qoe_ui_data",                     // name of the QoE schema (default name is already there)
    "isSmtp": true,                                         // email notification if "false" -> disabled
    "smtpHost": "smtp.somesite.com",                        // SMTP server, e.g., smtp.gmail.com
    "smpthUser": "user@somesite.com",                       // email address
    "smpthPassword": "password",                            // password from email above
    "smpthPort": 465,                                       // SMTP port
    "recipients": ["recipient1@somesite.com","recipient2@somesite.com"] // where to send the reports, separated by comas
    "isFtp": true,                                          // upload to FTP server. "false" - disabled              
    "ftpHost": "ftp.site.com",                              // FTP server
    "ftpUser": "ftpuser",                                   // FTP user
    "ftpPass": "ftppassword",                               // FTP password
    "cpeParameterNames": [                                  // Array of TR parameter and their handy names

    // Empty by default. Automatically populated once "init" was executed. 
        {
            "parameterName": "'InternetGatewayDevice.DeviceInfo.UpTime'",    // TR-069 parameter name
            "custName": "UpTime"                                             // Your KPI/column name
        },
        {
            "parameterName": "'InternetGatewayDevice.WANDevice.i.WANEthernetInterfaceConfig.Stats.BytesSent'",
            "custName": "BytesSent"
        },
        {
            "parameterName": "'InternetGatewayDevice.WANDevice.i.WANEthernetInterfaceConfig.Stats.BytesReceived'",
            "custName": "BytesReceived"
        },        
    ]
}
</pre>

- Execute: source venv/bin/activate
- Execute: python3 main.py init
- Check settings.json and put the convenient "custName" for each "parameterName"
- Execute: python3 main.py report to get the data 

- If you want to create several reports simultaneously, you either need to have 2 separate project directories or have 2 separate settings.json files which you'll be switching manually.

Usage example:
---
<pre>
[server-01.com:~/QoeDataReport_v1]# source venv/bin/activate
(venv) [server-01.com:~/QoeDataReport_v1]# python3 main.py

No arguments provided! Please review README.md for the usage instructions

Try initiate application first!
- ~$ python3 main.py init  // get QoE report metadata into settings.json

Then you can do something like:
- ~$ python3 main.py report  // creating of reports and sending them via email (if defined in settings.json)
(venv) [server-01.com:~/QoeDataReport_v1]#
(venv) [server-01.com:~/QoeDataReport_v1]# python3 main.py init

TR parameter names obtained.

Please update settings.json with respective KPI names

Once it is done. You can run:
- ~$ python3 main.py report  // instant report creating and sending it (if defined in settings.json)
(venv) [server-01.com:~/QoeDataReport_v1]#
(venv) [server-01.com:~/QoeDataReport_v1]# python3 main.py report
Finished!
(venv) [server-01.com:~/QoeDataReport_v1]# ls reports/ -lah
total 64K
drwxr-xr-x 2 root root  75 Jun 30 19:30 .
drwxr-xr-x 7 root root 310 Jun 30 19:30 ..
-rw------- 1 root root 61K Jun 30 19:30 server_01_com_Export_2021_06_30_19-30_13_SAST.csv
(venv) [server-01.com:~/QoeDataReport_v1]#
</pre>
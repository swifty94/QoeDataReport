# QoeDataReport

... Automated creating of CSV report with FT QoE monitoring data for specific monitoring.
---

Installation:
---
- clone this repo or download as is
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
- rename settings-sample.json to settings.json
- put your own details in each respective tag
- source venv/bin/activate
- python3 main.py init
- check settings.json and put the convenient "custName" for each "parameterName"
- python3 main.py report &

Example:
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

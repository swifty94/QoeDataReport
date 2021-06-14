# QoeDataReport

... Automated creating of CSV report with FT QoE monitoring data for specific monitoring.
---

Installation:
---
- clone this repo or download as is
- unzip on target location
- run ./install

Usage:
---    
- rename settings-sample.json to settings.json
- put your own details in each respective tag
- source venv/bin/activate
- python3 main.py init
- python3 main.py report

Example:
<pre>
(venv) master@devnull:~/Dev/QoeDataReport$ python3 main.py

No arguments provided! Please review README.md for the usage instructions

Try initiate application first!
- ~$ python3 main.py init  // get QoE report metadata into settings.json

Then you can do something like:
- ~$ python3 main.py report  // creating of reports and sending them via email (if defined in settings.json)

(venv) master@devnull:~/Dev/QoeDataReport$ 
</pre>


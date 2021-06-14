import mysql.connector
import re, socket, csv, sys, time, os
import smtplib, ssl, socket, shutil
import json
import base64
import logging
import logging.config
from os import path
from typing import Dict, List, AnyStr, Union
from datetime import datetime, date
from clickhouse_driver import connect
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.ini')
logging.config.fileConfig(log_file_path)

class JsonSettings(object):

    def __init__(self, json_file="settings.json"):
        self.json_file = json_file
        self.cn = __class__.__name__
        
    def parseJson(self, json_key: str) -> Union[List, AnyStr]:
        """
        :Accepts JSON file (path) and key as argument (both are type of String)\n
        :Return either List or String of respective values from settings
        """
        
        try:
            with open(self.json_file) as f:
                data = json.load(f)
            
            json_value = data[json_key]            
            return json_value
        except Exception as e:
            logging.error(f'{self.cn} Exception: {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} parsedKey: {json_key}')

    def updateJson(self, key: str, value: str):
        try:
            with open(self.json_file) as f:
                json_decoded = json.load(f)
            
            json_decoded[key] = value

            with open(self.json_file, 'w') as f:
                json.dump(json_decoded,f, indent=4)
        except Exception as e:
            logging.error(f'{self.cn} Exception: {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} updatedJson with key: {key} value: {value}')

class Email(object):
  """
  Class for reporting data once job is finished
  """
  def __init__(self):
    self.cn = __class__.__name__
    self.settings = JsonSettings()
    self.IS_SMTP = self.settings.parseJson("isSmtp")
    self.SMTP_PORT = self.settings.parseJson("smtpPort")
    self.SMTP_HOST = self.settings.parseJson("smtpHost")
    self.SMTP_USER = self.settings.parseJson("smtpUser")
    self.SMTP_PASS = self.settings.parseJson("smtpPass")
    self.RECEPIENTS = self.settings.parseJson("recipients")

  def send(self, attach):
    try:        
        if self.IS_SMTP:
            for receiver in self.RECEPIENTS:                
                host = socket.gethostname()      
                header = f"QoeDataReport Automatic email notification from {host}"
                message = MIMEMultipart("alternative")
                message["Subject"] = header
                message["From"] = self.SMTP_USER
                message["To"] = receiver                                
                timezone = time.tzname[0]
                now = datetime.now()
                date = now.strftime("%Y_%m_%d_%H-%M_%S")
                reportPath = self.settings.parseJson("reportFilePath")
                attach_file_name = f"{host}_Export_{date}_{timezone}.csv"                

                # Create the plain-text and HTML version of your message
                TEXT = """      
                Greetings!    \n
                QoE report finished \n
                File attached. \n
                Best Regards, \n
                QoeDataReport \n
                """

                HTML = """
                <!DOCTYPE html>
                <html lang="en">
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">    
                <body>
                <div> 
                    <p>Greetings!</p>
                    <p>QoE report finished.</p>        
                    <p>File attached</p>  
                    <p>Best Regards,</p>
                    <p>QoeDataReport</p>       
                </div>
                </body>
                </html>
                """
                
                shutil.copy(attach, attach_file_name)    
                f = open(attach_file_name, 'r')
                attachment = MIMEText(f.read())
                attachment.add_header('Content-Disposition', 'attachment', filename=attach_file_name)
                message.attach(attachment)      
                part1 = MIMEText(TEXT, "plain")
                part2 = MIMEText(HTML, "html")      
                message.attach(part1)
                message.attach(part2)                
                context = ssl._create_unverified_context()
                with smtplib.SMTP_SSL(self.SMTP_HOST, self.SMTP_PORT, context=context) as server:
                    server.login(self.SMTP_USER, self.SMTP_PASS)
                    logging.info(f"{self.cn} SMTP session established")
                    server.sendmail(self.SMTP_USER, receiver, message.as_string())
                    logging.info(f'{self.cn} Email sent ')
                    server.quit()  
                    os.remove(attach_file_name)
        else:
            logging.info(f"{self.cn} SMTP is not enabled")
    except Exception as e:
        logging.error(f"{self.cn} Exception {e}", exc_info=1)        

class FTDataProcessor(JsonSettings):
    def __init__(self):
        super().__init__()
        self.cn = __class__.__name__        
        self.qoeSchema = self.parseJson('qoeDbSchema')
        self.mysqlconf = self.parseJson('trDbString')   
        self.chconf = self.parseJson('qoeDbString')
        self.qoename = self.parseJson('qoeMonitoringName')

    def _today(self):
        dt = date.today()
        midnight = datetime.combine(dt, datetime.min.time())
        return midnight    
    
    def mysqlSelect(self, query) -> list:        
        try:                                               
            connection = mysql.connector.connect(**self.mysqlconf)
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            final = []
            for param in result:
                param = str(param).replace('(','').replace(')','').replace(',','')              
                final.append(param)
            return final
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
            logging.error(f'{self.cn} SQL: \n {query}')
            if cursor and connection:
                cursor.close()
                connection.close()
        finally:                            
            if cursor and connection:
                cursor.close()
                connection.close()
                
    def clickhouseSelect(self, query) -> list:
        try:            
            qoeConnection = connect(self.chconf)
            dbCursor = qoeConnection.cursor()
            dbCursor.execute(query)
            result = dbCursor.fetchall()            
            return result
        except Exception as e:
            qoeConnection.close()
            logging.error(f'{self.cn} error {e}', exc_info=1)
            logging.error(f'{self.cn} SQL: \n {query}')    
        finally:
            qoeConnection.close()
            
    def getCpeSerials(self) -> list:
        try:            
            qoe_monitoring_parent = self.mysqlSelect(f"select id from qoe_monitoring_parent where name = '{self.qoename}'")
            par_id = str(qoe_monitoring_parent).replace('[','').replace(']','').replace('\'','')
            par_id = int(par_id)            
            cpe_serials = self.mysqlSelect(f"select serial from cpe c, qoe_cpe_in_monitor q where c.id=q.cpe_id and monitoring_id={par_id};")
            return cpe_serials
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)            
        finally:
            logging.info(f'{self.cn} processed CpeSerials')
    
    def getParameterNameIds(self) -> list:
        try:
            cpe_serials = str(self.getCpeSerials()).replace('[','(').replace(']',')').replace('"','')
            parameter_name_ids = self.mysqlSelect(f"select distinct(name_id) from qoe_cpe_parameter where serial IN {cpe_serials}")
            return parameter_name_ids
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} processed ParameterNameIds')
    
    def getParameterNames(self) -> list:
        try:
            parameter_name_ids = self.getParameterNameIds()
            parameter_names = self.mysqlSelect(f'select name from qoe_cpe_parameter_name where id in {tuple(parameter_name_ids)}')
            return parameter_names
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} processed ParameterNames')
           
    def getKpiNames(self) -> None:
        try:
            logging.info(f'{self.cn} Attempt to update cpeParameterNames in settings.json')
            final_list = []                        
            for parameter in self.getParameterNames():
                item = {"parameterName": "", "custName": ""}                
                item["parameterName"] = parameter                
                final_list.append(item)                
            self.updateJson("cpeParameterNames",final_list)
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} updated cpeParameterNames in settings.json')

    def getQoeDbValue(self) -> list:
        try:
            values = []
            nids = self.getParameterNameIds()
            for serial in self.getCpeSerials():                
                sql = f"SELECT serial, created, value  FROM {self.qoeSchema}.cpe_data WHERE name_id IN {tuple(nids)} AND serial = {serial} AND created >= toDateTime('{self._today()}') ORDER BY created ASC"                
                kpiValue = self.clickhouseSelect(sql)                
                values.append(kpiValue)                
            return values
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} data processed')


class Report(JsonSettings):
    def __init__(self):
        super().__init__()
        self.cn = __class__.__name__

    def csvColumns(self) -> list:
        try:
            csvColumns = ["Serial","Timestamp"]
            qoeParams = self.parseJson("cpeParameterNames")
            for param in qoeParams:
                column = param["custName"]
                csvColumns.append(column)
            return csvColumns
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} csvColumns obtained')
                   
    def createFullDataModel(self) -> list:
        try:
            fullDataModel = []            
            kpiNames = []
            kpiValues = []
            kpiSerials = []
            kpiDates = []
            dataModel = {}
            FTData = FTDataProcessor()
            dataValues = FTData.getQoeDbValue()            
            qoeParams = self.parseJson("cpeParameterNames")
            
            for param in qoeParams:
                name = param["custName"]
                kpiNames.append(name)
                                
            for item in dataValues:
                for subitem in item:
                    value = subitem[2]
                    serial = subitem[0]
                    time = str(subitem[1])
                    kpiValues.append(value)
                    kpiSerials.append(serial)
                    kpiDates.append(time)                    
            
            for s in kpiSerials:
                dataModel["Serial"] = s
                fullDataModel.append(dataModel)
            
            for d in fullDataModel:
                for t in kpiDates:
                    d["Timestamp"] = t.replace(' ','_').replace(':','_')
                for n,v in zip(kpiNames, kpiValues):
                    d[n] = v                    

            return fullDataModel
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} collected FullDataModel')

    def write(self) -> str:
        try:
            logging.info(f'{self.cn} Started creating CSV')
            hostname = socket.gethostname()
            timezone = time.tzname[0]
            now = datetime.now()
            date = now.strftime("%Y_%m_%d_%H-%M_%S")
            reportPath = self.parseJson("reportFilePath")
            csvName = f"{hostname}_Export_{date}_{timezone}.csv"
            csvFile = reportPath + csvName
            csvColumns = self.csvColumns()
            csvData = self.createFullDataModel()
            logging.info(f'{self.cn} Items to be processed - {len(csvData)}')            
            with open(csvFile, 'w') as f:
                writer = csv.DictWriter(f, fieldnames=csvColumns)
                writer.writeheader()
                for data in csvData:
                    writer.writerow(data)
            return csvFile                                
        except IOError:
            logging.error(f'{self.cn} Excetion: {IOError}', exc_info=1)
        except Exception:
            logging.error(f'{self.cn} Excetion: {Exception}', exc_info=1)
        finally:
            logging.info(f'{self.cn} Finished creating CSV')
    
    def serve(self):
        pass


class UserInterface(Report):
    def __init__(self):
        super().__init__()
        self.FTData = FTDataProcessor()
        self.Mail = Email()

    def cli_runner(self) -> None:        
        try:            
            cli_arg = sys.argv[1]
            if cli_arg == 'init':
                self.FTData.getKpiNames()
                print('\nTR parameter names obtained.')
                print('\nPlease update settings.json with respective KPI names')
                print('\nOnce it is done. You can run:')
                print('- ~$ python3 main.py report  // instant report creating and sending it (if defined in settings.json)')
                exit(0)
            elif cli_arg == 'report':
                try:
                    report = self.write()
                    self.Mail.send(report)
                    exit(0)
                except Exception as err:
                    print(f"Exception: {err}")
                finally:
                    print("Finished!")                            
        except IndexError:
            print('\nNo arguments provided! Please review README.md for the usage instructions')
            print('\nTry initiate application first!')
            print('- ~$ python3 main.py init  // get QoE report metadata into settings.json')
            print('\nThen you can do something like:')
            print('- ~$ python3 main.py report  // creating of reports and sending them via email (if defined in settings.json)\n')
            exit(1)
        except KeyboardInterrupt as k:
            print("UserKeyboardInterrupt event received. Bye!")
            exit(0)

UserInterface = UserInterface()
UserInterface.cli_runner()
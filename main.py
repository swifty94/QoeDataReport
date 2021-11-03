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
import ftplib

log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.ini')
logging.config.fileConfig(log_file_path)

class JsonSettings(object):
    """
    Class for get/set data from/to *.json\n
    Default filename for __init__() is settings.json
    """
    def __init__(self, json_file="settings.json"):
        self.json_file = json_file
        self.cn = __class__.__name__
        
    def parseJson(self, json_key: str) -> Union[List, AnyStr]:
        """
        :param str json_key - key to look for in file \n
        :Return either List or String of respective values from settings
        """
        
        try:
            with open(self.json_file) as f:
                data = json.load(f)
            
            json_value = data[json_key]            
            return json_value
        except Exception as e:
            logging.error(f'{self.cn} Exception: {e}', exc_info=1)        

    def updateJson(self, key: str, value: str) -> None:
        """
        Void method
        :param str key - key for the respective value pair as second param
        :param str value - value         
        """
        try:
            with open(self.json_file) as f:
                json_decoded = json.load(f)
            
            json_decoded[key] = value

            with open(self.json_file, 'w') as f:
                json.dump(json_decoded,f, indent=4)
        except Exception as e:
            logging.error(f'{self.cn} Exception: {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} updatedJson key: {key}')


class FTP(object):
    """
    Class for reporting data via FTP once job is finished
    """
    def __init__(self):
        super().__init__()
        self.cn = __class__.__name__
        self.settings = JsonSettings()
        self.IS_FTP = self.settings.parseJson("isFtp")
        self.FTP_HOST = self.settings.parseJson("ftpHost")
        self.FTP_USER = self.settings.parseJson("ftpUser")
        self.FTP_PASS = self.settings.parseJson("ftpPass")
    
    def send(self, report_file: str) -> None:
        """
        Void method
        :param str report_file - path to file for sending
        """
        try:
            if self.IS_FTP:
                logging.info(f"{self.cn} FTP is enabled")
                logging.info(f"{self.cn} Attempt to send the file to {self.FTP_HOST}")
                session = ftplib.FTP(self.FTP_HOST, self.FTP_USER, self.FTP_PASS)            
                file_to_send = open(report_file,'rb')
                file_name = report_file.replace("reports/", "")
                session.storbinary(f'STOR {file_name}', file_to_send)
                file_to_send.close()
                filelist = session.nlst()
                for fn in filelist:
                    if file_name in fn:
                        logging.info(f"{self.cn} FTP: {fn} transferred")
                        logging.info(f"{self.cn} FTP: Success!")                    
                session.quit()                
            else:
                logging.info(f"{self.cn} FTP is not enabled")
        except Exception as e:
            logging.error(f"{self.cn} Exception {e}", exc_info=1)     

class Email(object):
  """
  Class for reporting data via email once job is finished
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

  def send(self, attach: str) -> None:
    """
    Void method
    :param str attach - path to attachment for the email
    """
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
                reportPath = 'reports/'
                attach_file_name = f"{host}_Export_{date}_{timezone}.csv"                

                # Create the plain-text and HTML version of your message
                TEXT = """      
                Greetings!    \n
                QoE report finished \n
                Report attached\n
                Best Regards, \n
                QoeDataReport \n
                https://github.com/swifty94/QoeDataReport\n
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
                    <p>Report attached</p>  
                    <p>Best Regards,</p>
                    <p>QoeDataReport</p>
                    <p>https://github.com/swifty94/QoeDataReport</p>   
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
                    status = server.noop()[0]
                    if status == 250:
                        logging.info(f"{self.cn} SMTP session: Established")
                        server.sendmail(self.SMTP_USER, receiver, message.as_string())
                        logging.info(f'{self.cn} Email sent ')
                        server.quit()                                                               
                    else:
                        logging.info(f"{self.cn} SMTP session: Failed")
                        logging.exception(f"{self.cn} Error occured during either establising SMTP session or sending an email")
                        logging.exception(f"{self.cn} Please validate the connection to your SMTP server and/or your credentials")
                        pass
                    os.remove(attach_file_name)
        else:
            logging.info(f"{self.cn} SMTP is not enabled")
    except Exception as e:
        logging.error(f"{self.cn} Exception {e}", exc_info=1)    

class FTDataProcessor(JsonSettings):
    """
    Class for collecting and processing data for a specific QoE monitoring\n
    defined in the settings.json 
    """
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
            logging.info(f'{self.cn} id from qoe_monitoring_parent = {par_id}')     
            qoe_monitoring_id = self.mysqlSelect(f"select group_id from qoe_monitoring where parent_id = {par_id}")
            qoe_monitoring_id = str(qoe_monitoring_id).replace('[','').replace(']','').replace('\'','')
            qoe_monitoring_id = int(qoe_monitoring_id)
            logging.info(f'{self.cn} group_id from qoe_monitoring = {qoe_monitoring_id}')
            cpe_serials = self.mysqlSelect(f"select serial from qoe_cpe where group_id={qoe_monitoring_id};")
            logging.info(f'{self.cn} serial from qoe_cpe count = {len(cpe_serials)}')    
            return cpe_serials
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)            
        finally:
            logging.info(f'{self.cn} processed CpeSerials')
    
    def getParameterNameIds(self) -> list:
        try:
            cpe_serials = str(self.getCpeSerials()).replace('[','(').replace(']',')').replace('"','')
            parameter_name_ids = self.mysqlSelect(f"select distinct(name_id) from qoe_cpe_parameter where serial in {cpe_serials}")
            parameter_name_ids = [int(x) for x in parameter_name_ids]
            logging.info(f"{self.cn} number of name_id in list {len(parameter_name_ids)}")
            return parameter_name_ids
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} processed ParameterNameIds')
    
    def getParameterNames(self) -> list:
        try:
            parameter_name_ids = self.getParameterNameIds()
            parameter_names = self.mysqlSelect(f'select name from qoe_cpe_parameter_name where id in {tuple(parameter_name_ids)}')
            [logging.info(f'{self.cn} got parameter: {x}') for x in parameter_names]
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
            kpiNames = []
            qoeParams = self.parseJson("cpeParameterNames")
            isDateRange = self.parseJson("collectDateRange")

            for param in qoeParams:
                name = param["custName"]                
                kpiNames.append(name)

            name_ids = self.getParameterNameIds()            
            for serial in self.getCpeSerials():                                
                sql_begin = "SELECT serial, created, value, name_id, multiIf("
                if isDateRange:
                    datesList = self.parseJson("dateRange")
                    begin, end = datesList[0], datesList[1]                    
                    sql_end = f" FROM {self.qoeSchema}.cpe_data WHERE name_id IN {tuple(name_ids)} AND serial = {serial} AND created >= toDateTime('{begin}') AND created <= toDateTime('{end}') ORDER BY created ASC"
                else:
                    sql_end = f" FROM {self.qoeSchema}.cpe_data WHERE name_id IN {tuple(name_ids)} AND serial = {serial} AND created >= toDateTime('{self._today()}') ORDER BY created ASC"
                for name_id, kpi_name in zip(name_ids,kpiNames):          
                    part = f"name_id = {name_id}, '{kpi_name}',"
                    sql_begin = sql_begin + part
                sql_begin = sql_begin + " 'Null value') as kpi"
                sql_full = sql_begin + sql_end
                logging.info(f'{self.cn} ClickhouseSqlQuery: {sql_full}')
                kpiValue = self.clickhouseSelect(sql_full)                
                values.append(kpiValue)
            return values
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} data processed')        
        

class Report(JsonSettings):
    """
    Class for building the final report data model\n
    and writing it to the CSV
    """
    def __init__(self):
        super().__init__()
        self.cn = __class__.__name__

    def csvColumns(self) -> list:
        try:
            csvColumns = ["ESN","CollectTime"]
            qoeParams = self.parseJson("cpeParameterNames")
            for param in qoeParams:
                column = param["custName"]
                csvColumns.append(column)
            return csvColumns
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)        

    def cpeDataTupleList(self) -> list:        
        try:
            fullData = []
            uniq = []
            FTData = FTDataProcessor()
            dataValues = FTData.getQoeDbValue()
            for item in dataValues:
                for x in item:
                    uniq = tuple(uniq)                    
                    if x[0] not in uniq and x[1] not in uniq and x[2] not in uniq:
                        uniq += (x[0],)
                        uniq += (x[1],)
                        uniq += ({x[4]:x[2]},)
                    elif x[0] in uniq and x[1] in uniq and x[2] not in uniq:
                        uniq += ({x[4]:x[2]},)
                    elif x[0] in uniq and x[1] not in uniq:                        
                        fullData.append(uniq)
                        uniq = list(uniq)
                        uniq[:] = []
                        continue
            return fullData
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)        
        finally:
            logging.info(f'{self.cn} created cpeDataTupleList')
                           
    def createCpeModel(self) -> dict:
        try:
            keys = self.csvColumns()
            cpeModel = {}
            for k in keys:
                cpeModel[k] = "Null"
            return cpeModel
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)        

    def createFullDataModel(self) -> list:
        try:
            fullDataModel = []
            cpeDataTupleList = self.cpeDataTupleList()
            for i in cpeDataTupleList:
                cpeModel = self.createCpeModel()                                
                serial = i[0]
                timestamp = str(i[1])
                timestamp = timestamp
                tup_len = len(i)
                kpis = i[2:tup_len]                
                for model_key in cpeModel.keys():                    
                    cpeModel["ESN"] = serial
                    cpeModel["CollectTime"] = timestamp                    
                    for d in kpis:
                        if type(d) == dict:
                            for key,value in d.items():
                                if model_key in d.keys():
                                    val = d[model_key]
                                    cpeModel[model_key] = val.replace(" ","")
                fullDataModel.append(cpeModel)
            
            return fullDataModel
        except Exception as e:
            logging.error(f'{self.cn} error {e}', exc_info=1)
        finally:
            logging.info(f'{self.cn} created FullDataModel')

    def write(self) -> str:
        try:
            logging.info(f'{self.cn} Started creating CSV')
            hostname = socket.gethostname()
            hostname = hostname.replace('.','_').replace('-','_').replace('_csv','.csv')
            timezone = time.tzname[0]
            now = datetime.now()
            date = now.strftime("%Y_%m_%d_%H-%M_%S")
            reportPath = 'reports/'
            csvName = f"{hostname}_Export_{date}_{timezone}.csv"
            csvFile = reportPath + csvName
            csvColumns = self.csvColumns()
            csvData = self.createFullDataModel()
            logging.info(f'{self.cn} Items to be processed - {len(csvData)}')            
            with open(csvFile, 'w', newline='') as f:
                writer = csv.DictWriter(f, delimiter=',', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n', fieldnames=csvColumns)
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

class UserInterface(Report):
    """
    Class with a single method for interraction with user\n
    using the CLI
    """
    def __init__(self):
        super().__init__()
        self.cn = __class__.__name__
        self.FTData = FTDataProcessor()
        self.Mail = Email()
        self.Ftp = FTP()

    def cli_runner(self) -> None:        
        try:            
            cli_arg = sys.argv[1]            
            logging.info(f"{self.cn} Received CLI argument: {cli_arg}")
            logging.info(f"{self.cn} Started processing")
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
                    self.Ftp.send(report)                               
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
        finally:
            logging.info(f"{self.cn} Finished processing")

if __name__ == "__main__":
    Interface = UserInterface()
    Interface.cli_runner()
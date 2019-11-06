import os
import re
import sqlite3
import time
import requests
import sys
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtCore import pyqtSignal, QThread

class WorkThread(QThread):
    progress_update = pyqtSignal(int)  # 信号类型：int


    def __init__(self,parent=None):
        super().__init__(parent)
        self.Url=None
        self.Accounts=None
        self.Proxies=None
        self.DB=None
        self.pause = False
        self.ProxyEnable=False
        self.ProxyUsedLimit=None
        self.RequestTimeout=None
        self.RequestArguments=None
        self.ProxyType=None
        self.ProxyCount=0
        self.ThreadID=None
        self.Interval=0
        self.Proxy=""


    def run(self):
        self.DoWork()


    def getCookies(self,cookie_jar):
        cookie_dict = cookie_jar.get_dict()
        found = ['%s=%s' % (name, value) for (name, value) in cookie_dict.items()]
        return ';'.join(found)


    def HttpRequest(self,Method,Url,Data,Timeout=30,ProxyEnable=False,ProxyType="http"):
        Response=None
        FirstRequest=True
        while Response == None:
            if ProxyEnable:
                if FirstRequest==False:
                    print("Thread["+str(self.ThreadID)+"] request with Proxy["+self.Proxie+"] was Failed.")
                self.Proxie = self.ChangeProxie()
                if self.Proxie==None:
                    break

            FirstRequest = False
            try:
                if Method=="GET":
                    if ProxyEnable:
                        Response = requests.get(Url, proxies={"http": ProxyType+'://' + self.Proxie,"https": ProxyType+'://' + self.Proxie}, timeout=Timeout)
                    else:
                        Response = requests.get(Url,timeout=Timeout)
                elif Method=="POST":
                    if ProxyEnable:
                        Response = requests.post(Url, data=Data, proxies={"http": ProxyType+'://' + self.Proxie,"https": ProxyType+'://' + self.Proxie},
                                                 timeout=Timeout)
                    else:
                        Response = requests.post(Url, data=Data,timeout=Timeout)
            except:
                break
        return Response


    def ChangeProxie(self):
        try:
            self.ProxyCount=self.ProxyCount+1
            self.Proxy= self.Proxies[self.ProxyCount]
            return self.Proxy
        except:
            print("Thread[" + str(self.ThreadID) + "] run out of Proxies.")
            self.Proxy= None
            return self.Proxy


    def DoWork(self):
        if len(self.Accounts)!=0:
            ProxyUsedCount=0
            conn = sqlite3.connect(self.DB)  # 建立数据库连接
            conn.text_factory = str
            cu = conn.cursor()
            for AccountsCount in range(len(self.Accounts) + 1):
                if AccountsCount < len(self.Accounts):
                    if self.pause:
                        print("Thread["+str(self.ThreadID)+"] Paused.")
                        while self.pause: time.sleep(1)
                    Line = re.search(r"(\w|\d_)*-{4}([^-])*", self.Accounts[AccountsCount])
                    if Line!=None:
                        if("ryerson" in self.Url):
                            Response = self.HttpRequest("GET",self.Url,None, self.RequestTimeout,self.ProxyEnable, self.ProxyType)
                            if Response==None:
                                break
                            execution = re.findall(r'name="execution" value="([^"]*)"', Response.text)[0]
                            self.RequestArguments["execution"]=execution

                        ArgumentsValues = re.compile("-{4}").split(Line.group(0))
                        for Key in self.RequestArguments:
                            MatchObject=re.search('\{\{!COL(\d*)\}\}',self.RequestArguments[Key]      )
                            if  MatchObject!=None :
                                ColumnNum=MatchObject.group(1)
                                self.RequestArguments[Key]=ArgumentsValues[int(ColumnNum)-1].rstrip("\n\r")
                        Response = self.HttpRequest("POST",self.Url,self.RequestArguments, self.RequestTimeout,self.ProxyEnable, self.ProxyType)
                        if Response == None:
                            break
                        ProxyUsedCount=ProxyUsedCount+1
                        if (Response.status_code != 401):
                            cookies = self.getCookies(Response.cookies)
                            cu.execute("""INSERT OR IGNORE INTO db (Accounts,Cookies) VALUES (?,?)""",
                                       (self.Accounts[AccountsCount], cookies))
                            conn.commit()  # 提交更改
                            print("Arguments[" + self.Accounts[AccountsCount] + "] Request Success.")
                        #else:
                            #print("Arguments[" + self.Accounts[AccountsCount] + "] Request Failed.")
                    self.progress_update.emit(1)
                    time.sleep(int(self.Interval))
            conn.close()  # 关闭数据库连接
            print("Thread["+str(self.ThreadID)+"] Complicate.")
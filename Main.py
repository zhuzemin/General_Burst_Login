import glob
from MakeWorkThread import *
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QFileDialog, QLineEdit, QGroupBox
from PyQt5 import QtWidgets
from MainWindow import Ui_MainWindow
import json

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class query_window(QtWidgets.QMainWindow):
    Accounts = None
    Proxies = None
    Url = "https://cas.ryerson.ca/login"
    DB = 'ryerson.db'
    thread=None
    AccountsFile="Accounts.txt"
    ProxiesFile="Proxies.txt"
    RequestArguments={}
    ConfigFIle="Profiles.json"
    Encording="gbk"
    Host=None
    config=None
    pool=None

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton_AccountsBrowser.clicked.connect(self.MakeopenFileNameDialog("Accounts"))
        self.ui.pushButton_Proxies_Browser.clicked.connect(self.MakeopenFileNameDialog("Proxies"))
        self.ui.pushButton_Start.clicked.connect(lambda :self.ThreadControl("start"))
        self.ui.pushButton_Pause.clicked.connect(self.thread_pause_resume)
        self.ui.pushButton_Cancel.clicked.connect(lambda :self.ThreadControl("terminate"))
        self.ui.progressBar.setValue(0)
        self.ui.checkBox_UseProxie.stateChanged.connect(self.checkBox_isChecked)
        self.thread = MakeWorkThread(self) # 创建一个线程
        if os.path.exists(self.AccountsFile):
            self.MakelistViewLoad(self.AccountsFile,"Accounts")
        if os.path.exists(self.ProxiesFile):
            self.MakelistViewLoad(self.ProxiesFile,"Proxies")
        self.ui.groupBox_Proxies.setEnabled(False)
        self.ui.actionLoad_Profile.triggered.connect(self.MakeopenFileNameDialog("ProfileLoad"))
        self.ui.lineEdit_Accounts.textChanged.connect(lambda :self.MakelistViewLoad(self.ui.lineEdit_Accounts.text(),"Accounts"))
        self.ui.lineEdit_Proxies.textChanged.connect(lambda :self.MakelistViewLoad(self.ui.lineEdit_Proxies.text(),"Proxies"))
        LatestProfile=self.FindLastModifiedFile(os.path.dirname(os.path.abspath(__file__)),"\*.json")
        if LatestProfile!=None:
            self.loadConfig(LatestProfile)
        self.ui.actionSave_Profile.triggered.connect(lambda:self.saveFileDialog("ProfileSave"))


    def saveFileDialog(self,flag):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","Support Files (*.json);;All Files (*)", options=options)
        if fileName:
            if flag=="ProfileSave":
                self.saveConfig(fileName)


    def saveConfig(self,filePath):
        self.config={}
        self.config["Url"]=self.ui.lineEdit_Url.text()
        self.config["Database"]=self.ui.lineEdit_db.text()
        self.config["Accounts"]=self.ui.lineEdit_Accounts.text()
        self.config["Proxies"]=self.ui.lineEdit_Proxies.text()
        self.config["Timeout"]=self.ui.spinBox_Timeout.value()
        self.config["Interval"]=self.ui.spinBox_Interval.value()
        self.config["MultiThreads"]=self.ui.spinBox_MultiThreads.value()
        self.config["ProxyEnable"]=self.ui.checkBox_UseProxie.isChecked()
        if self.ui.radioButton_ProxyTypeHttp.isChecked():
            self.config["ProxyType"]="http"
        elif self.ui.radioButton_ProxyTypeSocks5.isChecked():
            self.config["ProxyType"] ="socks5"
        self.config["PerProxyRequestLimit"]=self.ui.spinBox_PerProxyRequestLimit.value()
        self.config["Argvs"]={}
        for GroupBox in self.ui.groupBox_Arguments.children():
            if isinstance(GroupBox, QGroupBox):
                for LineEdit in GroupBox.children():
                    if isinstance(LineEdit, QLineEdit):
                        Json_GroupBoxArgv=re.sub("\[|\]","",GroupBox.title())
                        if Json_GroupBoxArgv in LineEdit.objectName():
                            if "Key" in LineEdit.objectName():
                                if LineEdit.text()!="":
                                    self.config["Argvs"][Json_GroupBoxArgv]={}
                                    self.config["Argvs"][Json_GroupBoxArgv]["Key"]=LineEdit.text()
                                else:
                                    break
                            elif "Value" in LineEdit.objectName():
                                self.config["Argvs"][Json_GroupBoxArgv]["Value"]=LineEdit.text()
        with open(filePath, 'w') as outfile:
            json.dump(self.config, outfile)


    def FindLastModifiedFile(self,Directory,FileType):
        list_of_files = glob.glob(Directory+FileType)  # * means all if need specific format then *.csv
        try:
            latest_file = max(list_of_files, key=os.path.getctime)
        except:
            return None
        return latest_file


    def loadConfig(self,filePath):
        with open(filePath, encoding=self.Encording) as f:
            config=json.load(f)
        #MatchObject=re.search("http(s?)://([^/]*)($|/)",self.ui.lineEdit_Url.text)
        MatchObject=re.search("http(s?)://([^/]*)($|/)",self.Url)
        if MatchObject != None:
            self.Host=MatchObject.group(2)
            #if config[self.Host]!=None:
            if config["Url"]!=None:
                self.ui.lineEdit_Url.setText(config["Url"])
                self.AccountsFile=config["Accounts"]
                self.ui.lineEdit_Accounts.setText(config["Accounts"])
                self.ProxiesFile=config["Proxies"]
                self.ui.lineEdit_Proxies.setText(config["Proxies"])
                self.ui.lineEdit_db.setText(config["Database"])
                self.ui.spinBox_Timeout.setValue(config["Timeout"])
                self.ui.spinBox_MultiThreads.setValue(config["MultiThreads"])
                self.ui.spinBox_Interval.setValue(config["Interval"])
                self.ui.checkBox_UseProxie.setChecked(config["ProxyEnable"])
                if config["ProxyType"].lower()=="http":
                    self.ui.radioButton_ProxyTypeHttp.setChecked(True)
                if config["ProxyType"].lower()=="socks5":
                    self.ui.radioButton_ProxyTypeSocks5.setChecked(True)
                self.ui.spinBox_PerProxyRequestLimit.setValue(config["PerProxyRequestLimit"])
                for Json_GroupBoxArgv in config["Argvs"]:
                        Json_LineEditKey,Json_LineEditValue = config["Argvs"][Json_GroupBoxArgv]
                        for GroupBox in self.ui.groupBox_Arguments.children():
                            if isinstance(GroupBox, QGroupBox):
                                for LineEdit in GroupBox.children():
                                    if isinstance(LineEdit, QLineEdit):
                                        if Json_GroupBoxArgv in LineEdit.objectName():
                                            if "Key" in LineEdit.objectName():
                                                LineEdit.setText(config["Argvs"][Json_GroupBoxArgv][Json_LineEditKey])
                                            elif "Value" in LineEdit.objectName():
                                                LineEdit.setText(config["Argvs"][Json_GroupBoxArgv][Json_LineEditValue])



    def radioButton_clicked(self,flag):
        self.thread.ProxyType=flag


    def checkBox_isChecked(self):
        if self.ui.checkBox_UseProxie.isChecked():
            self.ui.groupBox_Proxies.setEnabled(True)
        else:
            self.ui.groupBox_Proxies.setEnabled(False)


    def thread_pause_resume(self):
        if self.ui.pushButton_Pause.text() == "Pause":
            self.thread.pause = True
            self.thread.Pause()
            self.ui.pushButton_Pause.setText("Resume")
        else:
            self.thread.pause = False
            self.thread.Pause()
            self.ui.pushButton_Pause.setText("Pause")


    def ThreadControl(self,Trriger):
        if Trriger=="start":
            self.thread.progress_update.connect(self.setProgressVal)
            self.thread.Url=self.ui.lineEdit_Url.text()
            self.thread.Accounts=self.Accounts
            self.thread.Proxies=self.Proxies
            self.MakeRequestArguments()
            self.thread.RequestArguments=self.RequestArguments
            self.thread.DB=self.DB
            self.thread.ProxyEnable=self.ui.checkBox_UseProxie.isChecked()
            self.thread.RequestTimeout=int(self.ui.spinBox_Timeout.text())
            self.thread.ProxyUsedLimit=int(self.ui.spinBox_PerProxyRequestLimit.text())
            if self.ui.radioButton_ProxyTypeHttp.isChecked():
                self.thread.ProxyType="http"
            elif self.ui.radioButton_ProxyTypeSocks5.isChecked():
                self.thread.ProxyType ="socks5"
            self.thread.MultiThreads=self.ui.spinBox_MultiThreads.value()
            self.thread.Interval=self.ui.spinBox_Interval.value()
            self.thread.start()
        elif Trriger=="terminate":
            self.thread.Terminate()
            self.thread.terminate()
            self.setProgressVal(0)


    def setProgressVal(self, val):
        self.ui.progressBar.setValue(val)
        self.ui.lineEdit_CurrentAccountsLine.setText(str(val))


    def LoadFileByLine(self,fileName,Encoding="gbk"):
        if os.path.exists(fileName):
            with open(fileName, encoding=Encoding) as f:
                array = f.readlines()
            return array


    def MakelistViewLoad(self,fileName,flag):
        def listViewLoad():
            mode=QStandardItemModel()
            array=self.LoadFileByLine(fileName)
            if array!=None:
                for Line in array:
                    Line=QStandardItem(Line)
                    mode.appendRow(Line)
                if flag=="Accounts":
                    self.ui.lineEdit_Accounts.setText(fileName)
                    colums=re.compile("-{4}").split(array[0])
                    header=""
                    for i in range(1,len(colums)+1):
                        if i<len(colums):
                            header=header+"{{!COL"+str(i)+"}}"+"----"
                        else:
                            header=header+"{{!COL"+str(i)+"}}"
                    mode.insertRow(0,QStandardItem(header))
                    self.ui.listView_Accounts.setModel(mode)
                    self.Accounts=array
                    self.ui.progressBar.setMaximum(len(self.Accounts))
                elif flag == "Proxies":
                    self.ui.lineEdit_Proxies.setText(fileName)
                    self.ui.listView_Proxies.setModel(mode)
                    self.Proxies=array
        return listViewLoad()


    def MakeopenFileNameDialog(self,flag):
        def openFileNameDialog():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Support Files (*.txt *.json);;All Files (*);;Python Files (*.py)", options=options)
            if fileName:
                if flag=="Accounts":
                    self.MakelistViewLoad(fileName, flag)
                elif flag=="Proxies":
                    self.MakelistViewLoad(fileName,flag)
                elif flag == "ProfileLoad":
                    self.loadConfig(fileName)
        return openFileNameDialog


    def MakeRequestArguments(self):
        for GroupBox in self.ui.groupBox_Arguments.children():
            if isinstance(GroupBox, QGroupBox):
                key=None
                value=None
                for LineEdit in GroupBox.children():
                    if isinstance(LineEdit, QLineEdit):
                        if "Key" in LineEdit.objectName():
                            key=LineEdit.text()
                        elif "Value" in LineEdit.objectName():
                            value=LineEdit.text()
                        if key!=None and value!=None:
                            if len(key)>0:
                                self.RequestArguments.setdefault(key,value)
                                break




if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QtWidgets.QApplication(sys.argv)
    window = query_window()
    window.show()
    sys.exit(app.exec_())



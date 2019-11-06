import numpy
from WorkThread import *

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtCore import pyqtSignal, QThread


class MakeWorkThread(QThread):
    progress_update = pyqtSignal(int)  # 信号类型：int

    def __init__(self, parent=None):
        super().__init__(parent)
        self.Url = None
        self.Accounts = None
        self.Proxies = None
        self.DB = None
        self.pause = False
        self.ProxyEnable = False
        self.ProxyUsedLimit = None
        self.RequestTimeout = None
        self.RequestArguments = None
        self.ProxyType = None
        self.ProxiesCount = 0
        self.MultiThreads=1
        self.Interval=0
        self.Threads=[]
        self.TotalCount=0

    def run(self):
        self.DoWork()


    def DoWork(self):
        Count=1
        EveryThreadRequireProxys=numpy.array_split(self.Proxies,self.MultiThreads)
        for EveryThreadLoadArray in numpy.array_split(self.Accounts,self.MultiThreads):
            if self.pause:
                #print("Thread["+str(self.ThreadID)+"] Paused.")
                while self.pause: time.sleep(1)
            thread = WorkThread(self)  # 创建一个线程
            thread.Url = self.Url
            thread.Accounts = EveryThreadLoadArray
            numpy.insert(EveryThreadRequireProxys[Count - 1],0,"")
            thread.Proxies = EveryThreadRequireProxys[Count-1]
            thread.progress_update.connect(self.HandleProgress)
            #self.MakeRequestArguments()
            thread.RequestArguments = self.RequestArguments
            thread.DB = self.DB
            thread.ProxyEnable = self.ProxyEnable
            thread.RequestTimeout = int(self.RequestTimeout)
            thread.ProxyUsedLimit = int(self.ProxyUsedLimit)
            thread.ProxyType = self.ProxyType
            thread.ThreadID=Count
            thread.Interval=self.Interval
            thread.start()
            print("Thread["+str(Count)+"] Started.")
            self.Threads.append(thread)
            time.sleep(int(self.Interval))
            Count=Count+1


    def Pause(self):
        for thread in self.Threads:
            thread.pause=self.pause


    def HandleProgress(self,CurrentCount):
        self.TotalCount=self.TotalCount+CurrentCount
        self.progress_update.emit(self.TotalCount)


    def Terminate(self):
        for thread in self.Threads:
            thread.terminate()
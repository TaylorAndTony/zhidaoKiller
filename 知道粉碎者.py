import os
import threading
import time
import datetime
import yaml
import win10toast
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QTableWidgetItem
from PySide2.QtCore import QTimer


def give_me_date(struct=False):
    """ return the current date """
    formatted = time.strftime("%Y-%m-%d", time.localtime())
    if struct:
        y, m, d = [int(i) for i in formatted.split('-')]
        return (y, m, d)
    else:
        return formatted


def give_me_detailed_time():
    return time.strftime("%Y-%m-%d--%H-%M-%S", time.localtime())


def time_2_tuple(timetext):
    """ 时间文本转元祖 """
    y, m, d = [int(i) for i in timetext.split('-')]
    return (y, m, d)


def backup():
    with open('logs.yml', 'r', encoding='utf-8') as f:
        main = yaml.safe_load(f)
    with open(f'./backup/logs-{give_me_detailed_time()}.yml', 'w', encoding='utf-8') as d:
        yaml.dump(main, d)
    print(f'{give_me_date()}一辈分')


def threading_notice():
    def t():
        toast = win10toast.ToastNotifier()
        toast.show_toast(title="知道粉碎者",
                         msg=f"完成观看")

    th = threading.Thread(target=t)
    th.setDaemon(True)
    th.start()


class UI:
    def __init__(self):
        self.app = QApplication([])
        self.window = QUiLoader().load('ui.ui')
        self.window.beginWatching.clicked.connect(self.beginWatching)
        self.window.connADB.clicked.connect(self.connADB)
        self.window.refreshIt.clicked.connect(self.refreshIt)
        self.window.stopNow.clicked.connect(self.stopNow)
        # 列表主字典
        self.dct = {}
        # 计时器
        self.counddown = 30
        # 当前选中
        self.selected = ''
        # 内部逻辑计时器
        self.timer = QTimer(self.window)  # 初始化一个定时器
        self.timer.timeout.connect(self.timingFunc)  # 计时结束调用operate()方法

    def stopNow(self):
        self.timer.stop()

    def appendLine(self, text):
        """ append line into output area """
        self.window.outLine.appendPlainText(text)
        self.window.outLine.ensureCursorVisible()

    def runCmd(self, cmd):
        """ 执行命令，返回结果并填写入图形界面 """
        r = os.popen(cmd)
        t = r.read()
        self.appendLine(t)

    def insertItems(self) -> dict:
        """ insert watching cources into tree view"""
        with open('logs.yml', 'r', encoding='utf-8') as log:
            self.dct = yaml.safe_load(log)
        self.window.listOfCource.setRowCount(len(self.dct))
        self.appendLine(f'读取了 {len(self.dct)} 个数据')
        for i in self.dct:
            # i: {name:..., lastTime:..., continue:...}
            _name = self.dct[i]['name']
            _time = self.dct[i]['lastTime']
            _count = str(self.dct[i]['continue'])
            year, month, day = [int(i) for i in _time.split('-')]
            # 日期相等
            if time_2_tuple(_time) == give_me_date(True):
                _status = '今日已看'
            # 日期不等，计算时间间隔
            else:
                d1 = datetime.date(year, month, day)
                d2 = datetime.date(*give_me_date(True))
                delta = (d2 - d1).days
                _status = f'{delta} 天前'

            self.window.listOfCource.setItem(i - 1, 0, QTableWidgetItem(_name))
            self.window.listOfCource.setItem(i - 1, 1, QTableWidgetItem(_time))
            self.window.listOfCource.setItem(i - 1, 2, QTableWidgetItem(_count))
            self.window.listOfCource.setItem(i - 1, 3, QTableWidgetItem(_status))

    def update_selected(self):
        """ 更新炫中的记录 """
        currentrow = self.window.listOfCource.currentRow()
        now_watching = self.dct[currentrow + 1]['name']
        self.selected = now_watching
        self.appendLine(f'开始观看：{now_watching}，内部编号：{currentrow}')
        self.dct[currentrow + 1]['lastTime'] = give_me_date()
        self.dct[currentrow + 1]['continue'] = self.dct[currentrow + 1]['continue'] + 1
        self.appendLine(f'日期已更新：{give_me_date()}')
        with open('logs.yml', 'w', encoding='utf-8') as log:
            yaml.dump(self.dct, log)

    def timingFunc(self):
        """
        计时器的回调
        """
        self.counddown -= 1
        self.appendLine(f'观看{self.selected}，剩余时间：{self.counddown} 分钟')
        if self.counddown == 0:
            self.counddown = 30
            self.timer.stop()
            self.appendLine('时间结束')
            # 如果被选中并且需要执行命令
            # 同时发出win10通知
            if self.window.control.isChecked():
                # 执行ADB命令完成两次按下返回键
                self.runCmd(f'adb shell input keyevent 4')
                self.runCmd(f'adb shell input keyevent 4')
                # 发出win10通知
                threading_notice()
                print('finished')
                self.timer.stop()

    def beginWatching(self):
        """ Callback button of beginWatching """
        # back up files
        backup()
        # reading time
        self.counddown = int(self.window.howLong.text())
        # which one is selected
        self.update_selected()
        # timer
        # todo: here is the delay
        self.timer.start(1000)

    def connADB(self):
        """ Callback button of connADB """
        self.runCmd('adb start-server')
        self.runCmd('adb devices')

    def refreshIt(self):
        """ Callback button of refreshIt """
        self.insertItems()

    def run(self):
        self.window.show()
        self.app.exec_()


if __name__ == '__main__':
    ui = UI()
    ui.run()

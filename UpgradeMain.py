#!/usr/bin/python
# -*- coding: UTF-8 -*-
import threading
import queue
import time
import socketServer
from PublicLib.Upgrade.UpgradeMakeFrame import upgradeMakeFrame
import PublicLib.Upgrade.UpgradeDealFrame as df

class socketupgrade():
    def __init__(self):
        self.qRecv = queue.Queue()
        self.mf = upgradeMakeFrame()
        self.state = 0
        bitmap = [0] * 1024
        self.uplist = {"ip": "", "port": "", "bmap": bitmap}
        self.ADDRESS = ('192.168.127.16', 8888)  # 绑定地址
        self.upgradeCnt = 0


    def upgradeStartServer(self):
        tser = threading.Thread(target=socketServer.ServerStart, args=(self.ADDRESS,))
        tser.start()
        tmonitor = threading.Thread(target=socketServer.ServerMonitor, args=(self.qRecv,))
        tmonitor.start()


    def upgradeStartRecvThread(self):
        tser = threading.Thread(target=df.upgradeRecvProc, args=(self, ))
        tser.start()


    def upgradehandle(self, nSocket):
        print("[1、启动升级 2、检查漏包 3、检查版本 4、继续升级]")
        str = input("请输入需要执行的流程：")
        n = int(str, 10)
        senddata = ""

        if (n == 1):
            senddata = self.mf.upgradeStart()
            self.upgradeCnt = 0
        elif (n == 2):
            strindex = input("请输入需要查询的包序号：")
            senddata = self.mf.upgradeCheckPack(strindex)
        elif (n == 3):
            senddata = self.mf.upgradeCheckVision()
        else:
            pass

        if senddata:
            socketServer.SocketSend(nSocket, senddata)
            print(senddata)
        return n

    def upgradeProc(self):
        # 启动升级服务器
        self.upgradeStartServer()

        # 启动数据处理线程
        self.upgradeStartRecvThread()

        # 升级应用线程
        while 1:
            time.sleep(5)
            num = socketServer.GetLinkNum()
            print("当前连接数：", num)

            if (num > 0):
                nSocket = 0  # self.uim.socketComboBox.currentIndex()

                # 根据状态进行 1、启动升级 2、检查漏包 3、升级文件 4、检查版本
                if self.state == 0:
                    n = self.upgradehandle(nSocket)
                    if n == 1 or n > 10:
                        self.state = 1
                elif self.state == 2:  # 自动查漏包1
                    senddata = self.mf.upgradeCheckPack("1")
                    socketServer.SocketSend(nSocket, senddata)
                    self.state = 3
                elif self.state == 3:  # 自动查漏包2
                    senddata = self.mf.upgradeCheckPack("2")
                    socketServer.SocketSend(nSocket, senddata)
                    self.state = 4
                elif self.state == 4:  # 自动查版本号
                    senddata = self.mf.upgradeCheckVision()
                    socketServer.SocketSend(nSocket, senddata)
                    self.state = 1
                    self.upgradeCnt += 1
                    if self.upgradeCnt > 5:
                        self.state = 0  # 大于自动尝试次数，进入手动模式
                else:
                    i = df.upgradeGetCurPackNum(self)
                    if i < self.mf.packnum:
                        senddata = self.mf.upgradeSendFile(i)  # 读文件从0开始, 包序号从1开始
                        self.uplist["bmap"][i] = 1
                        print("升级ing, 当前包序号：", i)
                        socketServer.SocketSend(nSocket, senddata)
                        print(senddata)
                    if (i == 10) or (i > 10 and i >= n):
                        self.state = 0 # 手动
                    elif (i >= self.mf.packnum):
                        self.state = 2 # 自动查漏包



if __name__ == '__main__':
    su = socketupgrade()
    su.upgradeProc()

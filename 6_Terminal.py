import sys, os, getpass, socket, time
import multiprocessing
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QPlainTextEdit
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt, pyqtSignal, QProcess, QEvent
# from cmdHandle import CMDHandle
import setting as setting

MAP = {
    'U8':'8',
    'U16':'16',
    'U32':'32',
    'S8':'8',
    'S16':'16',
    'S32':'32',
    'FLOAT':'32',
    'DOUBLE':'32',
}

class FPGAConsoleEdit(QPlainTextEdit):
    commandSignal = pyqtSignal(str)
    commandZPressed = pyqtSignal(str)

    def __init__(self, parent=None, config=None, logger=None, data_update=None):
        super(FPGAConsoleEdit, self).__init__()
        self.parent, self.config, self.logger = parent, config, logger
        self.data_update = data_update  # 数据传输信号

        self.dataUpdateEnable = False  # 是否传出结果
        self.hit = 0  # df数据长度

        # self.fifo_cmd = multiprocessing.Queue(500)  # cmd 管道

        self.installEventFilter(self)
        self.setAcceptDrops(True)
        QApplication.setCursorFlashTime(1000)

        self.process = QProcess()
        # self.process.readyRead.connect(self.readyRead)
        self.process.finished.connect(self.processFin)
        self.process.readyReadStandardError.connect(self.onReadyReadStandardError)
        self.process.readyReadStandardOutput.connect(self.onReadyReadStandardOutput)

        # self.cmdHandle = CMDHandle(parent=self, cmd_fifo=self.fifo_cmd, data_update=self.data_update, logger=self.logger)
        # self.cmdHandle.start()

        self.name = ("% ")
        self.appendPlainText(self.name)
        self.commands = []  # This is a list to track what commands the user has used so we could display them when
        # up arrow key is pressed
        self.tracker = 0
        self.text = None
        self.setFont(QFont("Microsoft YaHei UI", 12))  # 控制台字体
        self.previousCommandLength = 0

    def initConsole(self):
        '''启动FPGA调试工具'''
        try:
            self.logger.info('控制台启动中...')

            # path = self.config.read_key('system tools', 'path', 'D:\\intelFPGA\\18.0\\quartus\\sopc_builder\\bin', str)
            path = os.path.join(setting.basepath, 'quartus\\sopc_builder\\bin')

            # self.handle(f'cd {path}')  # qss读取后再切地址

            self.oldEnv = os.environ['PATH']
            os.environ['PATH'] = path
            self.run('system-console -cli --disable_readline')
        except Exception as e:
            self.logger.exception(e)

    def reStart(self):
        '''重启控制台'''
        try:
            if self.process.state() != 2:
                self.run('system-console -cli --disable_readline')
        except Exception as e:
            self.logger.exception(e)

    def unlinkConsole(self):
        '''关闭控制台'''
        try:
            if self.process.state() == 2:
                self.process.kill()
        except Exception as e:
            self.logger.exception(e)

    def refreshConn(self):
        '''设备连接刷新'''
        refresh_cmd = 'refresh_connections' + '\n'
        self.insertPlainText(refresh_cmd)
        self.process.write(refresh_cmd.encode())

        self.textCursor().movePosition(QTextCursor.End)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.DragEnter):
            event.accept()
            print ('DragEnter')
            return True
        elif (event.type() == QEvent.Drop):
            print ('Drop')
            self.setDropEvent(event)
            return True
        else:
            return False ### super(QPlainTextEdit).eventFilter(event)

    def setDropEvent(self, event):
        if event.mimeData().hasUrls():
            f = str(event.mimeData().urls()[0].toLocalFile())
            self.insertPlainText(f)
            event.accept()
        elif event.mimeData().hasText():
            ft = event.mimeData().text()
            print("text:", ft)
            self.insertPlainText(ft)
            event.accept()
        else:
            event.ignore()

    # def mousePressEvent(self, e):

    def keyPressEvent(self, e):
        cursor = self.textCursor()

        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_A:  # Ctrl + A
            return

        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_Z:  # Ctrl + Z
            self.commandZPressed.emit("True")
            return

        # if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_C:  # Ctrl + C
        #     self.process.kill()
        #     # self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
        #     #                         + ":" + str(os.getcwd()) + "$ ")
        #     self.name = ("% ")
        #     self.appendPlainText("process cancelled")
        #     self.appendPlainText(self.name)
        #     self.textCursor().movePosition(QTextCursor.End)
        #     return

        if e.key() == Qt.Key_Return:  ### 16777220:  # This is the ENTER key
            text = self.textCursor().block().text()

            if text == self.name + text.replace(self.name, "") and text.replace(self.name, "") != "":  # This is to prevent adding in commands that were not meant to be added in
                self.commands.append(text.replace(self.name, ""))  # 添加到历史命令列表（未做除重）
                # print(self.commands)
            self.handle(text)
            self.commandSignal.emit(text)
            # self.appendPlainText(self.name)

            return

        if e.key() == Qt.Key_Up:  # 方向键 ↑ 按下事件, 历史cmd
            try:
                if self.tracker != 0:
                    cursor.select(QTextCursor.BlockUnderCursor)
                    cursor.removeSelectedText()
                    self.appendPlainText(self.name)

                self.insertPlainText(self.commands[self.tracker])
                self.tracker -= 1

            except IndexError:
                self.tracker = 0

            return

        if e.key() == Qt.Key_Down:  # 方向键 ↓ 按下事件, 历史cmd
            try:
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                self.appendPlainText(self.name)

                self.insertPlainText(self.commands[self.tracker])
                self.tracker += 1

            except IndexError:
                self.tracker = 0

        if e.key() == Qt.Key_Backspace:   ### 16777219:  # 退格键事件
            if cursor.positionInBlock() <= len(self.name):
                return

            else:
                cursor.deleteChar()

        self.textCursor().movePosition(QTextCursor.End)

        super().keyPressEvent(e)
        cursor = self.textCursor()
        e.accept()

    # def ispressed(self):
    #     return self.pressed

    # def readyRead(self):
    #     '''有可读数据槽函数'''
    #     print('有可读数据')

    def processFin(self):
        '''进程结束'''
        self.appendPlainText('进程结束\n')

    def onReadyReadStandardError(self):
        '''错误信息输出槽函数'''
        self.error = self.process.readAllStandardError().data().decode()
        self.logger.error(self.error)
        self.appendPlainText(self.error.strip('\n'))
        self.textCursor().movePosition(QTextCursor.End)

    def onReadyReadStandardOutput(self):
        '''标准信息输出槽函数'''
        self.result = self.process.readAllStandardOutput().data().decode()
        self.logger.info(self.result)
        self.appendPlainText(self.result.strip('\n'))
        self.textCursor().movePosition(QTextCursor.End)
        if self.result != "% " and 'master' not in self.result and self.dataUpdateEnable:
            if "%" not in self.result.split('\n% ')[0]:
                self.hit -= 1
                print('result:\n', self.result.split('\n% ')[0])
                # self.fifo_cmd.put(self.result.split('\n% ')[0].encode())
                self.data_update.emit(self.index, 'data', self.result.split('\n% ')[0])
                if self.hit <= 0:
                    self.dataUpdateEnable = False
            # self.resultData = self.result
            # self.data_update.emit(self.index, 'data', self.resultData)
            # self.fifo_cmd.put(self.result.encode())

    def open_service(self):
        '''set jd_path and open_service master'''

        # if self.process.waitForReadyRead(1000):
        setpath_cmd = 'set jd_path [lindex [get_service_paths master] 0]' + '\n'  # 不含\n 无法识别执行
        self.insertPlainText(setpath_cmd)
        self.process.write(setpath_cmd.encode())
        self.textCursor().movePosition(QTextCursor.End)
        if self.process.waitForReadyRead(500):

            open_cmd = 'open_service master $jd_path' + '\n'  # 不含\n 无法识别执行
            self.insertPlainText(open_cmd)
            self.process.write(open_cmd.encode())
            self.textCursor().movePosition(QTextCursor.End)


    def read_multiCmdHandle(self, df):
        '''对df中的数据进行读取'''
        try:
            self.cmdHandle.setupData(df)  # 线程加入df数据
            if self.process.state() == 2:

                self.open_service()

                self.hit = df.shape[0]

                self.dataUpdateEnable = True
                # self.cmdHandle.is_live = True
                self.index = 0
                for _, row in df.iterrows():
                    _addr = row['Addr']
                    _type = row['type']
                    _size = row['size']

                    _type = MAP[_type]

                    if self.process.waitForReadyRead(500):

                        read_cmd = f'master_read_{_type} $jd_path {_addr} {_size}' + '\n'  # 不含\n 无法识别执行
                        self.insertPlainText(read_cmd)
                        self.process.write(read_cmd.encode())
                        self.index += 1

            else:
                self.reStart()
                time.sleep(5)
                self.read_multiCmdHandle(df)
        except Exception as e:
            self.logger.exception(e)

    def write_multiCmdHandle(self, df):
        '''对df中的数据进行写入'''
        try:
            if self.process.state() == 2:

                self.open_service()

                # self.hit = df.shape[0]
                for _, row in df.iterrows():
                    _addr = row['Addr']
                    _type = row['type']
                    _size = row['size']
                    _data = row['data']

                    _type = MAP[_type]

                    write_cmd = f'master_write_{_type} $jd_path {_addr} {_data}' + '\n'  # 不含\n 无法识别执行
                    self.insertPlainText(write_cmd)
                    self.process.write(write_cmd.encode())
                    time.sleep(1)
            else:
                self.reStart()
                time.sleep(5)
                self.write_multiCmdHandle(df)
        except Exception as e:
            self.logger.exception(e)

    def write_wave(self, _addr, _data, _type='FLOAT'):
        '''波形写入'''
        try:
            if self.process.state() == 2:

                self.open_service()

                _type = MAP[_type]

                write_cmd = f'master_write_{_type} $jd_path {_addr} {_data}' + '\n'  # 不含\n 无法识别执行
                self.insertPlainText(write_cmd)
                self.process.write(write_cmd.encode())
                time.sleep(1)
            else:
                self.reStart()
                time.sleep(5)
                self.write_wave(_addr, _data, 'FLOAT')
        except Exception as e:
            self.logger.exception(e)

    def run(self, command):
        """Executes a system command."""
        if self.process.state() != 2:
            self.process.start(command)  # 异步调用
            self.textCursor().movePosition(QTextCursor.End)

    def handle(self, command):
        """Split a command into list so command echo hi would appear as ['echo', 'hi']"""
        real_command = command.replace(self.name, "")

        if command == "True":
            if self.process.state() == 2:
                self.process.kill()
                self.appendPlainText("Program execution killed, press enter")

        if real_command.startswith("python"):
            pass

        if real_command != "":
            command_list = real_command.split()  # 指令转为指令列表（格式化）
        else:
            command_list = None

        """指令格式化后实际执行"""
        if real_command == "clear":  # 清空console
            self.clear()

        elif command_list is not None and command_list[0] == "echo":
            self.appendPlainText(" ".join(command_list[1:]))

        elif real_command == 'restart': # 重启
            self.run('system-console -cli --disable_readline')

        elif real_command == "exit":  # 退出
            quit()

        elif command_list is not None and command_list[0] == "cd" and len(command_list) > 1:
            try:
                os.chdir(" ".join(command_list[1:]))
                # self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                #                         + ":" + str(os.getcwd()) + "$ ")
                self.name = ("% ")
                self.textCursor().movePosition(QTextCursor.End)

            except FileNotFoundError as E:
                self.appendPlainText(str(E))

        elif command_list is not None and len(command_list) == 1 and command_list[0] == "cd":
            os.chdir(str(Path.home()))
            print(os.chdir(str(Path.home())))
            # self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
            #                         + ":" + str(os.getcwd()) + "$ ")
            self.name = ("% ")
            self.textCursor().movePosition(QTextCursor.End)

        elif self.process.state() == 2:  # 进程Running状态下
            real_command = real_command + '\n'  # 不含\n 无法识别执行
            self.process.write(real_command.encode())

        elif command == self.name + real_command:
                self.run(real_command)
        else:
            pass

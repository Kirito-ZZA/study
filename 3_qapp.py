if __name__ == '__main__':

    import os
    import sys
    import signal
    import cgitb
    from PyQt5.QtWidgets import QSplashScreen, QApplication
    from PyQt5.QtCore import Qt, QCoreApplication, QTranslator, QT_VERSION_STR
    from PyQt5.QtGui import QPixmap

    # 异常处理设置
    # cgitb.enable(logdir=os.path.join(pwd, "log"), format='html')

    # Allow termination with CTRL + C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    QtVersion = QT_VERSION_STR
    qtVersionCompare = tuple(map(int, QtVersion.split(".")))
    if qtVersionCompare > (6, 0):
        # Qt6 seems to support hidpi without needing to do anything so continue
        pass
    elif qtVersionCompare > (5, 14):
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    else:  # qt 5.12 and 5.13
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    pwd = os.path.dirname(__file__)

    # 按需显示欢迎弹窗
    welcome = QSplashScreen(QPixmap(
        os.path.join(pwd, 'resource/pic/welcome.png')))
    welcome.show()

    # 加载其他配置等
    # ...

    app.processEvents()  # 防进程卡死

    # 加载语言国际化配置
    trans = QTranslator()
    trans.load(os.path.join(pwd, 'resource/translator/Zh_CN.qm'))
    app.installTranslator(trans)


    viewer = MainWindow()

    qss_path = ""

    with open(qss_path, 'r') as f:
        viewer.setStyleSheet(f.read())
        f.close()

    
    welcome.finish(viewer)
    viewer.show()

    sys.exit(app.exec_())

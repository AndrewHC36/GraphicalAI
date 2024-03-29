from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Slot

from homepage import Homepage
from file_handler import ReferencedFileHandler


class MainWindow(QMainWindow):
    def __init__(self, title):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(0, 0, 1920, 1080)
        self.showMaximized()

        wm_file = QMenu("File")
        wm_file.addAction("test a")
        wm_file.addSeparator()
        wm_file.addAction("test b")

        wm_edit = QMenu("Edit")
        wm_exec = QMenu("Run")

        wm_menubar = QMenuBar()
        wm_menubar.addMenu(wm_file)
        wm_menubar.addMenu(wm_edit)
        wm_menubar.addMenu(wm_exec)

        ws_statbar = QStatusBar()
        ws_statbar.addWidget(QLabel("v1.17.0"))

        lfhdnl = ReferencedFileHandler()
        wx_homepage = Homepage(lfhdnl)
        wx_homepage.sg_proj_submit.connect(self.change_page)

        self.setMenuBar(wm_menubar)
        self.setStatusBar(ws_statbar)
        self.setCentralWidget(wx_homepage)

    @Slot(object)
    def change_page(self, page):
        print("change page", page)
        if issubclass(page.__class__, QWidget):
            self.setCentralWidget(page)
        else:
            print(page, "is not a subclass of", QWidget)

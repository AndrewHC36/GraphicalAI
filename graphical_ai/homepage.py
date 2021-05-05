from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, Slot, QMargins
from PySide6.QtGui import QPalette, QColor, QFont

from project import Project
from file_handler import ProjectFileHandler, ReferencedFileHandler
from errors import *


class Homepage(QWidget):
    sg_proj_submit = Signal(object)  # object: the next page (through python object)

    def __init__(self, lfhndl: ReferencedFileHandler, parent=None):
        super().__init__(parent=parent)

        self.lfhndl = lfhndl

        wl_welc = QLabel("Welcome to GraphicalAI!")
        font: QFont = wl_welc.font()
        font.setPointSize(14)
        wl_welc.setFont(font)

        wx_np = NewProject()
        wx_np.sg_np_submitted.connect(self.sl_np_submit)

        lyt_lmid = QVBoxLayout()
        lyt_lmid.addWidget(wl_welc, 1)
        lyt_lmid.addWidget(wx_np, 9)

        wx_lp = LoadProject(self.lfhndl)
        wx_lp.sg_lp_submitted.connect(self.sl_np_submit)
        wx_lep = LoadExecProject(self.lfhndl)

        lyt_main = QHBoxLayout()
        lyt_main.addWidget(wx_lp, 40)
        lyt_main.addLayout(lyt_lmid, 20)
        lyt_main.addWidget(wx_lep, 40)

        self.setLayout(lyt_main)

    @Slot(object)  # object: project file handler
    def sl_np_submit(self, fhndl):  # slot - new project submitted
        wx_project = Project(fhndl, self.lfhndl)
        self.sg_proj_submit.emit(wx_project)


class ReferenceListItem(QWidget):
    def __init__(self, name: str, root_file: str, exists: bool, parent=None):
        super().__init__(parent=parent)

        self.name = name
        self.root_file = root_file
        self.exists = exists

        lyt_main = QVBoxLayout()
        lyt_main.setContentsMargins(1, 1, 1, 1)

        wl_name = QLabel(self.name)
        if not self.exists:
            pal: QPalette = wl_name.palette()
            pal.setColor(QPalette.Text, Qt.red)
            wl_name.setPalette(pal)
        font: QFont = wl_name.font()
        font.setPointSize(12)
        wl_name.setFont(font)

        wl_path = QLabel(self.root_file)
        pal: QPalette = wl_path.palette()
        pal.setColor(QPalette.Text, Qt.gray)
        wl_path.setPalette(pal)
        font: QFont = wl_path.font()
        font.setPointSize(8)
        wl_path.setFont(font)

        lyt_main.addWidget(wl_name)
        lyt_main.addWidget(wl_path)

        self.setLayout(lyt_main)


class LoadProject(QWidget):
    sg_lp_submitted = Signal(object)  # object: the file handler created

    def __init__(self, lfhndl: ReferencedFileHandler, parent=None):
        super().__init__(parent=parent)
        pal: QPalette = self.palette()
        pal.setColor(QPalette.Window, QColor(240, 240, 240))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

        self.wlw_proj = QListWidget(parent=self)
        self.wlw_proj.itemDoubleClicked.connect(self.sl_load_proj)

        for (name, root_file, exists) in lfhndl.loaded_projects():
            itm_a = QListWidgetItem()
            ref_a = ReferenceListItem(name, root_file, exists)
            itm_a.setSizeHint(ref_a.sizeHint())

            self.wlw_proj.addItem(itm_a)
            self.wlw_proj.setItemWidget(itm_a, ref_a)

        ql_main = QLabel("Load Project")
        font: QFont = ql_main.font()
        font.setPointSize(12)
        ql_main.setFont(font)

        qb_open = QPushButton("Open Projects")
        qb_open.clicked.connect(self.sl_open_proj)
        font: QFont = qb_open.font()
        font.setPointSize(12)
        qb_open.setFont(font)

        lyt_main = QVBoxLayout()
        lyt_main.addWidget(ql_main)
        lyt_main.addWidget(self.wlw_proj)
        lyt_main.addWidget(qb_open)

        self.setLayout(lyt_main)

    @Slot(object)
    def sl_load_proj(self, ref_obj: QListWidgetItem):
        w: ReferenceListItem = self.wlw_proj.itemWidget(ref_obj)
        try:
            self.sg_lp_submitted.emit(ProjectFileHandler.load_project(w.root_file))
        except ProjectFileAppError as e:
            if e.code == ProjectFileAppError.PROJ_FILE_DOESNT_EXIST:
                print("error: attempted to load project files that does not exist")
            else:
                raise e

    @Slot(bool)
    def sl_open_proj(self, _checked):
        (file_path, _filter) = QFileDialog.getOpenFileName(parent=None, caption="Open Project File",
                                                           filter="Project Files (project.yaml)")
        try:
            self.sg_lp_submitted.emit(ProjectFileHandler.load_project(file_path))
        except ProjectFileAppError as e:
            if e.code == ProjectFileAppError.PROJ_FILE_DOESNT_EXIST:
                print("error: attempted to load project files that does not exist")
            else:
                raise e


class NewProject(QWidget):
    sg_np_submitted = Signal(object)  # object: the file handler created

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        pal: QPalette = self.palette()
        pal.setColor(QPalette.Window, QColor(240, 240, 240))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

        # wb_next = QPushButton("Create a New Project!")
        # wb_next.clicked.connect(self.sl_np_submit)

        self.qle_name = QLineEdit("")
        self.qb_path = QPushButton("<Empty>")
        self.qb_path.clicked.connect(lambda _checked: self.sl_open_file_dir())

        qfl_creation = QFormLayout()
        qfl_creation.addRow("Project Name:", self.qle_name)
        qfl_creation.addRow("Project Path:", self.qb_path)

        # qb_loc_name = QPushButton("New Project")
        # qb_loc_name.clicked.connect(self.sl_create_proj)
        # font: QFont = qb_loc_name.font()
        # font.setPointSize(12)
        # qb_loc_name.setFont(font)

        qb_create = QPushButton("Create Project")
        qb_create.clicked.connect(lambda _checked: self.sl_create_proj())
        font: QFont = qb_create.font()
        font.setPointSize(12)
        qb_create.setFont(font)

        lyt_main = QVBoxLayout()
        # lyt_main.addWidget(qb_loc_name)
        # lyt_main.addWidget(QLabel("Project creation settings"))
        lyt_main.addLayout(qfl_creation)
        lyt_main.addWidget(qb_create)

        self.setLayout(lyt_main)

    @Slot()
    def sl_create_proj(self):
        self.sg_np_submitted.emit(
            ProjectFileHandler.create_project(self.qb_path.text(), self.qle_name.text())
        )

    @Slot()
    def sl_open_file_dir(self):
        proj_path = QFileDialog.getExistingDirectory(parent=None, caption="New Project Location")
        if proj_path != "":
            self.qb_path.setText(proj_path)



class LoadExecProject(QWidget):
    def __init__(self, lfhndl: ReferencedFileHandler, parent=None):
        super().__init__(parent=parent)
        pal: QPalette = self.palette()
        pal.setColor(QPalette.Window, QColor(240, 240, 240))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

        wlw_exec_proj = QListWidget(parent=self)
        font: QFont = wlw_exec_proj.font()
        font.setPointSize(14)
        wlw_exec_proj.setFont(font)

        wlw_exec_proj.addItem("exec project name a")
        wlw_exec_proj.addItem("exec project name b")
        wlw_exec_proj.addItem("exec project name c")

        ql_main = QLabel("Load Executable Project")
        font: QFont = ql_main.font()
        font.setPointSize(12)
        ql_main.setFont(font)

        qb_open = QPushButton("Open Executable Projects")
        font: QFont = qb_open.font()
        font.setPointSize(12)
        qb_open.setFont(font)

        lyt_main = QVBoxLayout()
        lyt_main.addWidget(ql_main)
        lyt_main.addWidget(wlw_exec_proj)
        lyt_main.addWidget(qb_open)

        self.setLayout(lyt_main)

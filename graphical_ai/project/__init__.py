from __base__ import *  # ~~~ automatically generated by __autoinject__.py ~~~
"""
Widgets that requires context of project info/data/meta to design the whole project workspace
"""

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, Slot, QMargins
from PySide6.QtGui import QPalette, QColor

from typing import List

from project.model import ModelPage, Model
from project.training import TrainingPage
from project.deployment import DeploymentPage
from file_handler import ProjectFileHandler, ReferencedFileHandler


class Project(QWidget):
    def __init__(self, fhndl: ProjectFileHandler, lfhndl: ReferencedFileHandler, parent=None):
        super().__init__(parent)

        self.fhndl = fhndl
        self.lfhndl = lfhndl
        self.models: List[Model] = []

        self.wx_model_page = ModelPage(self.fhndl, self.models, parent=self)
        self.wx_training_page = TrainingPage(self.fhndl, self.models, parent=self)
        self.wx_deployment_page = DeploymentPage(self.models, parent=self)
        self.wx_model_page.model_tabs.sg_model_list_refresh.connect(self.wx_training_page.sl_model_list_refresh)
        self.wx_model_page.model_tabs.sg_model_list_refresh.connect(self.wx_deployment_page.sl_model_list_refresh)

        self.pages = QStackedLayout()
        self.pages.addWidget(self.wx_model_page)
        self.pages.addWidget(self.wx_training_page)
        self.pages.addWidget(self.wx_deployment_page)

        self.wx_proj_tab = ProjectTabs(self.fhndl)
        self.wx_proj_tab.sg_prj_page_selc.connect(self.pages.setCurrentIndex)
        self.wx_proj_tab.sg_prj_save.connect(lambda: self.fhndl.save_project())

        self.lyt_main = QVBoxLayout()
        self.lyt_main.setMenuBar(self.wx_proj_tab)
        self.lyt_main.addLayout(self.pages)

        self.setLayout(self.lyt_main)

        margin = self.lyt_main.contentsMargins()
        margin.setTop(0)
        margin.setBottom(0)
        margin.setLeft(0)
        margin.setRight(0)
        self.lyt_main.setContentsMargins(margin)

        self.lyt_main.setSpacing(1)

        # to refresh other pages for models loaded from disk
        self.wx_model_page.model_tabs.sg_model_list_refresh.emit()


    def __del__(self):  # adds auto-save before the project object gets deleted
        # TODO: save project must be before you add project for new projects, because it root_file attr will be None
        self.fhndl.save_project()
        dprint("project (in future) saved")
        if not self.lfhndl.ref_proj_existed(self.fhndl.path):
            self.lfhndl.add_project(self.fhndl.name, self.fhndl.root_file)
        self.lfhndl.save()
        dprint("project auto-referenced before exit")
        dprint("object deleted")


class ProjectTabs(QWidget):
    sg_prj_page_selc = Signal(int)  # int: page number
    sg_prj_save = Signal()

    def __init__(self, fhndl: ProjectFileHandler, parent=None):
        super().__init__(parent=parent)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(247, 247, 247))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

        wcb_page_selc = QComboBox()
        wcb_page_selc.currentTextChanged.connect(self._sl_page_selc_change)
        wcb_page_selc.addItem("Modeling")
        wcb_page_selc.addItem("Training")
        wcb_page_selc.addItem("Deployment")

        wb_save_proj = QPushButton("Save Project")
        wb_save_proj.clicked.connect(self._sl_proj_save_click)

        lyt_main = QHBoxLayout()
        lyt_main.addWidget(QLabel(fhndl.name), 2)
        lyt_main.addWidget(wcb_page_selc, 4)
        lyt_main.addWidget(wb_save_proj, 4)

        self.setLayout(lyt_main)

        margin = lyt_main.contentsMargins()
        margin.setTop(0)
        margin.setBottom(0)
        lyt_main.setContentsMargins(margin)

    @Slot(str)
    def _sl_page_selc_change(self, text):
        try:
            page_no = {"Modeling": 0, "Training": 1, "Deployment": 2}[text]
        except KeyError:
            dprint(f"error: <{text}> page not implemented")
            page_no = 0

        self.sg_prj_page_selc.emit(page_no)

    @Slot(bool)
    def _sl_proj_save_click(self, _checked):
        self.sg_prj_save.emit()

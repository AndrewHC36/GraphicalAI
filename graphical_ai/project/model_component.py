from __base__ import *  # ~~~ automatically generated by __autoinject__.py ~~~

from PySide6.QtGui import *
from PySide6.QtCore import Signal, Slot

from model_view.components import *
from node_graph.nodes import export, NodeExec


class StaticView(QGraphicsView):
    def __init__(self, qscene: QGraphicsScene, view_size: int, parent=None):
        super().__init__(qscene, parent=parent)

        self.shift = False  # if True, it will scroll left and right instead of top and down

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSceneRect(QRectF(-view_size, -view_size, view_size*2, view_size*2))
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setForegroundBrush(QBrush(QColor(100, 100, 100, 50), Qt.BrushStyle.Dense1Pattern))
        self.show()

        # TODO: (literally gave up on this) how to center the origin to the center; currently the left-most model
        #   wont center through the self.centerOn()
        self.centerOn(self.scene().items()[-1])

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # super().keyPressEvent(event)
        if event.key() == Qt.Key_Shift:
            self.shift = True

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        # super().keyReleaseEvent(event)
        if event.key() == Qt.Key_Shift:
            self.shift = False

    # disabling mouse interaction

    def mousePressEvent(self, event:QMouseEvent) -> None:
        pass

    def mouseReleaseEvent(self, event:QMouseEvent) -> None:
        pass

    def mouseDoubleClickEvent(self, event:QMouseEvent) -> None:
        pass


class ActiveView(QGraphicsView):
    def __init__(self, qscene: QGraphicsScene, view_size: int, parent=None):
        super().__init__(qscene, parent=parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSceneRect(QRectF(-view_size, -view_size, view_size*2, view_size*2))
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.show()

        self.centerOn(self.scene().items()[-1])


class Model(QGraphicsScene):
    sg_temp_rename = Signal(str)

    def __init__(self, name: str, parent=None):
        super().__init__(parent=parent)

        self.name = name
        self.view_size = 10000  # as large as possible
        self.exec_node_dt = []  # list of exec node class
        self.has_model_id = False  # whether the Model has a model ID after saving for the first time from file handler
        self.saved = False  # whether the Model has been saved after the creation or update of the model

        self.attr_selcs = []  # a list of object reference to the model in the graphics view

        center_txt = QGraphicsTextItem(self.name)
        self.addItem(center_txt)

    def get_active_view(self, parent=None) -> QGraphicsView:
        """
        Creates and returns a graphic view of this scene that is active and interactable
        """

        return ActiveView(self, self.view_size, parent=parent)

    def get_static_view(self, parent=None):
        """
        Creates and returns a graphic view of this scene that is disabled and immutable
        """

        return StaticView(self, self.view_size, parent=parent)

    @classmethod
    def name_check(cls, name: str) -> bool:
        return str.isalnum(name)

    @Slot()
    def sl_add_node(self, cat: str, nd_name: str):
        self.saved = False
        self.sg_temp_rename.emit("*" + self.name)

        wx_node_cls: NodeExec = export[cat][nd_name]()  # class reference
        self.exec_node_dt.append(wx_node_cls)
        wx_node = wx_node_cls.interface(self, (0, 0))
        self.addItem(wx_node)
        wx_node.add_const_wx(self)

        attr_selcs = wx_node_cls.field_data["constant"]
        for attr_selc in list(attr_selcs.values()):
            if isinstance(attr_selc, AttributeSelector):
                self.attr_selcs.append(attr_selc)

    @Slot()
    def sl_clear_model(self):
        self.saved = False
        self.sg_temp_rename.emit("*" + self.name)

        self.clear()
        self.attr_selcs.clear()
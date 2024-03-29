from __base__ import *  # ~~~ automatically generated by __autoinject__.py ~~~

from typing import Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, Slot, QRectF, QPointF
from PySide6.QtGui import *

from model_view.connection import TempConnection, Connection
from model_view.components import InteractiveComponent, ComponentDescrp
from node_state import NodeState


class CT:
    """
    connector type
    --------------
    splits into three segments:
    1. Its Function => {INPUT, OUTPUT}
    2. Its Connectivity => {SINGLE, MULTIPLE}
    3. Its Data Type => {ANY, SCALAR, MATRIX, TENSOR, INT, STRING, BOOL, ...}
    0. Special Type => {NULL} to signify its useless and the connector is a placeholder
    """

    NULL        = 0b0000
    INPUT       = 0b0001
    OUTPUT      = 0b0010
    SINGLE      = 0b0100
    MULTIPLE    = 0b1000
    D_SCALAR    = 0b000000000001_0000
    D_MATRIX    = 0b000000000010_0000
    D_TENSOR    = 0b000000000100_0000
    T_ANY       = 0b000000011000_0000
    T_INT       = 0b000000001000_0000
    T_FLOAT     = 0b000000010000_0000

    REQR_CONNCT = None  # todo: warns the execution or something else that this connector requires a connection


class InputField:
    def __init__(self, name, dtyp):
        self.typ = CT.INPUT | dtyp
        self.name = name


class OutputField:
    def __init__(self, name, dtyp):
        self.typ = CT.OUTPUT | dtyp
        self.name = name


class ConstantField:
    def __init__(self, name: str, cc: ComponentDescrp):
        self.cc: ComponentDescrp = cc
        self.ic: Optional[InteractiveComponent] = None
        self.name = name

    def set_size(self, size: tuple):
        self.ic = InteractiveComponent(self.cc, size)


class FasterNode(QGraphicsItemGroup):
    def __init__(self, scene: QGraphicsScene, ndtg: str, name: str, state: NodeState, has_weights: bool, fld_dt: dict, pos=None):
        super().__init__(parent=None)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

        # a dict of three keys (input, output, constant) storing the field data of the node
        self.fld_dt = fld_dt

        self.ndtg = ndtg
        self.title = name
        self.has_weights = has_weights
        self.node_state = state
        self.fd_input = [InputField(name, ct) for (name, ct) in zip(self.fld_dt["input"].keys(), self.fld_dt["input"].values())]
        self.fd_output = [OutputField(name, ct) for (name, ct) in zip(self.fld_dt["output"].keys(), self.fld_dt["output"].values())]
        self.fd_constant = [ConstantField(name, cc) for (name, cc) in zip(self.fld_dt["constant"].keys(), self.fld_dt["constant"].values())]
        self.fd_wx_consts: list = []  # ordered
        self.connectors = []  # a list of connector to update its position
        self.prev_pos: QPointF = self.pos()

        self.size = [0, 0, 165, 100]

        gt_title = QGraphicsTextItem(self.title, parent=self)
        font: QFont = gt_title.font()
        font.setPointSize(10)
        font.setFamily("courier")
        gt_title.setFont(font)
        gt_title_rect = gt_title.boundingRect()
        gt_title.setPos(QPointF(self.size[0] + self.size[2] / 2 - gt_title_rect.width() / 2, self.size[1]))

        y_body = 16
        y_pad = 2
        yc_body = 19
        yc_pad = 2
        x_pad = 1
        z_val_body = 15
        conn_extrusion = 7

        self.size[3] = gt_title_rect.height()+max(len(self.fd_input),len(self.fd_output))*\
                       (y_pad+y_body)+yc_pad+(yc_pad+yc_body)*len(self.fd_constant)+6

        i: InputField
        for (ind, i) in enumerate(self.fd_input):
            gt_inputs = QGraphicsTextItem(i.name, parent=self)
            gt_inp_rect = gt_inputs.boundingRect()
            gt_inputs.setPos(QPointF(
                self.size[0]+x_pad,
                self.size[1]+gt_title_rect.height()+y_pad+(y_pad+y_body)*ind
            ))

            gt_inputs.setZValue(z_val_body)
            gt_inputs.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
            self.addToGroup(gt_inputs)

            gx_inp_conn = Connector(i.typ, pos=(
                self.size[0]+x_pad-conn_extrusion,
                self.size[1]+gt_title_rect.height()+y_pad+(y_pad+y_body)*ind+gt_inp_rect.height()/2-Connector.SIZE/2
            ))
            self.connectors.append(gx_inp_conn)
            scene.addItem(gx_inp_conn)

        o: OutputField
        for (ind, o) in enumerate(self.fd_output):
            gt_outputs = QGraphicsTextItem(o.name, parent=self)
            gt_out_rect = gt_outputs.boundingRect()
            gt_outputs.setPos(QPointF(
                self.size[0] + self.size[2] - gt_out_rect.width() - x_pad,
                self.size[1] + gt_title_rect.height() + y_pad + (y_pad + y_body) * ind
            ))

            gt_outputs.setZValue(z_val_body)
            gt_outputs.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
            self.addToGroup(gt_outputs)

            gx_out_conn = Connector(o.typ, pos=(
                self.size[0]+self.size[2]-gt_out_rect.width()-x_pad+gt_out_rect.width()+conn_extrusion-Connector.SIZE,
                self.size[1]+gt_title_rect.height()+y_pad+(y_pad+y_body)*ind+gt_out_rect.height()/2-Connector.SIZE/2
            ))
            self.connectors.append(gx_out_conn)
            scene.addItem(gx_out_conn)

        y_max_const = max(len(self.fd_input), len(self.fd_output))*(y_pad+y_body)+yc_pad

        self.fd_constant.reverse()
        c: ConstantField
        for (ind, c) in enumerate(self.fd_constant):
            ind = len(self.fd_constant)-ind-1

            gt_consts = QGraphicsTextItem(c.name, parent=self)
            # gt_const_rect = gt_consts.boundingRect()
            gt_consts.setPos(QPointF(
                self.size[0]+x_pad,
                self.size[1]+gt_title_rect.height()+y_max_const+(yc_pad+yc_body)*ind
            ))

            c.set_size((self.size[2]/2-x_pad*2, yc_body))
            gx_ic = c.ic
            gx_ic.setPos(QPointF(
                self.size[0]+self.size[2]/2,
                self.size[1]+gt_title_rect.height()+y_max_const+(yc_pad+yc_body)*ind+yc_pad
            ))

            gt_consts.setZValue(z_val_body)
            gt_consts.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

            self.addToGroup(gt_consts)
            self.fd_wx_consts.append(gx_ic)

        gr_base = QGraphicsRectItem(self.size[0], self.size[1]+gt_title_rect.height(), self.size[2],
                                    self.size[3]-gt_title_rect.height(), parent=self)
        if not self.has_weights:
            gr_base.setBrush(QBrush(QColor("#CCDDFF")))
        else:  # to have nodes with actual trainable weights with different color (cause there special smh)
            gr_base.setBrush(QBrush(QColor("#DDCCFF")))
        gr_base.setPen(QPen(QColor("transparent")))

        gr_title_base = QGraphicsRectItem(self.size[0], self.size[1], self.size[2], gt_title_rect.height(), parent=self)
        # if not self.has_weights:
        gr_title_base.setBrush(QBrush(QColor("#CCF0FF")))
        # else:
        #     gr_title_base.setBrush(QBrush(QColor("#F0CCFF")))
        gr_title_base.setPen(QPen(QColor("transparent")))

        gr_base.setZValue(10)
        gr_title_base.setZValue(11)
        gt_title.setZValue(12)

        gr_base.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        gr_title_base.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        gt_title.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        self.addToGroup(gr_base)
        self.addToGroup(gr_title_base)
        self.addToGroup(gt_title)

    def add_const_wx(self, scene):
        ic: InteractiveComponent
        for ic in self.fd_wx_consts:
            ic.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
            scene.addItem(ic)

    def update_connc(self):
        delta = QPointF(self.prev_pos.x()-self.x(), self.prev_pos.y()-self.y())

        for c in self.connectors:
            c.setPos(QPointF(c.x()-delta.x(), c.y()-delta.y()))
            pconnc: Connection
            for pconnc in c.prim_connct:
                pconnc.a = QPointF(c.x()+c.cpos[0]+Connector.SIZE/2, c.y()+c.cpos[1]+Connector.SIZE/2)
            sconnc: Connection
            for sconnc in c.scnd_connct:
                sconnc.b = QPointF(c.x()+c.cpos[0]+Connector.SIZE/2, c.y()+c.cpos[1]+Connector.SIZE/2)
        c: InteractiveComponent
        for c in self.fd_wx_consts:
            c.setPos(QPointF(c.x()-delta.x(), c.y()-delta.y()))

        self.prev_pos = self.pos()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseMoveEvent(event)

        self.update_connc()


class Connector(QGraphicsPolygonItem):
    SIZE = 10

    def __init__(self, ct: int, pos: tuple, z_val=None, parent=None):
        super().__init__(parent=parent)
        if z_val is not None: self.setZValue(z_val)
        self.setBrush(QBrush(QColor("#00FFFF")))
        self.setPen(QPen(QColor("#000000")))

        self.ct = ct
        self.cpos = pos  # central position for the selected polygon shape
        self.prim_connct = []  # primary connections: holds reference and updates connection's a-pos
        self.scnd_connct = []  # secondary connections: holds reference and updates connection's b-pos
        self.temp_connct = None

        polygon = QPolygonF()

        polygon.append(QPointF(pos[0], pos[1]))
        polygon.append(QPointF(pos[0], pos[1] + self.SIZE))
        polygon.append(QPointF(pos[0] + self.SIZE, pos[1] + self.SIZE))
        polygon.append(QPointF(pos[0] + self.SIZE, pos[1]))

        self.setPolygon(polygon)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        # note: calling super().mousePressEvent() will cause the view to pan and disable of properly dragging the connection
        # dprint("generated new temp connc")
        scene: QGraphicsScene = self.scene()
        # logical_pos = (self.x()+self.cpos[0]+Connector.SIZE/2, self.y()+self.cpos[1]+Connector.SIZE/2)
        self.temp_connct = TempConnection(
            (self.x() + self.cpos[0] + Connector.SIZE / 2, self.y() + self.cpos[1] + Connector.SIZE / 2))
        scene.addItem(self.temp_connct)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseMoveEvent(event)
        if self.temp_connct is not None:
            self.temp_connct.drag_line((event.scenePos().x(), event.scenePos().y()))

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.temp_connct is not None:
            # dprint("deleted temp connc", self.temp_connct)
            scene: QGraphicsScene = self.scene()
            scene.removeItem(self.temp_connct)
            del self.temp_connct
            self.temp_connct = None

            for i in scene.items(event.scenePos()):
                # dprint(i)
                if isinstance(i, Connector):
                    # checks whether the selected item vs. the current item is different in IO type
                    if (self.ct ^ i.ct) & 0b11 == 0b11:
                        connc = Connection(
                            QPointF(self.x() + self.cpos[0] + Connector.SIZE / 2,
                                    self.y() + self.cpos[1] + Connector.SIZE / 2),
                            QPointF(i.x() + i.cpos[0] + Connector.SIZE / 2, i.y() + i.cpos[1] + Connector.SIZE / 2)
                        )
                        scene.addItem(connc)
                        self.prim_connct.append(connc)
                        i.scnd_connct.append(connc)


class Node(QGraphicsProxyWidget):
    def __init__(self, pos=(0, 0), parent=None):
        super().__init__(parent=parent)

        self.wx_main = NodeInternal()
        self.setWidget(self.wx_main)

        self.setGeometry(QRectF(0, 0, 150, 100))
        self.setPos(pos[0], pos[1])


class NodeInternal(QWidget):
    def __init__(self):
        super().__init__(parent=None)
        self.setStyleSheet("background-color: #CCDDFF")

        lyt_inp_fields = QVBoxLayout()
        lyt_inp_fields.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lyt_inp_fields.addWidget(QLabel("inp field A"))
        # lyt_inp_fields.addWidget(QLabel("inp field B"))
        # lyt_inp_fields.addWidget(QLabel("inp field C"))

        lyt_out_fields = QVBoxLayout()
        lyt_out_fields.setAlignment(Qt.AlignTop | Qt.AlignRight)
        lyt_out_fields.addWidget(QLabel("out field A"))
        lyt_out_fields.addWidget(QLabel("out field A"))

        lyt_body = QHBoxLayout()
        lyt_body.addLayout(lyt_inp_fields)
        lyt_body.addLayout(lyt_out_fields)

        title = QLabel("Node Title")
        title.setStyleSheet("background-color: #CCF0FF; font: 12px courier")
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        title.setMargin(2)

        lyt_main = QVBoxLayout()
        lyt_main.setContentsMargins(2, 2, 2, 2)
        lyt_main.addWidget(title, 1)
        lyt_main.addLayout(lyt_body, 9)
        lyt_main.addWidget(QLabel("const field A"))
        # lyt_main.addWidget(QLabel("const field B"))
        # lyt_main.addWidget(QLabel("const field C"))
        # lyt_main.addWidget(QLabel("const field D"))

        self.setLayout(lyt_main)

        dprint(self.geometry(), self.pos())

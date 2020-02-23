from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import *

from typing import Dict, List

from src.debug import *
from src.gfx.connector import Connector
from src.state import StateHolder
from src.constants import *


class Model(QWidget):
	""" Model Class
		This is to render a model, a configurable node for data manipulation and data transfer
	"""
	MODEL_SIZE = (200, 50)
	NODE_SIZE = (16, 16)  # ~ connector size
	NODE_OFS = QPoint(0, 6)  # NOTE: inverted position (-x, -y)

	MOUSE_OFS = (0, 0)  # position offset when mouse on trigger

	def __init__(self, state: StateHolder, surf, pos, mdl_dt, parent=None):
		super().__init__(parent=parent)

		self.clicked = False
		self.state = state
		self.surf = surf
		self.field_y = 20
		self.base_pos = self.NODE_OFS  # basic position for properly rendering the position of node
		self.field = mdl_dt.field
		self.pos = pos
		self.title_txt = mdl_dt.name
		self.nmspc_id = mdl_dt.title

		self._inst_basic_ui()
		self._create_node()

		self.setStyleSheet("background-color: #CCDDFF")

		state.model_dt.append(self)

	def _create_fields(self, field: Dict[str, List[str]]):
		inp = QVBoxLayout()  # input area selection
		# [inp.addWidget(QLabel(f[0])) for f in field["input"]]

		ref = []
		for f in field["input"]:
			lbl = QLabel(f[0])
			ref.append(lbl)
			inp.addWidget(lbl)
		inp.addStretch()

		out = QVBoxLayout()  # output area selection
		[out.addWidget(QLabel(f[0])) for f in field["output"]]
		out.addStretch()

		usr = QFormLayout()  # user input area selection
		[usr.addRow(QLabel(f[0]), f[1]) for f in field["constant"]]

		return (inp, out, usr)

	def _create_node(self):
		for ind, fld in enumerate(self.field["input"]):
			self.surf.scene().addItem(
				Connector(self.state, (0, self.title.rect().height()+(self.field_y)*ind+self.NODE_OFS.y(), *self.NODE_SIZE), self,
				          TG_INPUT, [TG_OUTPUT], fld) )
		for ind, fld in enumerate(self.field["output"]):
			self.surf.scene().addItem(
				Connector(self.state, (0, self.title.rect().height()+(self.field_y)*ind+self.NODE_OFS.y(), *self.NODE_SIZE),
				          self, TG_OUTPUT, [TG_INPUT], fld) )
		self.updPosNode()

	def _inst_basic_ui(self):
		self.title = QLabel(self.title_txt, self)
		self.title.setAlignment(Qt.AlignTop)
		self.title.setFont(QtGui.QFont("courier", 10, QtGui.QFont.Bold))
		self.title.setStyleSheet("background-color: #CCF0FF")
		self.title.setAlignment(Qt.AlignCenter)

		inp, out, usr = self._create_fields(self.field)

		data_selector = QBoxLayout(QBoxLayout.LeftToRight)  # a horizontal layout for input and output
		data_selector.addLayout(inp)
		data_selector.addStretch()
		data_selector.addLayout(out)

		layout = QBoxLayout(QBoxLayout.TopToBottom)
		layout.addWidget(self.title)
		layout.addLayout(data_selector)
		layout.addLayout(usr)
		layout.addStretch()

		self.setLayout(layout)
		# self.move(self.pos[0], self.pos[1])
		self.setGeometry(self.pos[0], self.pos[1], self.MODEL_SIZE[0], self.MODEL_SIZE[1])

	def resizeEvent(self, QResizeEvent):
		""" updates the position of all the connectors, espaically the output fields """
		for o in self.surf.items():
			if isinstance(o, Connector):
				if o.tag == "out" and o.parent == self:
					o.setX(self.MODEL_SIZE[0]+QResizeEvent.size().width()-self.NODE_SIZE[0]/2)

	# built-in automatically called method
	def mousePressEvent(self, event):
		if event.button() == 1:  # 1 = left click
			self.clicked = True
			self.MOUSE_OFS = (-event.x(), -event.y())  # the event position is relative to this object

	# built-in automatically called method
	def mouseMoveEvent(self, event):
		if self.clicked:
			self.setGeometry(self.x()+event.x()+self.MOUSE_OFS[0], self.y()+event.y()+self.MOUSE_OFS[1],
			                 self.MODEL_SIZE[0], self.MODEL_SIZE[1])
			self.updPosNode()

	# built-in automatically called method
	def mouseReleaseEvent(self, event):
		if event.button() == 1:  # 1 = left click
			self.clicked = False

	# updates the position of the node
	def updPosNode(self):
		new_pos = QPoint(self.geometry().x(), self.geometry().y())
		for go in self.surf.scene().items():  # items (graphic objects) in the <scene> container
			if isinstance(go, Connector):  # filters other items
				if go.parent == self:
					if go.field in self.field["input"]:
						go.setPos(QPoint(new_pos.x()-self.NODE_SIZE[0]/2,
						    new_pos.y()))
					elif go.field in self.field["output"]:
						go.setPos(QPoint(new_pos.x()-self.NODE_SIZE[0]/2+self.width(),
						    new_pos.y()))
					elif go.field in self.field["constant"]:
						pass
					else:
						print("[MODEL] [ERROR] The node field is not in the model's field")

					# go.moveBy(new_pos.x()-self.base_pos.x(), new_pos.y()-self.base_pos.y())
				go.updatePairedPos()  # outside of the {IF} so if the opposite model decides to move, this function \
				#                      updates the connection from the other model
		self.base_pos = new_pos
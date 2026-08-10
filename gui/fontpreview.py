from PyQt5 import QtCore, QtGui, QtWidgets

import os, logging
import re
import shutil
from common import settings
from gui.pak import PakWidget
from gui.orphans import OrphanWidget
from gui.mugen import MugenWidget
from gui.volnorm import VolNormWidget
from gui.commandgen import CommandListGenerator
from data import ParsedLine, FileWrapper

from gui.util import FileInput

from gui.level.items import FontObject



from gui.main.fileselector import FileSelector

class ImageWidget(QtWidgets.QGraphicsView):
	
	def __init__(self):
		QtWidgets.QGraphicsView.__init__(self)
		
		
		self.scaleFactor = 1.0
	
	def wheelEvent(self, e):
		#scene.addItem(QtWidgets.QGraphicsPixmapItem(pic))
		#self.image.setPixmap(pic)
		
		if e.angleDelta().y() > 0:
			self.zoomIn(e)
			return
			self.image.setPixmap(self.pic.scaled(self.scaleFactor * self.pic.size()))
			#self.scaleImage(1.25)
			
			return
			factor = self.zoom / (self.zoom + 0.1)
			self.zoom += 0.1
		else:
			self.zoomOut(e)
			return
			self.image.setPixmap(self.pic.scaled(self.scaleFactor * self.pic.size()))
			#self.scaleImage(0.8)
			return
			factor = self.zoom / (self.zoom - 0.1)
			self.zoom -= 0.1
		self.scale(factor, factor)
		
		self.centerOn(e.x(), e.y())
		print( self.zoom)
		print( '')
	
	def zoom(self, factor, e=None):
		if e == None:
			self.scaleFactor *= factor
			self.scale(factor, factor)
			
			for w in [*self.parent.walls, *self.parent.basemaps]:
				w.adjustToZoom(self.scaleFactor)
			
			return
		
		oldPos = self.mapToScene(e.pos())
		
		targetViewportPos = e.pos();
		targetScenePos = self.mapToScene(e.pos())
		
		self.scaleFactor *= factor
		self.scale(factor, factor)
		
		
		
		# newPos = self.mapToScene(e.pos())
		# delta = newPos - oldPos
		# self.translate(delta.x(), delta.y())
		self.centerOn(targetScenePos)
		deltaViewportPos = targetViewportPos - QtCore.QPointF(self.viewport().width() / 2.0, self.viewport().height() / 2.0)
		viewportCenter = self.mapFromScene(targetScenePos) - deltaViewportPos;
		self.centerOn(self.mapToScene(viewportCenter.toPoint()));
		
		
		# if (e != None):
		# 	self.centerOn(e.scenePosition().x(), e.scenePosition().y())
		
	def zoomIn(self, e=None):
		self.zoom(1.25, e)
		
	def zoomOut(self, e=None):
		self.zoom(0.8, e)

     
class FontPreview(QtWidgets.QWidget):
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		#layout = QtWidgets.QBoxLayout()
		layout = QtWidgets.QFormLayout()
		
		dataPath = settings.get_option('general/data_path', '')
		
		self.imageReference = FileInput(self, 'openFile', dataPath + '/sprites/font.gif', 'Select font sprite reference', dataPath)
		layout.addRow(_('Font sprite reference') + ' : ', self.imageReference)
		
		
		self.textToPreview = QtWidgets.QLineEdit()
		self.textToPreview.textChanged.connect(self.updateFontObject)
		layout.addRow(_('Text to preview') + ' : ', self.textToPreview)
		
		
		self.spaceSpinner = QtWidgets.QSpinBox()
		self.spaceSpinner.setRange(-1,100)
		self.spaceSpinner.setValue(settings.get_option('misc/font_spacing', 0))
		self.spaceSpinner.valueChanged.connect(self.spaceValueChanged)
		layout.addRow(_('Space between letters') + ' : ', self.spaceSpinner)
		layout.addRow(QtWidgets.QLabel('(Set to -1 for monospace)'))
		
		self.changeBackgroundColorButton = QtWidgets.QPushButton('Change background color')
		self.changeBackgroundColorButton.clicked.connect(self.changeBGColor)
		layout.addRow(self.changeBackgroundColorButton)
		
		self.updateButton = QtWidgets.QPushButton(_('Update'))
		self.updateButton.clicked.connect(self.updateFontObject)
		layout.addRow(self.updateButton)
		
		self.scene = QtWidgets.QGraphicsScene()
		
		self.graphicsView = ImageWidget()
		
		self.graphicsView.setScene(self.scene)
		
		layout.addRow(self.graphicsView)
		
		
		self.setWindowTitle('Pixel Font Preview')
		self.setLayout(layout)
		self.show()
		
	def changeBGColor(self):
		color = QtWidgets.QColorDialog.getColor().name() 
		
		print('color', color)
		
		if(color != '#000000' and color != None and color != False):
			self.graphicsView.setBackgroundBrush(QtGui.QColor(color));
			
	def spaceValueChanged(self):
		
		value = self.spaceSpinner.value()
		settings.set_option('misc/font_spacing', value)
		
	def updateFontObject(self):
		text = self.textToPreview.text()
		self.scene.clear()
		self.scene.addItem(FontObject(text, self.imageReference.text()))
		


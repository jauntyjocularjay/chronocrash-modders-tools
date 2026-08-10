from PyQt5 import QtWidgets, QtGui, QtCore

from common import settings

import platform

class FontSelector(QtWidgets.QWidget):
	def __init__(self, prefix='editor', defaultFamily=None, defaultSize=12):
		QtWidgets.QWidget.__init__(self)

		self.prefix = prefix
		self.setMinimumSize(500, 450)

		db = QtGui.QFontDatabase()
		families = db.families()

		layout = QtWidgets.QVBoxLayout()
		self.setLayout(layout)
		
		listLayout = QtWidgets.QHBoxLayout()
		layout.addLayout(listLayout)
		
		fontW = QtWidgets.QListWidget()
		fontW.addItems(families)
		fontW.currentTextChanged.connect(self.changeFamily)
		self.fontW = fontW
		
		
		sizeW = QtWidgets.QListWidget()
		fontSizes = [4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,22,24,26,28,32, 48, 64, 72, 80, 96, 128]
		sizeW.addItems(map(str, fontSizes))
		sizeW.currentTextChanged.connect(self.changeSize)
		self.sizeW = sizeW
		
		listLayout.addWidget(fontW)
		listLayout.addWidget(sizeW)
		
		textEdit = QtWidgets.QPlainTextEdit()
		textEdit.setPlainText('José Long est un mage.')
		self.textEdit = textEdit

		layout.addWidget(textEdit)
		
		
		# Load settings
		if defaultFamily is None:
			fontFamilies = {'Windows':'Courier New',
	                        'Darwin': 'Menlo'}
			defaultFamily = fontFamilies.get(platform.system(), 'Monospace')
		currentFamily = settings.get_option(self.prefix + '/font_family', defaultFamily)
		if currentFamily in families:
			self.fontW.setCurrentRow(families.index(currentFamily))

		currentSize = settings.get_option(self.prefix + '/font_size', defaultSize)
		if currentSize in fontSizes:
			self.sizeW.setCurrentRow(fontSizes.index(currentSize))
		
	def changeFamily(self, family):
		f = self.textEdit.font()
		f.setFamily(family)
		self.textEdit.setFont(f)
		
	def changeSize(self, size):
		f = self.textEdit.font()
		f.setPointSize(int(size))
		self.textEdit.setFont(f)
		
	def save(self):
		if self.fontW.currentItem() is not None:
			settings.set_option(self.prefix + '/font_family', self.fontW.currentItem().text())
		if self.sizeW.currentItem() is not None:
			settings.set_option(self.prefix + '/font_size', int(self.sizeW.currentItem().text()))

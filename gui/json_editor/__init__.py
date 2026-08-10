from PyQt5 import QtCore, QtGui, QtWidgets

from gui.json_editor.keyselector import KeySelector

import json

class JSONGUIEditor(QtWidgets.QWidget):
	def __init__(self, parent):
		QtWidgets.QWidget.__init__(self, parent)
		self.parent = parent
		
		self.setMinimumSize(500,200)
		
		
		
		self.keySelector = KeySelector(self)
		
		layout = QtWidgets.QVBoxLayout()
		
		layout.addWidget(self.keySelector, 1)
		
		self.editor = QtWidgets.QPlainTextEdit()
		self.editor.setMinimumSize(500,200)
		self.key = None
		self.editor.textChanged.connect(self.updateKey)
		layout.addWidget(self.editor, 0)
		
		self.setLayout(layout)
		
		
	def loadFile(self, fd):
		self.JSON_data = json.loads("\n".join(fd.lines))
		
		self.keySelector.clear()
		self.keySelector.load(self.JSON_data.keys())
		
		print(self.JSON_data)
		
	def loadKey(self, key):
		print(self.JSON_data[key])
		
		self.key = key
		
		self.editor.setPlainText(self.JSON_data[key])
		
	def rebuildText(self):
		return json.dumps(self.JSON_data, indent=1).split('\n')
	
	def updateKey(self):
		if(self.key == None): return
		self.JSON_data[self.key] = self.editor.toPlainText()

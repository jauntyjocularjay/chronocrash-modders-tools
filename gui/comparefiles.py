from PyQt5 import QtCore, QtGui, QtWidgets

import os, logging, subprocess
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


     
class CompareFiles(QtWidgets.QWidget):
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		#layout = QtWidgets.QBoxLayout()
		layout = QtWidgets.QFormLayout()
		
		dataPath = settings.get_option('general/data_path', '')
		
		
		
		self.folder1 = FileInput(self, 'folder', settings.get_option('compare_tool/folder1', ''), 'Select folder 1', dataPath)
		layout.addRow(_('Folder 1') + ' : ', self.folder1)
		
		self.folder1.changed.connect(self.updateFile1LookFolder)
		
		
		
		self.folder2 = FileInput(self, 'folder', settings.get_option('compare_tool/folder2', ''), 'Select folder 2', dataPath)
		layout.addRow(_('Folder 2') + ' : ', self.folder2)
		self.folder2.changed.connect(self.updateFile2LookFolder)
		
		
		self.file1 = FileInput(self, 'openFile', settings.get_option('compare_tool/file1', ''), dataPath)
		self.file1.changed.connect(self.saveFile1Loc)
		layout.addRow(_('File 1') + ' : ', self.file1)
		
		
		self.file2 = FileInput(self, 'openFile', settings.get_option('compare_tool/file2', ''), dataPath)
		layout.addRow(_('File 2') + ' : ', self.file2)
		
		self.matchWithFile1 = QtWidgets.QPushButton(_('Match with file 1'))
		self.matchWithFile1.clicked.connect(self.matchWithFile1_func)
		layout.addRow(self.matchWithFile1)
		
		
		self.compareTool = FileInput(self, 'openFile', settings.get_option('compare_tool/compare_program_path', 'meld'), dataPath)
		
		layout.addRow(_('Compare program') + ' : ', self.compareTool)
		
		
		
		self.commandMask = QtWidgets.QLineEdit()
		self.commandMask.setText( settings.get_option('compare_tool/command_mask', '{program} {file1} {file2}'))
		layout.addRow(_('Command mask') + ' : ', self.commandMask)
		
		
		
		self.updateButton = QtWidgets.QPushButton(_('Start'))
		self.updateButton.clicked.connect(self.start)
		layout.addRow(self.updateButton)
		
	
		
		
		
		
		self.setWindowTitle('Compare files')
		self.setLayout(layout)
		self.show()
		
	def getFile1(self):
		return self.file1.text()
		
	def getFile2(self):
		return self.file2.text()
		
		   
		   
	def matchWithFile1_func(self):
		baseText = self.file1.text()
		
		# We remove folder part
		baseText =  baseText.replace(self.folder1.text(), '')
		
		self.file2.setText(self.folder2.text() + baseText)
		
	def saveFile1Loc(self):
		settings.set_option('compare_tool/file1', self.file1.text())
	
	
	def updateFile1LookFolder(self):
		self.file1.lookFolder = self.folder1.text()
		settings.set_option('compare_tool/folder1', self.folder1.text())
		
	def updateFile2LookFolder(self):
		self.file2.lookFolder = self.folder2.text()
		settings.set_option('compare_tool/folder2', self.folder2.text())
		
	def start(self):
		command = self.compareTool.text()
		
		commandMask = self.commandMask.text()
		
		
		settings.set_option('compare_tool/command_mask', commandMask)
		
		commandMask = commandMask.replace(' ', '@')
		commandMask = commandMask.replace('{program}', command)
		commandMask = commandMask.replace('{file1}', self.getFile1())
		commandMask = commandMask.replace('{file2}', self.getFile2())
		
		settings.set_option('compare_tool/compare_program_path', command)
		
		# subprocess.call(command + ' "' + self.getFile1() + '" "' + self.getFile2() +'"', shell=True)
		# subprocess.call(commandMask, shell=True)
		subprocess.Popen(commandMask.split('@'))
		


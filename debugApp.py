# -*- coding: utf-8 -*-
import os, sys, traceback, shutil
import locale
import time
from datetime import datetime
now = datetime.now()




import logging

qutepart_logger = logging.getLogger('qutepart')
qutepart_logger.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.DEBUG)

logFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'journal.log')
try:
	os.remove(logFile + '.1')
except:
	pass
if(os.path.isfile(logFile)): shutil.copyfile(logFile, logFile + '.1')
#logFile = 'journal2.log'
logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG)

from pyqttoast import Toast, ToastPreset, ToastPosition


# print log in example.log instead of the console, and set the log level to DEBUG (by default, it is set to WARNING)


#logFile = 'journal2.log'



logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.debug(now)




#print(logging.getLoggerClass().root.handlers[0].baseFilename)
#sys.stderr.write = logger.error
#sys.stdout.write = logger.info
#print = lambda *tup : logger.info(str(" ".join([str(x) for x in tup])))

#old_stdout = sys.stdout

#log_file = open("journal.log","w")

#sys.stdout = log_file



from random import uniform

from common import settings, util


import gettext
trans = gettext.NullTranslations()
trans.install()

from gui.main.everydayeditor import BasicEverydayEditor,EverydayEditor


from PyQt5 import QtCore, QtGui, QtWidgets

#from dialogeditor import DialogEditor

from gui.project import ProjectSelector
from gui.backupviewer import BackupViewer
from gui.main import MainEditorWidget
#from leveleditor import LevelEditorWidget

#from spritesorter import SpriteSorterWidget
from gui.menubar import MenuBar

from gui.main.fileselector import File

import style

TITLE = 'OpenBOR Utils & Tools'
TITLE = 'ChronoCrash Modders Tools'
import fallbackicons


class FocusSwitcher(QtWidgets.QLabel):
	
	def __init__(self, parent, text):
		self.parent = parent
		QtWidgets.QLabel.__init__(self, text)
		self.lastSwitch = 0
		
	def mousePressEvent(self, e):
		self.toggle()
		
	def enterEvent(self, e):
		if settings.get_option('gui/toggle_focus_mode_hover', False):
			t = time.time()
			# t = datetime.now().timestamp()
			if(t >= self.lastSwitch+1):
				self.toggle()
				self.lastSwitch = t
			
	def toggle(self):
		
		self.parent.switchFocus()
		
		

class HeaderWidget(QtWidgets.QWidget):
	
	# def __init__(self):
	# 	pass
		
	def setInfo(self, obj):
		pass


class Frame(QtWidgets.QMainWindow):
	
	def __init__(self, parent=None):
		self.logger = logging.getLogger()
		QtWidgets.QMainWindow.__init__(self, parent)
		self.setWindowTitle(TITLE)
		
		self.currentProject = {'path':'ok', 'name':'ok'}
	
		cw = QtWidgets.QWidget()
		

		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		cw.setLayout(layout)
		
		# Trick for EverydayEditor
		self.headerWidget = HeaderWidget()
		
		# self.editor = BasicEverydayEditor(self)
		self.editor = EverydayEditor(self)
		# path = '/run/media/piccolo/9a89a301-e26c-44a8-84ca-05251359304c/workspace/disco-capacitor/src/backend/ActionHandler.js';
		# self.editor.editor.detectSyntax(xmlFileName='javascript.xml')
		
		
		path = '/run/media/piccolo/SSD-DATA/1 - VERY IMPORTANT/CMT/mugen.py';
		self.editor.editor.detectSyntax(xmlFileName='python.xml')
		
		# path = '/home/piccolo/workspace/Daimao-Journal-JS-4/djournal/src/components/font-size.ts'
		# self.editor.editor.detectSyntax(xmlFileName='typescript.xml')
		
		# path = '/home/piccolo/workspace/Daimao-Journal-JS-4/djournal/src/components/MainMenu.jsx'
		# self.editor.editor.detectSyntax(xmlFileName='javascript-react.xml')
		# self.editor.editor.detectSyntax(xmlFileName='jsx.xml')
		
		# self.editor.editor.detectSyntax(xmlFileName='html.xml')
		
		# path = '/run/media/piccolo/9a89a301-e26c-44a8-84ca-05251359304c/workspace/night-club-app/src/app/layout.tsx';
		# self.editor.editor.detectSyntax(xmlFileName='typescript-react.xml')
		
		# self.editor.editor.detectSyntax(xmlFileName='css.xml')
		
		simpleText= True
		
		if(simpleText):
		
			txt = '''import { Extension } from '@tiptap/core';
import '@tiptap/extension-text-style';'''
        
			txt = '"oki"'
			
			
			txt = '''<oki></oki>
function oki(){
    return <oki></oki>
}

<oki></doki> <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>'''
			
			
			txt = '''button[aria-disabled='true'] {
  background-color: var(--interactive-normal);
}
button:focus-visible {
  box-shadow: 0 0 0 3px var(--background-modifier-border-focus);
}
button[disabled="true"] {
  cursor: not-allowed;
}'''
			
			txt = '''import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";'''
			
			
			txt = '''#Josay'''
            
			self.editor.editor.lines = txt.split('\n')
		
		else:
		
			f = open(path, 'r')
			lines = f.read()
			lines = lines.split('\n')
			self.editor.editor.lines = lines
		
		layout.addWidget(self.editor)
		
		self.setCentralWidget(cw)
		
	
	
	def switchFocus(self):
		self.focused = not self.focused
		
		if(self.focused):
			self.focusSwitcher.setText('UNFOCUS')
			theme = settings.get_option('gui/widgets_theme', None)
			if(theme != None and 'dark' in theme.lower()):
				self.focusSwitcher.setStyleSheet("background-color: green") 
			else:
				self.focusSwitcher.setStyleSheet("background-color: lightgreen") 
			self.meWidget.entityEditor.animSelector.hide()
			self.meWidget.entityEditor.frameViewer.hide()
			self.meWidget.headerWidget.hide()
			self.meWidget.leftSidePanel.hide()
			self.meWidget.menuBar.hide()
			self.meWidget.entityEditor.searchEntry.hide()
			self.meWidget.entityEditor.replaceEntry.hide()
		else:
			self.focusSwitcher.setText('Focus')
			self.focusSwitcher.setStyleSheet("") 
			self.meWidget.entityEditor.animSelector.show()
			self.meWidget.entityEditor.frameViewer.show()
			self.meWidget.headerWidget.show()
			self.meWidget.leftSidePanel.show()
			self.meWidget.menuBar.show()
			
			self.meWidget.entityEditor.searchEntry.show()
			self.meWidget.entityEditor.replaceEntry.show()
		
	def autoSave(self):
		if hasattr(self.mainWidget, "fileSelector"):
			self.mainWidget.backupUnsaved()
			self.mainWidget.fileSelector.saveSession()
			
		# settings.MANAGER.save() # don't think it's needed
		
		
		
	def createTrayIcon(self):
		trayIconMenu = QtWidgets.QMenu(self);
#		trayIconMenu.addAction(minimizeAction);
#		trayIconMenu.addAction(maximizeAction);
#		trayIconMenu.addAction(restoreAction);
#		trayIconMenu.addSeparator();
		trayIconMenu.addAction(_('&Quit'), self.quit)

		self.trayIcon = QtWidgets.QSystemTrayIcon(self)
		self.trayIcon.setContextMenu(trayIconMenu)
		
		
	# def changeEvent(self, e):
	# 	if e.type() == QtCore.QEvent.WindowStateChange:
	# 		if self.windowState() == QtCore.Qt.WindowMaximized:
	# 			self.maximized = True
	# 		elif self.windowState() == QtCore.Qt.WindowNoState:
	# 			self.maximized = False
				
	def closeEvent(self, e):
		#if self.trayIcon.isVisible():
			#self.hide()
			#e.ignore()
			#return
		logging.debug("close event")
		# self.quit(e)
		
	def dragEnterEvent(self, e):
		data = e.mimeData()
		
		if data.hasUrls():
			newUrls = []
			newText = ''
			for url in data.urls():
				path = url.toLocalFile()
				p, extension = os.path.splitext(path)
				if extension.lower() in ('.gif', '.png', '.pcx'):
					newText += path
					continue
				newUrls.append(url)
				
			# e.ignore()
			e.accept()
			data = QtCore.QMimeData()
			data.setText(newText)
			data.setUrls(newUrls)
			print(data.formats())

			#data.setUrls([QtCore.QUrl('file:///home/piccolo/workspace/OpenBOR/data/chars/abubo/7.gif')])
			print('*** PRINTING URLS ***')
			print(data.urls())
			
			e = QtGui.QDragEnterEvent(e.pos(), e.dropAction(), data, e.mouseButtons(), e.keyboardModifiers())
			print( e.mimeData().urls())
			print('*** END PRINTING URLS ***')
			e.accept()
		#QtWidgets.QMainWindow.dragEnterEvent(self, e)
			
	def dropEvent(self, e):
		
		data = e.mimeData()
		print("\nDROP EVENT", data.urls())
		print(data.formats())
				
		if data.hasUrls():
			for url in data.urls():
				path = url.toLocalFile()
				p, extension = os.path.splitext(path)
				if extension.lower() in ('.gif', '.png', '.pcx'):
					continue
				#path = url.toString()
				self.mainWidget.openFile(path)
		
	def newFile(self):
		#self.textEditor.clear()
		self.mainWidget.editNew()
		
		
	def notify(self, text, type='info', title=None):
		toast = Toast(self)
		toast.setDuration(5000)  # Hide after 5 seconds
		
		
		# Init font
		font = QtGui.QFont('Courier', 10)
		font2 = QtGui.QFont('Courier', 10, QtGui.QFont.Weight.Bold)

		# Set fonts
		toast.setTitleFont(font2)  # Default: QFont('Arial', 9, QFont.Weight.Bold)
		toast.setTextFont(font)   # Default: QFont('Arial', 9)
		
		toast.setText(text)
		toast.setPosition(ToastPosition.TOP_RIGHT)
		if(type == 'warning'):
			if(title == None): title = 'Warning'
			toast.applyPreset(ToastPreset.WARNING)
		else:
			if(title == None): title = 'Success'
			toast.applyPreset(ToastPreset.SUCCESS)  # Apply style preset
		toast.setTitle(title)
		toast.show()
		
	def openFile(self):
		self.mainWidget.openFile()
		
		
	# def quit(self, e=None):
	# 	logging.debug("MAIN FRAME QUIT EVENT " + str(e) )
	# 	if not self.meWidget.close(True):
	# 		if e is not None:
	# 			e.ignore()
	# 		return
	# 	settings.set_option('gui/maximized', self.maximized)
	# 	settings.set_option('gui/window_x', self.pos().x())
	# 	settings.set_option('gui/window_y', self.pos().y())
	# 	settings.MANAGER.save()
	# 	#settings.MANAGER.saveTimer.cancel()
	# 	app.quit()
			
			
	# def resizeEvent(self, e):
	# 	if(not self.maximized):
	# 		#pos = self.mapToGlobal(self.pos())
	# 		settings.set_option('gui/window_x', self.pos().x())
	# 		settings.set_option('gui/window_y', self.pos().y())
	# 		settings.set_option('gui/window_width', e.size().width())
	# 		settings.set_option('gui/window_height', e.size().height())
		
	def saveFile(self):
		self.mainWidget.save()
		
	def saveFileAs(self):
		self.mainWidget.saveAs()
			
			
	def setEditorTheme(self, name=None):
		if name is None and self.sender() != None:
			name = self.sender().data()
			
		if name is not None:
			import themes
			themes.setEditorTheme(name)
			settings.set_option('gui/editor_theme', name)
		self.mainWidget.setTheme()
		
	def setMode(self, mode, params={}):
		self.mainWidget.hide()
		self.mode = mode
		if mode == 'dialog':
			
			
			self.mainWidget = self.dialogWidget
		elif mode == 'project':
			self.projectSelector.reset()
			self.mainWidget = self.projectSelector
		elif mode == 'mainEditor':
			self.mainWidget = self.meWidget
		elif mode == 'backupViewer':
			self.backupViewer.reload(params)
			self.mainWidget = self.backupViewer
			
		self.mainWidget.show()
		
		
	def setTheme(self, name=None):
		if name is None and self.sender() != None:
			name = self.sender().data()
			
		if name is None: return
		global app
		path = os.path.join ('themes', 'widgets', name + '.css')
		if not os.path.exists(path): return
		f = open(path)
		content = f.read()
		f.close()
		app.setStyleSheet(style.STYLE_SHEET + content)
		settings.set_option('gui/widgets_theme', name)
		
		
	def setSession(self, name=None, save=False, savePrevious=True):
		logging.debug("Setting session from main frame... [" + str(name) + '] save=' + str(save))
		if name is None and self.sender() != None:
			name = self.sender().data()
		print(name)
		if name is None: return

	
		# Meant for "save session as" call (must be done before close which clears loadedFiles)
		if(save): self.mainWidget.fileSelector.saveSession(name)

		# Before changing, save current
		if(savePrevious and not self.meWidget.close(True)): # False mean there was unsaved files and the user canceled operation
			return

		if(name != ''):
			settings.set_option('general/last_session', name)
			
			if(self.mainWidget.currentProject != None):
				self.mainWidget.currentProject['last_session'] = name
				self.projectSelector.actualizeProject(self.mainWidget.currentProject)
		self.mainWidget.fileSelector.loadSession(name)
			
	def tabChange(self, index):
		pass
		
	def trayIconClick(self, reason):
		self.setVisible(not self.isVisible())



def excepthook(exc_type, exc_value, exc_tb):
	tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
	print("error catched!:")
	print("error message:\n", tb)
	logging.getLogger().exception('CRASH')
	logging.debug(tb)
	#QtWidgets.QApplication.quit()
	# or QtWidgets.QApplication.exit(0)
	msg = QtWidgets.QMessageBox()
	msg.setIcon(QtWidgets.QMessageBox.Warning)
	msg.setText("AN ERROR HAS OCCURED")
	msg.setInformativeText('PLEASE COPY THE ERROR MESSAGE AND REPORT IT HERE : <a href="https://www.chronocrash.com/forum/threads/chronocrash-modders-tools.2467">https://www.chronocrash.com/forum/threads/chronocrash-modders-tools.2467/</a><pre>\n\nTHEN CLICK "OK", SAVE EVERYTHING YOU CAN AND RESTART THE SOFTWARE BEFORE CONTINUING USING IT\n\n(OR CONTINUE USING IT AT YOUR OWN RISKS)\n\n' + tb + '</pre>')
	msg.setWindowTitle("CRASH REPORT")
	msg.setDetailedText(tb)
	msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
	#msg.buttonClicked.connect(msgbtn)
	
	retval = msg.exec_()

# sys.excepthook = excepthook

try:
	app = QtWidgets.QApplication(sys.argv)
	print(app.instance())
	
	memory = QtCore.QSharedMemory(app)
	memory.setKey("CMT")
	if memory.attach():
		print('already running')
	else:
		print('NOT running')
		memory.create(1)
	
	app.setApplicationName(TITLE)
	app.setStyleSheet(style.STYLE_SHEET)
	print (sys.argv)
	frame = Frame()
	frame.show()

	sys.exit(app.exec_())

except Exception:
	print('CRASH')
	logging.getLogger().exception('CRASH')
	raise

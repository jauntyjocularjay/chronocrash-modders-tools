# -*- coding: utf-8 -*-
import os, sys, traceback, shutil

# Once frozen, the bundled directories (icons, themes, data, ...) sit in
# sys._MEIPASS, but a lot of the code reaches them through paths relative to
# the working directory. Move there so both conventions agree, after turning
# the command line paths absolute while the original directory still applies.
if getattr(sys, 'frozen', False):
	sys.argv[1:] = [os.path.abspath(a) if os.path.exists(a) else a for a in sys.argv[1:]]
	os.chdir(sys._MEIPASS)

import locale
import time
from datetime import datetime
now = datetime.now()


import logging


from pyqttoast import Toast, ToastPreset, ToastPosition


# print log in example.log instead of the console, and set the log level to DEBUG (by default, it is set to WARNING)



logFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'journal.log')
try:
	os.remove(logFile + '.1')
except:
	pass
if(os.path.isfile(logFile)): shutil.copyfile(logFile, logFile + '.1')
#logFile = 'journal2.log'
# logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG)



logger = logging.getLogger()
logger.debug(now)
logger.debug(logFile)
logger.setLevel(logging.INFO)
#print(logging.getLoggerClass().root.handlers[0].baseFilename)
#sys.stderr.write = logger.error
#sys.stdout.write = logger.info
#print = lambda *tup : logger.info(str(" ".join([str(x) for x in tup])))

#old_stdout = sys.stdout

#log_file = open("journal.log","w")

#sys.stdout = log_file



from random import uniform

from common import settings, util


settings.DISABLE_STYLE_SHEET = False


import gettext
trans = gettext.NullTranslations()
trans.install()


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

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
# TITLE = 'cmt.py'
# TITLE = 'CMT'
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
		


class Frame(QtWidgets.QMainWindow):
	
	def __init__(self, parent=None):
		self.logger = logging.getLogger()
		QtWidgets.QMainWindow.__init__(self, parent)
		self.setWindowTitle(TITLE)
		
	
		
		
		try:
			self.setWindowIcon(QtGui.QIcon("icons/CMT.png"))
		except:pass
		
		if not QtGui.QIcon.hasThemeIcon("document-open"):
			import fallbackicons
			QtGui.QIcon.setThemeName('oxygen')
		
		try:
			self.move(settings.get_option('gui/window_x', 50), settings.get_option('gui/window_y', 50))
		except AttributeError:
			if(QtWidgets.QMessageBox.question(self, _('FATAL ERROR in settings'), _('Do you want to delete settings ?'), defaultButton=QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes):
				settings.delete()
				QtWidgets.QMessageBox.warning(self, _('Please restart'), _('Settings deleted please restart the app'))
				app.quit()

			
		self.resize(settings.get_option('gui/window_width', 700), settings.get_option('gui/window_height', 500))
		if(settings.get_option('gui/maximized', False)):
			self.maximized = True
			self.showMaximized()
		else:
			self.maximized = False
		
		
		

		#menuBar.setNativeMenuBar(False)
		#menuBar.setVisible(True)
		
		#self.mainTabWidget = QtWidgets.QTabWidget(self)
		#self.mainTabWidget.setTabPosition(QtWidgets.QTabWidget.West)
		#self.mainTabWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
		
		#ssWidget = SpriteSorterWidget()
		
		self.meWidget = MainEditorWidget(self)
		
		menuBar = MenuBar(self)
		self.setMenuBar(menuBar)
		
		self.meWidget.menuBar = menuBar
		#leWidget = LevelEditorWidget()
		
		cw = QtWidgets.QWidget()
		#toolWidget = ToolWidget()
		#self.mainTabWidget.addTab(cw, _('Dialog editor'))
		self.projectSelector = ProjectSelector(self)
		#self.mainTabWidget.addTab(self.projectSelector, _('Project Selector'))
		
		
		self.backupViewer = BackupViewer(self)
		
		#self.meWidget = meWidget
		#self.mainTabWidget.addTab(self.meWidget, _('Main editor'))
		#self.mainTabWidget.addTab(eeWidget, _('Entity editor'))
		#self.mainTabWidget.addTab(leWidget, _('Level editor'))
		#self.mainTabWidget.addTab(ssWidget, _('Sprite sorter'))
		#self.mainTabWidget.addTab(toolWidget, _('Tools'))

		#self.mainTabWidget.currentChanged.connect(self.tabChange)
		
		
		from data.db import DB
		if settings.ALPHA:
			self.DB = DB('backups-alpha.db')
		else:
			self.DB = DB('backups.db')
		File.DB = self.DB
		
		settings.DB = self.DB
		
		
		from dialogeditor import DialogEditor
		self.dialogWidget = DialogEditor()

		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		cw.setLayout(layout)
		
		self.setCentralWidget(cw)
		#self.setCentralWidget(self.mainTabWidget)
		#cw.addWidget(self.mainTabWidget)
		self.meWidget.hide()
		self.dialogWidget.hide()
		self.backupViewer.hide()
		layout.addWidget(self.projectSelector)
		layout.addWidget(self.meWidget)
		layout.addWidget(self.dialogWidget)
		layout.addWidget(self.backupViewer)

		#self.textEditor = DialogEditor()
		#layout.addWidget(self.textEditor)
		
		self.setAcceptDrops(True)
		self.mainWidget = self.meWidget
		
		
		self.setTheme(settings.get_option('gui/widgets_theme', 'Normal'))
		self.setEditorTheme(settings.get_option('gui/editor_theme', 'Normal'))
		
		
		self.autosaveTimer = QtCore.QTimer()
		interval = settings.get_option('autobackup/timeout', 60) * 1000
		# interval = 10000
		self.autosaveTimer.setInterval(interval)
		self.autosaveTimer.timeout.connect(self.autoSave)
		self.autosaveTimer.start()
		
		
		#self.createTrayIcon()
		#self.trayIcon.show()
		#self.trayIcon.activated.connect(self.trayIconClick)
		self.focused = False
		self.focusSwitcher = FocusSwitcher(self, 'FOCUS')
		self.window().statusBar().addWidget(self.focusSwitcher, 1)
		self.window().statusBar().addWidget(QtWidgets.QLabel(''), 6)
	
	
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
			# self.meWidget.menuBar.hide()
			self.meWidget.entityEditor.searchEntry.hide()
			self.meWidget.entityEditor.replaceEntry.hide()
			
			self.meWidget.editor.contentIndexerPanel.hide()
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
			
			self.meWidget.editor.contentIndexerPanel.show()
		
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
		
		
	def changeEvent(self, e):
		if e.type() == QtCore.QEvent.WindowStateChange:
			if self.windowState() == QtCore.Qt.WindowMaximized:
				self.maximized = True
			elif self.windowState() == QtCore.Qt.WindowNoState:
				self.maximized = False
				
	def closeEvent(self, e):
		#if self.trayIcon.isVisible():
			#self.hide()
			#e.ignore()
			#return
		logging.debug("close event")
		self.quit(e)
		
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
		
		
	def quit(self, e=None):
		logging.debug("MAIN FRAME QUIT EVENT " + str(e) )
		if(QtWidgets.QMessageBox.question(self, _('Close'), _('Are you sure you want to close ?'), defaultButton=QtWidgets.QMessageBox.Yes) != QtWidgets.QMessageBox.Yes):
			if e is not None:
				e.ignore()
			return
		if not self.meWidget.close(True):
			if e is not None:
				e.ignore()
			return
		settings.set_option('gui/maximized', self.maximized)
		settings.set_option('gui/window_x', self.pos().x())
		settings.set_option('gui/window_y', self.pos().y())
		settings.MANAGER.save_sync() # synchronous, and waits for any in-flight threaded save : guarantees the write completes before exit
		#settings.MANAGER.saveTimer.cancel()
		app.quit()
			
			
	def resizeEvent(self, e):
		if(not self.maximized):
			#pos = self.mapToGlobal(self.pos())
			settings.set_option('gui/window_x', self.pos().x())
			settings.set_option('gui/window_y', self.pos().y())
			settings.set_option('gui/window_width', e.size().width())
			settings.set_option('gui/window_height', e.size().height())
		
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
		if not settings.DISABLE_STYLE_SHEET:
			app.setStyleSheet(style.get_style_sheet() + content)
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
	msg.setText("AN ERROR HAS OCCURED " + settings.VERSION)
	msg.setInformativeText('PLEASE COPY THE ERROR MESSAGE AND REPORT IT HERE : <a href="https://www.chronocrash.com/forum/threads/chronocrash-modders-tools.2467">https://www.chronocrash.com/forum/threads/chronocrash-modders-tools.2467/</a><pre>\n\nTHEN CLICK "OK", SAVE EVERYTHING YOU CAN AND RESTART THE SOFTWARE BEFORE CONTINUING USING IT\n\n(OR CONTINUE USING IT AT YOUR OWN RISKS)\n\n' + tb + '</pre>')
	msg.setWindowTitle("CRASH REPORT " + settings.VERSION)
	msg.setDetailedText(tb)
	msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
	#msg.buttonClicked.connect(msgbtn)
	
	retval = msg.exec_()

sys.excepthook = excepthook

def run():

	global app

	try:
		app = QtWidgets.QApplication(sys.argv)
		print(app.instance())

		server_name = "CMT_SingleInstance"

		# Tenter de se connecter à une instance existante
		socket = QLocalSocket()
		socket.connectToServer(server_name)

		if socket.waitForConnected(500):
			# Instance existante trouvée : lui envoyer le fichier
			print('already running, sending file to existing instance')
			if len(sys.argv) > 1:
				socket.write(sys.argv[1].encode('utf-8'))
				socket.waitForBytesWritten()
			sys.exit(0)

		print('NOT running, starting new instance')

		# Pas d'instance existante : créer le serveur
		QLocalServer.removeServer(server_name)  # Nettoyer un socket orphelin
		server = QLocalServer()
		server.listen(server_name)

		app.setApplicationName(TITLE)

		# Courier was previously enforced by the stylesheet ; it is now the
		# default app font, overridable in Settings -> Application -> Font
		appFont = app.font()
		appFont.setFamily(settings.get_option('gui/font_family', 'Courier'))
		appFont.setPointSize(settings.get_option('gui/font_size', appFont.pointSize()))
		app.setFont(appFont)

		app.setStyleSheet(style.get_style_sheet())
		print (sys.argv)
		frame = Frame()

		# Gérer les connexions entrantes
		def handle_new_connection():
			client = server.nextPendingConnection()
			if client.waitForReadyRead(1000):
				file_path = client.readAll().data().decode('utf-8')
				if file_path:
					frame.mainWidget.openFile(file_path)
					# Forcer la fenêtre au premier plan sous Linux (seulement si pas déjà active)
					if not frame.isActiveWindow():
						frame.setWindowState(frame.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
						frame.raise_()
						frame.activateWindow()
						# Astuce supplémentaire pour certains window managers
						frame.setWindowFlags(frame.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
						frame.show()
						frame.setWindowFlags(frame.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
						frame.show()
			client.deleteLater()

		server.newConnection.connect(handle_new_connection)

		# Ouvrir le fichier passé en argument au démarrage
		if len(sys.argv) > 1:
			frame.mainWidget.openFile(sys.argv[1])

		frame.show()

		sys.exit(app.exec_())

	except Exception:
		print('CRASH')
		logging.getLogger().exception('CRASH')
		raise


run()

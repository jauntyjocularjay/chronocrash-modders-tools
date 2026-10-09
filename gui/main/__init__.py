import os, re, time, mimetypes, platform

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *

from common import util
from common import settings
from gui.util import FileInput

from gui.portrait import IconViewer, Portrait

from gui.main.everydaypart import EverydayPart

from data import ParsedLine

from gui.main.fileselector import FileSelector, File
from gui.main.everydayeditor import EverydayEditor
from gui.entity import EntityEditorWidget
from gui.level import LevelEditorWidget
from gui.level.items import Entity

from gui.json_editor import JSONGUIEditor

ROOT_PATH = '/home/piccolo/workspace/OpenBOR/'

from qutepart.syntax.colortheme import ColorTheme




class MainEditorWidget(QtWidgets.QWidget):
	
	def __init__(self, core):
		QtWidgets.QWidget.__init__(self)
		
		self.core = core
		
		self.loaded_projects = {}
		layout = QtWidgets.QHBoxLayout()
		splitter = QtWidgets.QSplitter(self)
		self.splitter = splitter
		self.splitter.splitterMoved.connect(self.splitterMoved)
		layout.addWidget(splitter)
		self.setLayout(layout)
		layout.setContentsMargins(0, 0, 0, 0)
		
		
		self.currentProject = {'name':'none', 'path':''}
		self.pending_file_to_open = None

		self.fileSelector = FileSelector(self)

		self.editor = EverydayEditor(self)
		self.editor.fileSelector = self.fileSelector 
		
		
		self.setupFavorites()

		self.currentPath = None
		
		

		
		#self.loadProject()
		
		
		leftSide = QtWidgets.QWidget()
		self.leftSidePanel = leftSide
		leftLayout = QtWidgets.QVBoxLayout()
		leftSide.setLayout(leftLayout)
		leftLayout.setContentsMargins(0, 0, 0, 0)
		leftLayout.setSpacing(0)
		leftLayout.addWidget(self.fileSelector.projectFilterBar)
		
		leftLayout.addWidget(self.fileSelector, 1)
		
		
		rightSide = QtWidgets.QWidget()
		rightLayout = QtWidgets.QVBoxLayout()
		rightLayout.setContentsMargins(0, 0, 0, 0)
		rightSide.setLayout(rightLayout)
		
		self.headerWidget = HeaderWidget(self)
		rightLayout.addWidget(self.headerWidget, 0)
		rightLayout.addWidget(self.editor, 1)
		
		self.entityEditor = EntityEditorWidget(self)
		self.levelEditor = LevelEditorWidget()
		rightLayout.addWidget(self.entityEditor, 1)
		rightLayout.addWidget(self.levelEditor, 1)
		self.entityEditor.hide()
		self.levelEditor.hide()
		
		
		
		self.JSON_editor = JSONGUIEditor(self)
		rightLayout.addWidget(self.JSON_editor, 1)
		self.JSON_editor.hide()
		
		
		
		
		splitter.addWidget(leftSide)
		splitter.addWidget(rightSide)
		
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("F1")), self, self.fileSelector.switchProjectFilter)
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+T")), self, self.openNewTab)
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+D", "Edit|Comment")), self, self.editor.comment)
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Shift+Ctrl+D", "Edit|Uncomment")), self, self.editor.uncomment)
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+F", "Edit|Find")), self, self.focusForSearch)
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+G")), self, self.focusForGoTo)
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+R", "Edit|Replace")), self, self.editor.focusForReplace)
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+G")), self, self.focusForGoTo)
		
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+W", "File|Close")), self, self.fileSelector.close)
		
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+PgDown")), self, self.editor.selectPreviousTab)
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+PgUp")), self, self.editor.selectNextTab)
		
		# QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+S", "File|Save")), self, self.core.saveFile)

		
		#QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+H", "File|Close")), self, self.editor.editor.highlightCurrentWord)
				
		self.splitter.setStretchFactor(0,0)
		self.splitter.setStretchFactor(1,1)
		
		
		self.temp_look_folder = None
		
		self.clearingCache = False
		
		self.currentView = 'text'
	
	def openNewTab(self):
		# self.currentProject['path']
		fd = self.fileSelector.addFile(os.path.dirname(self.editor.editor.fd.path) + '/New')
		fd.lines = []
		self.loadFile(fd, False)
		
	def reloadSplitterPos(self):
		splitterPos = settings.get_option('gui/splitter_pos', 0)
		if(splitterPos != 0):
			self.splitter.moveSplitter(splitterPos, 1)
	
	
	def splitterMoved(self, pos, index):
		if(self.isVisible()):
			settings.set_option('gui/splitter_pos', pos)
			settings.set_option('gui/splitter_index', index)
		
	
	def addFavorite(self):
		text = QtWidgets.QInputDialog.getText(self, _("Create animation"), _("Name"))[0]
		
		if(text != ''):
			data_path = settings.get_option('general/data_path', '')
			saved_favorites = settings.get_option('misc/shortcuts', [])
			todoPath = os.path.join(data_path, text + '.txt')
			saved_favorites.append({'key':text, 'path':todoPath});
			
			
			settings.set_option('misc/shortcuts', saved_favorites)
			
			fd = File(todoPath)
			fd.loadFromDisk(True)
			self.favorites[text] = fd
			
			return text
		return ''
	
	def focusForSearch(self):
		# print("focusForSearch", self.currentView)
		# elif(self.core.mode == 'backupViewer'):
		# 	self.core.backupViewer.editor.focusForSearch()
		if self.currentView == 'text' or self.currentView == 'text|text':
			self.editor.focusForSearch()
		elif self.currentView == 'anim':
			self.entityEditor.focusForSearch()
			
	def focusForGoTo(self):
		if self.currentView == 'text' or self.currentView == 'text|text':
			self.editor.focusForSearch(True)
		
	def backupUnsaved(self):
		self.updateFD()
		
		self.fileSelector.backupUnsaved()
		
		
		
		for key in self.favorites:
			fd = self.favorites[key]
			if not fd.saved:
				fd.save()
				#fd.backupUnsaved()

		# Auto-save notes
		from gui.main.fileselector import FileDB
		for fd in FileDB._allNotes.values():
			if not fd.saved:
				fd.save()
	
	def close(self, all=False):
		self.levelEditor.looping = False
		self.backupUnsaved()
		return self.fileSelector.close(all)
	
	
	def clearCache(self):
		self.clearingCache = True
		self.entityEditor.pixmapCache.clear()
		self.entityEditor.frameEditor.opponent = None
		LevelEditorWidget.PIXMAP_CACHE.clear()
		Entity.PIXMAP_CACHE.clear()
		Entity.LOADED_MODELS_REFERENCE.clear()
		self.clearingCache = False
		
	def editNew(self):
		fd = self.fileSelector.addFile('New')
		fd.lines = []
		self.loadFile(fd, False)
		

	def entitiesHaveBeenReloaded(self):
		self.entityEditor.frameEditor.bindingEditor.reloadModels()
		self.entityEditor.frameEditor.onionSkinEditor.reloadModels()
		
		
	def loadProject(self, project=None):

		if project is None:
			path = settings.get_option('general/data_path', '')
		else:
			path = project['path']
			
		self.currentProject = project
		
		
		self.switchProjectCore(path)
		
		global ROOT_PATH
		
		self.fileSelector.projectChanged(ROOT_PATH)
		
		if(not 'is_OpenBOR' in project or project['is_OpenBOR']):
			self.fileSelector.setMode('library')
			self.fileSelector.loadLibrary(False)
		else:
			self.fileSelector.setMode('opened')

		self.fileSelector.hydrateProjectSessionFiles(project)
		
		self.menuBar.addProjectQuickAccess(project)
		
		# self.fileSelector.loadLibrary(True)
		
		# self.reloadSplitterPos()
		
		
	def switchProjectCore(self, path, fd=None):
		
		if(fd != None):
			if(fd.projectName == 'Unknown'): return
			path = self.loaded_projects[ fd.projectName]['path']
		
		global ROOT_PATH
		print('loading project', path)
		ROOT_PATH = os.path.dirname(path)
		print('root path = ', ROOT_PATH)
		
		for project in self.loaded_projects.values():
			# print("comparing projects")
			# print(project['path'])
			# print(path)
			# self.core.notify(project['path'] + ' VS ' + ROOT_PATH)
			if project['path'] == path:
				# self.core.notify("Changing current project")
				self.currentProject = project
		

		
		FileSelector.ROOT_PATH = ROOT_PATH
		EntityEditorWidget.ROOT_PATH = ROOT_PATH
		
		Entity.projectChanged(ROOT_PATH)
		LevelEditorWidget.projectChanged(ROOT_PATH)
		
		self.entityEditor.projectChanged(ROOT_PATH)
		
		self.entitiesHaveBeenReloaded()
		
		self.headerWidget.toggleButtons()
		
		
		
	def loadFile(self, fd, rel=True):

		self.temp_look_folder = None

		print('\nMAIN WIDGET loading file', fd)
		#if(type(f) == str) : path = f
		path = fd.path
		if hasattr(fd, 'selectExclusive'):
			fd.selectExclusive()
		self.headerWidget.setInfo(fd)
		
		self.updateFD()
		# self.core.notify('main.loadFile', 'warning')
		# WARNING Don't think this one is necessary, done by setCurrent(fd) later (because recentBar is updated when focused change, check eventFilter in EverydayEditor)
		# self.editor.addRecentFile(fd)
		
		# New file is not level, but previous was, so we wan't stay in Level view
		if(fd.category != 'Level' and self.currentView in ('level') and fd.lines != None):
			self.setView("text")
			self.headerWidget.textAction.setChecked(True)
			
		if(fd.category != 'Entity' and self.currentView in ('anim', 'frame') and fd.lines != None):
			self.setView("text")
			self.headerWidget.textAction.setChecked(True)


		
			
		
		#if(fd.category == 'Level' and self.currentView in ('anim', 'frame')):
			#self.setView("text")
			#self.headerWidget.textAction.setChecked(True)
		   
		#if(fd.category == 'Entity' and self.currentView in ('level')):
			#self.setView("text")
			#self.headerWidget.textAction.setChecked(True)

		
		self.editor.setCurrent(fd)
		
		
		
		if self.currentView in ('anim', 'frame'):
			self.switchProjectCore(None, fd)
			self.entityEditor.loadLines(fd.lines)
		elif self.currentView == 'level':
			self.switchProjectCore(None, fd)
			# print('z', fd.z)
			self.levelEditor.loadFile(fd)
		elif self.currentView == 'JSON':
			self.JSON_editor.loadFile(fd)




	def openFile(self, path=None, defaultCategory="file"):
		
		if path is None:
			current = self.editor.current()
			
			if(self.temp_look_folder != None):
				lookFolder = self.temp_look_folder
			
			elif current is None or current.path is None:
				lookFolder = ROOT_PATH
			else:
				lookFolder = os.path.dirname(self.editor.current().path)
				
			path = QtWidgets.QFileDialog.getOpenFileName(self, directory=lookFolder)[0]
			
		
		if(path is not None and path != ''):

			fd = self.fileSelector.addFile(path)
			if fd is None:  # User chose to open another project
				return

			fd.category = defaultCategory

			self.fileSelector.setSelectedFile(fd)
			fd.loadFromDisk()

			self.loadFile(fd, False)
		
	def remove(self, fd):
		self.editor.remove(fd)

			 
	def save(self):
		self.updateFD()
		current = self.editor.current()
		if current is None:
			return
		if current.path is None and not hasattr(current, 'noteId'):
			self.saveAs()
		else:
			current.lines = self.editor.getLines()
			current.save()

			self.editor.updateSaveIcon()
			
	def saveAs(self):
		current = self.editor.current()
		if current is None or current.path is None:
			lookFolder = ROOT_PATH
		else:
			# lookFolder = os.path.dirname(self.editor.current().path)
			lookFolder = self.editor.current().path
			
		path = QtWidgets.QFileDialog.getSaveFileName(self, directory=lookFolder)[0]
		if(path is not None and path != ''):
			oldPath = current.getLongText()
			current.path = path
			self.save()
			
			
			self.fileSelector.remove(oldPath) # Old replaced
			
			

			
			fd = self.fileSelector.addFile(path)
			if fd is None:  # User chose to open another project
				return

			self.fileSelector.setSelectedFile(fd)
			fd.loadFromDisk()
			self.loadFile(fd, False)
			fd.category = current.category
			
			
			
	
	def setupFavorites(self):
		
		self.favorites = {}

		data_path = settings.get_option('general/data_path', '')
		logPath = os.path.join(os.path.dirname(data_path), 'Logs', 'OpenBorLog.txt')
		todoPath = os.path.join(data_path, 'TODO.txt')

		
		
		favorites = {'Log': logPath, 'Todo':todoPath}
		
		saved_favorites = settings.get_option('misc/shortcuts', [])
		
		
		for fav in saved_favorites:
			
			favorites[fav['key']] = fav['path']
		
		numberOfTodoShortcuts = settings.get_option('misc/number_of_todo_shortcuts', 1)
		for i in range(1, numberOfTodoShortcuts):
			todoPath = os.path.join(data_path, 'TODO' + str(i+1) + '.txt')
			favorites[str(i+1)] = todoPath
		
		for key, path in favorites.items():
			fd = File(path)
			fd.loadFromDisk(True)
			self.favorites[key] = fd

	# Favorites are opened in the regular text editor (like notes), so they share the recent bar
	def openFavorite(self, key):
		if self.currentView not in ('text', 'text|text'):
			self.setView('text')
			self.headerWidget.textAction.setChecked(True)
		self.loadFile(self.favorites[key], False)


	'''
		Change the current view
	
	'''
	def setView(self, view):
		self.updateFD()
		self.headerWidget.setInfo( self.editor.current())
		
		widgets = [self.editor, self.entityEditor, self.levelEditor, self.JSON_editor]
	
		if view == 'text':
			self.editor.setDoubleView(False)
			
			
			for w in widgets : w.hide()
			self.editor.show()
			# self.reloadSplitterPos()
			
			
		elif view == 'text|text':
			
			self.editor.setDoubleView(True)
			
			
			
			for w in widgets : w.hide()
			self.editor.show()

		elif view == 'anim':
			for w in widgets : w.hide()
			lines = self.editor.getLines()
			
			self.switchProjectCore(None, self.editor.current())
			
			
			self.entityEditor.loadLines(lines)
			
			# Load anim we were editing in text view
			lineNumber, c = self.editor.editor.cursorPosition
			while lineNumber > 0:
				pLine = ParsedLine( lines[lineNumber])
				part = pLine.nextKeyword()
				if part == 'anim':
					part = pLine.next() # the anim name : a value, keep its original case
					self.entityEditor.loadAnim(part)
					break
				lineNumber -= 1
				
			self.entityEditor.show()
			self.entityEditor.reloadSplitterPos()
			self.entityEditor.frameEditor.graphicView.centerOn(0,0)
			
			
		elif view == 'level':
			for w in widgets : w.hide()
			self.levelEditor.show()
			if(hasattr(self.editor.current(), 'z')):
				self.levelEditor.z = self.editor.current().z
			if(hasattr(self.editor.current(), 'HUD_settings')):
				self.levelEditor.HUD_settings = self.editor.current().HUD_settings
			self.switchProjectCore(None, self.editor.current())
			self.levelEditor.loadLines(self.editor.getLines())
		elif view == 'JSON':
			for w in widgets : w.hide()
			self.JSON_editor.show()
			self.JSON_editor.loadFile(self.editor.current())


			
		self.currentView = view
		

	def setTheme(self):
		import themes
		data1 = dict(themes.EDITOR_THEME.items('Editor Colors'))
		data2 = dict(themes.EDITOR_THEME.items('Default Item Styles'))
		fontColor = data2['Normal'].split(',')
		
		
		fontFamilies = {'Windows':'Courier New',
                        'Darwin': 'Menlo'}
		fontFamily = fontFamilies.get(platform.system(), 'Monospace')

		css = ["background-color:rgb(" + str( data1['Color Background']) + ")",
			"selection-background-color: rgb(" + str( data1['Color Selection']) + ")",
			"color: #" + str( fontColor[0]),
			"selection-color: #" + str( fontColor[1]),
			"font-family:" + settings.get_option("editor/font_family", fontFamily)
			]
		

		selectionColor = data1['Color Highlighted Line']
		searchColor = data1['Color Search Highlight']
		
		r, g, b = map(int, selectionColor.split(','))
		rS, gS, bS = map(int, searchColor.split(','))
		#'color:#ff839496;selection-color:#ff839496;"
		
		self.editor.themeData = {'css':css, 'searchColor':QtGui.QColor(rS, gS, bS), 'currentLine':QtGui.QColor(r, g, b)}
		
		for editor in (self.editor.getEditors() + [self.entityEditor.editor]):
			if(not settings.DISABLE_STYLE_SHEET):
				editor.setStyleSheet('QPlainTextEdit {' + ';'.join(css) + '}')
			editor.searchColor = QtGui.QColor(rS, gS, bS)
			editor.highlightColor = QtGui.QColor(r, g, b)
			editor._updateExtraSelections()
		
		
		ColorTheme.setThemeDescr(data2, dict(themes.EDITOR_THEME.items('Highlighting C - Schema ' + themes.EDITOR_THEME.name)))
		
		self.editor.updateTheme()
		self.entityEditor.updateTheme()
		
		
		
		
	# This function updates the content of file object (FD) with editor lines.
	# But also, first, if currentView is animation or level, it updates editor lines with rebuilded lines.
	# And then only, it updates the content of FD with editor lines
	
	# if the tie between current editor (self.editor.editor) is broken, then anim and level view will fill the wrong FD.
	def updateFD(self):
		# TODO update data from current editor (eg entityEditor) in main editor if view is not text
		if(self.currentView == 'anim'):
			self.editor.setLines(self.entityEditor.getFullLines())
			if self.entityEditor.currentAnim != None:
				self.editor.scrollTo(QtCore.QRegExp("anim(\\s)"+self.entityEditor.currentAnim))
		elif(self.currentView == 'level'):
			self.levelEditor.looping = False
			lines = self.levelEditor.rebuildText()
			self.editor.setLines(lines)
		elif(self.currentView == 'JSON'):
			lines = self.JSON_editor.rebuildText()
			self.editor.setLines(lines)
		self.editor.updateFD()
		


class HeaderWidget(QtWidgets.QWidget):
	
	TYPE_FIELDS = (('File', _('File')), ('Entity', _('Entity')), ('Level', _('Level')), ('Script', _('Script')))
	
	TYPE_FIELDMODEL = QtGui.QStandardItemModel()
	for key, label in TYPE_FIELDS:
		TYPE_FIELDMODEL.appendRow([QtGui.QStandardItem(key), QtGui.QStandardItem(label)])
	
	def __init__(self, parent):
		self.parent = parent
		QtWidgets.QWidget.__init__(self)
		layout = QtWidgets.QHBoxLayout()
		layout.setContentsMargins(11, 11,11,0)
		self.setLayout(layout)
		# self.setStyleSheet("QWidget { background-color:green; }");
		
		self.pic = QtGui.QIcon.fromTheme('accessories-text-editor').pixmap(32)
		self.pic = QtGui.QPixmap('icons/oxygen/accessories-text-editor.png')
		#self.pic = self.pic.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
		self.iconWidget= QtWidgets.QLabel()
		self.iconWidget.setStyleSheet("border: 1px solid black");
		self.iconWidget.setPixmap(self.pic)
		
		layout.addWidget(self.iconWidget, 0)
		
		self.fileTypeCB = QtWidgets.QComboBox()
		self.fileTypeCB.setModel(self.TYPE_FIELDMODEL)
		self.fileTypeCB.setModelColumn(1)
		self.fileTypeCB.setToolTip(_('Change file category'))
		
		self.fileTypeCB.currentIndexChanged[int].connect(self.setFileType)
		
		self.fileTypeCB.setObjectName("fileTypeCB")
		

		layout.addWidget(self.fileTypeCB)
		
		self.label = QtWidgets.QLabel('-')
		font = QtGui.QFont()
		font.setPointSize(16)
		self.label.setFont(font)

		layout.addWidget(self.label, 0)
		layout.addSpacing(100)
		
		
		#buttonGroup = QtWidgets.QButtonGroup()
		
		actionGroup = QtWidgets.QActionGroup(self)
		self.mainActionGroup = actionGroup
		self.buttonBar = QtWidgets.QToolBar()
		
		smallScreenMode = settings.get_option('gui/small_screen', False)
		if smallScreenMode:
			self.buttonBar.setStyleSheet('QToolButton#MainToolButton {  margin:0px 0px; padding: 0px 0px; }')
			labels = {'Text':'T', 'Text|Text':'T|T', 'Animation':'A', 'Scripts':'S', 'Level':'L', 'JSON':'J'}
		else:
			labels = {'Text':'Text', 'Text|Text':'Text|Text', 'Animation':'Animation', 'Scripts':'Scripts', 'Level':'Level', 'JSON':'JSON'}
		b1 = self.buttonBar.addAction(labels['Text'], lambda:self.parent.setView('text'))
		b1.setToolTip(_('Text'))
		b1bis = self.buttonBar.addAction(labels['Text|Text'], lambda:self.parent.setView('text|text'))
		b1bis.setToolTip('Text|Text')
		b2 = self.buttonBar.addAction(labels['Animation'], lambda:self.parent.setView('anim'))
		b2.setToolTip('Animation')
		#b3 = self.buttonBar.addAction('Frame', lambda:self.parent.setView('frame'))
		b4 = self.buttonBar.addAction(labels['Scripts'], lambda:self.parent.setView('scripts'))
		b4.setToolTip('Scripts')
		b5 = self.buttonBar.addAction(labels['Level'], lambda:self.parent.setView('level'))
		b5.setToolTip('Level')
		
		b6 = self.buttonBar.addAction(labels['JSON'], lambda:self.parent.setView('JSON'))
		b6.setToolTip('JSON')
		

		self.buttons = {'Level':b5, 'Scripts':b4, 'Animation':b2, 'JSON':b6}
		
		self.textAction = b1
		self.animationAction = b2
		self.levelAction = b5
	
		#b3.setCheckable(True)
		b4.setEnabled(False)
		
		
		
		font.setPointSize(12)
		for b in (b1, b1bis, b2, b4, b5, b6):
			b.setCheckable(True)
			for w in b.associatedWidgets():
				w.setObjectName( "MainToolButton" )
			#import style
			#b.setStyleSheet(style.STYLE_SHEET)
			b.setFont(font)
			actionGroup.addAction(b)
		b1.setChecked(True)
		#buttonGroup.addButton(self.buttonBar.widgetForAction(b1))
		#buttonGroup.addButton(self.buttonBar.widgetForAction(b2))
		#buttonGroup.addButton(self.buttonBar.widgetForAction(b3))
		
		
		
		layout.addWidget(self.buttonBar)
		
		
		layout.addStretch(1)
		self.quickAccessBar = QtWidgets.QToolBar()
		self.favoriteActions = []

		for key in sorted(self.parent.favorites):
			b = self.addFavoriteAction(key)
			b = self.quickAccessBar.widgetForAction(b)
			b.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
			b.customContextMenuRequested.connect(self.showFavoriteContextMenu)

		layout.addWidget(self.quickAccessBar)
		addFavButton = QtWidgets.QPushButton("+")
		layout.addWidget(addFavButton)
		addFavButton.clicked.connect(self.addFavorite)
		self.settingType = False
		
	def showFavoriteContextMenu(self, point):
		button = self.sender()
		popMenu = QtWidgets.QMenu(self)
		
		renameAction = popMenu.addAction('Rename')
		changeFileAction = popMenu.addAction('Change file')
		
		  

		r = popMenu.exec_(button.mapToGlobal(point))
		
		# TODO
		

		
	def addFavorite(self):
		key = self.parent.addFavorite()
		if (key == ''): return
		self.addFavoriteAction(key)

	# Not part of mainActionGroup : favorites are files, not views. Checked state follows the current file (see setInfo)
	def addFavoriteAction(self, key):
		b = self.quickAccessBar.addAction(key)
		b.triggered.connect(lambda checked=False, k=key: self.parent.openFavorite(k))
		b.setData(key)
		b.setCheckable(True)
		self.favoriteActions.append(b)
		return b

		
	def toggleButtons(self):
		project = self.parent.currentProject
		isOpenBOR = ('is_OpenBOR' not in project) or project['is_OpenBOR']
		self.parent.editor.genPathsAction.setVisible(isOpenBOR)
		if(isOpenBOR):
			for key in ['Animation', 'Level', 'Scripts']:
				b = self.buttons[key]
				b.setVisible(True)
			b = self.buttons['JSON']
			b.setVisible(False)
				
		else:
			for key in ['Animation', 'Level', 'Scripts']:
				b = self.buttons[key]
				b.setVisible(False)
				
# 				for w in b.associatedWidgets():
# 					
# 					if isinstance(w, QtWidgets.QToolButton):
# 						print('olea', w)
# 						w.setVisible(False)
# 						# w.hide()
			
		
		
	def setInfo(self, fd):
		self.window().setWindowTitle(settings.get_option('general/last_session', 'Default') + ': ' + fd.name + ' — CMT')
		if fd.category == 'Entity':
			self.animationAction.setEnabled(True)
		else:
			self.animationAction.setEnabled(False)
			
		if fd.category == 'Level':
			self.levelAction.setEnabled(True)
		else:
			self.levelAction.setEnabled(False)
		txt = fd.getLongText()
		if len(txt) > 20 : txt = '...' + txt[-20:]
		self.setText(txt)
		for action in self.favoriteActions:
			action.setChecked(self.parent.favorites.get(action.data()) is fd)
		if fd.iconPath is not None:
			print(fd.iconPath)
			self.pic.load(fd.iconPath)
			self.pic = self.pic.scaledToWidth(25)
			self.iconWidget.setPixmap(self.pic)
		else:
			self.iconWidget.setPixmap(QtGui.QPixmap())
			
		
		toMatch = fd.category
		pos = 0

		self.settingType = True
		while pos < len(self.TYPE_FIELDS) and not self.TYPE_FIELDS[pos][0] == toMatch :
			pos += 1
		if pos < len(self.TYPE_FIELDS) and self.TYPE_FIELDS[pos][0] == toMatch:
			self.fileTypeCB.setCurrentIndex(pos)
		self.settingType = False
			
			
	def setFileType(self, pos=None):
		if self.settingType: return
		if pos is None:
			pos = self.fileTypeCB.currentIndex()

		key = self.TYPE_FIELDS[pos][0]
		
		fd = self.parent.editor.current()
		fd.category = key
		self.setInfo(fd)
		
	def setText(self, text):
		self.label.setText(text)

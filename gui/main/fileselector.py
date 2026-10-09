import os, shutil, logging

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from guilib.treemodel import TreeModel, TreeItem, FilterModel
from operator import attrgetter

from common import settings, xdg, util
from data import ParsedLine, FileWrapper, Cache
from gui.modales import CreateFileDialog, ProjectSettingsDialog

from gui.util import FileInput, loadSprite, AccessOrderedToolbar
from gui.level.items import Entity

import hashlib

MD5_CACHE = {}


SELECTED_COLOR = [100,100,255]

class File:
	def __init__(self, path=None, projectName=None):
		if path is not None:
			self.name = os.path.basename(path)
		else:
			self.name = 'Unknown'
			
		if(projectName is not None):
			self.projectName = projectName
		else:
			self.projectName = 'Unknown'
			
		self.path = path
		self.lines = None
		self.originalLines = None
		self.saved = True
		self.iconPath = None
		self.category = 'File'
		self.state = 0
		self.isVisible = False
		self.isAddedToAView = False
		self.mtime = None
		self.charenc = None
		self.createPathIfNeeded = False
		
		
	def getLongText(self):
		if self.path is not None: return self.path
		else: return self.name
		
		
	@staticmethod
	def fromDic(dic):
		f = File(dic['path'])
		f.category = dic['category']
		f.state = dic['state']
		f.iconPath = dic['iconPath']
		if 'visible' in dic:
			f.isVisible = dic['visible']
		if 'project' in dic:
			f.projectName = dic['project']
			
		if 'versions' in dic:
			f.versions_keys = dic['versions']
			f.versions = {}
			f.version = dic['version']
		
		return f
		
		
	def __str__(self):
		dic = {'path':self.path, 'category':self.category, 'iconPath':self.iconPath, 'state':self.state, 'visible':self.isVisible, 'project':self.projectName}
		if(hasattr(self, 'versions')):
			versions = list(self.versions.keys())
			
			if(hasattr(self, 'versions_keys')):
				for key in self.versions_keys:
					if key not in versions:
						versions.append(key)
			
			dic['versions'] = versions
			dic['version'] = self.version
		
		return str(dic)
	
	
	@util.threaded
	def backupUnsaved(self):
		content = '\n'.join(self.lines)
		
		oldContent = File.DB.getLastRevision(self.path, 1)
		
		if(oldContent == content):
			#print('content is same, pass')
			return
		#print('content different, go')
		
		version = None
		if hasattr(self, 'version'):
			version = self.version
		
		
		File.DB.addBackup([self.path, content, 1, 1, version])
		
	
	def checkMTime(self):
		if(not settings.get_option('general/check_external_file_update', True)): return True
		if self.path is None or self.mtime is None:
			return True
			
		try:
			mtime = os.path.getmtime(self.path)
		except:
			return True
			
		print('comparing', self.mtime, mtime);
		if self.mtime != mtime:
			return False
		return True
		
	def updateMTime(self):
		print('updating mtime')
		self.mtime = os.path.getmtime(self.path)
	
	def checkSave(self):
		if self.originalLines == None : return
		
		
		self.prepareChange()
		
		changedDetected = False
		
		if self.originalLines != self.lines : 
			self.saved = False
			self.notifyChange()
			return
	
		# Alternative method, maybe safer
# 		i = 0
# 		
# 		while i < len(self.originalLines) and i < len(self.lines):
# 			if self.originalLines[i] != self.lines[i]:
# 				print('DIFF', self.originalLines[i], self.lines[i])
# 				self.saved = False
# 				changedDetected = True
# 				return
# 			i+=1
		if(not changedDetected): 
			print('No changed detected')
			self.saved = True # useful in case of reverse
			self.notifyChange()
			
			
		
	def isLoaded(self):
		#print('isloaded', self.path)
		#print('isLoaded', self.lines)
		if self.path is None : return True
		elif self.lines is not None : return True
		return False
		
	def loadFromDisk(self, setupIfNotExist=False):
		# print('loading from disk', self.path)
		try:
			f = FileWrapper(self.path)

			lines = f.getLines()
			self.charenc = f.charenc
			self.originalLines = list(lines)
			self.lines = lines
			self.saved = True
			self.mtime = os.path.getmtime(self.path)
			
		except FileNotFoundError:
			print('File not found', self.path)
			if setupIfNotExist:
				self.originalLines = []
				self.lines = []
				self.saved = True
		
	def notifyChange(self):
		# index = self.node.model.indexOfNode(self.node)
		# self.node.model.dataChanged.emit(index, index, [FileModel.itemRole, Qt.DecorationRole])
		if hasattr(self, "node"):
			self.node.model.layoutChanged.emit();
		
		
	def prepareChange(self):
		if hasattr(self, "node"):
			self.node.model.layoutAboutToBeChanged.emit();
		pass
		
	def save(self):
		version = None
		if hasattr(self, 'version'):
			version = self.version
		
		@util.threaded
		def saveDBBackup(path, oldContent):
			lastRevContent = File.DB.getLastRevision(path, 0)
			if(oldContent != lastRevContent):
				File.DB.addBackup([path, oldContent, 0, 1, version])
		
		@util.threaded
		def saveDBBackupCurrent(path, content):
			File.DB.addBackup([path, content, 0, 1, version])
		
		saveFolder = os.path.dirname(self.path)
		
		if(self.createPathIfNeeded and not os.path.exists(saveFolder) ):
			os.makedirs(saveFolder)
		
		fileExists = False
		if(os.path.isfile(self.path)):
			fileExists = True
			
			fileName = os.path.basename(self.path)
			
			if(not settings.get_option('general/disable_advanced_auto_backup', False)):
				if(self.originalLines != None):
					content = '\n'.join(self.originalLines)
					saveDBBackup(self.path, content)
				
				# lastRevContent = File.DB.getLastRevision(self.path, 0)
				# if(content != lastRevContent):
				# 	File.DB.addBackup([self.path, content, 0, 1])
					
			if(not settings.get_option('general/disable_auto_backup', False)):
				shutil.copyfile(self.path, os.path.join(saveFolder, '.'+fileName + '.1'))
			
		
		use_safe_write = settings.get_option('general/safe_file_write',  True)
		try_different_encoding_if_error = settings.get_option('general/change_encoding_write_error',  True)
		
		if(use_safe_write):
		
			if(self.path not in MD5_CACHE):
				MD5_CACHE[self.path] = hashlib.md5(self.path.encode('utf-8')).hexdigest()
			md5 = MD5_CACHE[self.path]
		
		
		
			# First we try to save the file in a separate copy
			pathCopy = os.path.join(saveFolder, md5)
			if(fileExists):
				shutil.copyfile(self.path, pathCopy)
			
			savePath = pathCopy
			
		else:
			savePath = self.path
			
		has_been_write_error = False
		warn_about_error = False
		
		
		# self.charenc = 'ASCII' # ONLY FOR DEBUG purposes
		
		if(self.charenc != None):
			f = open(savePath, 'w', encoding=self.charenc)
		else:
			f = open(savePath, 'w')
		content = '\n'.join(self.lines)
		
		try:
			f.write(content)
		except:
			has_been_write_error = True
			
			if(try_different_encoding_if_error):
				self.charenc = None
				f.close()
				f = open(savePath, 'w') # reopen the file without forcing any encoding
				try:
					f.write(content)
				except:
					# Last resort : the locale default used above (e.g. cp1252 on Windows) can
					# fail again on pasted characters ; utf-8 can encode any character
					self.charenc = 'utf-8'
					f.close()
					f = open(savePath, 'w', encoding='utf-8')
					try:
						f.write(content)
					except:
						warn_about_error = True
			else:
				warn_about_error = True
				
		if(warn_about_error):
			QtWidgets.QMessageBox.warning(File.connectedWidget, _('Write error'), _('Something went wrong during write process, saved canceled'))
			logging.debug('Fatal Write error : ' + savePath + ' ' + self.path)
			f.close()
			if(use_safe_write):
				os.remove(pathCopy) # Comment this if you want to keep temp MD5 file
			return # abort save; self.saved stays False so the UI still shows the file as unsaved
			
		f.close()
		
		if(use_safe_write):
			if(not has_been_write_error) : shutil.copyfile(pathCopy, self.path)
			os.remove(pathCopy) # Comment this if you want to keep temp MD5 file
		
		self.mtime = os.path.getmtime(self.path)
		
		if(not settings.get_option('general/disable_advanced_auto_backup', False)):
			saveDBBackupCurrent(self.path, content)
			
		
		self.originalLines = list(self.lines)
		self.saved = True
		
		if(hasattr(self, 'versions')): # If has versions, also save content in version model
			try:
				versionFD = self.versions[self.version]
				versionFD.lines = list(self.lines)
				versionFD.save()
			except KeyError:
				pass
		
		
	def snapshot(self, comment=None):
		version = None
		if hasattr(self, 'version'):
			version = self.version
			
		@util.threaded
		def saveDBBackupCurrent(path, content):
			File.DB.addBackup([path, content, 0, 10, version, comment])
			
		content = '\n'.join(self.lines)
		saveDBBackupCurrent(self.path, content)


class FileDB:
	"""A File-like object backed by a database note instead of a disk file."""
	_allNotes = {}

	def __init__(self, noteId, label):
		FileDB._allNotes[noteId] = self
		self.noteId = noteId
		self.name = label
		self.path = 'note://' + str(noteId)
		self.lines = None
		self.originalLines = None
		self.saved = True
		self.iconPath = None
		self.category = 'Note'
		self.state = 0
		self.isVisible = False
		self.isAddedToAView = False
		self.mtime = None
		self.charenc = None
		self.createPathIfNeeded = False
		self.projectName = '*'
		self.bgColor = None
		self.fgColor = None

	def selectExclusive(self):
		for other in FileDB._allNotes.values():
			if other is not self:
				other.state = 0
		self.state = 1

	def getLongText(self):
		return self.name

	def isLoaded(self):
		return self.lines is not None

	def loadFromDisk(self, setupIfNotExist=False):
		content = File.DB.getNoteContent(self.noteId)
		self.lines = content.split('\n') if content else ['']
		self.originalLines = list(self.lines)
		self.saved = True

	def save(self):
		content = '\n'.join(self.lines)
		File.DB.updateNote(self.noteId, content)
		self.originalLines = list(self.lines)
		self.saved = True

	def checkSave(self):
		if self.originalLines is None:
			return
		self.prepareChange()
		if self.originalLines != self.lines:
			self.saved = False
		else:
			self.saved = True
		self.notifyChange()

	def notifyChange(self):
		if hasattr(self, "node"):
			self.node.model.layoutChanged.emit()

	def prepareChange(self):
		if hasattr(self, "node"):
			self.node.model.layoutAboutToBeChanged.emit()

	def checkMTime(self):
		return True

	def updateMTime(self):
		pass

	def backupUnsaved(self):
		pass

	def snapshot(self, comment=None):
		pass


class CustomTreeView( QtWidgets.QTreeView):


	def drawBranches(self, painter, rect, index):
		
		item = self.model().data(index, FileModel.itemRole)
		try:
			if(item.fd.state == 1):
				painter.fillRect(rect, QtGui.QColor(*SELECTED_COLOR));
		except:
			pass
		# else
		# painter->fillRect(rect, Qt::green);

		QtWidgets.QTreeView.drawBranches(self, painter, rect, index)

class FileSelector(QtWidgets.QWidget):
	
	ROOT_PATH = '/home/piccolo/workspace/OpenBOR/'
	
	def __init__(self, parent):
		self.mainEditor = parent
		
		self.load_session_based_on_loaded_projects = False
		
		File.connectedWidget = parent
		QtWidgets.QWidget.__init__(self)
		
		trueLayout = QtWidgets.QHBoxLayout()
		trueLayout.setContentsMargins(0, 0, 0, 0)
		
		w = QtWidgets.QWidget()
		tabBar = QtWidgets.QTabBar()
		tabBar.setShape(QtWidgets.QTabBar.RoundedWest)
		
		self.tabs = ['Entities', 'Levels', 'Scripts', 'System']
		for label in self.tabs:
			tabBar.addTab(_(label))
		tabBar.currentChanged.connect(self.setLibraryMode)
		
		wrapperLayout = QtWidgets.QHBoxLayout()
		layout = QtWidgets.QVBoxLayout()
		w.setLayout(wrapperLayout)
		
		wrapperLayout.addWidget(tabBar)
		wrapperLayout.addLayout(layout)
		wrapperLayout.setContentsMargins(0, 0, 0, 0)
		wrapperLayout.setSpacing(0)
		layout.setContentsMargins(0, 0, 0, 0)
		
		# self.setStyleSheet('background:red;')
		
		txt = _('FILE SELECTOR')
		txt = '\n'.join(txt)
		label = QtWidgets.QLabel(txt)
		trueLayout.addStretch()
		trueLayout.addWidget(label)
		trueLayout.addWidget(w, 1)
		trueLayout.addStretch()
		
		self.cacheLabel = label
		self.cacheLabel.hide()
		self.content = w
		self.setLayout(trueLayout)
		
		
		self.sessions_content = {}
		
		
		w = QtWidgets.QWidget()
		l = QtWidgets.QHBoxLayout()
		
		w.setLayout(l)
		
		
		# w.setStyleSheet('background : blue;')
		
		self.projectFilterBar = w
		
		self.projectButtonBar = AccessOrderedToolbar(self)
		self.projectButtonBar.automaticRecentFirst = True
		self.projectButtonBar.changed.connect(self.loadSubSession)
		
		self.projectButtonBar.setStyleSheet("QToolBar { margin:0px 0px;} QToolButton { padding: 2px; margin:0px 2px; }  QToolButton::on {padding : 10px;  }");
		
		self.projectButtonBar.showItemContextMenuExternal = self.showProjectContextMenu
		
		
		l.addWidget(self.projectButtonBar, 1)
		
		addIcon = QtGui.QIcon.fromTheme('list-add')
		addAnim = QtWidgets.QPushButton(addIcon, '')
		addAnim.clicked.connect(self.openProject)
		addAnim.setToolTip(_('Load another project'))
		l.addWidget(addAnim, 0)
		
		
		# layout.addWidget(w, 0)
		
		actionGroup = QtWidgets.QActionGroup(self)
		self.buttonBar = QtWidgets.QToolBar()
		
		theme = settings.get_option('gui/widgets_theme', None)
		
		openIcon = QtGui.QImage('icons/folder.png')
		if(theme == "Dark"): openIcon.invertPixels()
		openIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(openIcon))
		# openIcon = QtGui.QIcon(QtGui.QPixmap('icons/folder.png'))
		b1 = self.buttonBar.addAction(openIcon, _('Open file'), self.mainEditor.openFile)
		addIcon = QtGui.QIcon.fromTheme('list-add')
		addAnim = self.buttonBar.addAction(addIcon, _('Create file'), self.createFile)
		self.buttonBar.addSeparator()
		self.buttonBar.addSeparator()
		self.buttonBar.addSeparator()
		
		libraryIcon = QtGui.QImage('icons/library.png')
		if(theme == "Dark"): libraryIcon.invertPixels()
		libraryIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(libraryIcon))
		
		filesIcon = QtGui.QImage('icons/box.png')
		if(theme == "Dark"): filesIcon.invertPixels()
		filesIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(filesIcon))
		

		b1 = self.buttonBar.addAction(libraryIcon, 'Library', lambda:self.setMode('library'))
		b1bis = self.buttonBar.addAction(filesIcon, 'Opened', lambda:self.setMode('opened'))

		notesIcon = QtGui.QImage('icons/note.svg')
		if(theme == "Dark"): notesIcon.invertPixels()
		notesIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(notesIcon))
		b1notes = self.buttonBar.addAction(notesIcon, 'Notes', lambda:self.setMode('notes'))

		b1.setCheckable(True)
		b1bis.setCheckable(True)
		b1notes.setCheckable(True)

		b1.setChecked(True)

		self.libraryButton = b1
		self.openedButton = b1bis
		self.notesButton = b1notes
		
		self.buttonBar.addSeparator()
		self.buttonBar.addSeparator()
		self.buttonBar.addSeparator()
		expandIcon = QtGui.QImage('icons/expand.png')
		if(theme == "Dark"): expandIcon.invertPixels()
		expandIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(expandIcon))
		
		collapseIcon = QtGui.QImage('icons/collapse.png')
		if(theme == "Dark"): collapseIcon.invertPixels()
		collapseIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(collapseIcon))
		
		self.collapseAllButton = self.buttonBar.addAction(collapseIcon, 'Collapse All', self.collapseAll)
		self.expandAllButton = self.buttonBar.addAction(expandIcon, 'Expand All', self.expandAll)
		
		reloadIcon = QtGui.QImage('icons/reload.svg')
		if(theme == "Dark"): reloadIcon.invertPixels()
		reloadIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(reloadIcon))
		self.buttonBar.addAction(reloadIcon, 'Reload',  lambda:self.loadLibrary(True))
		
		actionGroup.addAction(b1)
		actionGroup.addAction(b1bis)
		actionGroup.addAction(b1notes)
		
		
		layout.addWidget(self.buttonBar, 0)

		self.currentFilter = ''
		
		
		self.treeView = CustomTreeView(self)
		self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.treeView.customContextMenuRequested.connect(self.showContextMenu)
		self.treeView.expanded.connect(self.expandChange)
		self.treeView.collapsed.connect(self.expandChange)
		
		
		self.libraryModels = {}
		for key in ('Entities', 'Levels', 'Scripts', 'System'):
			model = FileModel()
			model.isFilled = False
			self.libraryModels[key] = model

		self.openedModel = FileModel()
		self.notesModel = FileModel()
		self.treeView.setSortingEnabled(True)
		
		self.treeView.setAnimated(True)
		
		
		
		
		
		
		
		
		searchButton = QtWidgets.QPushButton()
		
		searchIcon = QtGui.QImage('icons/search.svg')
		if(theme == "Dark"): searchIcon.invertPixels()
		searchIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(searchIcon))
		
		##searchButton.setIcon(QtGui.QIcon.fromTheme('search'))
		searchButton.setIcon(searchIcon)
		searchButton.clicked.connect(self.search)
		
		self.searchEntry = QtWidgets.QLineEdit()
		self.searchEntry.setPlaceholderText(_('Search (press F2 to focus)'))
		self.searchEntry.installEventFilter(self)
		
		if settings.get_option('misc/search_on_text_change', True):
			self.searchKeyDebounce = QtCore.QTimer()
			self.searchKeyDebounce.setInterval(250)
			self.searchKeyDebounce.setSingleShot(True)
			self.searchKeyDebounce.timeout.connect(self.search)
			
			self.searchEntry.textChanged.connect(self.searchKeyDebounce.start)
		
		hboxSearch = QtWidgets.QHBoxLayout()
		hboxSearch.setContentsMargins(0, 5, 0, 5)
		w = QtWidgets.QWidget()
		w.setLayout(hboxSearch)
		
		
		
		hboxSearch.addWidget(self.searchEntry, 1)
		hboxSearch.addWidget(searchButton)

		# "Search in project" hint label (shown when no results in opened files)
		self.searchInProjectHint = QtWidgets.QLabel()
		self.searchInProjectHint.setWordWrap(True)
		self.searchInProjectHint.setCursor(QtCore.Qt.PointingHandCursor)
		self.searchInProjectHint.setStyleSheet("QLabel { padding: 6px; color: palette(link); } QLabel:hover { text-decoration: underline; }")
		self.searchInProjectHint.hide()
		self.searchInProjectHint.mousePressEvent = lambda e: self.searchInProject()
		self._projectSearchTimer = None
		self._projectSearchMode = False
		self.projectSearchModel = FileModel()


		if settings.get_option('gui/file_selector_search_bottom', False):
			layout.addWidget(self.treeView, 1)
			layout.addWidget(self.searchInProjectHint, 0)
			layout.addWidget(w, 0)

		else:
			layout.addWidget(w, 0)
			layout.addWidget(self.searchInProjectHint, 0)
			layout.addWidget(self.treeView, 1)
			
		
		
			
		
		
		self.filterModel = FilterModel()
		self.filterModel.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.filterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

		self.filterModel.setSourceModel(self.libraryModels['Entities'])
		
		self.treeView.setModel(self.filterModel)
		self.filterModel.sort(0)
		#self.treeView.setModel(self.model)
	
		self.treeView.activated.connect(self.loadItem)
		if not settings.get_option('gui/double_click_to_load_element', False):
			self.treeView.clicked.connect(self.loadItem)
		self.treeView.mouseReleaseEvent = self.mouseReleaseEvent
		
		header = self.treeView.header()
		header.setStretchLastSection(False)
		#header.setDefaultSectionSize(60)
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
		
		

		
		
		self.timeLine = QtCore.QTimeLine(400, self);
		self.timeLine.setUpdateInterval(20)
		
		#connect(timeLine, SIGNAL(frameChanged(int)), progressBar, SLOT(setValue(int)));
		self.timeLine.frameChanged.connect(self.tmp)
		
		self.loadedFiles = {}
		self.loadedPaths = []
		self.expandedFolders = set() # WARNING DEPRECATED?
		self.folderNodes = {'':None}
		
		self.openedItem = None
		# print(self.metaObject().className())
		self.setObjectName( "FileSelector" )
		
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("F2", "Edit|Search")), self, self.focusForSearch)
		
		self.mode = 'library'
		self.libraryMode = 'Entities'
		self.sessionName = None
		self.isSavingSession = False
		self.lastSaveTime = 0
		self.lastSaveName = None
		
		self.PROJECTS_VARS = {}
		
		
	

	def projectChanged(self, projectRoot=None, updateProjectBar=True):
		
		
		
		
		if(projectRoot in self.PROJECTS_VARS):
			vars = self.PROJECTS_VARS[projectRoot]
			
			self.libraryModels = vars['libraryModels']
			
		else:
			
		
			
			self.libraryModels = {}
			for key in ('Entities', 'Levels', 'Scripts', 'System'):
				model = FileModel()
				model.isFilled = False
				self.libraryModels[key] = model
			
			
			vars = {}
			
			vars['libraryModels'] = self.libraryModels
			
			
			self.PROJECTS_VARS[projectRoot] = vars
			
		# self.reloadProjectBar()
		
		if updateProjectBar:
			self.projectButtonBar.addItem(self.mainEditor.currentProject)
			self.projectButtonBar.addItem({'path':'*', 'name':'*', 'font_color':None, 'background_color':None})
			
			if('is_OpenBOR' in self.mainEditor.currentProject and not self.mainEditor.currentProject['is_OpenBOR']):
				self.libraryButton.setVisible(False)
			else:
				self.libraryButton.setVisible(True)
	
	
	
	def showProjectContextMenu(self, point, button, item):
		if item.name == '*':
			return
		popMenu = QtWidgets.QMenu(self)

		projectSettings = popMenu.addAction(_('Settings'))
		popMenu.addSeparator()
		close = popMenu.addAction(_('Close'))

		r = popMenu.exec_(button.mapToGlobal(point))

		if(r == close):
			self.closeProject(item.name, item)
		elif(r == projectSettings):
			self.showProjectSettings(item)
			
			
	def closeProject(self, projectName, projectItem):
		self.projectButtonBar.removeItem(projectItem)

	def showProjectSettings(self, item):
		projectName = item.name
		projectPath = item.path
		dialog = ProjectSettingsDialog(projectName, projectPath)
		dialog.exec_()

	def switchProjectFilter(self):
		if(len (self.mainEditor.loaded_projects) > 1):
			for key in self.mainEditor.loaded_projects:
				if(key == self.projectButtonBar.getCurrent().name):
					continue
				else:
					self.projectButtonBar.toggleItem(self.mainEditor.loaded_projects[key])
					return
	
	def openProject(self):
		self.mainEditor.core.setMode('project')
	
	def reloadProjectBar(self):
		
		b = self.projectButtonBar.addAction('*', self.loadSubSession)
		b.setData('*')
		b.setCheckable(True)
		actionGroup.addAction(b)
		
		
		
		
		b = self.projectButtonBar.addAction('current', self.loadSubSession)
		b.setData('current')
		b.setCheckable(True)
		actionGroup.addAction(b)
		
		
		for k in self.mainEditor.loaded_projects:
			
			b = self.projectButtonBar.addAction(k, self.loadSubSession)
			b.setData(k)
			b.setCheckable(True)
			actionGroup.addAction(b)
			
	

		
		
	def addFile(self, path, iconPath=None):
		if path == 'New':
			#self.setMode('opened')
			if path in self.loadedPaths:
				i = 2
				path = 'New ' + str(i)
				while path in self.loadedPaths:
					i+=1
					path = 'New ' + str(i)
			
			
		
		
		#if self.openedItem != None:
			#self.openedItem.state = 0
		
		if path not in self.loadedPaths:
			# First we try to match the root with an opened project
			project = None
			for key in self.mainEditor.loaded_projects:
				p = self.mainEditor.loaded_projects[key]

				if(p['path'] in path): # root path of project is in file path
					project = key

					currentProjectFilter = self.projectButtonBar.getCurrent().name
					if(currentProjectFilter != project and currentProjectFilter != '*'):
						self.projectButtonBar.toggleItem(p)
			# 	similarityPath = 0
			# 	i = 0
			# 	while(i < len(p.path) and i < len(path)):
			# 		if p.path[i] == path[i]:
			# 		similarityPath += 1

			if(project is None): # If not default's to currently selected project, or last project opened if no project filtered
				# Check if file matches an unloaded project
				all_projects = settings.get_option('general/projects', [])
				matching_project = None
				for p in all_projects:
					if p['path'] in path:
						matching_project = p
						break

				if matching_project is not None:
					# Found a matching unloaded project, load it and open the file
					self.mainEditor.pending_file_to_open = path
					self.mainEditor.core.projectSelector.loadProject(matching_project)
					return None

				# No matching project found, ask user if they want to open a different project
				reply = QtWidgets.QMessageBox.question(
					self,
					_('Project mismatch'),
					_("The file you are trying to open doesn't match the path of any project.\n\nDo you want to open another project?"),
					QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
					QtWidgets.QMessageBox.No
				)
				if reply == QtWidgets.QMessageBox.Yes:
					self.mainEditor.pending_file_to_open = path
					self.mainEditor.core.setMode('project')
					return None

				project = self.projectButtonBar.getCurrent().name
				if(project == '*'):
					project = self.mainEditor.currentProject['name']
			
			fd = File(path, project)
			self.loadedPaths.append(path)
			self.loadedFiles[path] = fd
			# print('APPENDING', path)
			fd.state = 1
			if path.startswith('New'): fd.path = None
			# self.reloadFilesModel()
			
			self.reloadFilesModel_pre();
			
			
			self.makeSureVisible(fd)
		fd = self.loadedFiles[path]

		return fd
	
	'''
		Open a file from library model
	'''
	def addFromLibrary(self, fd):
		print('\n Opening file from Library...')
		if fd.path not in self.loadedPaths:
			print('was not loaded')
			self.loadedPaths.append(fd.path)
			self.loadedFiles[fd.path] = fd
			fd.state = 1
			
			
			self.reloadFilesModel()
			self.makeSureVisible(fd)
			
			
	def createFile(self):
		if self.mode == 'notes':
			self.createNote()
			return
		d = CreateFileDialog()
		if d.exec() == 1:
			print(d.filePath, d.category)
			self.mainEditor.openFile(d.filePath, d.category)
			# print('know xxx ' + d.filePath)
			


	def createNote(self):
		from datetime import date
		defaultLabel = date.today().strftime('%Y-%m-%d')
		label, ok = QtWidgets.QInputDialog.getText(self, _('New note'), _('Label:'), QtWidgets.QLineEdit.Normal, defaultLabel)
		if ok and label:
			noteId = File.DB.createNote(label)
			self.loadNotes()
			fd = self._noteFDs[noteId]
			fd.loadFromDisk()
			fd.selectExclusive()
			self.mainEditor.loadFile(fd, False)

	def loadNotes(self):
		self.notesModel.reset()
		if not hasattr(self, '_noteFDs'):
			self._noteFDs = {}
		rows = File.DB.getAllNotes()
		for i, row in enumerate(rows):
			noteId = row['ID']
			if noteId in self._noteFDs:
				fd = self._noteFDs[noteId]
			else:
				fd = FileDB(noteId, row['label'])
				self._noteFDs[noteId] = fd
			noteItem = Item(self.notesModel.rootItem, [noteId, row['label'], i, None, None, fd], self.notesModel)
			self.notesModel.rootItem.append(noteItem)
		self.notesModel.layoutChanged.emit()
		self.filterModel.sort(-1)

	def collapseAll(self, button=None, parentIndex=QtCore.QModelIndex()):
		self.treeView.collapseAll()
		# for i in range(self.filterModel.rowCount(parentIndex)):
		# 	index = self.filterModel.index(i, 0, parentIndex)
		# 	item = index.data(FileModel.itemRole)
		# 	# print(i, item.isExpanded)
		# 	# if item.isExpandedWithoutFilter:
		# 	self.treeView.setExpanded(index, False)
		# 	self.collapseAll(parentIndex=index)
	
	

	
	def expandAll(self, button=None, parentIndex=QtCore.QModelIndex()):
		self.treeView.expandAll()
		# for i in range(self.filterModel.rowCount(parentIndex)):
		# 	index = self.filterModel.index(i, 0, parentIndex)
		# 	item = index.data(FileModel.itemRole)
		# 	# print(i, item.isExpanded)
		# 	# if item.isExpandedWithoutFilter:
		# 	self.treeView.setExpanded(index, True)
		# 	self.expandAll(parentIndex=index)
	
	def focusForSearch(self):
		self.enterEvent(None)
		if self.searchEntry.hasFocus() and (not 'is_OpenBOR' in self.mainEditor.currentProject or self.mainEditor.currentProject['is_OpenBOR'] == True):
			if self.mode == 'opened':
				self.setMode('library')
			else:
				self.setMode('opened')
		self.searchEntry.setFocus()
		self.searchEntry.selectAll()
	
	'''
		Make sure associated node is visible in treeView
	'''
	def makeSureVisible(self, fd):
		node = fd.node
		print('Making sure ', node.label, ' is visible')
		while node != None:
			node.isExpanded = True
			node = node.parent()
		self.restoreExpandedState()
		
		
	def hydrateProjectSessionFiles(self, project):
		if self.load_session_based_on_loaded_projects:
			if(project['name'] in self.excluded_session_files):
				for dic in self.excluded_session_files[project['name']]:
					path = dic['path']
					self.loadedFiles[path] = File.fromDic(dic)
					self.loadedPaths.append(path)
				del self.excluded_session_files[project['name']]
				
				expandedFolders = self.expandedFolders_fromSession.copy()
				
				for fd in self.folderNodes.values():
					if fd is not None and fd.isExpanded:
						expandedFolders.append(fd.path)
				
				self.reloadFilesModel_pre(expandedFolders)
					
			
			
	def loadSession(self, name):
		
		reaffect_unknown_project = -1
		
		self.load_session_based_on_loaded_projects = True
		
		self.excluded_session_files = {}
		
		print("loading session", name)
		path = os.path.join(xdg.get_data_home(), 'sessions') + os.sep + name
		#if not os.path.exists(path) : return
		self.loadedPaths = []
		self.loadedFiles = {}
		expandedFolders = []
		if name != '' and os.path.exists(path):
			self.sessionName = name
			f = open(path, 'r')
			lines = f.read().split('\n')
			section = 0
			
			if lines[0] != '':
				for line in lines:
					if line == '': section+=1
					
					elif section == 0: # List of files
						dicStr = line
						if dicStr == '': continue
						#import ast
						dic = eval(dicStr)
						path = dic['path']
						if os.path.exists(path):
							if('project' in dic and dic['project'] == 'Unknown'):
								
								if(reaffect_unknown_project == -1):
									if(QtWidgets.QMessageBox.question(self, _('File with Unknown project'), _('Some files in this session have unknown projects. Would you like to set them to the current project ("Yes") or keep unknown ("No") ?'), defaultButton=QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes):
										reaffect_unknown_project = 1
									else:
										reaffect_unknown_project = -1
								if(reaffect_unknown_project == 1):
									dic['project'] = self.mainEditor.currentProject['name']
								
							if(self.load_session_based_on_loaded_projects and 'project' in dic and dic['project'] not in self.mainEditor.loaded_projects):
								if( dic['project'] not in self.excluded_session_files):
									self.excluded_session_files[dic['project']] = []
								self.excluded_session_files[dic['project']].append(dic)
								continue
								
							self.loadedFiles[path] = File.fromDic(dic)
							self.loadedPaths.append(path)
						
					elif section  == 1: # Expanded folders
						# pass
						expandedFolders.append(line)
		else:
			self.sessionName = None
			fd = self.addFile('New')
			self.mainEditor.editor.setCurrent(fd)
			
		self.expandedFolders_fromSession = expandedFolders
		self.reloadFilesModel_pre(expandedFolders, True)

		

			

	def loadSubSession(self, data=None):
		# self.mainEditor.core.notify('Load sub', 'warning')
		if(data is not None):
			projectID = data.name
			# self.projectButtonBar.addItem(data)
		else:
			projectID =self.sender().data()
			
		
		
		
		if(projectID != '*'):
			p = self.mainEditor.loaded_projects[projectID]
			# print('TARATATA', projectID, self.mainEditor.loaded_projects[projectID])
			self.mainEditor.temp_look_folder = p['path']
			
			
			if('is_OpenBOR' not in p or p['is_OpenBOR']):
				self.mainEditor.switchProjectCore(p['path'])
				self.projectChanged(os.path.dirname( p['path'] ), False)
			
				# self.setMode('library')
				self.loadLibrary(False)

		
		txt =self.currentFilter
		
		if(projectID == 'current'):
			projectID = self.mainEditor.currentProject['name'];
			
			
		self.saveExpandedStateWithoutFilters()
		
		# FILTER MODE
		self.treeView.model().setProjectFilter(projectID)
		self.treeView.model().setFilterRole(Qt.DisplayRole)
		regExp = QtCore.QRegExp(txt, QtCore.Qt.CaseInsensitive)
		self.treeView.model().setFilterRegExp(regExp)
		
		# if(txt == '' and projectID == '*'):
		if(txt == ''):
			self.restoreExpandedStateWithoutFilters()
		else:
			self.restoreExpandedState() # not really a restoring but a matching of visual expanding with expanded state in data
		
		# LOAD MODE
		# self.reloadFilesModel([], False, projectID)
		
		
	def tmp(self, val):
		self.mainEditor.splitter.setSizes([val, self.mainEditor.rect().width()])
		
	
	'''
		Append data to model (creating a node)
	'''
	def append(self, dataTuple, parentNode=None, model=None):
		# print(dataTuple, parentNode)
		if(model is None):
			model = self.libraryModels[self.libraryMode]
			#model = self.treeView.model()
		if(parentNode == None):
			parentNode = model.rootItem
			index = QtCore.QModelIndex() #self.model.createIndex(0,0)
			#index = self.treeView.rootIndex()
		else:
			index = parentNode.index
			#if(parentNode.isExpanded):
				#print('OOOOOUI', parentNode.isExpanded)
			#self.treeView.setExpanded(index, True)
		#print('APPEND', index.isValid())
		item = model.append(parentNode, Item(parentNode, dataTuple, model), index)
		if(parentNode == None): model.modelReset.emit()
		return item
	
	'''
		Append an (existing) node to model
	'''
	def appendNode(self, node, parentNode=None, model=None):
		if(model is None):
			model = self.libraryModels[self.libraryMode]
		if(parentNode == None):
			parentNode = model.rootItem
			index = QtCore.QModelIndex()
		else:
			index = parentNode.index
		node.parentItem = parentNode # Important
		model.append(parentNode, node, index)
		
	
	def close(self, closeAll=False):
		self.mainEditor.updateFD() # Important if we are to delete a file that we are currently editing
		if closeAll:
			# Check unsaved notes
			if hasattr(self, '_noteFDs'):
				unsavedNotes = [fd for fd in self._noteFDs.values() if not fd.saved]
				if len(unsavedNotes) > 0:
					d = UnsavedFileDialog(unsavedNotes)
					if d.exec() == 0:
						return False
			self.saveSession()
			res = self.closeFolder('')
			self.reloadFilesModel()

		else:
			res = self.closeFile()
			self.reloadFilesModel_pre()
		return res
		
		
	def closeFile(self, fd=None):
		if fd is None:
			if(self.mainEditor.currentView in ['anim', 'level']):
				self.mainEditor.setView('text')
				
			fd = self.mainEditor.editor.current()
			print('\nDELETE', fd)
		if not fd.saved:
			d = UnsavedFileDialog([fd])
			if d.exec() == 0:
				return False
				
		
		print(fd.getLongText())
		self.remove(fd.getLongText())
		
		
		return True
		
	def closeFolder(self, folder):
		if(self.mainEditor.currentView in ['anim', 'level']):
			self.mainEditor.setView('text')
		unsavedfiles = []
		pathsToClose = []
		for path in self.loadedPaths:
			if folder in path:
				pathsToClose.append(path)
				fd = self.loadedFiles[path]
				if not fd.saved:
					unsavedfiles.append(fd)
		if len(unsavedfiles) > 0:
			d = UnsavedFileDialog(unsavedfiles)
			if d.exec() == 0:
				return False
		for path in pathsToClose:
			self.remove(path)
			
		return True
		
	
	def deleteItem(self, index):
		item = index.data(FileModel.itemRole)
		self.mainEditor.updateFD() # Important if we are to delete a file that we are currently editing
		
		itemPath = item.path
		if itemPath is None:
			return
	
		print('ISDIR',os.path.isdir(itemPath))
		if os.path.isdir(itemPath): # If folder then be sure to remove subfiles
			if not self.closeFolder(itemPath) : return
		else:
			if item.fd != None:
				fd = item.fd
			if not self.closeFile(fd): return
			
		self.reloadFilesModel()
	
	def expandChange(self, index):
		# print('expand change', self.treeView.isExpanded(index))
		self.treeView.model().setData(index, self.treeView.isExpanded(index), FileModel.expandedRole)
		#if self.mode == 'opened': # DEPRECATED ?
			#item = index.data(FileModel.itemRole)
			#if item.path is not None and os.path.isdir(item.path):
				#if self.treeView.isExpanded(index):
					#self.expandedFolders.add(item.path)
				#else:
					#self.expandedFolders.remove(item.path)
		
		
	def enterEvent(self, e):
		if self.content.isVisible() and not settings.get_option('gui/auto_collapse', True) : return # Do not expand if already expanded
		self.treeView.update()
		self.timeLine.stop()
		self.content.show()
		self.cacheLabel.hide()
		self.timeLine.setFrameRange(self.mainEditor.splitter.sizes()[0], 300);
		self.timeLine.start()
		##self.mainEditor.splitter.setSizes([300, self.mainEditor.rect().width()])
		#b = QtCore.QByteArray()
		#b.append("sizes")
		#self.animate = QtCore.QPropertyAnimation(self.mainEditor.splitter, b)
		### Nous rentrons le délai de l'animation en ms
		#self.animate.setDuration(800)
		### Nous indiquons les propriétés de départ
		#self.animate.setStartValue([300,600])
		### Puis les propriétés de fin
		#self.animate.setEndValue([100,600])
		### Et enfin nous démarrons l'animation
		#self.animate.start()
		
		
	def backupUnsaved(self, folder=''):
		if(settings.get_option('general/disable_advanced_auto_backup', False)):
			return
		
		self.mainEditor.updateFD() # Important if we are to delete a file that we are currently editing
		
		
		for path in self.loadedPaths:
			if folder in path:
				
				fd = self.loadedFiles[path]
				if not fd.saved:
					fd.backupUnsaved()
		
		
	def leaveEvent(self, e):
		if self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())):
			return
		
		if not settings.get_option('gui/auto_collapse', True) : return
		self.cacheLabel.show()
		self.content.hide()
		self.timeLine.stop()
		self.timeLine.setFrameRange(self.mainEditor.splitter.sizes()[0], 100);
		self.timeLine.start()
		#self.mainEditor.splitter.setSizes([100, self.mainEditor.rect().width()])
	
	
	'''
		Load library (default to entities library)
	'''
	def loadLibrary(self, reset=False):
		data = []
		model = self.libraryModels[self.libraryMode]
		
		
		
		if(self.mode == 'library'):
			self.filterModel.setSourceModel(model)
		if reset:
			# clear all caches
			ent_cache = Cache('entities_data', FileSelector.ROOT_PATH)
			ent_cache.clear()
			

			self.mainEditor.clearCache()
			
			
		
		
			model.reset()
			#for model_to_reset in self.libraryModels.values():
				#model_to_reset.reset()
			
		if model.isFilled and not reset:
			return
			
		
		
		currentProjectFilter = self.projectButtonBar.getCurrent()
		if(currentProjectFilter.name != "*"):
			currentProjectName = currentProjectFilter.name
		else:
			currentProjectName = self.mainEditor.currentProject['name']
		
		if self.libraryMode == 'Entities':
			
			
			
			path = os.path.join(FileSelector.ROOT_PATH, 'data', 'models.txt')
			print(path)
			if not os.path.isfile(path):
				print('WARNING : no models.txt')
				return
				
			
			ent_cache = Cache('entities_data', FileSelector.ROOT_PATH)
			
			Entity.AVAILABLE_MODELS.clear()
			
			
			f = FileWrapper(path)
			lines = f.getLines()
			
			loadEntData = True
			
			
			print("\nLoading entities...")
			# print(len(lines))
			# print(ent_cache.fullID)
			
			for i, line in enumerate(lines):
				pLine = ParsedLine(line)
				part = pLine.next()
				if part is None : continue
				if part.lower() == 'know' or part.lower() == 'load':
					# print(pLine.line, pLine.getNumberOfParts())
					if(pLine.getNumberOfParts() < 3) :
						logging.debug('Incomplete line : ' + pLine.line)
					else:
						name = pLine.next().lower()
						Entity.AVAILABLE_MODELS.append(name)
						path = pLine.next()
						
						# if os.path.sep == '\\':
						# 	path = path.replace('/', '\\')
						
						
						type = 'none'
						icon = None
						
						
						
						if loadEntData:
							if name in ent_cache.data :
								ent_data = ent_cache.data[name]
								type = ent_data['type']
								icon = ent_data['icon']
							else :
						
								# fullPath = os.path.join(FileSelector.ROOT_PATH, path)
								fullPath = FileSelector.ROOT_PATH + '/' + path
								if not os.path.exists(fullPath) : continue
								# print(fullPath)
								f = FileWrapper(fullPath)
								lines2 = f.getLines()
								
								
								for i, line2 in enumerate(lines2):
									pLine2 = ParsedLine(line2)
									part = pLine2.nextKeyword()
									if part == 'type':
										type = pLine2.next().lower()
									if part == 'icon':
										icon = pLine2.next()
										
									if i > 100:
										break
										
								ent_cache.data[name] = {'type':type, 'icon':icon}
						
						#print(name, type)
						currentData = {'pos':i, 'label':name, 'path':path, 'type':type, 'icon':icon}
						data.append(currentData)
				
			categories = ['player', 'enemy', 'npc', 'obstacle', 'panel', 'none', 'text', 'endlevel', 'trap', 'item', 'steamer', 'unknown']
			categorieNodes = {}
			for i, c in enumerate(categories):
				node = self.append([c, c, i, None, 'icons/' + c +'.png', None])
				node.showCount = True # display the number of entities of this type
				categorieNodes[c] = node
				
				
			for i, d in enumerate(data):
				#print(d)
				#if d['type'] != 'player':
					#pass
				# path = os.path.join(FileSelector.ROOT_PATH, d['path'])
				path = FileSelector.ROOT_PATH + '/' + d['path']
				fd = File(path)
				if d['icon'] is not None:
					iconPath = os.path.join(FileSelector.ROOT_PATH, d['icon'])
					d['icon'] = iconPath
					fd.iconPath = iconPath
				fd.category = 'Entity'
				fd.projectName = currentProjectName
				if d['type'] in categorieNodes : parentNode = categorieNodes[d['type']]
				else : parentNode = categorieNodes['unknown']
				#parentNode = categorieNodes['unknown']
				self.append((d['label'], d['label'], i, path, d['icon'], fd), parentNode)
			
			self.libraryModels[self.libraryMode].modelReset.emit()
			
			# update cache
			ent_cache.save()
			self.mainEditor.entitiesHaveBeenReloaded()
			
				
		elif self.libraryMode == 'Levels':
			path = os.path.join(FileSelector.ROOT_PATH, 'data', 'levels.txt')
			if not os.path.isfile(path): return
			f = FileWrapper(path)
			lines = f.getLines()
			
			levelsAlreadyAdded = []
			# levels declared before any "z" line still need usable bounds
			z = {'xMin':160, 'xMax':232, 'BGHeight':160}
			HUD_settings = {'lbarsize':{'width':100, 'height':5}}
			
			for i, line in enumerate(lines):
				pLine = ParsedLine(line)
				part = pLine.next()
				if part is None : continue
				if part.lower() == 'set':
					levelsAlreadyAdded = [] # reset every set
					name = pLine.next()
					parentNode = self.append((name, name, i, None, None, None), None)
					#print(name)
					
				elif part.lower() == 'z':
					xMin = 160
					xMax = 232
					BGHeight = 160
					
					val = pLine.next()
					if(val != None):
						xMin = val
						
					val = pLine.next()
					if(val != None):
						xMax = val
						
					val = pLine.next()
					if(val != None):
						BGHeight = val
						
					z = {'xMin':xMin, 'xMax':xMax, 'BGHeight':BGHeight}
					
					
					
				elif part.lower() == 'file':
					path = pLine.next()
					if(path in levelsAlreadyAdded): continue
					levelsAlreadyAdded.append(path)
					# path = os.path.join(FileSelector.ROOT_PATH, path)
					path = FileSelector.ROOT_PATH + '/' + path
					fd = File(path)
					fd.category = 'Level'
					fd.projectName = currentProjectName
					#print('z', z)
					fd.z = z
					fd.HUD_settings = HUD_settings
					self.append((os.path.basename(path), os.path.basename(path), i, path, None, fd), parentNode)
					
				elif part.lower() == 'lbarsize':
					width = int(pLine.next())
					height = int(pLine.next())
					HUD_settings['lbarsize'] = {'width':width, 'height':height}
				elif part.lower() in ['p1life', 'p2life', 'p3life', 'p4life'] :
					x = int(pLine.next())
					y = int(pLine.next())
					HUD_settings[part.lower()] = {'x':x, 'y':y}
				elif part.lower() in ['p1namej', 'p2namej', 'p3namej', 'p4namej'] :
					x = int(pLine.next())
					y = int(pLine.next())
					HUD_settings[part.lower()] = {'x1':x, 'y1':y}
				elif part.lower() in ['p1icon', 'p2icon', 'p3icon', 'p4icon'] :
					x = int(pLine.next())
					y = int(pLine.next())
					HUD_settings[part.lower()] = {'x':x, 'y':y}
					
			
			print('HUD_settings', HUD_settings)
			self.libraryModels[self.libraryMode].modelReset.emit()
					
		elif self.libraryMode == 'Scripts':
			def scanDir(dir, parentNode):
				for name in os.listdir(dir):
					path = os.path.join(dir, name)
					if os.path.isdir(path):
						node = self.append((name, name, 0, path, ':folder', None), parentNode)
						scanDir(path, node)
					else:
						if name.endswith('~'): continue
						if name.endswith('.1'): continue
						node = self.append((name, name, 0, path, None, File(path, currentProjectName)), parentNode)
						
			path = os.path.join(FileSelector.ROOT_PATH, 'data', 'scripts')
			if not os.path.exists(path): return
			#node = self.append(('scripts', 'scripts', 0, path, None, None), None)
			scanDir(path, None)
			
			self.libraryModels[self.libraryMode].modelReset.emit()
			
		elif self.libraryMode == 'System':
			
			for name in ('models.txt', 'levels.txt', 'lifebar.txt', 'menu.txt', 'script.txt', 'video.txt'):
				
				path = os.path.join(FileSelector.ROOT_PATH, 'data', name)
				if not os.path.isfile(path): continue
				node = self.append((name, name, 0, path, None, File(path, currentProjectName)), None)
				
			self.libraryModels[self.libraryMode].modelReset.emit()
			
		model.isFilled = True
		
		if(self.mode == 'library'):
			self.filterModel.setSourceModel(model)
			self.restoreExpandedState()
	
	
	def loadItem(self, index):
		
		item = index.data(FileModel.itemRole)
		fd = item.fd

		if fd is None or (fd.path is not None and os.path.isdir(fd.path)): return

		# Notes mode: load note content and open in editor, stay in notes mode
		if isinstance(fd, FileDB):
			fd.selectExclusive()
			if not fd.isLoaded(): fd.loadFromDisk()
			self.mainEditor.loadFile(fd, False)
			return

		self.mainEditor.temp_look_folder = None # reset temp_look_folder




		if(fd.projectName != 'Unknown' and fd.projectName not in self.mainEditor.loaded_projects):
			project = self.mainEditor.core.projectSelector.getProjectByName(fd.projectName)
			if(project != None):
				self.mainEditor.loadProject(project)



		modifiers = QtWidgets.QApplication.keyboardModifiers()
		stayInLibrary = False
		if (modifiers & QtCore.Qt.ControlModifier): stayInLibrary = True


		if fd.path in self.loadedFiles and self.loadedFiles[fd.path] != fd:
			item.fd = self.loadedFiles[fd.path]
			fd = self.loadedFiles[fd.path]


		#if self.openedItem is not None:
			#self.openedItem.state = 0

		fd.state = 1
		self.updateStates(exception=fd)


		self.openedItem = fd
		#print(fd, fd.path, os.path.isdir(fd.path))

		#print(fd)
		if not fd.isLoaded() : fd.loadFromDisk()
		self.mainEditor.loadFile(fd, False)

		if self.mode == 'library':
			self.addFromLibrary(fd)
		elif self._projectSearchMode:
			self.addFromLibrary(fd)
			self._exitProjectSearchMode()

		if stayInLibrary:
			return
		self.setMode('opened')
		self.saveExpandedStateWithoutFilters()
		self.searchEntry.setText('')
		self.search()
		
		
		
	def mouseReleaseEvent(self, e):
		
		if e.button() == Qt.MidButton:
			i = self.treeView.indexAt(QtCore.QPoint(e.x(), e.y()))
			if(i.column() != 0):
				i= i.sibling(i.row(), 0)
			self.treeView.setExpanded(i, not self.treeView.isExpanded(i))
		else:
			QtWidgets.QTreeView.mouseReleaseEvent(self.treeView, e)

	
	def reloadFilesModel_pre(self, expandedFolders=[], reset=False, projectFilter='*'):
		# self.loadedPaths.sort()
		# AVOID proxy error
		if(self.mode == 'opened'):
			self.filterModel.setSourceModel(None)
		self.reloadFilesModel(expandedFolders, reset)
		if(self.mode == 'opened'):
			self.filterModel.setSourceModel(self.openedModel)
		
		header = self.treeView.header()
		header.setStretchLastSection(False)
		#header.setDefaultSectionSize(60)
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
			
	def reloadFilesModel(self, expandedFolders=[], reset=False, projectFilter='*'):
		def match(pattern):
			nb = 0
			for f1 in folders:
				if f1 == f: continue
				if pattern in f1:
					nb += 1
			#print(nb)
			return nb
		
		#self.mode = 'library'

		#self.openedModel.rootItem.childItems = []
		self.openedModel.reset()
	
		if reset:
			folderNodes = {'':None}
			previousFolderNodes = {}
		else:
			previousFolderNodes = self.folderNodes
			
			#self.openedModel.rootItem.empty()
			for n in previousFolderNodes.values(): # We'll reuse previous items, so we must empty them
				if n is not None:
					#n.index = None
					n.empty()
					
			#self.openedModel.rootItem.emptyTree() # Nodes still exist
			folderNodes = {'':None}
		iconPath = None
		folders = []
		
		#self.loadedFiles = [
		      #'/home/piccolo/workspace/OpenBOR/data/scripts/dcancel.c', '/home/piccolo/workspace/OpenBOR/data/chars/zangief/zangief.txt', '/home/piccolo/workspace/OpenBOR/data/chars/amingo/amingo.txt']

		filesToAdd = []
		# loadedPaths contains all files, then filesToAdd will be used later
		for path in self.loadedPaths:
			if(projectFilter != '*'):
				fd = self.loadedFiles[path]
				if(fd.projectName != projectFilter):
					continue
			filesToAdd.append(path)
			if path.startswith('New'): # Rather check if fd.orginalLines is None
				continue
			
			folders.append(os.path.dirname(path))
			#if not reset and self.loadedFiles[path].isAddedToAView : continue
			#if reset or not self.loadedFiles[path].isAddedToAView:
			
		folders = list(set(folders))
		#folders = sorted(folders, key=len)
		folders.sort(key=lambda x: x.count(os.path.sep))
		#folders = sorted(folders, key=lambda p: (-p.count(os.path.sep), p))
		# print(folders)
		
		for f in folders:
			# print('\n*** Processing folder ***', f)
			# How to handle a folder ?
			if f in folderNodes : continue # Already present as a node, pass
		
			# Will any of my parent folders be present somewhere else ?
			# Goal : find the highest parent that will be needed as a node (global approach, prepare roots)
			
			parent = os.path.dirname(f)
			parentNode = None
			parentsToAdd = []
			# Tant que pas de node trouvée ET pas à la racine ET une différence de match avec son parent
			currentMatch = match(f)
			while parentNode is None and parent != os.path.dirname(parent) and match(parent) != currentMatch:
				
				if parent in folderNodes:
					parentNode = folderNodes[parent]
				else:
					parentsToAdd.append(parent)
					currentMatch = match(parent)
					parent = os.path.dirname(parent)
					
			
			
			# print('Reason left', parent, '[parentNode exists :', parentNode is not None, '] [parent is root :', parent == os.path.dirname(parent), '] [same match with pParent:', match(parent) == match(os.path.dirname(parent)))
			#if(parent not in parentsToAdd and parent not in folderNodes and  match(parent) > 0): # and match(parent) != match(os.path.dirname(parent)
				#parentsToAdd.append(parent)
				
			
			if len(parentsToAdd) > 0:
				parentsToAdd.reverse()
				# print('toADD', parentsToAdd)
				#print(parent, parentNode)
				parentOfFirst = os.path.dirname(parentsToAdd[0])

				# print(folderNodes)
				if parentOfFirst in folderNodes:
					parentNode = folderNodes[parentOfFirst]

				# print('parentOfFirst', parentOfFirst, parentNode)
				
				for parent in parentsToAdd:
					if parent in previousFolderNodes : 
						node = previousFolderNodes[parent]
						self.appendNode(node, parentNode, self.openedModel)
					else :
						node = self.append((os.path.basename(parent), os.path.basename(parent), 0, parent, ':folder', None), parentNode, self.openedModel)
						if parent in expandedFolders : node.isExpanded = True
					folderNodes[parent] = node
					parentNode = node
				# print(folderNodes)
		
			#return
		
			# Local approach, gap filling (branch to root)
			parentNode = None
			parent = os.path.dirname(f)
			parents = []
			parentsToAdd = []
			while parentNode is None and parent != os.path.dirname(parent):
				if parent in folderNodes:
					parentNode = folderNodes[parent]
				else:
					parents.append(parent)
				parent = os.path.dirname(parent)
			# print('PARENTS PHASE 2', parentNode, parents)		
			#print(parents)
			
			if parentNode is not None: # A noded parent found
				# parents contains not "noded" parents folder, so we node them
				parents.reverse()
				for parent in parents:
					if parent in previousFolderNodes : 
						node = previousFolderNodes[parent]
						self.appendNode(node, parentNode, self.openedModel)
					else :
						node = self.append((os.path.basename(parent), os.path.basename(parent), 0, parent, ':folder', None), parentNode, self.openedModel)
						if parent in expandedFolders : node.isExpanded = True
					folderNodes[parent] = node
					parentNode = node
			
			if f in previousFolderNodes : 
				node = previousFolderNodes[f]
				self.appendNode(node, parentNode, self.openedModel)
			else :
				node = self.append((os.path.basename(f), os.path.basename(f), 0, f, ':folder', None), parentNode, self.openedModel)
			folderNodes[f] = node
			if f in expandedFolders : node.isExpanded = True
		# *** END FOLDERS ***
		
		
		# *** BEGIN FILES TO ADD ***
		for path in filesToAdd:
			if '/app/' in path: # Special case for Next.JS router:
				pos = path.index('/app/') + len('/app')
				dirname = path[0:pos]
				parentNode = folderNodes[dirname]
				baseName = path[pos:]
			else:
				parentNode = folderNodes[os.path.dirname(path)]
				baseName = os.path.basename(path)
			fd = self.loadedFiles[path]
			fd.isAddedToAView = True
			fd.baseName = baseName
			#if fd.isVisible : # DEPRECATED?
				#parentNode.isExpanded = True
				#self.expandedFolders.add(parentNode.path)
			node = self.append((baseName, baseName, 0, path, iconPath, fd), parentNode, self.openedModel)
			fd.node = node
			
		self.folderNodes = folderNodes
		
		
		self.openedModel.modelReset.emit()
		
		

		if(self.mode == 'opened'):
			#self.treeView.update()
			self.filterModel.setSourceModel(self.openedModel)
			
			#print('****')
			#def trav(parentIndex):
				#print('GOING THROUGH', self.filterModel.rowCount(parentIndex))
				#for i in range(self.filterModel.rowCount(parentIndex)):
					#print('in child ', end="")
					#index = self.filterModel.index(i, 0, parentIndex)
					#item = index.data(FileModel.itemRole)
					#print(item.label, item.childItems)
					#trav(index)
				
			#trav(QtCore.QModelIndex())
			#print('****')
			self.restoreExpandedState()
			#WARNING self.treeView.expandAll()

			
			
	def remove(self, path):
		if path in self.loadedPaths:
			
			# Also remove file from editor recent bar
			self.mainEditor.editor.recentBar.removeItem({'path':path})
			
			self.loadedPaths.remove(path)
			self.mainEditor.remove(self.loadedFiles[path])
			del self.loadedFiles[path]
			
		
	def saveExpandedStateWithoutFilters(self, parentIndex=QtCore.QModelIndex()):
		for i in range(self.filterModel.rowCount(parentIndex)):
			index = self.filterModel.index(i, 0, parentIndex)
			item = index.data(FileModel.itemRole)
			item.isExpandedWithoutFilter = item.isExpanded
			self.saveExpandedStateWithoutFilters(index)
			
	def restoreExpandedState(self, parentIndex=QtCore.QModelIndex(), level=0):
		# if(level == 0): print('\nrestoreExpandedState', parentIndex)
		for i in range(self.filterModel.rowCount(parentIndex)):
			index = self.filterModel.index(i, 0, parentIndex)
			item = index.data(FileModel.itemRole)
			# print(i, item.label, item.isExpanded)
			if item.isExpanded:
				self.treeView.setExpanded(index, item.isExpanded)
			self.restoreExpandedState(index, level+1)
		# if(level == 0): print('\n\n')
	
	def restoreExpandedStateWithoutFilters(self, parentIndex=QtCore.QModelIndex()):
		# print('restoreExpandedState', parentIndex)
		for i in range(self.filterModel.rowCount(parentIndex)):
			index = self.filterModel.index(i, 0, parentIndex)
			item = index.data(FileModel.itemRole)
			
			# print(i, item.isExpanded)
			# if item.isExpandedWithoutFilter:
			self.treeView.setExpanded(index, item.isExpandedWithoutFilter)
			self.restoreExpandedStateWithoutFilters(index)

			
			
	def setMode(self, mode):
		if mode == 'library':
			#self.treeView.setModel(self.model)
			self.filterModel.setSourceModel(self.libraryModels[self.libraryMode])
			self.libraryButton.setChecked(True)
			self.filterModel.sort(0)
		elif mode == 'notes':
			self.loadNotes()
			self.filterModel.setSourceModel(self.notesModel)
			self.notesButton.setChecked(True)
		else:
			if self.mode != 'opened': # or self.filterModel.sourceModel() != self.openedModel:
				#self.treeView.setModel(self.openedModel)
				self.filterModel.setSourceModel(self.openedModel)
			#self.treeView.expandAll()
			#self.libraryButton.setChecked(False)
			self.openedButton.setChecked(True)
			self.filterModel.sort(0)

		self.restoreExpandedState()
		self.mode = mode
	
	def setLibraryMode(self, index):
		selectedMode = self.tabs[index]
		if selectedMode == self.libraryMode:
			if self.mode == 'library':
				self.setMode('opened')
			else:
				self.setMode('library')
		else:
			self.libraryMode = selectedMode
			self.loadLibrary()
			self.setMode('library')
	
	def setSelectedFile(self, fd):
		pass
		#Method 2 
		# selectionModel = self.treeView.selectionModel()
		# selectionModel.select(self.openedModel.indexOfNode(fd.node), QtCore.QItemSelectionModel.Select) # , 
		
		# Method 1
		# self.treeView.setCurrentIndex(self.openedModel.indexOfNode(fd.node))
	
	def eventFilter(self, obj, event):
		if obj == self.searchEntry and event.type() == QtCore.QEvent.KeyPress:
			if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
				if event.modifiers() & QtCore.Qt.ControlModifier:
					self._onCtrlEnterSearch()
				else:
					self._onSearchEnter()
				return True
		return super().eventFilter(obj, event)

	def _onSearchEnter(self):
		txt = self.searchEntry.text()
		if txt == '': return
		if not settings.get_option('misc/search_on_text_change', True):
			self.search()
		elif self._projectSearchTimer is None:
			# a pending debounced search() would otherwise fire afterwards and cancel the project search
			self.searchKeyDebounce.stop()
			self.searchInProject()

	def _onCtrlEnterSearch(self):
		self.search()

	def search(self):
		txt = self.searchEntry.text()

		# Leave project search before filtering : otherwise the (possibly huge) project results
		# tree gets filtered and expanded for nothing, just before being discarded
		self._exitProjectSearchMode()

		if(txt != self.currentFilter or txt == ''):
			self.treeView.model().expandResults = 0
		elif(txt == self.currentFilter):
			self.mainEditor.core.notify('expandResults += 1', 'warning')
			self.treeView.model().expandResults += 1


		self.currentFilter = txt

		if(txt != ''):
			self.saveExpandedStateWithoutFilters()




		self.treeView.model().setFilterRole(Qt.DisplayRole)
		regExp = QtCore.QRegExp(txt, QtCore.Qt.CaseInsensitive)
		self.treeView.model().setFilterRegExp(regExp)
		if(txt == ''):
			self.restoreExpandedStateWithoutFilters()
		else:
			self.restoreExpandedState() # not really a restoring but a matching of visual expanding with expanded state in data
		#self.treeView.expandAll()

		# Show "search in project" hint if no results in opened files mode
		self._updateSearchInProjectHint(txt)

	def _updateSearchInProjectHint(self, txt):
		if txt == '' or self.mode != 'opened':
			self.searchInProjectHint.hide()
			return

		projectFilter = self.projectButtonBar.getCurrent().name
		if projectFilter != '*':
			scope = _('project') + ' "' + projectFilter + '"'
		else:
			scope = _('loaded projects')

		searchOnChange = settings.get_option('misc/search_on_text_change', True)
		hasResults = self.filterModel.rowCount() > 0
		if hasResults and not searchOnChange:
			self.searchInProjectHint.hide()
			return

		enterHint = _('Press Enter or click') if searchOnChange else _('Click')
		if hasResults:
			self.searchInProjectHint.setText(
				enterHint + _(' here to search in ') + scope + '.'
			)
		else:
			self.searchInProjectHint.setText(
				_('No results. ') + enterHint + _(' here to search in ') + scope + '.'
			)
		self.searchInProjectHint.setCursor(QtCore.Qt.PointingHandCursor)
		self.searchInProjectHint.show()

	def _exitProjectSearchMode(self):
		if self._projectSearchTimer is not None:
			self._projectSearchTimer.stop()
			self._projectSearchTimer = None
		if self._projectSearchMode:
			self._projectSearchMode = False
			if hasattr(self, '_savedProjectFilter'):
				self.filterModel.setProjectFilter(self._savedProjectFilter)
			# detach before reset, so the proxy/view don't process the reset of a big model
			self.filterModel.setSourceModel(self.openedModel)
			self.projectSearchModel.reset()

	def searchInProject(self):
		txt = self.searchEntry.text()
		if txt == '': return

		# Stop any previous search
		if self._projectSearchTimer is not None:
			self._projectSearchTimer.stop()
			self._projectSearchTimer = None

		self._projectSearchMode = True
		self.searchInProjectHint.setText(_('Searching...'))
		self.searchInProjectHint.setCursor(QtCore.Qt.ArrowCursor)

		# Switch to the project search model
		self.projectSearchModel.reset()
		self.filterModel.setFilterRegExp(QtCore.QRegExp('', QtCore.Qt.CaseInsensitive))
		self._savedProjectFilter = self.filterModel.projectFilter
		self.filterModel.setProjectFilter('*')
		self.filterModel.setSourceModel(self.projectSearchModel)

		# Determine which projects to scan
		projectFilter = self.projectButtonBar.getCurrent().name
		if projectFilter != '*' and projectFilter != 'current':
			projectsToScan = {projectFilter: self.mainEditor.loaded_projects[projectFilter]}
		else:
			projectsToScan = dict(self.mainEditor.loaded_projects)

		self._projectSearchProjectPaths = {name: data['path'] for name, data in projectsToScan.items()}
		self._projectSearchTreeMode = settings.get_option('gui/project_search_tree_mode', True)
		self._projectSearchFolderNodes = {'': None}

		# Build a generator that walks all project directories
		pattern = txt.lower()
		def _matchesBlacklistPattern(name, blPattern):
			"""Check if name matches a simple wildcard pattern (only * supported)."""
			if '*' not in blPattern:
				return name == blPattern
			# Convert simple wildcard to prefix/suffix check
			if blPattern.startswith('*') and blPattern.endswith('*'):
				return blPattern[1:-1] in name
			elif blPattern.startswith('*'):
				return name.endswith(blPattern[1:])
			elif blPattern.endswith('*'):
				return name.startswith(blPattern[:-1])
			else:
				# Pattern like "foo*bar"
				parts = blPattern.split('*', 1)
				return name.startswith(parts[0]) and name.endswith(parts[1])

		def fileGenerator():
			for projectName, projectData in projectsToScan.items():
				projectPath = projectData['path']
				whitelist = settings.get_option('project/' + projectName + '/search_whitelist', [])
				blacklist = settings.get_option('project/' + projectName + '/search_blacklist', [])

				if whitelist:
					# Only walk whitelisted directories
					walkRoots = []
					for wDir in whitelist:
						fullPath = os.path.join(projectPath, wDir)
						if os.path.isdir(fullPath):
							walkRoots.append(fullPath)
				else:
					walkRoots = [projectPath]

				for walkRoot in walkRoots:
					for dirpath, dirnames, filenames in os.walk(walkRoot):
						# Filter out blacklisted directories
						filtered = []
						for d in dirnames:
							if d.startswith('.'):
								continue
							skip = False
							for bl in blacklist:
								if _matchesBlacklistPattern(d, bl):
									skip = True
									break
							if not skip:
								filtered.append(d)
						dirnames[:] = filtered

						for filename in filenames:
							# Filter out blacklisted files
							if blacklist:
								skip = False
								for bl in blacklist:
									if _matchesBlacklistPattern(filename, bl):
										skip = True
										break
								if skip:
									continue
							if pattern in filename.lower():
								yield os.path.join(dirpath, filename), projectName

		self._projectSearchGen = fileGenerator()
		self._projectSearchCount = 0

		# Use a timer to add results progressively
		self._projectSearchTimer = QtCore.QTimer()
		self._projectSearchTimer.setInterval(0)
		self._projectSearchTimer.timeout.connect(self._projectSearchStep)
		self._projectSearchTimer.start()

	def _projectSearchStep(self):
		BATCH_SIZE = 20
		added = 0
		for i in range(BATCH_SIZE):
			try:
				path, projectName = next(self._projectSearchGen)
			except StopIteration:
				self._projectSearchTimer.stop()
				self._projectSearchTimer = None
				if self._projectSearchCount == 0:
					self.searchInProjectHint.setText(_('No files found.'))
				else:
					self.searchInProjectHint.setText(str(self._projectSearchCount) + _(' file(s) found.'))
				if self._projectSearchTreeMode:
					QtCore.QTimer.singleShot(0, self.treeView.expandAll)
				return

			fd = File(path, projectName)
			fd.state = 0

			if self._projectSearchTreeMode:
				# Tree mode: group by folders
				folder = os.path.dirname(path)
				if folder not in self._projectSearchFolderNodes:
					self._buildSearchFolderNode(folder)
				parentNode = self._projectSearchFolderNodes[folder]
				label = os.path.basename(path)
			else:
				# Flat mode: show relative path
				projectPath = self._projectSearchProjectPaths.get(projectName, '')
				relPath = path[len(projectPath):].lstrip(os.sep) if path.startswith(projectPath) else path
				parentNode = None
				label = relPath

			node = self._appendToSearchModel(label, path, fd, parentNode)
			fd.node = node
			added += 1
			self._projectSearchCount += 1

		if added > 0:
			if self._projectSearchTreeMode:
				QtCore.QTimer.singleShot(0, self.treeView.expandAll)
			self.searchInProjectHint.setText(_('Searching... ') + str(self._projectSearchCount) + _(' file(s) found so far.'))

	def _appendToSearchModel(self, label, path, fd, parentNode):
		'''Append a node to projectSearchModel using proper beginInsertRows/endInsertRows'''
		model = self.projectSearchModel
		if parentNode is None:
			parentNode = model.rootItem
			parentIndex = QtCore.QModelIndex()
		else:
			parentIndex = model.createIndex(parentNode.row(), 0, parentNode)

		rowCount = parentNode.childCount()
		model.beginInsertRows(parentIndex, rowCount, rowCount)
		node = Item(parentNode, (label, label, 0, path, None, fd), model)
		parentNode.append(node)
		model.endInsertRows()
		return node

	def _buildSearchFolderNode(self, folder):
		if folder in self._projectSearchFolderNodes:
			return self._projectSearchFolderNodes[folder]

		parent = os.path.dirname(folder)
		if parent == folder:  # root
			self._projectSearchFolderNodes[folder] = None
			return None

		if parent not in self._projectSearchFolderNodes:
			self._buildSearchFolderNode(parent)

		parentNode = self._projectSearchFolderNodes[parent]
		name = os.path.basename(folder)
		node = self._appendToSearchModel(name, folder, None, parentNode)
		node.isExpanded = True
		node.iconPath = ':folder'
		self._projectSearchFolderNodes[folder] = node
		return node


	def saveProjectSession(self, name):
		if(self.mainEditor.currentProject != None):
			self.mainEditor.currentProject['last_session'] = name
			self.mainEditor.core.projectSelector.actualizeProject(self.mainEditor.currentProject)
		
	def saveSession(self, name=None):
		if self.isSavingSession:
			return
			
		
		import datetime
		now = datetime.datetime.now()
		
			
		# >>> now
		# datetime.datetime(2009, 1, 6, 15, 8, 24, 78915)
			
		self.isSavingSession = True
		if name is None:
			name = self.sessionName
		if name is None:
			name = 'Default'
		logging.debug(str(now) + ' STARTING SAVE SESSION : ' + str(name))
		
		
		ts = now.timestamp()
		if(name == self.lastSaveName and ts < self.lastSaveTime + 2):
			logging.debug(str(now) + ' SAVE CANCEL because too close to last save')
			self.isSavingSession = False
			return
		
		self.lastSaveTime = ts
		self.lastSaveName = name
		settings.set_option('general/last_session', name)
		self.saveProjectSession(name)
		
		if name is None:
			self.isSavingSession = False
			return # TODO dialog for saving
		
		
		
		#output = '\n'.join(map(str, self.loadedFiles.values()))
		
		toSave = []
		for fd in self.loadedFiles.values():
			if fd.path is not None and os.path.exists(fd.path):
				fd.isVisible = os.path.dirname(fd.path) in self.expandedFolders
				toSave.append(fd)

			
		
				
		
		logging.debug('FILES TO SAVE : ' + str(toSave))
		output = '\n'.join(map(str, toSave))
		
		# we also save back the original excluded/filtered files of the session
		if(hasattr(self, "excluded_session_files")):
			for project in self.excluded_session_files:
				for dic in self.excluded_session_files[project]:
					output += "\n" + str(dic)
		
		output += '\n\n'
		
		
		
		
		expandedFolders = []
		for fd in self.folderNodes.values():
			if fd is not None and fd.isExpanded:
				logging.debug(fd.path)
				output += fd.path + '\n'
				expandedFolders.append(fd.path)
			
		if(hasattr(self, "expandedFolders_fromSession")):
			for path in self.expandedFolders_fromSession:
				if path not in expandedFolders:
					output += path + '\n'
			
		if(output.strip() != ''):
			#for path in self.loadedFiles:
				#f.write(path + "\n")
				
			if name in self.sessions_content and self.sessions_content[name] == output:
				pass # not need to save, content has not changed
			else:
				
				sessionPath = os.path.join(xdg.get_data_home(), 'sessions') + os.sep + name
				# Also save in backup DB
				@util.threaded
				def _backupSession(params):
					File.DB.addBackup(params)
				_backupSession([sessionPath, output, 0, 1, 'standard'])

				f = open(sessionPath, 'w')
				f.write(output)
				f.close()
				self.sessions_content[name] = output
		logging.debug('END OF SAVE SESSION : ' + name)
		self.isSavingSession = False
		
	def showContextMenu(self, pos):
		
		def actionTriggered(action):
			print("menu_action triggered", action)
			if action is None: return
			if action == delete:
				self.deleteItem(index)
			elif action == copyLocation:
				clipboard = QtWidgets.QApplication.clipboard()
				clipboard.setText(itemPath)
			elif action == openInFileBrowser:
				import subprocess
				import sys
				filePath = itemPath
				if sys.platform == 'linux':
					# Detect default file manager and use appropriate command
					default_fm = ''
					try:
						result = subprocess.run(
							['xdg-mime', 'query', 'default', 'inode/directory'],
							capture_output=True, text=True
						)
						default_fm = result.stdout.strip().lower()
					except:
						pass

					try:
						if 'LFB' in default_fm or 'lfb' in default_fm:
							subprocess.Popen(['/home/piccolo/workspace/Daimao-Journal-JS-4/dist/life-file-browser/life-file-browser', '--select', filePath])
						elif 'nemo' in default_fm and shutil.which('nemo'):
							subprocess.Popen(['nemo', filePath])
						elif 'nautilus' in default_fm and shutil.which('nautilus'):
							subprocess.Popen(['nautilus', '--select', filePath])
						elif 'dolphin' in default_fm and shutil.which('dolphin'):
							subprocess.Popen(['dolphin', '--select', filePath])
						elif 'thunar' in default_fm and shutil.which('thunar'):
							subprocess.Popen(['thunar', filePath])
						elif 'pcmanfm' in default_fm and shutil.which('pcmanfm'):
							subprocess.Popen(['pcmanfm', filePath])
						elif 'caja' in default_fm and shutil.which('caja'):
							subprocess.Popen(['caja', filePath])
						else:
							# Fallback: D-Bus method
							subprocess.Popen(['dbus-send', '--session', '--dest=org.freedesktop.FileManager1',
								'--type=method_call', '/org/freedesktop/FileManager1',
								'org.freedesktop.FileManager1.ShowItems',
								'array:string:file://' + filePath, 'string:'])
					except:
						# Last resort: open parent folder
						subprocess.Popen(['xdg-open', os.path.dirname(filePath)])
				elif sys.platform == 'darwin':
					subprocess.Popen(['open', '-R', filePath])
				elif sys.platform == 'win32':
					subprocess.Popen(['explorer', '/select,', filePath])
			elif action == compare1:
				self.compare1_path = item.fd.path
	
			elif action in open_equivalent:
				destinationProject = open_equivalent[action]
				compare1_path = item.fd.path
				# we remove project root from path, to get only the relative path
				relativePath = compare1_path.replace(  self.mainEditor.loaded_projects[ item.fd.projectName ]['path'], '' )
				compare2_path = self.mainEditor.loaded_projects[ destinationProject]['path'] + relativePath
				
				self.mainEditor.openFile(compare2_path, item.fd.category)
				
			elif action == compare2 or action in compare_to_equivalents:
				
				
				if action == compare2:
					self.compare2_path = item.fd.path
				else:
					destinationProject = compare_to_equivalents[action]
					self.compare1_path = item.fd.path
					# we remove project root from path, to get only the relative path
					relativePath = self.compare1_path.replace(  self.mainEditor.loaded_projects[ item.fd.projectName ]['path'], '' )
					self.compare2_path = self.mainEditor.loaded_projects[ destinationProject]['path'] + relativePath
				
				
				import subprocess
				
				command = settings.get_option('compare_tool/compare_program_path', 'meld')
				commandMask = settings.get_option('compare_tool/command_mask', '{program} {file1} {file2}')
				commandMask = commandMask.replace(' ', '@')
				commandMask = commandMask.replace('{program}', command)
				commandMask = commandMask.replace('{file1}', self.compare1_path)
				commandMask = commandMask.replace('{file2}', self.compare2_path)
				
				subprocess.Popen(commandMask.split('@'))
				# subprocess.Popen([command, self.compare1_path, self.compare2_path])
				# subprocess.call(command + ' "' + self.compare1_path + '" "' + self.compare2_path +'"', shell=True)
				
			popMenu.close()
		
		index = self.sender().indexAt(pos)
		if not index.isValid() : return
		item = index.data(FileModel.itemRole) #internalPointer()

		# folder and category nodes have no file descriptor, only a path (None for categories)
		isFolder = item.fd is None
		itemPath = item.path if isFolder else item.fd.path
		if isFolder and itemPath is None: return

		popMenu = QtWidgets.QMenu(self)
		delete = compare1 = compare2 = None
		if not isFolder:
			delete = popMenu.addAction(QtGui.QIcon.fromTheme('list-remove'), _("Close"))
		copyLocation = popMenu.addAction(QtGui.QIcon.fromTheme('edit-copy'), _("Copy location"))
		openInFileBrowser = popMenu.addAction(QtGui.QIcon.fromTheme('folder-open'), _("Open in file browser"))
		if not isFolder:
			compare1 = popMenu.addAction(_("Compare 1"))
			compare2 = popMenu.addAction(_("Compare 2"))

		compare_to_equivalents = {}
		open_equivalent = {}
		
		simpleActions = False
		
		actions_to_add = {'compare':[], 'open':[]} 
		actions_tmp = []
		
		
		
		for projectName in (self.mainEditor.loaded_projects if not isFolder else []):
			if(projectName != item.fd.projectName):
				
				if simpleActions:
					action = popMenu.addAction(_("Compare to equivalent in project ") + projectName)
					compare_to_equivalents[action] = projectName 
					action = popMenu.addAction(_("Open equivalent in project ") + projectName)
					open_equivalent[action] = projectName
					#for w in action.associatedWidgets():
					#w = popMenu.widgetForAction(action)
						#w = action.defaultWidget()
						#print('TULIA', w)
						#w.setStyleSheet("QToolButton { background:red; } ");
				else:
					
					projectData = self.mainEditor.loaded_projects[projectName]
				
					button= QtWidgets.QToolButton(popMenu);
					#button.setFixedSize(50,50);
					button.setText(_("Compare to equivalent in project ") + projectName)
					button.setStyleSheet("QToolButton { color:" + projectData['font_color'] + ";background:" + projectData['background_color']  + "; } QToolButton:hover { font-weight:bold;} ");
					action=QtWidgets.QWidgetAction(self);
					action.setDefaultWidget(button);
					
					#button.triggered.connect(actionTriggered)

					button.pressed.connect(lambda x=action:actionTriggered(x))
					#action.triggered.connect(lambda:actionTriggered(action))
					
					actions_to_add['compare'].append(action)
					
					compare_to_equivalents[action] = projectName 
					
					
					button= QtWidgets.QToolButton(popMenu);
					#button.setFixedSize(50,50);
					button.setText(_("Open equivalent in project ") + projectName)
					button.setStyleSheet("QToolButton { color:" + projectData['font_color'] + ";background:" + projectData['background_color']  + "; } QToolButton:hover { font-weight:bold;} ");
					action=QtWidgets.QWidgetAction(self);
					action.setDefaultWidget(button);
					
					#button.triggered.connect(actionTriggered)
					button.pressed.connect(lambda x=action :actionTriggered(x))
					#action.triggered.connect(lambda:actionTriggered(action))
					
					actions_to_add['open'].append(action)
					
					open_equivalent[action] = projectName 
			
		# that way they are grouped by action type, cleared like that
		for key in ['compare', 'open']:
			for action in actions_to_add[key]:
				popMenu.addAction(action);

				
		
		action = popMenu.exec_(self.sender().mapToGlobal(pos))
		
		actionTriggered(action)
		
			
			
	def updateStates(self, exception=None):
		
		self.treeView.clearSelection()
		self.openedModel.layoutAboutToBeChanged.emit();
		
		
		
		
		
		for oFd in self.loadedFiles.values():
			if(oFd == exception):continue
		
			if oFd.state != 0:
				if oFd.state == 10:
					oFd.state = 0
				else:
					# oFd.state += 1
					oFd.state += 0.15
					
		self.openedModel.layoutChanged.emit();

		
class Item(TreeItem):
	def __init__(self, parent, data, model):
		TreeItem.__init__(self, data[1], parent)
		self.ID = data[0]
		self.label = data[1]
		self.pos = data[2]
		self.path = data[3]
		self.fd = data[5]
		if(self.fd != None):
			self.fd.node = self

		self.subelements = []
		self.showCount = False # if True, display the number of children next to the label
		self.iconPath =  data[4]
		self.icon = None
		
		self.model = model
		
	def __str__( self ):
		return self.label
		
	def __repr__(self):
		return self.label
	
	
	def copy(self):
		new = Item(self, [self.ID, self.label, self.pos, self.path, self.iconPath, self.fd], self.parent(), self.model)
		
	def getFilter(self):
		'''
			ex : {"artist":"AC/DC", "album":"Back In Black", "title":"You Shook Me All Night Long"}
		'''
		dic = {}
		item = self
		while(item.parent() != None): # Don't  eval rootItem 
			dic[item.type] = item.label
			item = item.parent()
		return dic
		
class FileModel(TreeModel):
	icon_size = 25
	unsavedIcon = None
	bigFont = None
	
	itemRole = Qt.UserRole+2
	expandedRole = Qt.UserRole+1
	expandedRoleWithoutFilter = Qt.UserRole+3
	containsRole = Qt.UserRole+4
	expandWithoutContainsRole = Qt.UserRole+5
	filterTextRole = Qt.UserRole+7
	
	def __init__(self):
		TreeModel.__init__(self)
		self.columnsFields = ('pos', 'ID', 'label')
		theme = settings.get_option('gui/widgets_theme', None)
		if FileModel.unsavedIcon is None:
			
			#FileModel.unsavedIcon = QtGui.QIcon.fromTheme('document-save').pixmap(self.icon_size-5)
			saveImage = QtGui.QImage('icons/save.svg')
			if(theme == "Dark"): saveImage.invertPixels()
		
			FileModel.unsavedIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(saveImage)).pixmap(self.icon_size-5)
			FileModel.bigFont = QtGui.QFont()
			FileModel.bigFont.setPointSize(12)
			
		
		
		self.defaultFontColor = [0,0,0]
		if(theme != None and 'dark' in theme.lower()):
			self.defaultFontColor = [240,240,240]


	def columnCount(self, parent):
		return 2

	def data(self, index, role):
		if not index.isValid():
			return None
		item = index.internalPointer()
		
		if role == self.itemRole:
			return item
		elif role == self.expandedRole:
			return item.isExpanded
		elif role == self.expandedRoleWithoutFilter:
			return item.isExpandedWithoutFilter
		elif role == self.containsRole:
			return item.containsFilter
		elif role == self.expandWithoutContainsRole:
			return item.expandWithoutContains
		elif role == self.filterTextRole:
			# raw label : the displayed one may contain the number of children
			if index.column() == 0:
				return item.label
		elif role == Qt.DisplayRole:
			if index.column() == -1:
				return item.pos
			elif index.column() == 0:
				if item.showCount:
					return item.label + ' (' + str(item.childCount()) + ')'
				return item.label
				
		elif role == Qt.DecorationRole and index.column() == 0:
			if item.fd is not None and item.fd.saved is False:
				return self.unsavedIcon
			if(item.icon is None):
				#try:
				path = None
				if item.fd is not None:
					path = item.fd.iconPath
				if item.iconPath is not None:
					path = item.iconPath
					
				if path is not None:
					if path[0] == ':':
						item.icon = QtGui.QIcon.fromTheme('folder').pixmap(self.icon_size)
						
					else:
						try:
							item.icon =  QtGui.QPixmap.fromImage(loadSprite(path))
						except:
							pass
						if(item.icon == None or item.icon.isNull()):
							#item.icon = self.icons[item.type]
							pass
						else:
							if(item.path is None):
								size = 40
							else:
								size = self.icon_size
							item.icon = item.icon.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation) #scaledToHeight(icon_size)
								
						#except:
							pass
						#item.icon = self.icons[item.label]
				
			return item.icon

		elif role == Qt.ToolTipRole:
			return item.path
		
		elif role == Qt.BackgroundRole and (item.fd is not None and item.fd.state > 0):
			def tint(x):
				return int(x + factor * (255-x))

			
			if(item.fd.state == 1): # top of the chain (~ selected)
				color = SELECTED_COLOR
			else:
			
				factor = item.fd.state * 0.1
				color = [215,223,1]
				color = map(tint, color)

			return QtGui.QBrush(QtGui.QColor(*color))
		elif role == Qt.FontRole and item.path is None:
			return FileModel.bigFont
		elif role == Qt.ForegroundRole and (item.fd is not None and item.fd.state > 0):
			if(item.fd.state == 1):
				color = [255,255,255]
			else:
				if(item.fd.state < 10):
					color = [0,0,0]
				else:
					color = self.defaultFontColor
			return QtGui.QBrush(QtGui.QColor(*color))
		return None

	def flags(self, index):
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled
	
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			if section == 0:
				return '#'
			elif section == 1:
				return 'ID'
			elif section == 2:
				return 'Label'
			
		return None
		
	def mimeData(self, indexes):
		'''
			What is passed during drag operations
		'''
		data = QtCore.QMimeData()
		selection = []
		for i in indexes:
			selection.append(i.internalPointer().getFilter())
		data.setData('bullseye/library.items', str(selection))
		return data
		
	def mimeTypes(self):
		'''
			FIXME Not used, didn't manage to find out how to automatically serialize items (tddhus overrided mimeData instead)
		'''
		return ('bullseye/library.items',)
	
	def setData(self, index, value, role):
		if not index.isValid():
			return None
		item = index.internalPointer()
		
		if role == self.expandedRole:
			item.isExpanded = value
			return 1
		elif role == self.expandedRoleWithoutFilter:
			item.isExpandedWithoutFilter = value
			return 1
		elif role == self.containsRole:
			item.containsFilter = value
			return 1
		elif role == self.expandWithoutContainsRole:
			item.expandWithoutContains = value
			return 1
		else:
			return TreeModel.setData(self, index, value, role)
			
		
	def sort(self, columnIndex, order):
		self.layoutAboutToBeChanged.emit()
		if(order == QtCore.Qt.AscendingOrder):
			reverse = False
		else:
			reverse = True
		reverse = True
			
		def sort(elt, reverse):
			elt.childItems = sorted(elt.childItems, key=attrgetter(self.columnsFields[columnIndex]), reverse=reverse)
			for childElt in elt.childItems:
				sort(childElt, reverse)
				
		sort(self.rootItem, reverse)
		
		self.layoutChanged.emit()

class UnsavedFileDialog(QtWidgets.QDialog):
	def __init__(self, files):
		self.files = files
		QtWidgets.QWidget.__init__(self)
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(QtWidgets.QLabel(_('The following documents have been modified. Do you want to save them before closing ?')), 0)
		tableView = QtWidgets.QTableView()
		tableView.setMinimumWidth(400)
		
		tableView.verticalHeader().hide()
		self.foldersModel = QtGui.QStandardItemModel(0, 2)
		self.foldersModel.setHorizontalHeaderLabels([_("Documents"), _("Location")])
		for fd in files:
			checkBox = QtGui.QStandardItem(fd.name)
			checkBox.setCheckable(True)
			checkBox.setCheckState(QtCore.Qt.Checked)
			#if dig:
				#checkBox.setCheckState(QtCore.Qt.Checked)
			self.foldersModel.appendRow([checkBox, QtGui.QStandardItem(fd.getLongText())])
		
		tableView.setModel(self.foldersModel)
		tableView.horizontalHeader().setSectionResizeMode (1, QtWidgets.QHeaderView.Stretch)
		tableView.horizontalHeader().setSectionResizeMode (0, QtWidgets.QHeaderView.Fixed)
		tableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		
		layout.addWidget(tableView, 1)
		
		selectAll = QtWidgets.QPushButton(_('Select All'))
		selectAll.pressed.connect(self.selectAll)
		layout.addWidget(selectAll, 0)
		
		buttonLayout = QtWidgets.QHBoxLayout()
		buttonLayout.addStretch()
		#annuler abandonner enregistrer
		cancelButton = QtWidgets.QPushButton(_('Cancel Closing'))
		cancelButton.pressed.connect(self.reject)
		saveButton = QtWidgets.QPushButton(_('Save'))
		saveButton.pressed.connect(self.save)
		dontsaveButton = QtWidgets.QPushButton(_('Don\'t save'))
		dontsaveButton.pressed.connect(self.accept)
		buttonLayout.addWidget(cancelButton, 0)
		buttonLayout.addWidget(dontsaveButton, 0)
		buttonLayout.addWidget(saveButton, 0)
		
		layout.addLayout(buttonLayout)
		
		self.setLayout(layout)
		
	def save(self):
		lookFolder = os.path.dirname(settings.get_option('general/data_path'))
		toActuallySave = []
		for i in range(self.foldersModel.rowCount()):
			if self.foldersModel.item(i, 0).checkState() == QtCore.Qt.Checked:
				toActuallySave.append(self.foldersModel.item(i, 1).text())
			
		for fd in self.files:
			if fd.getLongText() in toActuallySave:
				if fd.path is None:
					path = QtWidgets.QFileDialog.getSaveFileName(self, caption=_('Save As') + ' (' + fd.getLongText() + ')', directory=lookFolder)[0]
					if path is None or path  == '': return
					else : 
						lookFolder = os.path.dirname(path) # Change lookFolder for next files
						fd.path = path
				fd.save()
		self.accept()
		
	def selectAll(self):
		for i in range(self.foldersModel.rowCount()):
			self.foldersModel.item(i, 0).setCheckState(QtCore.Qt.Checked)

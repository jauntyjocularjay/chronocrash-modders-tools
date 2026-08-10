import os, re, time, mimetypes, logging

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *

from common import util
from common import settings
from gui.util import FileInput


class ProjectSelector(QtWidgets.QWidget):
	
	LOAD_TEXT = 'Select a game project\n or register a new one'
	SESSION_LOADED = False
	
	def __init__(self, parent):
		self.mainFrame = parent
		QtWidgets.QWidget.__init__(self)
		
		self.layout = QtWidgets.QVBoxLayout()
		
		self.projectLayout = QtWidgets.QVBoxLayout()
		self.projectLayout.setContentsMargins(100, 100, 100, 100)
		
		buttonLayout = QtWidgets.QHBoxLayout()
		
		
		
		
		addButton = QtWidgets.QPushButton(QtGui.QIcon.fromTheme('list-add'), _('Add'))
		addButton.pressed.connect(self.addProject)
		delButton = QtWidgets.QPushButton(QtGui.QIcon.fromTheme('list-remove'), _('Remove'))
		delButton.pressed.connect(self.removeProject)
		
		
		buttonLayout.addWidget(addButton)
		buttonLayout.addWidget(delButton)
		
		self.label = QtWidgets.QLabel(_('Register a game project by clicking the add button\nand selecting the game data folder'))
		font = self.label.font()
		font.setPointSize(32)
		self.label.setFont(font)
		self.label.setContentsMargins(50, 50, 50, 50);
		
		
		self.layout.addWidget(self.label, 0)
		self.layout.addLayout(buttonLayout)
		
		projectWidget = QtWidgets.QWidget()
		
		projectWidget.setLayout(self.projectLayout)
		# self.projectLayout.addStretch(1)
		# projectWidget.setMaximumSize(300,2000)
		# projectWidget.setMinimumSize(-1, 800)
		self.projectLayout.addWidget(QtWidgets.QLabel(_('Register a game project by clicking the add button\nand selecting the game data folder')))
		
		
		self.askSessionCheckBox = QtWidgets.QCheckBox('Ask session')
		self.askSessionCheckBox.setChecked(settings.get_option( 'general/ask_load_session_start', True))
		self.askSessionCheckBox.stateChanged.connect(self.askSessionCheckBoxChanged)
		self.layout.addWidget(self.askSessionCheckBox)
		
		self.settingsLocationButton = QtWidgets.QPushButton('Overwrite CMT settings and cache location')
		self.settingsLocationButton.clicked.connect(self.chooseSettingsLocation)
		
		self.layout.addWidget(self.settingsLocationButton)
		
		scrollArea = QtWidgets.QScrollArea()
		scrollArea.setWidgetResizable(True) # CRITICAL
		scrollArea.setWidget(projectWidget)
		self.layout.addWidget(scrollArea, 1)
		
		self.setLayout(self.layout)
		
		self.layout.setAlignment(self.label, QtCore.Qt.AlignCenter)
		self.layout.setAlignment(buttonLayout, QtCore.Qt.AlignCenter)
		# self.layout.setAlignment(self.projectLayout, QtCore.Qt.AlignCenter)
		# self.layout.setAlignment(scrollArea, QtCore.Qt.AlignCenter)
		
		projects = settings.get_option('general/projects', [])
		self.projects = []
		self.projects_paths = []
		for p in projects:
			if not isinstance(p, dict):
				self.projects.append({'path':p})
				self.projects_paths.append(p)
			else:
				self.projects.append(p)
				self.projects_paths.append(p['path'])
				
		
		if len(self.projects) > 0:
			self.label.setText(_(self.LOAD_TEXT))
		
		self.loadProjectsList()
		
		self.mode = 'load'
		
		# button = QtWidgets.QPushButton("test")
		# button.pressed.connect(self.projectClicked)
		
		# self.projectLayout.addWidget(button)
		# self.projectLayout.addSpacing(50)
		
		
	def askColor(self, label):
		if(label is not None):
			QtWidgets.QMessageBox.information(self, _('Select color'), label + '\n\nClick ok to proceed')
		
		
		colorObject = QtWidgets.QColorDialog.getColor()
		if not colorObject.isValid(): color = None
		else : color = colorObject.name() 
		
		print('color', color)
		
		while not( color != None and color != False):  #color != '#000000' and
			colorObject = QtWidgets.QColorDialog.getColor()
			if not colorObject.isValid(): color = None
			else : color = colorObject.name() 
			
		return color
			

	def askSessionCheckBoxChanged(self):
		settings.set_option('general/ask_load_session_start', self.askSessionCheckBox.isChecked())

	def addProject(self):
		path = QtWidgets.QFileDialog.getExistingDirectory(self, _('Choose a mod data folder'))
		if path == '': return # Canceled
		print(path)
		files = os.listdir(path)
		print(files)
		is_OpenBOR = True
		if 'models.txt' not in map(lambda x:x.lower(), files) or path in self.projects_paths:
			if(QtWidgets.QMessageBox.question(self, _('Error'), _('No models.txt found in this folder. Are you sure you want to continue ?'), defaultButton=QtWidgets.QMessageBox.Yes) != QtWidgets.QMessageBox.Yes):
				return
			is_OpenBOR = False
			
		
		
		name = QtWidgets.QInputDialog.getText(self, _("Project name"), _("Name"))[0]
		
		background_color = self.askColor(_('Please select a BACKGROUND color for this project'))
		font_color = self.askColor(_('Please select a FONT color for this project'))

		# if text != '':
		
		self.projects.append({'path':path, 'name':name, 'background_color':background_color, 'font_color':font_color, 'is_OpenBOR':is_OpenBOR})
		# self.projects.append("test")
		
		settings.set_option('general/projects', self.projects)
		self.loadProjectsList()
		

	def chooseSettingsLocation(self):
		path = QtWidgets.QFileDialog.getExistingDirectory(self, _('Choose the new settings & cache folder'))
		if path == '': return # Canceled
	
		f = open('overwrite-settings-path.ini', 'w')
		f.write(path)
		f.close()
		
		QtWidgets.QMessageBox.information(self, _('Please restart'), _("You'll need to restart the app for that setting to be properly applied"))
		
		
	def getProjectByName(self, name):
		for project in self.projects:
			if 'name' in project and project['name'] == name : return project
		return None
		
	def loadProject(self, project):
		def loadSession(project, projectAlreadyOpened=False, resetSession=False):
			if resetSession:
				session = ''
			elif 'last_session' in project:
				session = project['last_session']
			else:
				session = settings.get_option('general/last_session', 'Default')
			
			
			if(not 'is_OpenBOR' in project or project['is_OpenBOR']):
				pass
			else:
				self.mainFrame.meWidget.fileSelector.setMode('opened')
			
			self.mainFrame.setSession(session, projectAlreadyOpened, projectAlreadyOpened)
			self.mainFrame.meWidget.menuBar.reloadSessionsList()
			
			
		projectAlreadyOpened = len(self.mainFrame.meWidget.loaded_projects) > 0
		keepSession = False
		resetSession = False
		if(projectAlreadyOpened and QtWidgets.QMessageBox.question(self, _('Keep current session'), _('Keep current session ?'), defaultButton=QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes):
			keepSession = True
			
		elif(self.mainFrame.meWidget.currentProject['path'] != ''):
			if('last_session' in project and project['last_session'] == self.mainFrame.meWidget.currentProject['last_session']):
				resetSession = True # because same session, and user said he don't want to keep current session
			
		
		self.label.setText(_('Now loading project...'))
		settings.set_option('general/data_path', project['path'])
		
		self.hide()
		self.mainFrame.setMode('mainEditor')
		self.mainFrame.meWidget.loadProject(project)
		# self.mainFrame.setMode('mainEditor') # old order was this
		self.mainFrame.meWidget.reloadSplitterPos()
		self.mainFrame.meWidget.editor.reloadSplitterPos()
		if(not ProjectSelector.SESSION_LOADED or (projectAlreadyOpened and not keepSession)):
			logging.debug("Setting session from project manager...")
			
			askLoad = settings.get_option( 'general/ask_load_session_start', True)
			
			
			if(askLoad):
				if(QtWidgets.QMessageBox.question(self, _('Last session'), _('Do you want to load last session ?'), defaultButton=QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes):
					settings.set_option( 'general/load_session_start', True)
					loadSession(project, projectAlreadyOpened, resetSession)
				else:
					settings.set_option( 'general/load_session_start', False)
			else:
				if(settings.get_option( 'general/load_session_start', True)):
					loadSession(project, projectAlreadyOpened, resetSession)
				
				
			ProjectSelector.SESSION_LOADED = True

		# Open pending file if any
		if self.mainFrame.meWidget.pending_file_to_open is not None:
			pending_file = self.mainFrame.meWidget.pending_file_to_open
			self.mainFrame.meWidget.pending_file_to_open = None
			self.mainFrame.meWidget.openFile(pending_file)


	def loadProjectsList(self):
		def clearLayout(layout):
			while layout.count():
				child = layout.takeAt(0)
				if child.widget() is not None:
					child.widget().deleteLater()
				elif child.layout() is not None:
					clearLayout(child.layout())
		
		#child = True
		#while child != None:
			#child = self.projectLayout.takeAt(0)
			#child.deleteLater()
			
		clearLayout(self.projectLayout)
			

		
		for p in self.projects:
			name = ''
			if('name' in p):
				name = p['name'].upper() + ' : \n\n'
			button = QtWidgets.QPushButton(name + p['path'])
			button.setProperty('project', p)
			button.pressed.connect(self.projectClicked)
			
			if('background_color' in p and 'font_color' in p):
				button.setStyleSheet("QPushButton { padding:20px; color: " + p['font_color']  + "; background: " + p['background_color']  + "; }");
			
			button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
			button.customContextMenuRequested.connect(self.showProjectContextMenu)
			
			self.projectLayout.addWidget(button)
			self.projectLayout.addSpacing(10)
			
			
	def projectClicked(self):
		projectPath = self.sender().property('project')['path']
		currentProject = None
		for p in self.projects:
			if p['path'] == projectPath:
				currentProject = p
				break
				
				
		if('name' not in currentProject):
			name = QtWidgets.QInputDialog.getText(self, _("Project name"), _("Please create a name for this project"))[0]
			
			if(name == '' or name == None) : return
			
			p['name'] = name
			
			settings.set_option('general/projects', self.projects)
			
		if('background_color' not in currentProject or 'font_color' not in currentProject):
			background_color = self.askColor(_('Please select a BACKGROUND color for this project'))
			p['background_color'] = background_color
			
			font_color = self.askColor(_('Please select a FONT color for this project'))
			p['font_color'] = font_color
			
			settings.set_option('general/projects', self.projects)
		
		if self.mode == 'load':
			
			if 'legacy_commands' not in currentProject:
				if(p['is_OpenBOR']):
					useLegacy = QtWidgets.QMessageBox.question(self, _('Legacy commands'), _('Do you want to use legacy commands style for this project ?'), defaultButton=QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes
					
					p['legacy_commands'] = useLegacy
					settings.set_option('general/projects', self.projects)
				else:
					p['legacy_commands'] = False
	
			
			if 'use_project_settings' not in currentProject:
				useProjectSettings = QtWidgets.QMessageBox.question(self, _('Load settings directly from project folder'), _('Do you want CMT to load and save settings directly from this project folder ?'), defaultButton=QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes
				
				p['use_project_settings'] = useProjectSettings
				settings.set_option('general/projects', self.projects)
				settings.MANAGER.save()
				
			if p['use_project_settings']:
				settings.MANAGER.location = os.path.join(p['path'], 'cmt-settings.ini')
				settings.MANAGER.read(settings.MANAGER.location)
				self.mainFrame.meWidget.menuBar.reset()
				
				
				
	
				
			
			settings.set_option('misc/legacy_commands', p['legacy_commands'])
			self.mainFrame.meWidget.menuBar.legacyCommandsOption.setChecked(p['legacy_commands'])
				
			
			self.loadProject(currentProject)
		elif self.mode == 'remove':
			self.projects.remove(currentProject)
			settings.set_option('general/projects', self.projects)
			self.sender().deleteLater()
			self.mode = 'load' # set click mode back to 'load'
			self.label.setText(_(self.LOAD_TEXT))
			
	def removeProject(self):
		if self.mode == 'remove':
			self.mode = 'load'
			self.label.setText(_(self.LOAD_TEXT))
		else:
			self.label.setText(_('Click on the project you want to remove\n or click on remove button again to cancel'))
			self.mode = 'remove'
			
	
	def reset(self):
		self.label.setText(_(self.LOAD_TEXT))
	
	def showProjectContextMenu(self, point):
		
		
		button = self.sender()
		
		self.contextActionProject = button.property('project')
		
		self.popMenu = QtWidgets.QMenu(self)
		
		rename = self.popMenu.addAction('Edit name')
		editBG = self.popMenu.addAction('Edit background color')
		editFG = self.popMenu.addAction('Edit font color')
		self.popMenu.addSeparator()
		isOpenBOR = self.popMenu.addAction('is OpenBOR project')
		isOpenBOR.setCheckable(True)
		isOpenBOR.setChecked('is_OpenBOR' not in self.contextActionProject or self.contextActionProject['is_OpenBOR'])
		remove = self.popMenu.addAction('Remove')       

		r = self.popMenu.exec_(button.mapToGlobal(point))
		
		print(r, rename)
		
		if(r == rename): self.contextEditName()
		if(r == editBG):self.contextEditColor('background_color')
		if(r == editFG):self.contextEditColor('font_color')
		if(r == remove):self.contextRemoveProject()
		if(r == isOpenBOR):
			self.contextActionProject['is_OpenBOR'] = r.isChecked()
			self.actualizeProject(self.contextActionProject)
			self.loadProjectsList()
		
	def actualizeProject(self, inputP):
		i = 0
		for p in self.projects:
			
			if(p['path'] == inputP['path']):
				self.projects[i] = inputP
			i+= 1
		settings.set_option('general/projects', self.projects)
		settings.MANAGER.save() # write changes to disk
		

		
		
	def contextEditName(self):
		name = QtWidgets.QInputDialog.getText(self, _("Project name"), _("Name"))[0]
		
		if(name == ''): return
	
		# print(self.contextActionProject)
		
		self.contextActionProject['name'] = name
		
		# print(self.contextActionProject)
		
		# print(self.projects)
		
		self.actualizeProject(self.contextActionProject)
		
		self.loadProjectsList()
		
	def contextEditColor(self, colorField):
		color = self.askColor(None)
		
		self.contextActionProject[colorField] = color
		
		self.actualizeProject(self.contextActionProject)
		
		self.loadProjectsList()
		
	def contextRemoveProject(self):
		self.actualizeProject(self.contextActionProject)
		self.projects.remove(self.contextActionProject)
		settings.set_option('general/projects', self.projects)
		# self.sender().deleteLater()
		# self.mode = 'load' # set click mode back to 'load'
		# self.label.setText(_(self.LOAD_TEXT))
		
		self.loadProjectsList()

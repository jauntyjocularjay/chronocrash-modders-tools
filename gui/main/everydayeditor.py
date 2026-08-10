import os, re, time, mimetypes, platform

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *

from common import util
from common import settings, xdg
from gui.util import FileInput, getSpriteShowingPath, loadSprite, AccessOrderedToolbar

from gui import modales

from gui.portrait import IconViewer, Portrait

from gui.main.everydaypart import EverydayPart

from data import ParsedLine

from gui.main.fileselector import FileSelector, File
from gui.entity import EntityEditorWidget
# from gui.entity.animselector import AnimSelector
#fro gui.content_indexer import ContentIndexerPanel
from gui.json_editor.keyselector import KeySelector

from gui.level import LevelEditorWidget

ROOT_PATH = '/home/piccolo/workspace/OpenBOR/'

from qutepart.syntax.colortheme import ColorTheme


import unicodedata


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')



class AbstractEverydayEditor(QtWidgets.QWidget):
	def __init__(self, parent):
		self.parent = parent
		
		self.goToRequest = 0
		self.goToMode = False
		
		QtWidgets.QWidget.__init__(self)
		
		
	def current(self):
		return self.editor.fd
		
		
	def comment(self):
		
		# return EverydayPart.comment(self.editor)
		
		#print (self.editor._highlighter.syntax().comment)
		with self.editor:
			start, end = self.editor.selectedPosition
			
			
			if (end[0] < start[0]) or (end[0] == start[0] and end[1] < start[1]):

				tmp = end
				end = start
				start = tmp
			print(start, end)
			
			startCol = start[1]
			start = start[0]
			endCol = end[1]+2
			end = end[0]
			
			
			
			
				
				#tmp = endCol
				#endCol = startCol
				#startCol = tmp
			#print(start, end)
			
			cs = self.getCommentString(start)
			multiLine = False
			if(cs == '/*'):
				closeCS = '*/'
				multiLine = True
				
			
		
				
			
				
			if(multiLine):
				if(start == end and startCol == endCol-2):
					lineContent = self.editor.lines[start]
					self.editor.lines[start] = cs + lineContent + closeCS
					return
				
				
				lineContent = self.editor.lines[start]
				j = startCol
				lineContent = lineContent[0:j] + cs + lineContent[j:] # insert(j, '#')
				self.editor.lines[start] = lineContent
				
				lineContent = self.editor.lines[end]
				j = endCol
				lineContent = lineContent[0:j] + closeCS + lineContent[j:] # insert(j, '#')
				self.editor.lines[end] = lineContent
				
				return
			
			for i in range(start, end+1):
				lineContent = self.editor.lines[i]
				if len(lineContent) == 0:
					continue
				j = 0
				while j < len(lineContent) and lineContent[j] in (' ', '	'):
					j+=1
				if j != len(lineContent):
					lineContent = lineContent[0:j] + cs + lineContent[j:] # insert(j, '#')
					self.editor.lines[i] = lineContent
			
		
	def uncomment(self):
		with self.editor:
			start, end = self.editor.selectedPosition
			
			if (end[0] < start[0]) or (end[0] == start[0] and end[1] < start[1]):

				tmp = end
				end = start
				start = tmp
			print(start, end)
			
			startCol = start[1]
			start = start[0]
			endCol = end[1]+2
			end = end[0]
				
			cs = self.getCommentString(start)
			multiLine = False
			if(cs == '/*'):
				closeCS = '*/'
				multiLine = True
			
			if(multiLine):
				lineContent = self.editor.lines[start]
				lineContent = lineContent.replace(cs, '', 1)
				self.editor.lines[start] = lineContent
				
				lineContent = self.editor.lines[end]
				lineContent = lineContent[::-1]
				lineContent = lineContent.replace(cs, '', 1)
				lineContent = lineContent[::-1]
				self.editor.lines[end] = lineContent
				
				
				
				
				return
				
			
			for i in range(start, end+1):
				lineContent = self.editor.lines[i]
				if len(lineContent) == 0:
					continue
				j = 0
				while j < len(lineContent) and lineContent[j] in (' ', '	'):
					j+=1
				if j != len(lineContent) and lineContent[j:j+len(cs)] == cs:
					lineContent = lineContent[0:j] + lineContent[j+len(cs):]
					self.editor.lines[i] = lineContent
	
	
	def getLines(self):
		return self.editor.lines
		
	def focusForSearch(self, goToMode=False):
		self.goToMode = goToMode
		print('focusForSearch');
		self.editor.initialSearchPos = None # so that it will takes cursor current position
		self.searchEntry.setFocus()
		selection = self.editor.selectedText
		
		line, column = self.editor.cursorPosition 
		self.editor.cursorPosition = line, (column - len(selection))

		if selection != '':
			text = selection
			self.searchEntry.setText(text)
		self.searchEntry.selectAll()
		
	def focusForReplace(self):
		self.replaceEntry.setFocus()
		# selection = self.editor.selectedText
  # 
		# if selection != '':
		# 	text = selection
		# 	self.searchEntry.setText(text)
		self.replaceEntry.selectAll()
		
	def getCommentString(self, blockNumber):
		
		def get_context_comment(editor):
			"""Obtenir le commentaire approprié pour le contexte actuel du curseur"""
			block = editor.textCursor().block()
			userData = block.userData()
		
			if userData is None or userData.data is None:
				# Fallback sur le commentaire global
				return editor._highlighter.syntax().comment
		
			lineData = userData.data
			contextStack = lineData[0]
			currentContext = contextStack.currentContext()
		
			# Récupérer le commentaire de la syntaxe du contexte actuel
			context_syntax = currentContext.parser.syntax
			if hasattr(context_syntax, 'comment'):
				return context_syntax.comment

			# Fallback
			return editor._highlighter.syntax().comment

		
		lang = self.editor.language()
		#print('langage', lang)
		if lang is None : return '#'
		if lang == 'Entity':
			context = self.editor.getContext(blockNumber)
			#print('context', context, context == 'Script')
			if context == 'Script' : return '//'
			else : return '#'
		elif lang == 'C':
			return '//'
		else:
			try:
				#print('here', self.editor._highlighter.syntax().__dir__())
				#print('here', vars(self.editor._highlighter.syntax()))
				#return self.editor._highlighter.syntax().comment
				return get_context_comment(self.editor)
			except:
				pass
		return '#'
	
	def notifyChange(self):
		if self.updating : return
		# if self.editor.fd.saved:
		self.updateFD()
		self.editor.fd.checkSave()
			
	def refresh(self):
		fd = self.current()
		if fd.path is None : return
		if(QtWidgets.QMessageBox.question(self, _('Refresh file'), _('Are you sure you want to reload the current file ?'), defaultButton=QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes):
			fd.loadFromDisk()
			self.setLines(fd.lines)
			
	def replace(self):
		replaceEntry = self.replaceEntry
		if(self.editor.selectedText != ''):
			self.editor.selectedText = replaceEntry.text()
			self.search()
		
	def replaceAll_OLD(self):
		
		self.editor.updatingCursor = True
		text = self.searchEntry.text()
		replaceWith = self.replaceEntry.text()
		lines = self.editor.lines
		newLines = []
		for line in lines:
			newLines.append(line.replace(text, replaceWith))
		
		self.editor.lines = newLines
		self.editor.updatingCursor = False
		
		
		
	def replaceAll(self):
		
		
		
		replaceEntry = self.replaceEntry
		newTxt = replaceEntry.text()
		
		if(self.editor.selectedText != ''):
			self.editor.replaceAllRaw(self.searchEntry.text(), newTxt)
			return
		
		self.editor.initialSearchPos = self.editor.textCursor()
		self.editor.moveCursor(QtGui.QTextCursor.Start)
		i= 0
		while self.search(True, False):
			
			self.editor.selectedText = newTxt
			i+=1
			# self.search(True, False)
			
		QtWidgets.QMessageBox.information(self, _('Replaced'), _(str(i) + " entries replaced"))
		
	def goTo(self, text):
		self.goToRequest +=1
		if(len(text) < 3): return
		
		
		
		goToRequest = self.goToRequest
		
		i =0
		for line in self.editor.lines:
			if(goToRequest != self.goToRequest):
				return
			index = line.lower().find(text)
			if(index != -1):
				if(index == 0 or (len(line[index-1].strip()) == 0)): # second condition means there should be some kind of space before the term
					self.editor.cursorPosition = (i, 0)
					#self.parent.core.notify('Go to ' + text + ' at ' +str(i), 'warning')
					return
			i+=1
	
	def search(self, searchForward=True, loop=True):
		self.editor.setCenterOnScroll(True)
		
		print('editor', self.editor.initialSearchPos)
		if(self.editor.initialSearchPos == None):
			self.editor.initialSearchPos = self.editor.textCursor()
			
		text = self.searchEntry.text()
		print('text', text)
		if(text == ''): 
			self.searchEntry.setStyleSheet("")
			self.editor.setTextCursor(self.editor.initialSearchPos)
			self.editor.initialSearchPos = None
			return False
		
		if(self.goToMode):
			return self.goTo(text)

		if searchForward:
			options = QtGui.QTextDocument.FindFlags()
		else:
			options = QtGui.QTextDocument.FindBackward
		result = self.editor.find(text, options) # first try to search from cursor to end of document
		
		if(result):
			if(not self.dark):
				self.searchEntry.setStyleSheet("QLineEdit { background: rgb(175, 255, 175); }");
			else:
				self.searchEntry.setStyleSheet("QLineEdit { background: rgb(60, 145, 60); }");
			return True
		
		elif(loop and not result):
			self.editor.moveCursor(QtGui.QTextCursor.Start)
			if not self.editor.find(text, options): # then try to search from start to end of document
			
			
				# self.editor.moveCursor(self.editor.initialSearchPos)
				self.editor.setTextCursor(self.editor.initialSearchPos)
				self.editor.initialSearchPos = None
			
				if(not self.dark):
					self.searchEntry.setStyleSheet("QLineEdit { background: rgb(255, 175, 175); }");
				else:
					self.searchEntry.setStyleSheet("QLineEdit { background: rgb(120, 50, 50); }");
				 # selection-background-color: rgb(233, 99, 0);
				 
				return False
			else:
				
				if(not self.dark):
					self.searchEntry.setStyleSheet("QLineEdit { background: rgb(175, 255, 175); }");
				else:
					self.searchEntry.setStyleSheet("QLineEdit { background: rgb(60, 145, 60); }");
				return True
	
			
				
			

			
	def searchPrevious(self):
		self.search(False)
		
	def searchTextChanged(self):
		if(self.editor.initialSearchPos != None):
			self.editor.setTextCursor(self.editor.initialSearchPos)
		
		self.search()
			
		
		
			
	def setLines(self, lines):
		self.updating = True
		self.editor.lines = lines
		self.updating = False
		
	def scrollTo(self, text):
		self.editor.setCenterOnScroll(True)
		self.editor.find(text)

	
	
	
class EverydayEditor(AbstractEverydayEditor):
	def __init__(self, parent, params={}):
		AbstractEverydayEditor.__init__(self, parent)
		
		mainLayout = QtWidgets.QHBoxLayout()
		
		# self.animSelector = AnimSelector(self, ['hideUpperBar'])
		
		# BEGIN self.alternateVersionBar
		
		#self.contentIndexerPanel = ContentIndexerPanel(self)
		self.alternateVersionBar =  AccessOrderedToolbar(self, {'itemMaxWidth':'200px', 'useColor':False});

		self.alternateVersionBar.addItem({'name':'Standard', 'path':'standard'  })
		
		self.alternateVersionBar.changed.connect(self.loadNamedVersion)
		
		w = QtWidgets.QWidget()
		l = QtWidgets.QHBoxLayout()
		
		w.setLayout(l)
		
		l.addWidget(self.alternateVersionBar, 1)
		
		addIcon = QtGui.QIcon.fromTheme('list-add')
		addAnim = QtWidgets.QPushButton(addIcon, '')
		addAnim.clicked.connect(self.addAlternateVersion)
		addAnim.setToolTip(_('Add alternate version'))
		l.addWidget(addAnim, 0)
		
		# END
		
		
		self.contentIndexerPanel = KeySelector(self, ['hideUpperBar'], {'addOnTop':w})
		
		# self.contentIndexerPanel.load(['Tosay', 'Marino'])
		
		self.checking = False
		
		self.doubleView = False
		
		
		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(5, 0, 5, 5)
		
		editorLayout = QtWidgets.QSplitter()
		self.splitter = editorLayout
		editorLayout.splitterMoved.connect(self.splitterMoved)
		# layout.setSpacing(0)
		
		editorContainerWidget = QtWidgets.QWidget()
		
		editorContainerWidget.setLayout(layout)
		
		if(settings.get_option('editor/anim_selector_on_left', False)):
			
			# mainLayout.addWidget(self.animSelector, 0)
			mainLayout.addWidget(self.contentIndexerPanel, 0)
			mainLayout.addWidget(editorContainerWidget, 1)
			
		else:
			mainLayout.addWidget(editorContainerWidget, 1)
			mainLayout.addWidget(self.contentIndexerPanel, 0)
			
		
		# self.animSelector.hide()
		
		self.setLayout(mainLayout)
		
		
		self.stack1 = QtWidgets.QStackedWidget()
		self.stack1.fd_list = {}
		self.stack2 = QtWidgets.QStackedWidget()
		self.stack2.hide()
		self.stack2.fd_list = {}
		
		
		self.themeData = None
		self.editor = self.addToStack(File(), self.stack1)
		self.addToStack(File(), self.stack2)
		
		
		#selection = QtWidgets.QTextEdit.ExtraSelection()
		#selection.cursor = self.editor.textCursor()
		##selection.format.setBackground(lineColor)
		#selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
		#self.editor.setExtraSelections([selection])

		# Initialize current FileData
		
		
		
		
		
		editorLayout.addWidget(self.stack1)
		editorLayout.addWidget(self.stack2)
		
		if('disable_contentIndexPanel' not in params):
		
			editorLayout.addWidget(self.contentIndexerPanel)
		
		theme = settings.get_option('gui/widgets_theme', None)
		
		if(theme == "Dark"):
			self.dark = True
		else:
			self.dark = False
		
		
		self.buttonBar = QtWidgets.QToolBar()
		# self.buttonBar.setContentsMargins(0, 0, 0, 0)

		self.buttonBar.setStyleSheet("QToolBar { margin:0px; padding:0px; }");
		 # border-top:1px solid #c9c9c9;
		# saveIcon = QtGui.QIcon.fromTheme('document-save')
		saveImage = QtGui.QImage('icons/save.svg')
		if(theme == "Dark"): saveImage.invertPixels()
		
		saveIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(saveImage))
		
		save = self.buttonBar.addAction(saveIcon, _('Save file (Ctrl+S)'), self.save)
		self.saveAction = save
		# self.saveAction.setVisible(False)
		self.saveAction.setEnabled(False)
		
		saveImage = QtGui.QImage('icons/undo.svg')
		if(theme == "Dark"): saveImage.invertPixels()
		
		undoIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(saveImage))
		save = self.buttonBar.addAction(undoIcon, _('Undo (Ctrl+Z)'), self.undo)
		
		saveImage = QtGui.QImage('icons/redo.svg')
		if(theme == "Dark"): saveImage.invertPixels()
		
		redoIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(saveImage))
		save = self.buttonBar.addAction(redoIcon, _('Redo (Ctrl+Shift+Z)'), self.redo)
		
		saveImage = QtGui.QImage('icons/snapshot.svg')
		if(theme == "Dark"): saveImage.invertPixels()
		
		
		snapshotIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(saveImage))
		save = self.buttonBar.addAction(snapshotIcon, _('Capture snapshot of file'), self.snapshot)

		headerAction = self.buttonBar.addAction(_('Heading'), self.insertHeader)

		if(self.parent.currentProject != None and (not( 'is_OpenBOR' in self.parent.currentProject) or self.parent.currentProject['is_OpenBOR'])):
			genPaths = self.buttonBar.addAction( _('Generate paths'), self.generatePaths)
		
		viewRevisions = self.buttonBar.addAction( _('View revisions'), self.viewRevisions)
		
		self.boldButton = self.buttonBar.addAction( _('Bold'), self.toggleBold)
		self.boldButton.setCheckable(True)
		self.boldButton.setChecked(settings.get_option('editor/force_bold', True))
		
		self.buttonBar.addSeparator()
		
		self.c1 = self.buttonBar.addAction( _('C1'), self.setCompare1)
		self.c2 = self.buttonBar.addAction( _('C2'), self.setCompare2)
		self.goCompare = self.buttonBar.addAction( _('Go'), self.compareSelected)
		
		self.buttonBar.addSeparator()
		
		
		barLayout = QtWidgets.QHBoxLayout()
		barWidget = QtWidgets.QWidget()
		barWidget.setLayout(barLayout)
		
		# self.recentFiles = {}
		# self.recentFilesQueue = []
		# self.recentFilesGroup = QtWidgets.QActionGroup(self)
		# self.recentBar = QtWidgets.QToolBar()
		self.recentBar = AccessOrderedToolbar(self, {'itemMaxWidth':'200px'});
		self.recentBar.changed.connect(self.loadRecentFile)
		self.recentBar.setStyleSheet("QToolBar {  margin :0px;} QToolButton { padding: 2px; margin:0px 2px; }  QToolButton::on {padding : 10px;  }");
		self.recentBar.showItemContextMenuExternal = self.showRecentFileContextMenu
		
		barLayout.addWidget(self.buttonBar, 0)
		barLayout.addWidget(self.recentBar, 1)
		
		
		
		layout.addWidget(barWidget, 0)
		
		layout.addWidget(editorLayout, 1)
		
		
		
		
		actionBox = QtWidgets.QHBoxLayout()
		# findNext = QtWidgets.QPushButton(QtGui.QIcon.fromTheme('go-down'), None)
		# findPrevious = QtWidgets.QPushButton(QtGui.QIcon.fromTheme('go-up'), None)
		findNext = QtWidgets.QPushButton(redoIcon, None)
		findPrevious = QtWidgets.QPushButton(undoIcon, None)
		findNext.pressed.connect(self.search)
		findPrevious.pressed.connect(self.searchPrevious)
		searchEntry = QtWidgets.QLineEdit()
		searchEntry.returnPressed.connect(self.search)
		self.searchEntry = searchEntry
		# searchEntry.textChanged.connect(self.filter)
		searchEntry.textChanged.connect(self.searchTextChanged)
		actionBox.addWidget(QtWidgets.QLabel(_('Search') + ' :'), 0)
		
		actionBox.addWidget(searchEntry, 1)
		actionBox.addWidget(findNext, 0)
		actionBox.addWidget(findPrevious, 0)
		
		layout.addLayout(actionBox, 0)
		
		actionBox = QtWidgets.QHBoxLayout()
		replace = QtWidgets.QPushButton(_('&Replace'))
		replaceAll = QtWidgets.QPushButton(_("Replace &All"))
		replace.pressed.connect(self.replace)
		replaceAll.pressed.connect(self.replaceAll)
		#scrollToCurrentButton.clicked.connect(self.scrollToCurrent)
		replaceEntry = QtWidgets.QLineEdit()
		replaceEntry.returnPressed.connect(self.replace)
		#searchEntry.textChanged.connect(self.filter)
		actionBox.addWidget(QtWidgets.QLabel(_('Replace') + ' :'), 0)
		actionBox.addWidget(replaceEntry, 1)
		actionBox.addWidget(replace, 0)
		actionBox.addWidget(replaceAll, 0)
		
		layout.addLayout(actionBox, 0)
		
		self.replaceEntry = replaceEntry
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("F5", "Refresh")), self, self.refresh)
		self.updating = False
		# self.setAcceptDrops(True)
		
		
		self.loadFileDebounce = QtCore.QTimer()
		self.loadFileDebounce.setInterval(500)
		self.loadFileDebounce.setSingleShot(True)
		self.loadFileDebounce.timeout.connect(self.postLoadFile)
		
		self.focusDebounce = QtCore.QTimer()
		self.focusDebounce.setInterval(500)
		self.focusDebounce.setSingleShot(True)
		self.focusDebounce.timeout.connect(self.postFocus)

		
		
		
		self.setTabOrder(self.searchEntry, self.replaceEntry)
		
	def addAlternateVersion(self):
		name = None
		if name == None:
			name = QtWidgets.QInputDialog.getText(self, _("Create alternate version"), _("Name"))[0]
			
		if(name == None or name == ''): return
			
		key = slugify(name)
			
		self.alternateVersionBar.addItem({'name':name, 'path':key  })
		
		self.manuallyAddedVersion = key
		
		self.alternateVersionBar.togglePath(key)
		
		
				
	
	def reloadSplitterPos(self):
		splitterPos = settings.get_option('gui/editor_splitter_pos1', 0)
		if(splitterPos != 0):
			self.splitter.moveSplitter(splitterPos, 1)
			
		splitterPos = settings.get_option('gui/editor_splitter_pos2', 0)
		if(splitterPos != 0):
			self.splitter.moveSplitter(splitterPos, 2)
	
	def splitterMoved(self, pos, index):
		if(self.isVisible()):
			
			if(not self.doubleView):
				print("Editor splitterMoved", pos, index)
				settings.set_option('gui/editor_splitter_pos' + str(index), pos)
				# settings.set_option('gui/editor_splitter_index', index)
	
	
	def loadContentIndexerPanel(self, lines):
		keys = []
		if(self.editor.fd.path == None):
			self.contentIndexerPanel.clear()
			return

		def extractHeaderTitle(line):
			"""Extract title from a header box middle line."""
			# Unicode style: ║ title ║
			if '║' in line:
				parts = line.split('║')
				if len(parts) >= 3:
					return parts[1].strip()
			# Block style: █ title █ (but not block inverse which has █▌ and ▐█)
			if '█' in line and '▌' not in line and '▐' not in line:
				parts = line.split('█')
				if len(parts) >= 3:
					return parts[1].strip()
			# Block inverse style: █▌ title ▐█
			if '█▌' in line and '▐█' in line:
				start = line.find('█▌') + 2
				end = line.find('▐█')
				if start < end:
					return line[start:end].strip()
			# ASCII style: | title |
			if '|' in line:
				parts = line.split('|')
				if len(parts) >= 3:
					return parts[1].strip()
			return None

		def isHeaderTitleLine(line):
			"""Check if line is the middle line of a header box (contains the title)."""
			# Must have matching border characters on both sides
			# Unicode: ║...║
			if line.count('║') >= 2:
				return True
			# Block inverse: █▌...▐█
			if '█▌' in line and '▐█' in line:
				return True
			# Block (not inverse): █...█ with content between
			if line.count('█') >= 2 and '▌' not in line and '▐' not in line and '▄' not in line and '▀' not in line:
				return True
			# ASCII: |...|
			if line.count('|') >= 2 and '+' not in line:
				return True
			return False

		if self.editor.fd.path.endswith('.py'):

			for lineNum, line in enumerate(lines):
				# Check for header title
				if isHeaderTitleLine(line):
					title = extractHeaderTitle(line)
					if title:
						keys.append({'name': title, 'isHeader': True, 'startLine': lineNum})
						continue

				parts = line.split()
				try:
					index = parts.index('def')
					nextWord = parts[index+1]
					parts = nextWord.split('(')
					nextWord = parts[0]
					keys.append({'name': 'def ' + nextWord, 'isHeader': False, 'startLine': lineNum})
				except:
					pass

		else:
			inClass = False
			inFunction = False
			for lineNum, line in enumerate(lines):
				# Check for header title first
				if isHeaderTitleLine(line):
					title = extractHeaderTitle(line)
					if title:
						keys.append({'name': title, 'isHeader': True, 'startLine': lineNum})
						continue

				parts = line.split('//')
				line_clean = parts[0]
				parts = line_clean.split()
				if(len(parts) == 0): continue
				# if(parts[0].startswith ( '//')): continue

				# print(parts)
				if('class' in parts):
					inClass = True
					continue

				# remove everything between quotes
				# line = re.sub("(?<=\")(.*?)(?=\")", '',  line)
				line_clean = re.sub('"([^"]*)"', '', line_clean)
				line_clean = re.sub('\'([^\']*)\'', '', line_clean)

				if(inClass):
					# print('inClass')
					if(not inFunction):
						index = line_clean.index('{') if '{' in line_clean else None
						index_parenthese = line_clean.index('(') if '(' in line_clean else None

						if(index != None and index_parenthese != None and index_parenthese < index):
							inFunction = True
							brackets_open = line_clean.count('{') # line.count('{') NOTE not bad, but should ignore params (ignore curly brackets in first parentheses)
							brackets_close = line_clean.count('}')
							subIndex = 0
							while parts[subIndex] in ['async', 'static']:
								subIndex+=1
							keys.append({'name': parts[subIndex], 'isHeader': False, 'startLine': lineNum})

							if(brackets_open == brackets_close): # one liner function
								inFunction = False
					else:
						brackets_open += line_clean.count('{')
						brackets_close += line_clean.count('}')

						# if(len(keys) > 0):
						# 	print(keys[-1], brackets_open, brackets_close)

						if(brackets_open == brackets_close):
							inFunction = False

				else:
					if(parts[0] == 'function'):
						keys.append({'name': 'function ' + parts[1], 'isHeader': False, 'startLine': lineNum})


			pass

		# Calculate endLine for each section (startLine of next section - 1, or end of file)
		totalLines = len(lines)
		for i, key in enumerate(keys):
			if i + 1 < len(keys):
				key['endLine'] = keys[i + 1]['startLine'] - 1
			else:
				key['endLine'] = totalLines - 1

		self.contentIndexerPanel.clear()
		self.contentIndexerPanel.load(keys)
	
	def loadKey(self, key):
		self.editor.setCenterOnScroll(True)
		self.goTo(key.lower())

	def highlightCurrentSection(self, lineNumber):
		"""Find the section (function or header) containing the given line and highlight it in contentIndexerPanel."""
		self.contentIndexerPanel.selectByLine(lineNumber)

	def setCompare(self, ID):
		output = self.editor.selectedText
		
		has_selected = True
		
		if(len(output) == 0):
			has_selected = False
			self.parent.core.notify('You can select specific part of text to compare', 'warning')
			
			# return
			
			output = '\n'.join(list(self.editor.lines))
		
		dirPath = xdg.get_data_home()
		
		f = open(os.path.join(dirPath, 'tmp_compare' + ID +'.txt'), 'w')
		f.write(output)
		f.close()
		
		if(has_selected):
			self.parent.core.notify('Selected text is set for comparison on side ' + ID)
		else:
			self.parent.core.notify('No selected text, whole file is set for comparison on side ' + ID)
		
	def setCompare1(self):
		self.setCompare('1');
		
	def setCompare2(self):
		self.setCompare('2');
		
	def compareSelected(self):
		self.parent.core.notify('Starting comparison of selected texts')
		
		import subprocess
		dirPath = xdg.get_data_home()
		self.compare1_path = os.path.join(dirPath, 'tmp_compare' + '1' +'.txt')
		self.compare2_path = os.path.join(dirPath, 'tmp_compare' + '2' +'.txt')
		
		
			
		command = settings.get_option('compare_tool/compare_program_path', 'meld')
		commandMask = settings.get_option('compare_tool/command_mask', '{program} {file1} {file2}')
		commandMask = commandMask.replace(' ', '@')
		commandMask = commandMask.replace('{program}', command)
		commandMask = commandMask.replace('{file1}', self.compare1_path)
		commandMask = commandMask.replace('{file2}', self.compare2_path)
		
		subprocess.Popen(commandMask.split('@'))
		
	
	def showRecentFileContextMenu(self, point, button, item):
		popMenu = QtWidgets.QMenu(self)

		load_in_actions = {}
		selectedAction = [None]  # Use list to allow modification in nested function

		def actionTriggered(action):
			selectedAction[0] = action
			popMenu.close()

		for projectName in self.parent.loaded_projects:
			if(projectName != item.projectName):
				projectData = self.parent.loaded_projects[projectName]

				buttonWidget = QtWidgets.QToolButton(popMenu)
				buttonWidget.setText(_('Open equivalent in project ') + projectName)
				buttonWidget.setStyleSheet("QToolButton { color:" + projectData['font_color'] + ";background:" + projectData['background_color']  + "; } QToolButton:hover { font-weight:bold;} ")
				action = QtWidgets.QWidgetAction(self)
				action.setDefaultWidget(buttonWidget)

				buttonWidget.pressed.connect(lambda x=action: actionTriggered(x))

				popMenu.addAction(action)
				load_in_actions[action] = projectName

		popMenu.exec_(button.mapToGlobal(point))

		r = selectedAction[0]
		if(r in load_in_actions):
			destinationProject = load_in_actions[r]
			compare1_path = item.path

			# we remove project root from path, to get only the relative path
			relativePath = compare1_path.replace(  self.parent.loaded_projects[ item.projectName ]['path'], '' )

			compare2_path = self.parent.loaded_projects[ destinationProject]['path'] + relativePath

			self.parent.openFile(compare2_path)
	
	
	def addRecentFile(self, fd):
		# We need to make sure fd is colored if multiple projects are opened
		if(fd.projectName != 'Unknown' and (len( self.parent.loaded_projects) > 1 or settings.get_option('gui/enable_color_with_one_project', False)) ):
			if fd.projectName in self.parent.loaded_projects:
				project = self.parent.loaded_projects[fd.projectName]
				# fd.bgColor = 'red'
				# fd.fgColor = 'white'
				fd.bgColor = project['background_color'];
				fd.fgColor = project['font_color'];
			# else:
			# 	for item in self.parent.loaded_projects.items():
			# 		if item.name == fd.projectName:
			# 			fd.bgColor = item['background_color'];
			# 			fd.fgColor = item['font_color'];
					
				
		self.recentBar.addItem(fd)
		
# 		if(fd.path in self.recentFiles):
# 			pathToRemove = fd.path # not removed by itself
# 			del self.recentFilesQueue[ self.recentFilesQueue.index(pathToRemove) ]
# 			actionToRemove = self.recentFiles[ pathToRemove  ]
# 			self.recentBar.removeAction(actionToRemove)
# 			del self.recentFiles[pathToRemove]
# 		else: # not present, so potentially need to make space
# 			if(len(self.recentFilesQueue) > 5):
# 				pathToRemove = self.recentFilesQueue.pop() # remove by itself
# 				actionToRemove = self.recentFiles[ pathToRemove  ]
# 				self.recentBar.removeAction(actionToRemove)
# 				del self.recentFiles[pathToRemove]
# 		
# 		if(len(self.recentFiles) > 0):
# 			firstAction = self.recentFiles[  self.recentFilesQueue[0] ]
# 		else:
# 			firstAction = None
# 		
# 		action = self.recentBar.addAction(fd.name,  lambda:self.loadRecentFile(fd))
# 		self.recentBar.insertAction(firstAction, action)
# 		action.setActionGroup(self.recentFilesGroup)
# 		action.setCheckable(True)
# 		action.setChecked(True)
# 		
# 		self.recentFiles[fd.path] = action
# 		self.recentFilesQueue.insert(0, fd.path)
		
		
	def snapshot(self):
		comment = QtWidgets.QInputDialog.getText(self, _("Comment for this snapshot"), _("Comment"))[0]
			
		if(comment == None or comment == ''): comment = None
		self.editor.fd.snapshot(comment)
		self.parent.core.notify('Snapshot created', 'success')
	
	def loadNamedVersion(self, version):
		# self.parent.core.notify('load version ' + version.path, 'warning')
		
		# NOTE revision.path = "standard", "alternate", ...
		
		fd = self.editor.fd
		
		versionKey = version.path
		
		if not hasattr(fd, 'version'):
			previousVersion = 'standard'
		else:
			previousVersion = fd.version
		
		
		
		
		
		
		
		if not hasattr(fd, 'versions'): fd.versions = {}
		
		
		
		
		project = self.parent.loaded_projects[fd.projectName]
		
		dirPath = xdg.get_data_home()
		
		# self.parent.core.notify('dirPath ' + dirPath, 'warning')
		
		rPath_base = fd.path.replace(project['path'], '')
		if(rPath_base.startswith('/')): rPath_base = rPath_base[1:]
		rPath = rPath_base  + '.' + versionKey
		
		# if(rPath.startswith('/')): rPath = rPath[1:]
		
		# self.parent.core.notify('rPath ' + rPath, 'warning')
		
		versionPath_project = os.path.join(dirPath, fd.projectName)
		
		# print('versionPath', versionPath_project)
		# print('rPath', rPath)
		
		versionPath = os.path.join(versionPath_project, rPath)
		print('rPath', rPath)
		
		# self.parent.core.notify('version path ' + versionPath, 'warning')
		
		if not previousVersion in fd.versions:
			rPath = rPath_base  + '.' + previousVersion
			previous_versionPath = os.path.join(versionPath_project, rPath)
			versionFD = File(previous_versionPath, fd.projectName)
			versionFD.createPathIfNeeded = True
			fd.versions[previousVersion] = versionFD
			versionFD.loadFromDisk(True)
		
		
		if not versionKey in fd.versions:
			
			versionFD = File(versionPath, fd.projectName)
			versionFD.createPathIfNeeded = True
			fd.versions[versionKey] = versionFD
			versionFD.loadFromDisk(True)
			
			if(hasattr(self, 'manuallyAddedVersion') and self.manuallyAddedVersion == versionKey):
				self.manuallyAddedVersion = None
				if(QtWidgets.QMessageBox.question(self, _('Copy content'), _('Do you want to use current content as base for this new version ?'), defaultButton=QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes):
					versionFD.lines = list(fd.lines)
			
		else:
			versionFD = fd.versions[versionKey]
			
		# self.parent.updateFD() # save editor lines to file
		# need the equivalent for version, save editor lines to version
		previous_FD = fd.versions[previousVersion]
		previous_FD.lines = list(self.editor.lines)
		previous_FD.save()
		self.editor.saveScroll()
		previous_FD.cursorPosition = self.editor.cursorPosition
		previous_FD.previousScroll = self.editor.previousScroll
		
		self.editor.lines = versionFD.lines
		fd.version = versionKey
		
		if(hasattr(versionFD, 'previousScroll')):
			self.editor.cursorPosition = versionFD.cursorPosition
			self.editor.previousScroll = versionFD.previousScroll
			self.editor.restoreScroll()
			
		self.loadFileDebounce_ignoreVersion_once = True
		self.loadFileDebounce.start()
		
		
	def loadPotentialVersionList(self):
		fd = self.editor.fd
		
		if fd.projectName == 'Unknown' or fd.projectName not in self.parent.loaded_projects: return

		project = self.parent.loaded_projects[fd.projectName]
		
		dirPath = xdg.get_data_home()
		
		# self.parent.core.notify('dirPath ' + dirPath, 'warning')
		
		rPath_base = fd.path.replace(project['path'], '')
		if(rPath_base.startswith('/')): rPath_base = rPath_base[1:]
		rPath = rPath_base  + '.' # Here we only add the dot. After the dot there should be a potential version
		
		# if(rPath.startswith('/')): rPath = rPath[1:]
		
		# self.parent.core.notify('rPath ' + rPath, 'warning')
		
		versionPath_project = os.path.join(dirPath, fd.projectName)
		
		# print('versionPath', versionPath_project)
		# print('rPath', rPath)
		
		versionPath = os.path.join(versionPath_project, rPath)
		
		dir = os.path.dirname(versionPath)
		fileName = os.path.basename(versionPath) # "Blabla.js."
		
		added = False
		standardAdded = False
		if not os.path.exists(dir): return
		for path in os.listdir(dir):
			if path.startswith(fileName) and not path.endswith('.1'):
				added = True
				versionName = path.replace(fileName, '')
				if(versionName == 'standard'): standardAdded = True
				self.alternateVersionBar.addItem({'name':versionName, 'path':versionName})
			
		if added and not standardAdded:
			self.alternateVersionBar.addItem({'name':'standard', 'path':'standard'})
		
		
	def loadRecentFile(self, fd):
		
		self.parent.loadFile(fd)
		
	#@util.threaded
	def detectSyntax(self, editor, path):
		if(path is not None):
			extension = os.path.splitext(path)[1]
		else:
			extension = None
			
		if extension == '.txt':
			#self.editor.detectSyntax(xmlFileName='c.xml')
			theme = settings.get_option('gui/editor_theme', None)
			print("checking theme")
			if(theme != None and 'dark' in theme.lower()):
				print("theme is dark")
				editor.detectSyntax(xmlFileName='entity-dark.xml')
			else:
				editor.detectSyntax(xmlFileName='entity.xml')
		elif extension == '.jsx':
			# editor.detectSyntax(xmlFileName='jsx.xml')
			editor.detectSyntax(xmlFileName='javascript-react.xml')
		elif extension == '.ts':
			editor.detectSyntax(xmlFileName='typescript.xml')
		elif extension == '.tsx':
			editor.detectSyntax(xmlFileName='typescript-react.xml')
		else:
			editor.detectSyntax(sourceFilePath=path)

				
	def addToStack(self, fd, stack=None):
		
				
		
		if stack is None: # Take current stack
			stack = self.editor.parent()
		
		editor = EverydayPart()
		editor.setTheme(self.themeData)
		
		editor.fd = fd
		
		
		self.initSettings(editor)
		stack.fd_list[fd] = editor
		stack.addWidget(editor)
		
		if fd.path is not None:
			extension = os.path.splitext(fd.path)[1]
			#mt = mimetypes.guess_type(path)[0]
			#print(mt)
		else:
			extension = None
		self.detectSyntax(editor, fd.path)
		if fd.lines != None:
			editor.lines = list(fd.lines)
			
		self.changeDebounce = QtCore.QTimer()
		self.changeDebounce.setInterval(2500)
		self.changeDebounce.setSingleShot(True)
		self.changeDebounce.timeout.connect(self.notifyChange)
		# editor.textChanged.connect(self.notifyChange) # TODO debounce this
		editor.textChanged.connect(self.notifyChange_debounceStart)
		editor.toolTipEvent.connect(self.showToolTip) # TODO-REENABLE
		# editor.installEventFilter(self) # NOTE : overkill because only used for focusIn. Replaced with focusInSignal
		editor.focusInSignal.connect(self.editorGotFocus)
		editor.doubleClickSignal.connect(self.highlightCurrentSection)
		return editor

		
		
	def initSettings(self, editor):
		# fontFamily = settings.get_option('editor/font_family', 'Courier')
		# fontSize = settings.get_option('editor/font_size', 12)
		
		
		fontFamilies = {'Windows':'Courier New',
                        'Darwin': 'Menlo'}
		fontFamily = fontFamilies.get(platform.system(), 'Monospace')
		
		fontFamily = settings.get_option('editor/font_family', fontFamily)
		fontSize = settings.get_option('editor/font_size', 10)
		font = QtGui.QFont(fontFamily)
		font.setPointSize(fontSize)
		editor.setFont(font)
		editor.currentFont = font
		
		editor.drawIncorrectIndentation = False
		editor.indentUseTabs = True
		

		
	# def dropEvent(self,e):
	# 	print("\nEditor Drop Event")
	# 	super().dropEvent(e)
		
	def eventFilter(self, obj, e):
		print('eventFilter', e.type(), e.FocusIn)
		if(e.type() == e.FocusIn and type(obj) == EverydayPart):
			# self.editor = obj
			# return True
			
			if self.stack1.indexOf(obj) != -1:
				self.parent.headerWidget.setInfo(obj.fd)
			elif self.stack2.indexOf(obj) != -1:
				self.parent.headerWidget.setInfo(obj.fd)
			
			#self.editor.fd.state = 0
			obj.fd.state = 1
		
			# Update recent bar (only really useful here if split view)
			# self.recentBar.addItem(obj.fd)
			self.addRecentFile(obj.fd) # same, but also adds project color
			
			self.editor = obj
			self.focusDebounce.start()
			
			

		#else:
		return False
		
	def editorGotFocus(self, editor, e):
		self.eventFilter(editor, e)
		pass
		
	
	def checkChangeOutside(self):
		self.checking = True
		fd = self.editor.fd
		if not fd.checkMTime():
			dialogResponse = QtWidgets.QMessageBox.question(self, _('Refresh file'), _('This file was changed outside CMT, would you like to reload it ? (' + str(fd.mtime) +')'), defaultButton=QtWidgets.QMessageBox.Yes)
			print('dialogResponse', dialogResponse)
			if(dialogResponse == QtWidgets.QMessageBox.Yes):
				fd.loadFromDisk()
				self.setLines(fd.lines)
			else:
				fd.updateMTime()
		self.checking = False

	def keyPressEvent(self, e):
		
				
		if e.key() == QtCore.Qt.Key_Escape:
			print('escape pressed')
			self.editor.initialSearchPos = None
		else:
			AbstractEverydayEditor.keyPressEvent(self, e)
	


	def updateTheme(self):
		for fd in self.stack1.fd_list:
			editor = self.stack1.fd_list[fd]
			self.detectSyntax(editor, fd.path)
	
	def getEditors(self):
		return list(self.stack1.fd_list.values()) + list(self.stack2.fd_list.values())
	
	
	def generatePaths(self):
		res = modales.GeneratePathsDialog(self.editor).exec()

		#self.editor.selectedText = res

	def insertHeader(self):
		# Get comment prefix based on current file language
		commentPrefix = self.getCommentString(self.editor.textCursor().blockNumber())
		res = modales.InsertHeaderDialog(self.editor, commentPrefix).exec()
		# self.loadFileDebounce_ignoreVersion_once = True
		# self.loadFileDebounce.start()
		
		self.setCurrent(self.editor.fd)


	def loadAnim(self, ID):
		#self.scrollTo(QtCore.QRegExp("anim(\\s)"+ID))
		self.editor.search(QtCore.QRegExp("anim(\\s)"+ID))
		
	def updateSaveIcon(self):
		fd = self.editor.fd
		if(fd.saved): self.saveAction.setEnabled(False)
		else : self.saveAction.setEnabled(True)
		
	def notifyChange_debounceStart(self):
		if self.updating: return
		self.changeDebounce.start()
	
	def notifyChange(self):
		if self.updating : return
		AbstractEverydayEditor.notifyChange(self)
		fd = self.editor.fd
		if(fd.saved): self.saveAction.setEnabled(False)
		else : self.saveAction.setEnabled(True)
		
		self.updating = True
		
		
		self.enableSync = True
		
		
		# syncing content if file opened in multiple views
		if self.enableSync and self.stack1.indexOf(self.editor) != -1:
			
			if fd in self.stack2.fd_list:
				toSyncEditor = self.stack2.fd_list[fd]
				#pos = toSyncEditor.cursorPosition
				toSyncEditor.saveScroll()
				toSyncEditor.lines = list(self.editor.lines)
				#toSyncEditor.setCenterOnScroll(True)
				#toSyncEditor.cursorPosition = pos
				
				#toSyncEditor.moveCursor(QtGui.QTextCursor.Start)
				toSyncEditor.restoreScroll()
				
		if self.enableSync and self.stack2.indexOf(self.editor) != -1:
			
			if fd in self.stack1.fd_list:
				toSyncEditor = self.stack1.fd_list[fd]
				toSyncEditor.saveScroll()
				
				#pos = toSyncEditor.cursorPosition
				toSyncEditor.lines = list(self.editor.lines)
				#toSyncEditor.cursorPosition = pos
				toSyncEditor.restoreScroll()
		self.updating = False
	
	
	def redo(self):
		self.editor.redo()
	
	def remove(self, fd):
		if fd in self.stack1.fd_list:
			
			editor = self.stack1.fd_list[fd]
			wasCurrent = False
			if(editor == self.editor):
				wasCurrent = True
			self.stack1.removeWidget(editor)
			del self.stack1.fd_list[fd]
			if(wasCurrent):
				
				self.editor = self.stack1.currentWidget()
				self.parent.headerWidget.setInfo(self.editor.fd)
				self.recentBar.addItem(self.editor.fd)

		
		if fd in self.stack2.fd_list:
			editor = self.stack2.fd_list[fd]
			wasCurrent = False
			if(editor == self.editor):
				wasCurrent = True
			
			self.stack2.removeWidget(editor)
			del self.stack2.fd_list[fd]
			if(wasCurrent):
				self.editor = self.stack2.currentWidget()
				self.parent.headerWidget.setInfo(self.editor.fd)
			
		
			

	def selectNextTab(self):
		# self.parent.core.notify('Select next tab', 'warning')
		self.recentBar.toggleNext()
		
	def selectPreviousTab(self):
		self.recentBar.togglePrevious()
			
	def setDoubleView(self, doubleView):
		self.doubleView = doubleView
		if doubleView:
			
			width = int(self.stack1.currentWidget().frameGeometry().width() / 2)
			
			
			self.stack1.show()
			self.stack2.show()
			self.editor.setFocus()
			
			self.splitter.moveSplitter(width, 1)
		else:
		
			
		
			self.stack2.hide()
			self.editor = self.stack1.currentWidget()
			self.editor.setFocus()
			
			self.reloadSplitterPos()
			
			

		
		
	def setCurrent(self, fd, stack=None):
		
		if(fd.saved): self.saveAction.setEnabled(False)
		else : self.saveAction.setEnabled(True)
		
		if stack is None: # Take current stack
			stack = self.editor.parent()
		
		
		firstLoad = False
		
		print('stack is', stack)
		if fd not in stack.fd_list:
			print('was not in stack')
			editor = self.addToStack(fd, stack)
			firstLoad = True
		else:
			print('was in stack')
			editor = stack.fd_list[fd]

		stack.setCurrentWidget(editor)
		editor.setFocus()
		
		if(fd.category == 'Entity'):
			# self.animSelector.show()
			# self.contentIndexerPanel.hide()
			self.contentIndexerPanel.toggleOption('animation', True)
			self.contentIndexerPanel.loadFrom(editor.lines)
		else:
			# self.animSelector.hide()
			# self.contentIndexerPanel.show()
			self.contentIndexerPanel.toggleOption('animation', False)
			self.postLoadFile_firstLoad = firstLoad
			self.loadFileDebounce.start()
			
		
		
	def postFocus(self):
		# Update fileSelector to reflect focused item
		fd = self.editor.fd
		if(hasattr(self, "fileSelector")):
			self.fileSelector.updateStates(fd)

		#return True
		
		if not self.checking:
			self.checkChangeOutside()
			
	def postLoadFile(self):
		fd =  self.editor.fd
		# lines = fd.lines # doesn't encompass unsaved
		lines = self.editor.lines # encompass unsaved
		self.loadContentIndexerPanel(lines)
		
		if hasattr(self, 'loadFileDebounce_ignoreVersion_once') and self.loadFileDebounce_ignoreVersion_once:
			self.loadFileDebounce_ignoreVersion_once = False
			return
		
		self.alternateVersionBar.reset()
		version = None
		standardAdded = False
		
		
		
		
		if hasattr(fd, 'versions'):
			if not fd.versions: #means empty
				if hasattr(fd, 'versions_keys'):
					for key in fd.versions_keys:
						if key == 'standard': standardAdded = True
						self.alternateVersionBar.addItem({'name':key, 'path':key})
			else:
				for key in fd.versions:
					if key == 'standard': standardAdded = True
					self.alternateVersionBar.addItem({'name':key, 'path':key})
					
			version = fd.version
		if not standardAdded : self.alternateVersionBar.addItem({'name':'Standard', 'path':'standard'})
		
		if version is not None:
			# pass
			# Ça faut le faire seulement quand c'est la première fois qu'on charge ce fichier
			if self.postLoadFile_firstLoad :
				if version not in fd.versions:
					self.parent.core.notify('Missing version ' + version, 'warning')
					# In that case cannot delay the potential
					self.loadPotentialVersionList()
					self.alternateVersionBar.togglePath(version)
				else:
					self.alternateVersionBar.togglePath(version)
			else:
				# False parameter ensures this is just a cosmetic change (we highlight the right version in alternateVersionBar)
				if version not in fd.versions:
					self.parent.core.notify('Missing version ' + version, 'warning')
					self.loadPotentialVersionList()
					self.alternateVersionBar.togglePath(version, False)
				else:
					self.alternateVersionBar.togglePath(version, False)
		elif self.postLoadFile_firstLoad :
			# No version in session, but should also check in disk...
			self.loadPotentialVersionList()
		
		
		#self.editor.current.lines = list(self.editor.lines)
		#self.updating = True
		#editor.lines = fd.lines
		#self.editor.current = fd
		#self.updating = False
		
	def extractData(self, command, pLine):
		if(command not in('bglayer', 'fglayer', 'background', 'panel', 'frontpanel')):
			return ''
		params = {
	    'bglayer':["path" ,"xratio" ,"zratio" ,"xposition" ,"zposition" ,"xspacing" ,"zspacing" ,"xrepeat" ,"zrepeat" ,"transparency" ,"alpha" ,"watermode" ,"amplitude" ,"wavelength" ,"wavespeed" ,"bgspeedratio"],
	    
	    'fglayer':['path' ,"z" ,"xratio" ,"zratio" ,"xposition" ,"zposition" ,"xspacing" ,"zspacing" ,"xrepeat" ,"zrepeat" ,"transparency" ,"alpha" ,"watermode" ,"amplitude" ,"wavelength" ,"wavespeed" ,"bgspeedratio"],
	    
	    'background':["path" ,"xratio" ,"zratio" ,"xposition" ,"zposition" ,"xspacing" ,"zspacing" ,"xrepeat" ,"zrepeat" ,"transparency" ,"alpha"],
	    	
	    'panel':['path'],
	    'frontpanel':['path']
	    	
	    
		}
		
		i = 1
		txt = '<ul>'

		while(pLine.next() != None and i < len(params[command])):
			print('command', command, pLine.current(), params[command])
			txt += '<li>' + params[command][i] + ' = ' + pLine.current() + '</li>'
			i+= 1
			
		notSet = params[command][i:]
		if(len(notSet) > 0):
			txt += '<li>Not set : ' + ', '.join(notSet) + '</li>'
		return txt
	
	

	
	
	def showToolTip(self, lineNumber, text, e):
		try:
			if text.count('\n') > 0:
				lines = text.split('\n')
				frameCount = 0
				for line in lines:
					pLine = ParsedLine(line)
					part = pLine.next()
					if part == 'frame':
						frameCount += 1
						
				output = 'Selected "frame" count : ' + str(frameCount)
				QToolTip.showText(e.globalPos(), output)
				return
			elif text != '':
				pLine = ParsedLine(text)
				part = pLine.next()
				if part in ('frame', 'bglayer', 'fglayer', 'background', 'panel', 'frontpanel'):
					p = pLine.next()
					if(p is None): return
					print('tooltip', part, p)
					data_path = settings.get_option('general/data_path', '')
					path = os.path.join(os.path.dirname(data_path), p)
					print(path)
					
					
					com = pLine.getCom()
				
				
					transp = 0
					if('transp=' in com):
						parts = com.split('transp=')
						part = parts[1]
						parts = part.split(';')
						transp = parts[0]
					
					
					
					
					
					img = loadSprite(path, transp)
					data = QtCore.QByteArray()
					buffer = QtCore.QBuffer(data)
					#buffer.open(QtCore.QIODevice.WriteOnly);
					img.save(buffer, 'PNG')
					#print('ELIA', data.toBase64())
					b64 =  str(data.toBase64())[2:-1]
					text = "<div><img alt='Embedded Image' src='data:image/png;base64," + b64 + "' />"
					#text += "<img src='" + getSpriteShowingPath(path) + "'></div>"
					text += self.extractData(part, pLine)
					
					if(part == 'frame'):
						frameCount = 0
						part = None
						lineNumber = lineNumber -1
						while lineNumber >= 0 and part != 'anim':
							line = self.editor.lines[lineNumber]
							pLine = ParsedLine(line)
							part = pLine.next()
							if part == 'frame' :
								frameCount += 1
							lineNumber -=1
							
						text += '<br /><div>Frame number : ' + str(frameCount) + '</div>'
					
					QToolTip.showText(e.globalPos(), text)
					return
			QToolTip.hideText()
		except IndexError:
			print('TOOL TIP INDEX ERROR')
		
	def save(self):
		self.updateFD()
		current = self.current()
		if current is None:
			return
		if current.path is None and not hasattr(current, 'noteId'):
			self.parent.saveAs()
		else:
			current.lines = self.getLines()
			current.save()

			if getattr(self, "updateSaveIcon", None) != None:
				self.updateSaveIcon()
	
	
	
	def toggleBold(self):
		checked = self.boldButton.isChecked()
		settings.set_option('editor/force_bold', checked)
		QtWidgets.QMessageBox.information(self, _('Please restart'), _("This setting will be applied on next restart"))
	
	def updateFD(self):
		self.editor.fd.lines = list(self.editor.lines)
		self.editor.fd.checkSave()
		#self.editor2.current.lines = list(self.editor2.lines)
			


	def undo(self):
		self.editor.undo()
		
	def viewRevisions(self):
		self.parent.core.setMode('backupViewer', {'path':self.current().path})
	
	
	
class BasicEverydayEditor(AbstractEverydayEditor):
	def __init__(self, parent):
		AbstractEverydayEditor.__init__(self, parent)
		layout = QtWidgets.QVBoxLayout()
		self.setLayout(layout)
		self.editor = EverydayPart()
		
		editorLayout = QtWidgets.QSplitter()
		editorLayout.addWidget(self.editor)
		layout.addWidget(editorLayout, 1)
		
		searchEntry = QtWidgets.QLineEdit()
		searchEntry.returnPressed.connect(self.search)
		self.searchEntry = searchEntry
		
		self.dark = False
		
		layout.addWidget(searchEntry, 0)

'''
	A version that use a single instance of editor widget
'''
class EverydayEditorLight(AbstractEverydayEditor):
	def __init__(self, parent):
		AbstractEverydayEditor.__init__(self, parent)
		layout = QtWidgets.QVBoxLayout()
		self.setLayout(layout)
		self.editor1 = EverydayPart()
		self.editor2 = EverydayPart()
		self.editor2.hide()
		self.editor = self.editor1
		#font = QtGui.QFont("Monospace")
		font = QtGui.QFont("Courier")
		font.setPointSize(12)
		self.editor.setFont(font)
		self.editor.currentFont = font
		
		self.editor.drawIncorrectIndentation = False
		self.editor.indentUseTabs = True
		
		font = QtGui.QFont("Courier")
		font.setPointSize(12)
		self.editor2.setFont(font)
		self.editor2.currentFont = font
		
		
		
		#selection = QtWidgets.QTextEdit.ExtraSelection()
		#selection.cursor = self.editor.textCursor()
		##selection.format.setBackground(lineColor)
		#selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
		#self.editor.setExtraSelections([selection])

		# Initialize current FileData
		self.editor1.current = File()
		self.editor2.current = File()
		
		self.editor1.installEventFilter(self)
		self.editor2.installEventFilter(self)
		
		self.editor1.textChanged.connect(self.notifyChange)
		
		editorLayout = QtWidgets.QSplitter()
		
		editorLayout.addWidget(self.editor1)
		editorLayout.addWidget(self.editor2)
		
		layout.addWidget(editorLayout, 1)
		
		actionBox = QtWidgets.QHBoxLayout()
		findNext = QtWidgets.QPushButton(QtGui.QIcon.fromTheme('go-down'), None)
		findPrevious = QtWidgets.QPushButton(QtGui.QIcon.fromTheme('go-up'), None)
		#scrollToCurrentButton.clicked.connect(self.scrollToCurrent)
		searchEntry = QtWidgets.QLineEdit()
		searchEntry.returnPressed.connect(self.search)
		self.searchEntry = searchEntry
		#searchEntry.textChanged.connect(self.filter)
		actionBox.addWidget(findNext, 0)
		actionBox.addWidget(findPrevious, 0)
		actionBox.addWidget(searchEntry, 1)
		
		layout.addLayout(actionBox, 0)
		
		actionBox = QtWidgets.QHBoxLayout()
		scrollToCurrentButton = QtWidgets.QPushButton(QtGui.QIcon.fromTheme('go-jump'), None)
		replaceAll = QtWidgets.QPushButton(_("Replace &All"), self.replaceAll)
		#scrollToCurrentButton.clicked.connect(self.scrollToCurrent)
		replaceEntry = QtWidgets.QLineEdit()
		replaceEntry.returnPressed.connect(self.replace)
		#searchEntry.textChanged.connect(self.filter)
		actionBox.addWidget(scrollToCurrentButton, 0)
		actionBox.addWidget(replaceEntry, 1)
		
		layout.addLayout(actionBox, 0)
		
		self.replaceEntry = replaceEntry
		self.updating = False
		
		


		
	def eventFilter(self, obj, e):
		#print(e.type(), e.FocusIn)
		if(e.type() == e.FocusIn and (obj == self.editor1 or obj == self.editor2)):
			if obj == self.editor1:
				self.parent.headerWidget.setInfo(self.editor2.current)
				self.editor2.current.state = 0
			else:
				self.parent.headerWidget.setInfo(self.editor1.current)
				self.editor1.current.state = 0
			obj.current.state = 1
			self.editor = obj
			#return True
		#else:
		return False
	

	
	
	def getEditors(self):
		return [self.editor1, self.editor2]
	
	

		
		

		

			
	def setDoubleView(self, doubleView):
		if doubleView:
			self.editor1.show()
			self.editor2.show()
			self.editor.setFocus()
		else:
			self.editor2.hide()
			self.editor = self.editor1
			self.editor.setFocus()
			
	def setCurrent(self, fd):
		self.editor.current.lines = list(self.editor.lines)
		self.updating = True
		self.editor.lines = fd.lines
		self.editor.current = fd
		self.updating = False
		self.editor.setFocus()
		
		
	def updateFD(self):
		self.editor1.current.lines = list(self.editor1.lines)
		self.editor2.current.lines = list(self.editor2.lines)


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from common import settings

from guilib.treemodel import TreeModel, TreeItem
from operator import attrgetter

import re

from data import ParsedLine




class CustomQLineEdit(QtWidgets.QLineEdit):
	
	def __init__(self, associatedWidget):
		QtWidgets.QLineEdit.__init__(self)
		self.associatedWidget = associatedWidget
		

			
	
	def keyPressEvent(self, e):
		#print('keyPressEvent', e, e.key());
		if(e.key() == 16777235 or e.key() == 16777237) or e.key() == 16777220: #'up' 'down' 'enter'
			self.associatedWidget.keyPressEvent(e)
			if(e.key() == 16777220): # 'enter'
				self.setText('')
		
		QtWidgets.QLineEdit.keyPressEvent(self, e)



class MultiFilterMode:
    AND = 0
    OR = 1


class MultiFilterProxyModel(QtCore.QSortFilterProxyModel):    
    def __init__(self, *args, **kwargs):
        QtCore.QSortFilterProxyModel.__init__(self, *args, **kwargs)
        self.filters = {}
        self.multi_filter_mode = MultiFilterMode.AND

    def setFilterByColumn(self, column, regex):
        if isinstance(regex, str):
            regex = re.compile(regex, re.IGNORECASE)
        self.filters[column] = regex
        self.invalidateFilter()

    def clearFilter(self, column):
        del self.filters[column]
        self.invalidateFilter()

    def clearFilters(self):
        self.filters = {}
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filters:
            return True

        results = []
        for key, regex in self.filters.items():
            text = ''
            index = self.sourceModel().index(source_row, key, source_parent)
            if index.isValid():
                text = self.sourceModel().data(index, Qt.DisplayRole)
                if text is None:
                    text = ''
            # results.append(regex.match(text))
            results.append(regex.search(text))

        if self.multi_filter_mode == MultiFilterMode.OR:
            return any(results)
        return all(results)


class KeySelector(QtWidgets.QWidget):
	def __init__(self, parent, options=['noRefresh'], otherParams={}):
		self.mainEditor = parent
		QtWidgets.QWidget.__init__(self)
		
		trueLayout = QtWidgets.QHBoxLayout()
		trueLayout.setContentsMargins(0, 0, 0, 0)
		w = QtWidgets.QWidget()
		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		w.setLayout(layout)
		
		txt = _('ANIMATIONS')
		txt = '\n'.join(txt)
		label = QtWidgets.QLabel(txt)
		trueLayout.addStretch()
		trueLayout.addWidget(label)
		trueLayout.addWidget(w, 1)
		trueLayout.addStretch()
		self.setLayout(trueLayout)
		
		self.cacheLabel = label
		self.cacheLabel.hide()
		self.content = w
		
		
		self.showLabel = settings.get_option('entity/anim_show_comment_label', True)
		
		
		
		self.columnCount = 2
		
		if 'columnCount' in otherParams:
			self.columnCount = otherParams['columnCount']
			
			
		if(not self.showLabel):
			self.columnCount = 2
		
		
		actionGroup = QtWidgets.QActionGroup(self)
		self.buttonBar = QtWidgets.QToolBar()
		addIcon = QtGui.QIcon.fromTheme('list-add')
		addAnim = self.buttonBar.addAction(addIcon, _('Add animation'), self.createAnim)
		
		#removeIcon = QtGui.QIcon.fromTheme('edit-delete')
		removeIcon = QtGui.QIcon.fromTheme('list-remove')
		addAnim = self.buttonBar.addAction(removeIcon, _('Delete animation'), self.deleteAnim)
		self.buttonBar.addSeparator()
		#deleteIcon = QtGui.QIcon.fromTheme('list-remove')
		#deleteAnim = self.buttonBar.addAction(libraryIcon, 'Remove', self.deleteAnim)

		addAnim = self.buttonBar.addAction(_('Header'), self.showHeader)
		
		
		self.options = options
		
		if('addOnTop' in otherParams):
			layout.addWidget(otherParams['addOnTop'], 0)
		
		layout.addWidget(self.buttonBar, 0)
		if 'hideUpperBar' in options:
			self.buttonBar.hide()
		
		
		
		self.treeView = QtWidgets.QTreeView(self)
		self.model = AnimModel(self)
		self.filterModel = MultiFilterProxyModel()
		self.filterModel.setSourceModel(self.model)
		self.treeView.setSortingEnabled(True)
		self.treeView.setModel(self.filterModel)
	
	
		self.treeView.hideColumn(0)
		
		self.treeView.activated.connect(self.loadAnim)
		if not settings.get_option('gui/double_click_to_load_element', False):
			self.treeView.clicked.connect(self.loadAnim)
		
		header = self.treeView.header()
		header.setStretchLastSection(False)
		#header.setDefaultSectionSize(60)
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		header.setSectionResizeMode (1, QtWidgets.QHeaderView.Stretch)
		if self.columnCount > 2:
			header.setSectionResizeMode (2, QtWidgets.QHeaderView.Stretch)
		
		
		theme = settings.get_option('gui/widgets_theme', None)
		
		#searchButton = QtWidgets.QToolButton()
		searchButton = QtWidgets.QPushButton()
		searchIcon = QtGui.QImage('icons/search.svg')
		if(theme == "Dark"): searchIcon.invertPixels()
		searchIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(searchIcon))
		searchButton.setIcon(searchIcon)
		#searchButton.setIcon(QtGui.QIcon.fromTheme('search'))
		searchButton.clicked.connect(self.search)
		
		hboxSearch = QtWidgets.QHBoxLayout()
		w = QtWidgets.QWidget()
		w.setLayout(hboxSearch)
		self.searchEntry = CustomQLineEdit(self.treeView)
		self.searchEntry.setPlaceholderText(_('Search (press F3 to focus)'))
		self.searchEntry.returnPressed.connect(self.search)
		
		if settings.get_option('misc/search_on_text_change', False):
			self.searchEntry.textChanged.connect(self.search)
		
		
		hboxSearch.addWidget(self.searchEntry, 1)
		hboxSearch.addWidget(searchButton)
		
		if not'noRefresh' in options:
			reloadIcon = QtGui.QImage('icons/reload.svg')
			if(theme == "Dark"): reloadIcon.invertPixels()
			reloadIcon = QtGui.QIcon(QtGui.QPixmap.fromImage(reloadIcon))
			
			refreshButton = QtWidgets.QPushButton()
			refreshButton.setIcon(reloadIcon)
			refreshButton.clicked.connect(self.refresh)
			
			
			hboxSearch.addWidget(refreshButton)
		
		
		layout.addWidget(w, 0)
		layout.addWidget(self.treeView)
		
		
		self.timeLine = QtCore.QTimeLine(400, self)
		self.timeLine.setUpdateInterval(20)
		
		#connect(timeLine, SIGNAL(frameChanged(int)), progressBar, SLOT(setValue(int)));
		self.timeLine.frameChanged.connect(self.tmp)
		
		QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("F3", "Edit|Search Anim")), self, self.focusForSearch)
		
		
	def toggleOption(self, key, value):
		print("toggleOption", key, value)
		if value:
			if key in self.options: pass
			else : self.options.append(key)
		else:
			if key in self.options: self.options.remove(key)
			
		if key == 'animation':
			# self.toggleOption('hideUpperBar', not value)
			
			if value and self.showLabel:
				self.columnCount = 3
			else:
				self.columnCount = 2
				
		if key == 'hideUpperBar':
			if(value) : self.buttonBar.hide()
			else : self.buttonBar.show()
	
	def showHeader(self):
		self.mainEditor.loadAnim('header')
		
	def tmp(self, val):
		self.mainEditor.mainSplitter.setSizes([val, self.mainEditor.rect().width()])
		
		
	def append(self, dataTuple, parentNode=None, isHeader=False, startLine=None, endLine=None):
		if(parentNode == None):
			parentNode = self.model.rootItem
		return self.model.append(parentNode, AnimItem(parentNode, dataTuple, isHeader, startLine, endLine))
	
	
	def clear(self):
		self.model.reset()
		
		
	def createAnim(self):
		text = QtWidgets.QInputDialog.getText(self, _("Create animation"), _("Name"))[0]

		if text != '': # TODO make sure animation name is valid (startswith freespecial, etc OR in idle, walk, rise, etc
			self.mainEditor.addAnim(text)
			self.append((text, '' , 999, text))
			
	def deleteAnim(self):
		if(self.currentAnimID == "idle"):
			return
		if(self.currentAnimName == None):
				QtWidgets.QMessageBox.warning(self, _('Load an animation first'), _('Load an animation before deleting it'))
				return
		
		if(QtWidgets.QMessageBox.question(self, _('Delete animation'), _('Are you sure you want to delete animation' + ' ' + self.currentAnimName + ' ?'), defaultButton=QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes):
			self.currentAnimName = "idle";
			self.mainEditor.deleteAnim(self.currentAnimID)
			self.mainEditor.loadAnim("idle")
		
		
	def enterEvent(self, e):
		if(not hasattr(self.mainEditor, 'mainSplitter')):return
		
		if self.content.isVisible() and not settings.get_option('gui/auto_collapse', True) : return # Do not expand if already expanded
		self.content.show()
		self.cacheLabel.hide()
		self.timeLine.setFrameRange(self.mainEditor.mainSplitter.sizes()[0], 300);
		self.timeLine.start()
		
		
	def focusForSearch(self):
		print('focus for search - Anim')
		self.enterEvent(None)
		
		self.searchEntry.setFocus()
		self.searchEntry.selectAll()
		
	def leaveEvent(self, e):
		if(not hasattr(self.mainEditor, 'mainSplitter')):return
		if self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())):
			return
		
		if not settings.get_option('gui/auto_collapse', True) : return
		self.cacheLabel.show()
		self.content.hide()
		self.timeLine.setFrameRange(self.mainEditor.mainSplitter.sizes()[0], 100);
		self.timeLine.start()
		
	def load(self, data):

		self.showLabel = settings.get_option('entity/anim_show_comment_label', True)
		if(not self.showLabel):
			self.columnCount = 2
			# header = self.treeView.header()
			# header.setSectionResizeMode (2, QtWidgets.QHeaderView.Fixed)
			# header.resizeSection(2, 0)
			self.treeView.hideColumn(2)

		self.currentAnimName = None

		if 'animation' in self.options:
			self.currentAnimName = None
			for i, d in enumerate(data):
				ID = d.get('ID', d.get('name', ''))
				ID_edited = d.get('ID_edited', ID)
				label = d.get('label', '')
				isHeader = d.get('isHeader', False)
				startLine = d.get('startLine', None)
				endLine = d.get('endLine', None)
				self.append((ID, label, i, ID_edited), isHeader=isHeader, startLine=startLine, endLine=endLine)
			return

		for d in data:
			# Support both old format (string) and new format (dict with name/isHeader/startLine/endLine)
			if isinstance(d, dict):
				# Support both 'name' (from loadContentIndexerPanel) and 'ID' (from loadFrom)
				name = d.get('name', d.get('ID', ''))
				label = d.get('label', '')
				isHeader = d.get('isHeader', False)
				startLine = d.get('startLine', None)
				endLine = d.get('endLine', None)
				self.append((name, label, name, name), isHeader=isHeader, startLine=startLine, endLine=endLine)
			else:
				self.append((d, '', d, d))
		
		
	def refresh(self):
		
		self.loadFrom()
			
	def loadFrom(self, lines=None):
		self.showLabel = settings.get_option('entity/anim_show_comment_label', True)
		if(not self.showLabel):
			self.columnCount = 2
			# header = self.treeView.header()
			# header.setSectionResizeMode (2, QtWidgets.QHeaderView.Fixed)
			# header.resizeSection(2, 0)
			self.treeView.hideColumn(2)

		if lines == None:
			lines = self.mainEditor.editor.lines

		self.updating = True
		self.currentAnim = None

		sectionLines = []
		data = {'ID':'header', 'label':'', 'lines':sectionLines, 'isHeader': False, 'startLine': 0}
		dicData = {'header':data}
		fullData = [data]

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

		name = None

		for lineNum, line in enumerate(lines):
			# Check for header title (formatted title box)
			if isHeaderTitleLine(line):
				title = extractHeaderTitle(line)
				if title:
					sectionLines = []
					data = {'ID': title, 'label': '', 'lines': sectionLines, 'isHeader': True, 'startLine': lineNum}
					fullData.append(data)
					dicData[title] = data
					sectionLines.append(line)
					continue

			pLine = ParsedLine(line)
			part = pLine.next()
			if part != None : part = part.lower()
			if part == 'anim':
				label = pLine.getCom()
				animID = pLine.next()
				sectionLines = []
				data = {'ID':animID, 'label':label, 'lines': sectionLines, 'isHeader': False, 'startLine': lineNum}
				fullData.append(data)
				dicData[animID] = data
			sectionLines.append(line)

		# Calculate endLine for each section
		totalLines = len(lines)
		for i, d in enumerate(fullData):
			if i + 1 < len(fullData):
				d['endLine'] = fullData[i + 1]['startLine'] - 1
			else:
				d['endLine'] = totalLines - 1

		self.dicData = dicData
		self.fullData = fullData
		for key in dicData:
			print(key)

		self.clear()
		self.load(fullData)

		
		
	
	def loadAnim(self, index):
		self.currentAnimID = index.data(AnimModel.itemRole).ID
		self.currentAnimName = self.currentAnimID
		
		# ???
		#if(self.currentAnimID.lower() == 'idle'):
			#return
		
		label = index.data(AnimModel.itemRole).label
		if(label != ''): self.currentAnimName += '(' + label + ')'
		
		if('animation' in self.options): return self.mainEditor.loadAnim(index.data(AnimModel.itemRole).ID)
		self.mainEditor.loadKey(index.data(AnimModel.itemRole).ID)
		
		
	def search(self):
		txt = self.searchEntry.text()

		# QT original filter function
		# self.treeView.model().setFilterRole(Qt.DisplayRole)
		# self.treeView.model().setFilterKeyColumn(1)

		#self.treeView.model().setFilterRegExp(text)
		# regExp = QtCore.QRegExp(txt, QtCore.Qt.CaseInsensitive)
		# self.treeView.model().setFilterRegExp(regExp)

		# custom model filter function
		self.treeView.model().multi_filter_mode = MultiFilterMode.OR
		self.treeView.model().setFilterByColumn(1, txt)
		self.treeView.model().setFilterByColumn(2, txt)

		#self.treeView.model().setFilterRegExp('/(.*)' + txt +'(.*)/i')

	def selectByKey(self, key):
		"""Select and scroll to the item with the given key (ID) in the tree view."""
		# Search through all items in the model
		rootItem = self.model.rootItem
		foundIndex = None

		def searchInChildren(parent, parentIndex):
			nonlocal foundIndex
			for row, child in enumerate(parent.childItems):
				if hasattr(child, 'ID') and child.ID == key:
					# Found it - create the index
					childIndex = self.model.index(row, 1, parentIndex)
					foundIndex = childIndex
					return True
				# Search in children recursively
				childIndex = self.model.index(row, 0, parentIndex)
				if searchInChildren(child, childIndex):
					return True
			return False

		# Start search from root
		searchInChildren(rootItem, QtCore.QModelIndex())

		if foundIndex and foundIndex.isValid():
			# Map to filter model index
			filterIndex = self.filterModel.mapFromSource(foundIndex)
			if filterIndex.isValid():
				# Select the item
				self.treeView.setCurrentIndex(filterIndex)
				# Scroll to center
				self.treeView.scrollTo(filterIndex, QtWidgets.QAbstractItemView.PositionAtCenter)

	def selectByLine(self, lineNumber):
		"""Select and scroll to the item containing the given line number."""
		rootItem = self.model.rootItem
		foundIndex = None

		def searchInChildren(parent, parentIndex):
			nonlocal foundIndex
			for row, child in enumerate(parent.childItems):
				# Check if this item contains the line
				if hasattr(child, 'startLine') and child.startLine is not None:
					if hasattr(child, 'endLine') and child.endLine is not None:
						if child.startLine <= lineNumber <= child.endLine:
							childIndex = self.model.index(row, 1, parentIndex)
							foundIndex = childIndex
							return True
				# Search in children recursively
				childIndex = self.model.index(row, 0, parentIndex)
				if searchInChildren(child, childIndex):
					return True
			return False

		# Start search from root
		searchInChildren(rootItem, QtCore.QModelIndex())

		if foundIndex and foundIndex.isValid():
			# Map to filter model index
			filterIndex = self.filterModel.mapFromSource(foundIndex)
			if filterIndex.isValid():
				# Select the item
				self.treeView.setCurrentIndex(filterIndex)
				# Scroll to center
				self.treeView.scrollTo(filterIndex, QtWidgets.QAbstractItemView.PositionAtCenter)

class AnimItem(TreeItem):
	def __init__(self, parent, data, isHeader=False, startLine=None, endLine=None):
		TreeItem.__init__(self, data[1], parent)
		self.ID = data[0]
		self.label = data[1]
		self.pos = data[2]
		self.ID_edited = data[3]
		self.isHeader = isHeader
		self.startLine = startLine
		self.endLine = endLine

		self.subelements = []
		
	def __str__( self ):
		return self.label
		
	def __repr__(self):
		return self.label
		
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
		
class AnimModel(TreeModel):
	
	itemRole = Qt.UserRole+2
	
	def __init__(self, parent):
		TreeModel.__init__(self)
		self.parent = parent
		self.columnsFields = ('pos', 'ID', 'label')


	def columnCount(self, parent):
		return self.parent.columnCount

	def data(self, index, role):
		if not index.isValid():
			return None
		item = index.internalPointer()
		if role == self.itemRole:
			return item
		elif role == Qt.DisplayRole:
			if index.column() == 0:
				return None
				return item.pos
			elif index.column() == 1:
				if(hasattr(item, 'ID_edited')):
				   return item.ID_edited
				return item.ID
			elif index.column() == 2:
				# return None
				return item.label
		elif role == Qt.FontRole:
			# Return bold and larger font for header items
			if hasattr(item, 'isHeader') and item.isHeader:
				font = QtGui.QFont()
				font.setBold(True)
				font.setPointSize(font.pointSize() + 2)
				return font

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
			FIXME Not used, didn't manage to find out how to automatically serialize items (thus overrided mimeData instead)
		'''
		return ('bullseye/library.items',)
		
	def sort(self, columnIndex, order):
		print('sorting before')
		self.layoutAboutToBeChanged.emit()
		if(order == QtCore.Qt.AscendingOrder):
			reverse = False
		else:
			reverse = True

		headerElt = self.rootItem.childItems[0]
			
		def sort(elt, reverse):
			elt.childItems = sorted(elt.childItems, key=attrgetter(self.columnsFields[columnIndex]), reverse=reverse)
			for childElt in elt.childItems:
				sort(childElt, reverse)
				
		sort(self.rootItem, reverse)



		headerIndex = self.rootItem.childItems.index(headerElt)
		print('sorting', headerIndex)
		self.rootItem.childItems.pop(headerIndex)
		self.rootItem.childItems.insert(headerElt, 0)
		
		self.layoutChanged.emit()

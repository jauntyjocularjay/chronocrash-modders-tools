from common import settings, util

from qutepart import Qutepart, getIcon


from qutepart.syntaxhlighter import SyntaxHighlighter

from PyQt5.QtCore import QRect, Qt, pyqtSignal, QRegExp, QEvent, QMimeData

from PyQt5.QtGui import QColor, QBrush, \
                        QFont, \
                        QIcon, QKeySequence, QPainter, QPen, QPalette, \
                        QTextCharFormat, QTextCursor, \
                        QTextBlock, QTextFormat, QDropEvent, QTextDocument

from PyQt5.QtWidgets import QAction, QPlainTextEdit, QTextEdit

class EverydayPart(Qutepart):

	toolTipEvent = pyqtSignal(int, str, object)
	focusInSignal = pyqtSignal(object, object)
	newExtraSelection = pyqtSignal(object)
	doubleClickSignal = pyqtSignal(int)  # Emits line number on double-click
	tabAlwaysIndent = True

	def __init__(self, *args):
		
		self.updatingCursor = False
		self.highlightCurrentWordJustFinished = False
		# self.mousePressed = False
		Qutepart.__init__(self, *args)
		
		self.completionEnabled = settings.get_option('editor/completion_enabled', True)
		
		
		SyntaxHighlighter.FORCE_BOLD = settings.get_option('editor/force_bold', True)
		# SyntaxHighlighter.FORCE_BOLD = False
		
		self.selectionChanged.connect(self.highlightCurrentWord)
		#self.newExtraSelection.connect(self.addExtraSelection)
		
		self.wordHighlighted = False
		self.mousePressed = False
		
		self.searchColor = QColor('#ffffa3')
		
		ovw_highlight_color = settings.get_option('editor/color_highlighted_line', None)
		
		if(ovw_highlight_color != None):
			self.overwriteHighlightColor = QColor(ovw_highlight_color)

		
		self.initialSearchPos = None
		
		if(settings.get_option('editor/scroll_instead_of_wrap', False)): self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap);
		
		
		self._initActions_everyDay()

		
	
	
	def _initActions_everyDay(self):
		"""Init shortcuts for text editing
		"""
		def createAction(text, shortcut, slot, iconFileName=None):
			"""Create QAction with given parameters and add to the widget
			"""
			action = QAction(text, self)
			if iconFileName is not None:
				action.setIcon(QIcon( getIcon(iconFileName)))

			keySeq = shortcut if isinstance(shortcut, QKeySequence) else QKeySequence(shortcut)
			action.setShortcut(keySeq)
			action.setShortcutContext(Qt.WidgetShortcut)
			action.triggered.connect(slot)

			self.addAction(action)

			return action
		
		# indentation
		if EverydayPart.tabAlwaysIndent:
			self.increaseIndentAction = createAction('Increase indentation', 'Tab',self._onShortcutIndent, 'indent.png')
	
	
	def _currentLineExtraSelections(self):
		if(hasattr(self, 'overwriteHighlightColor') and self.overwriteHighlightColor != None):
			try:
				previousColor = self._currentLineColor
				self._currentLineColor = self.overwriteHighlightColor
				result = Qutepart._currentLineExtraSelections(self)
				self._currentLineColor = previousColor
				return result
			except:
				return Qutepart._currentLineExtraSelections(self)
		else:
			return Qutepart._currentLineExtraSelections(self)
		
		
	def _updateExtraSelections(self):
		if(self.updatingCursor):return
    
		if(self.highlightCurrentWordJustFinished):
			self.highlightCurrentWordJustFinished = False
			return
    
		print("updating cursor updateExtra")
		return Qutepart._updateExtraSelections(self) 
	
	def addExtraSelection(self, selection):
		pass
		
		
	def comment(self):
		lines = self.lines[self._selectedLinesSlice()]
		
		minIndent = min([len(line) - len(line.lstrip()) for line in lines if line.strip()])
		
		print('minIndent', minIndent, lines)
		
		startBlockNumber, endBlockNumber = self._selectedBlockNumbers()
		
		for i in range(startBlockNumber, endBlockNumber):
			self.lines[i] = '{}{} {}'.format(self.lines[i][:minIndent], '//', self.lines[i][minIndent:])
	
	def dropEvent(self, e):
		data = QMimeData()
		text = e.mimeData().text()
		data_path = settings.get_option('general/data_path', '')
		newText = []
		first = True
		
		extensionsToCheck = ('.wav', '.ogg', '.bor')
		
		
		for line in text.split('\n'):

			if data_path in line:
				#print(line)
				command = 'frame'
				#if line.endswith(extensionsToCheck):
				if any(x in line for x in extensionsToCheck):
					command = 'sound'
				newLine = '	' + command + ' data' + line[line.index(data_path)+len(data_path):]
				if first:
					newLine = '\n' + newLine
				newText.append(newLine)
			else:
				newText.append(line)
			
			if first:
				first = False
		data.setText('\n'.join(newText))
		#data.setUrls([])
		e = QDropEvent(e.pos(), e.dropAction(), data, e.mouseButtons(), e.keyboardModifiers())
		
		Qutepart.dropEvent(self, e)
		
	def event(self, e):
		if e.type() == QEvent.ToolTip:
			#QHelpEvent* helpEvent = static_cast<QHelpEvent*>(event);
			start, end = self.selectedPosition
			if start != end:
				self.toolTipEvent.emit(start, self.selectedText, e)
			else:
				cursor = self.cursorForPosition(e.pos())
				cursor.select(QTextCursor.LineUnderCursor)
				line = cursor.block().blockNumber()
				if (len(cursor.selectedText())!= 0):
					self.toolTipEvent.emit(line, cursor.selectedText(), e)
			return True

		return Qutepart.event(self, e)
		
	def focusInEvent(self, e):
		Qutepart.focusInEvent(self, e)
		self.focusInSignal.emit(self, e)
		
	def keyPressEvent(self, e):
		if e.text() == '	' and EverydayPart.tabAlwaysIndent: # tab
			start, end = self.selectedPosition
			start = start[0]
			end = end[0]
			if end < start:
				tmp = end
				end = start
				start = tmp
			#line, col = self.cursorPosition
			for line in range(start, end+1):
				self.insertText((line, 0), e.text())

		else:
			Qutepart.keyPressEvent(self, e)
		
	def mousePressEvent(self, e):
		self.mousePressed = True
		Qutepart.mousePressEvent(self, e)
		
	def mouseReleaseEvent(self, e):
		self.mousePressed = False
		Qutepart.mouseReleaseEvent(self, e)

	def mouseDoubleClickEvent(self, e):
		Qutepart.mouseDoubleClickEvent(self, e)
		# Emit signal with current line number
		lineNumber = self.textCursor().blockNumber()
		self.doubleClickSignal.emit(lineNumber)

	def getContext(self, blockNumber, col=None):
		block = self.document().findBlockByNumber(blockNumber)
		data = block.userData().data[0]
		if(data == None): return None
		context = data.currentContext()
		data = context.name
		
		return data
	
	def saveScroll(self):
		self.previousScroll = self.verticalScrollBar().sliderPosition()
		print('saveScroll', self.previousScroll)
		
	def restoreScroll(self):
		self.verticalScrollBar().setSliderPosition(self.previousScroll)

	def highlightCurrentWord(self): # PROBABLY DAIMAO
		print("highlight current word");
		
		
	
		#@threaded
		def buildFormat():
			#selection = QTextEdit.ExtraSelection()
			#cursor = self.textCursor()
			#selection.format.setBackground(self.searchColor)
			#selection.cursor = cursor
			#format.setForeground(Qt.black);
			regex = QRegExp(word)
			# Process the displayed document
			pos = 0
			index = regex.indexIn(self.text, pos)
			
			previousScroll = self.verticalScrollBar().sliderPosition()
			previousSelected = self.selectedPosition
			
			self.moveCursor(QTextCursor.Start);
			extraSelections = []
			while self.find(word):
				print("found")
				selection = QTextEdit.ExtraSelection()
				selection.cursor = self.textCursor()
				selection.format.setBackground(self.searchColor)
				extraSelections.append(selection)
				
			#for e in extraSelections:
				#print(e.cursor.block().text())
			
			
			QPlainTextEdit.setExtraSelections(self, extraSelections)
			
			
			#while (index != -1 and index != 0):
				## Select the matched text and apply the desired format
				#cursor.setPosition(index)
				#cursor.movePosition(QTextCursor.EndOfWord, 1)
				##cursor.mergeCharFormat(selection.format)
				
				##selection.append(
				## Move to the next match
				#pos = index + regex.matchedLength()
				#index = regex.indexIn(self.text, pos)
			
			self.selectedPosition = previousSelected
			self.verticalScrollBar().setSliderPosition(previousScroll)
			endBuild()

		
		def endBuild():
			self.updatingCursor = False
			self.highlightCurrentWordJustFinished = True 

			#self.selectionChanged.connect(self.highlightCurrentWord)
			if self._highlighter != None:
				return
				self._highlighter._document.contentsChange.connect(self._highlighter._onContentsChange)
				
		
		if self.updatingCursor or self.mousePressed: return
	
		# self.blockSignals(True)
		self.updatingCursor = True
		word = self.selectedText
		# print('word', '|' + word + '|')
		if len(word) == 0 or word[0] in ('\t', ' ') or word[-1] in ('\t', ' '):
			self.setExtraSelections([])
			#QPlainTextEdit.setExtraSelections(self, [])
			self.updatingCursor = False
			self.blockSignals(False)
			return
		
		
		# print('word', 'continue')
		#try:
			#if self._highlighter != None:
				#self._highlighter._document.contentsChange.disconnect(self._highlighter._onContentsChange)
		#except TypeError:
			#pass
		#self._highlighter
		
		#self.selectionChanged.disconnect(self.highlightCurrentWord)
		
		# Reset previous
		self.updatingCursor = True
		#cursor = self.textCursor()
		#cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor);
		#cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor);
		
		#cursor.setCharFormat(QTextCharFormat())

		#word = self.selectedText
		#if len(word) == 0 :
			##if self.wordHighlighted:
				##self.wordHighlighted = False
			#endBuild()
			#return

		
		#QSignalBlocker(self.document())
		#
		
		self.updatingCursor = False
		
		
		
		
		start, end = self.absSelectedPosition
		if start > end:
			tmp = start
			start = end
			end = tmp

		if start == 0:
			startChar = ' '
		else:
			startChar = self.text[ start-1]
			
		if end >= len(self.text):  # End of text
			endChar = ' '
		else : endChar = self.text[ end]
		
		print(startChar, endChar)
		
		delimiters = ('.', ',', ' ', '	', '-', ';', '(', ')', '{', '}', '/', '\n')
		#print('here', startChar, endChar)
		if(startChar not in delimiters  or endChar not in delimiters) : return
		#print('good')
		
		self.updatingCursor = True

		# print('word', 'continue 2')
		buildFormat()
		# self.blockSignals(False)
		
		#cursor.select(QTextCursor.WordUnderCursor);
		
		

		##cursor.setPosition(begin, QTextCursor.MoveAnchor);
		##cursor.setPosition(end, QTextCursor.KeepAnchor);
		#cursor.setCharFormat(format)
		##cursor.mergeCharFormat(fmt); # I did try also cursor.setCharFormat(fmt)

	def search(self, text, searchForward=True, loop=True):
		self.setCenterOnScroll(True)
		
		print('editor', self.initialSearchPos)
		if(self.initialSearchPos == None):
			self.initialSearchPos = self.textCursor()
			
		
		print('text', text)
		if(text == ''): 
			#self.searchEntry.setStyleSheet("")
			self.setTextCursor(self.initialSearchPos)
			self.initialSearchPos = None
			return False

		if searchForward:
			options = QTextDocument.FindFlags()
		else:
			options = QTextDocument.FindBackward
		result = self.find(text, options) # first try to search from cursor to end of document
		
		if(result):
			#self.searchEntry.setStyleSheet("QLineEdit { background: rgb(175, 255, 175); }");
			return True
		
		elif(loop and not result):
			self.moveCursor(QTextCursor.Start)
			if not self.find(text, options): # then try to search from start to end of document
			
			
				# self.editor.moveCursor(self.editor.initialSearchPos)
				self.setTextCursor(self.initialSearchPos)
				self.initialSearchPos = None
			
			
				#self.searchEntry.setStyleSheet("QLineEdit { background: rgb(255, 175, 175); }");
				 # selection-background-color: rgb(233, 99, 0);
				 
				return False
			else:
				
				#self.searchEntry.setStyleSheet("QLineEdit { background: rgb(175, 255, 175); }");
				return True
	
	
	def replace(self, text1, text2):
		if(self.selectedText != ''):
			self.selectedText = text2
			self.search(text1)
			
	def replaceAllRaw(self, text, replaceWith):
		self.updatingCursor = True
		
		if(self.selectedText == ''):
		
			lines = self.lines
			newLines = []
			for line in lines:
				newLines.append(line.replace(text, replaceWith))
			
			self.lines = newLines
		else:
			self.selectedText = self.selectedText.replace(text, replaceWith)
		self.updatingCursor = False
	
	def setTheme(self, data):
		
		if data is None or settings.DISABLE_STYLE_SHEET:
			return
		print(';'.join(data['css']))
		self.setStyleSheet('QPlainTextEdit {' + ';'.join(data['css']) + '}')
		self.searchColor = data['searchColor']
		self.highlightColor = data['currentLine']
		#self.highlightColor = QColor('#2CA2AE')
	
	
	def wheelEvent(self, e):
		if (e.modifiers() & Qt.ControlModifier):
			if e.angleDelta().y() > 0:
				step = 1
			else:
				step = -1
			font = self.currentFont
			font.setPointSize(font.pointSize()+step)
			self.setFont(font)
		else:
			Qutepart.wheelEvent(self, e)


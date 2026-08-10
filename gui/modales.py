# -*- coding: utf-8 -*-
import os
from common import settings, xdg
from guilib import treemodel
from PyQt5 import QtWidgets, QtGui, QtCore

from gui.util import FileInput
from gui.settings.fontselector import FontSelector

VERSION = settings.VERSION


class ShortcutSettingsWidget(QtWidgets.QWidget):
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		lay = QtWidgets.QFormLayout()

		#self.basePath = QtWidgets.QLineEdit()
		#self.basePath.setText(settings.get_option('general/datapath', ''))
		
		lay.addRow(_("<p style='color:red;font-weight:bold;'>You need to reload the app for</p>"), QtWidgets.QLabel(_("<p style='color:red;font-weight:bold;'>the new shortcuts to be in effect</p>")))
		
		#lay.addRow(QtWidgets.QLabel(_("<p style='color:red;font-weight:bold;'>You need to reload the app for the new shortcuts to be in effect</p>")))
		
		self.bodyBox = QtWidgets.QLineEdit()
		self.attackBox = QtWidgets.QLineEdit()
		self.bodyBox.setText(settings.get_option('shortcuts/set_body_box', 'B'))
		self.attackBox.setText(settings.get_option('shortcuts/set_attack_box', 'A'))
		
		lay.addRow(_('[Local] Set body box') + ' : ', self.bodyBox)
		lay.addRow(_('[Local] Set attack box') + ' : ', self.attackBox)
		
		self.zoomIn = QtWidgets.QLineEdit()
		self.zoomIn.setText(settings.get_option('shortcuts/zoom-in', '+'))
		lay.addRow(_('[Local] Zoom-out sprite') + ' : ', self.zoomIn)
		self.zoomOut = QtWidgets.QLineEdit()
		self.zoomOut.setText(settings.get_option('shortcuts/zoom-out', '-'))
		lay.addRow(_('[Local] Zoom-out sprite') + ' : ', self.zoomOut)
		
		self.zoomInGlobal = QtWidgets.QLineEdit()
		self.zoomInGlobal.setText(settings.get_option('shortcuts/zoom-in_global', 'Ctrl++'))
		lay.addRow(_('[Global] Zoom-out sprite') + ' : ', self.zoomInGlobal)
		self.zoomOutGlobal = QtWidgets.QLineEdit()
		self.zoomOutGlobal.setText(settings.get_option('shortcuts/zoom-out_global', 'Ctrl+-'))
		lay.addRow(_('[Global] Zoom-out sprite') + ' : ', self.zoomOutGlobal)
		
		self.playAnim = QtWidgets.QLineEdit()
		self.playAnim.setText(settings.get_option('shortcuts/play_animation', 'P'))
		lay.addRow(_('[Local] Play/stop animation') + ' : ', self.playAnim)
		
		self.playAnimGlobal = QtWidgets.QLineEdit()
		self.playAnimGlobal.setText(settings.get_option('shortcuts/play_animation_global', 'Ctrl+P'))
		lay.addRow(_('[Global] Play/stop animation') + ' : ', self.playAnimGlobal)
		
		self.previousFrame = QtWidgets.QLineEdit()
		self.previousFrame.setText(settings.get_option('shortcuts/previous_frame_global', 'Ctrl+Left'))
		lay.addRow(_('[Global] Previous frame') + ' : ', self.previousFrame)
		
		self.nextFrame = QtWidgets.QLineEdit()
		self.nextFrame.setText(settings.get_option('shortcuts/next_frame_global', 'Ctrl+Right'))
		lay.addRow(_('[Global] Next frame') + ' : ', self.nextFrame)
		
		
		listPrograms = settings.get_option('misc/run_menu_programs', [])
		
		self.programs_widgets = []
		i = 1
		for p in listPrograms:
			w = QtWidgets.QLineEdit()
			w.setText(settings.get_option('shortcuts/run_program_' + str(i), 'Ctrl+' + str(i)))
			
			if (len(p) > 30):
				p = p[len(p)-30:]
			
			lay.addRow(_('[Global] Run program ' + str(i) + '(...' + p + ')') + ' : ', w)
			self.programs_widgets.append(w)
			i+=1
		
		self.setLayout(lay)
		
	def save(self):
		settings.set_option('shortcuts/set_body_box', self.bodyBox.text())
		settings.set_option('shortcuts/set_attack_box', self.attackBox.text())
		
		settings.set_option('shortcuts/zoom-in', self.zoomIn.text())
		settings.set_option('shortcuts/zoom-out', self.zoomOut.text())
		settings.set_option('shortcuts/zoom-in_global', self.zoomInGlobal.text())
		settings.set_option('shortcuts/zoom-out_global', self.zoomOutGlobal.text())
		
		settings.set_option('shortcuts/play_animation', self.playAnim.text())
		settings.set_option('shortcuts/play_animation_global', self.playAnimGlobal.text())
		
		settings.set_option('shortcuts/previous_frame_global', self.previousFrame.text())
		settings.set_option('shortcuts/next_frame_global', self.nextFrame.text())
		
		listPrograms = settings.get_option('misc/run_menu_programs', [])
		i = 1
		for p in listPrograms:
			w = self.programs_widgets[i-1]
			settings.set_option('shortcuts/run_program_' + str(i), w.text())





class EditorSettingsWidget(QtWidgets.QWidget):
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		l = QtWidgets.QVBoxLayout()
		
		self.fs = FontSelector()
		l.addWidget(self.fs, 1)
		
		#lColor = QtWidgets.QHBoxLayout()
		#lColor
		self.buttonHighlightColor = QtWidgets.QPushButton(_('Color for highligted line'))
		self.buttonHighlightColor.clicked.connect(self.changeHighlightColor)
		l.addWidget(self.buttonHighlightColor)
		
		
		self.checkbox = QtWidgets.QCheckBox(_('Long lines : horizontal scroll instead of wrap'))
		self.checkbox.setChecked(settings.get_option('editor/scroll_instead_of_wrap', False))
		
		l.addWidget(self.checkbox)
		
		self.setLayout(l)
		
		
		
		
	def changeHighlightColor(self):
		color = QtWidgets.QColorDialog.getColor().name() 
		
		print('color', color)
		
		if(color != '#000000' and color != None and color != False):
		
			settings.set_option('editor/color_highlighted_line', color)
		
	def save(self):
		
		settings.set_option('editor/scroll_instead_of_wrap', self.checkbox.isChecked())
		self.fs.save()
		
		
class AppSettingsWidget(QtWidgets.QWidget):
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		l = QtWidgets.QVBoxLayout()

		appFont = QtWidgets.QApplication.font()
		self.fs = FontSelector('gui', appFont.family(), appFont.pointSize())
		l.addWidget(self.fs, 1)

		tip = QtWidgets.QLabel(_("Tip : this font applies to the whole app interface (menus, panels, dialogs...). To change the font of the text editor, go to the section Editor -> Fonts and colors."))
		tip.setWordWrap(True)
		tip.setStyleSheet('color: gray; font-style: italic;')
		l.addWidget(tip)

		self.setLayout(l)

	def save(self):
		self.fs.save()

		# hot-reload : apply the new font to the whole app, no restart needed
		app = QtWidgets.QApplication.instance()
		appFont = app.font()
		appFont.setFamily(settings.get_option('gui/font_family', appFont.family()))
		appFont.setPointSize(settings.get_option('gui/font_size', appFont.pointSize()))
		app.setFont(appFont)
		# re-applying the stylesheet forces a repolish of every existing widget :
		# with an app stylesheet active, widgets created before setFont() would
		# keep their old font otherwise (we reuse app.styleSheet() to preserve the theme part)
		app.setStyleSheet(app.styleSheet())


class AutoBackupWidget(QtWidgets.QWidget):
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		lay = QtWidgets.QFormLayout()
		
		
		self.autoSaveEvery = QtWidgets.QSpinBox()
		self.autoSaveEvery.setMinimum(10)
		self.autoSaveEvery.setMaximum(10000)
		self.autoSaveEvery.setValue(settings.get_option('autobackup/timeout', 60))
		
		self.maxNumberOfRevisions_saved = QtWidgets.QSpinBox()
		self.maxNumberOfRevisions_saved.setMaximum(10000)
		self.maxNumberOfRevisions_saved.setValue(settings.get_option('autobackup/max_number_revisions_saved_per_file', 50))
		
		self.maxNumberOfRevisions_unsaved = QtWidgets.QSpinBox()
		self.maxNumberOfRevisions_unsaved.setMaximum(10000)
		self.maxNumberOfRevisions_unsaved.setValue(settings.get_option('autobackup/max_number_revisions_unsaved_per_file', 50))
		
		self.autoDeleteDays = QtWidgets.QSpinBox()
		self.autoDeleteDays.setMaximum(10000)
		self.autoDeleteDays.setValue(settings.get_option('autobackup/auto_delete_revisions_after_days', 90))
		
		# Adapter ça pour chaque type
		
		lay.addRow(_('Trigger auto-backup unsaved every (seconds)') + ' : ', self.autoSaveEvery)
		lay.addRow(_(' '), QtWidgets.QWidget())
		
		label = QtWidgets.QLabel(_('Backup Type 1 : last revisions / sequential history'))
		label.setStyleSheet("font-weight: bold; color: black")
		lay.addRow(label,  QtWidgets.QWidget())
		lay.addRow(_('Max number of saved revisions per file') + ' : ', self.maxNumberOfRevisions_saved)
		lay.addRow(_('Max number of UNsaved revisions per file') + ' : ', self.maxNumberOfRevisions_unsaved)
		lay.addRow(_('Automatically delete revisions older than (days)') + ' : ', self.autoDeleteDays)
		
		lay.addRow(_(' '), QtWidgets.QWidget())
		
		
		self.type2_keep_one_revision_per = QtWidgets.QSpinBox()
		self.type2_keep_one_revision_per.setMaximum(1)
		self.type2_keep_one_revision_per.setValue(settings.get_option('autobackup/type2_keep_one_revision_per', 1))
		
		self.type_2_autoDeleteAfter = QtWidgets.QSpinBox()
		self.type_2_autoDeleteAfter.setMaximum(10000)
		self.type_2_autoDeleteAfter.setValue(settings.get_option('autobackup/type2_auto_delete_revisions_after', 365))
		
		label = QtWidgets.QLabel(_('Backup Type 2 : spread history backup (days)'))
		label.setStyleSheet("font-weight: bold; color: black")
		lay.addRow(label, QtWidgets.QWidget())
		lay.addRow(_('Keep a revision per day') + ' : ', self.type2_keep_one_revision_per)
		lay.addRow(_('Automatically delete revisions older than (days)') + ' : ', self.type_2_autoDeleteAfter)
		
		
		
		lay.addRow(_(' '), QtWidgets.QWidget())
		
		
		self.type3_keep_one_revision_per = QtWidgets.QSpinBox()
		self.type3_keep_one_revision_per.setMaximum(1)
		self.type3_keep_one_revision_per.setValue(settings.get_option('autobackup/type3_keep_one_revision_per', 0))
		
		self.type_3_autoDeleteAfter = QtWidgets.QSpinBox()
		self.type_3_autoDeleteAfter.setMaximum(10000)
		self.type_3_autoDeleteAfter.setValue(settings.get_option('autobackup/type3_auto_delete_revisions_after', 100))
		
		
		label = QtWidgets.QLabel(_('Backup Type 3 : spread history backup (hours)'))
		label.setStyleSheet("font-weight: bold; color: black")
		lay.addRow(label, QtWidgets.QWidget())
		lay.addRow(_('Keep a revision per hour') + ' : ', self.type3_keep_one_revision_per)
		lay.addRow(_('Automatically delete revisions older than (hours)') + ' : ', self.type_3_autoDeleteAfter)
		
		self.setLayout(lay)
		
	def save(self):
		settings.set_option('autobackup/timeout', self.autoSaveEvery.value())
		
		settings.set_option('autobackup/max_number_revisions_saved_per_file', self.maxNumberOfRevisions_saved.value())
		settings.set_option('autobackup/max_number_revisions_unsaved_per_file', self.maxNumberOfRevisions_unsaved.value())
		settings.set_option('autobackup/auto_delete_revisions_after_days', self.autoDeleteDays.value())
		
		settings.set_option('autobackup/type2_keep_one_revision_per', self.type2_keep_one_revision_per.value())
		settings.set_option('autobackup/auto_delete_revisions_after_type2', self.type_2_autoDeleteAfter.value())
		
		settings.set_option('autobackup/type3_keep_one_revision_per', self.type3_keep_one_revision_per.value())
		settings.set_option('autobackup/type3_auto_delete_revisions_after', self.type_3_autoDeleteAfter.value())


class LevelSettingsWidget(QtWidgets.QWidget):
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		lay = QtWidgets.QFormLayout()

		#self.basePath = QtWidgets.QLineEdit()
		#self.basePath.setText(settings.get_option('general/datapath', ''))
		self.lineWeight = QtWidgets.QSpinBox()
		self.dotSize = QtWidgets.QSpinBox()
		self.lineWeight.setValue(settings.get_option('level/line_weight', 2))
		self.dotSize.setValue(settings.get_option('level/dot_size', 10))
		
		lay.addRow(_('Wall/Hole line weight') + ' : ', self.lineWeight)
		lay.addRow(_('Wall/Hole dot size') + ' : ', self.dotSize)
		
		self.setLayout(lay)
		
	def save(self):
		settings.set_option('level/line_weight', self.lineWeight.value())
		settings.set_option('level/dot_size', self.dotSize.value())

class LevelGroupsTintColorsSetter(QtWidgets.QWidget):
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		lay = QtWidgets.QFormLayout()
		
		self.defaultColors = [
		(230, 0, 0),
		(230, 230, 0),
		(0, 230, 230),
		(230, 0, 230),
		(0, 230, 0),
		(0, 0, 230)
		
		]
		
		
		self.colors = []
		for i in range(6):
			defaultValue = QtGui.QColor(*self.defaultColors[i]).name()
			value = settings.get_option('level/group_tint_color' + str(i), defaultValue)
			self.colors.append(value)
			
		

		self.buttons = []
		for i in range(6):
			button = QtWidgets.QPushButton('    ')
			button.setStyleSheet('QPushButton {background-color: ' + self.colors[i] + ' }')
			button.clicked.connect(self.changeColor)
			self.buttons.append(button)
			lay.addRow(_('Color') + ' ' + str(i+1) + ' : ', button)
		
		self.setLayout(lay)

		
		
		
		
		
		
	def changeColor(self):
		
		i = self.buttons.index(self.sender())
		
		defaultColor = self.colors[i]
		
		color = QtWidgets.QColorDialog.getColor(QtGui.QColor(defaultColor), self).name() 
		
		print('color', color)
		
		if(color != '#000000' and color != None and color != False):
			settings.set_option('level/group_tint_color' + str(i), color)
			
			self.sender().setStyleSheet('QPushButton {background-color: ' + color + ' }')
			
			# settings.set_option('editor/color_highlighted_line', color)
		
	def save(self):
		pass
		# settings.set_option('level/line_weight', self.lineWeight.value())
		# settings.set_option('level/dot_size', self.dotSize.value())		
		
class MiscSettingsWidget(QtWidgets.QWidget):
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		lay =  QtWidgets.QGridLayout()
		
		#self.basePath = QtWidgets.QLineEdit()
		#self.basePath.setText(settings.get_option('general/datapath', ''))
		lay.addWidget(QtWidgets.QLabel(_("ImageMagick convert bin")), 0, 0)
		imageMagickPath = settings.get_option('misc/imagemagick_path', 'convert')
		self.imageMagickPath = FileInput(self, 'saveFile', '', 'Select ImageMagick convert binary', imageMagickPath, '')
		lay.addWidget(self.imageMagickPath, 0, 1)
		
		lay.addWidget(QtWidgets.QLabel(_("Number of TODO shortcuts")), 1, 0)
		numberOfTodoShortcuts = settings.get_option('misc/number_of_todo_shortcuts', 1)
		self.numberOfTodoShortcuts = QtWidgets.QSpinBox()
		self.numberOfTodoShortcuts.setValue(numberOfTodoShortcuts)
		lay.addWidget(self.numberOfTodoShortcuts, 1, 1)
		
		
		lay.addWidget(QtWidgets.QLabel(_("Entity editor - Ignore commands")), 2, 0)
		ignore_commands = settings.get_option('entity/ignore_commands', [])
		ignore_commands_string = ','.join(ignore_commands)
		self.ignoreCommands = QtWidgets.QLineEdit(ignore_commands_string)
		lay.addWidget(self.ignoreCommands, 2, 1)
		lay.addWidget(QtWidgets.QLabel("(Use coma (,) as separator)"), 3, 0)
		
		
		lay.addWidget(QtWidgets.QLabel(_("Null collision format")), 4, 0)
		null_collision_format = settings.get_option('entity/null_collision_format', 'none')
		self.nullCollisionFormat = QtWidgets.QLineEdit(null_collision_format)
		lay.addWidget(self.nullCollisionFormat, 4, 1)
		
		self.setLayout(lay)
		
	def save(self):
		settings.set_option('misc/imagemagick_path', self.imageMagickPath.text())
		
		settings.set_option('misc/number_of_todo_shortcuts', self.numberOfTodoShortcuts.value())
		
		val = self.ignoreCommands.text()
		if(val == ''):
			tab = []
		else:
			tab = val.split(',')
		settings.set_option('entity/ignore_commands', tab)
		
		
		val = self.nullCollisionFormat.text()
		null_collision_format = settings.set_option('entity/null_collision_format', val)
		
		

		

class SettingsEditor(QtWidgets.QDialog):
	def __init__(self, section='general'):
		QtWidgets.QDialog.__init__(self)
		self.setWindowTitle(_('Settings editor'))
		mainLayout = QtWidgets.QVBoxLayout()
		buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)


		self.widgetLayout = QtWidgets.QHBoxLayout()
		
		# --- Sections selector
		treeView = QtWidgets.QTreeView(self)
		treeView.setMinimumWidth(200)
		treeView.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
		self.sections = treemodel.SimpleTreeModel()
		def addSection(key, text, iconPath=None, parent=None):
			node = treemodel.SimpleTreeItem(parent, key, iconPath, text)
			self.sections.append(parent, node)
			return node

		appNode = addSection('application', _('Application'))
		addSection('application', _('Font'), None, appNode)
		editorNode = addSection('editor', _('Editor'))
		addSection('editor', _('Fonts and colors'), None, editorNode)
		addSection('dialog', _('Dialog editor'))
		levelNode = addSection('level', _('Level editor'))
		addSection('level_groups_tint_colors', _('Groups Tint Colors'), None, levelNode)
		addSection('shortcuts', _('Keyboard shortcuts'))
		addSection('misc', _('Miscellaneous'))
		addSection('autobackup', _('Auto-Backup'))
		treeView.setModel(self.sections)
		treeView.clicked.connect(self.sectionActivated)
		self.widgetLayout.addWidget(treeView, 0)
		
		
		

		
		self.basePath = QtWidgets.QLineEdit()
		self.basePath.setText(settings.get_option('general/datapath', ''))
		
		addFolderButton = QtWidgets.QPushButton('...')
		def add_folder():
				folderPath = QtWidgets.QFileDialog.getExistingDirectory(self)
				self.basePath.setText(folderPath)
		addFolderButton.clicked.connect(add_folder)
		
		w = QtWidgets.QWidget()
		l = QtWidgets.QHBoxLayout()
		w.setLayout(l)
		l.addWidget(self.basePath, 1)
		l.addWidget(addFolderButton, 0)
		
		lay = QtWidgets.QFormLayout()
		lay.addRow(_('Mod data folder') + ' : ', w)
		
		# TODO define dialog files columns order
		self.dialogFormatCB = QtWidgets.QComboBox()
		self.dialogFormatCB.addItem('Volcanic / CRxTRDude')
		self.dialogFormatCB.addItem('Piccolo')
		self.dialogFormatCB.setCurrentIndex(settings.get_option('dialog/format', 0))
		
		lay.addRow(_('Dialog format') + ' : ', self.dialogFormatCB)
		
		w = QtWidgets.QWidget()
		w.setLayout(lay)
		
		self.widgets = {}
		
		self.widgets['dialog'] = w
		self.activeWidget = w
		self.widgetLayout.addWidget(w, 1)
		
		
		
		# APPLICATION (app font)
		w = AppSettingsWidget()
		self.widgetLayout.addWidget(w, 1)
		w.hide()
		self.widgets['application'] = w

		# FONT & EDITOR
		w = EditorSettingsWidget()
		self.widgetLayout.addWidget(w, 1)
		w.hide()
		self.widgets['editor'] = w
		
		w = LevelSettingsWidget()
		self.widgetLayout.addWidget(w, 1)
		w.hide()
		self.widgets['level'] = w
		
		w = LevelGroupsTintColorsSetter()
		self.widgetLayout.addWidget(w, 1)
		w.hide()
		self.widgets['level_groups_tint_colors'] = w
		
		w = ShortcutSettingsWidget()
		self.widgetLayout.addWidget(w, 1)
		w.hide()
		self.widgets['shortcuts'] = w
		
		w = MiscSettingsWidget()
		self.widgetLayout.addWidget(w, 1)
		w.hide()
		self.widgets['misc'] = w
		
		
		w = AutoBackupWidget()
		self.widgetLayout.addWidget(w, 1)
		w.hide()
		self.widgets['autobackup'] = w
		
		mainLayout.addLayout(self.widgetLayout)
		mainLayout.addWidget(buttonBox)
		
		
		
		self.setLayout(mainLayout)
		
	def accept(self):
		#print('TO COMPLETE')
		#settings.set_option('general/datapath', self.basePath.text())
		settings.set_option('dialog/format', self.dialogFormatCB.currentIndex())
		
		self.widgets['application'].save()
		self.widgets['editor'].save()
		self.widgets['level'].save()
		self.widgets['shortcuts'].save()
		self.widgets['misc'].save()
		self.widgets['autobackup'].save()
		
		settings.MANAGER.save()
		self.informRestart()
		QtWidgets.QDialog.accept(self)
		
		
	
		
		
		
	def informRestart(self):
		QtWidgets.QMessageBox.information(self, _('Please restart'), _("You'll probably need to restart the app for new settings to be properly applied"))
		
	def loadSection(self, section):
		self.activeWidget.hide()
		self.activeWidget = self.widgets[section]
		self.activeWidget.show()
		
		print(self.activeWidget)
		
	def sectionActivated(self, index):
		section = index.internalPointer().key
		self.loadSection(section)
		
class AboutDialog(QtWidgets.QDialog):
	def __init__(self):
		QtWidgets.QDialog.__init__(self)
		self.setWindowTitle(_('About ChronoCrash Modders Tools'))
		mainLayout = QtWidgets.QVBoxLayout()
		
		textEdit = QtWidgets.QTextBrowser()
		text = '''<p>Version : ''' + VERSION + '''</p>
		<p>This tool is meant for editing games built with OpenBOR / ChronoCrash engines.</p>
		<p>It is inspired from OpenBOR Stats and Fighter Factory, and is developped by Piccolo (<a href="https://daimao.fondation-magister.org">daimao.fondation-magister.org</a>).</p>
		
		<p>Special thanks to BeasTie, DJGameFreakTheIguana, Maxman, O Ilusionista and Kratus for their thorough feedbacks and suggestions.</p>
		<p><a href="http://www.chronocrash.com/">ChronoCrash website</a></p>
		<p>Press "Escape" to close</p>

		'''
		
		#<p>Credits to the ChronoCrash community.</p>
		#\nicon\nPresentation ChronoCrash community\nLink to ChronoCrash'
		
		textEdit.setText(text)
		textEdit.setReadOnly(True)
		textEdit.setOpenExternalLinks(True)
		textEdit.setMinimumWidth(400)
		textEdit.setMinimumHeight(300)
		mainLayout.addWidget(textEdit)
		
		self.setLayout(mainLayout)
		
		
class DonateDialog(QtWidgets.QDialog):
	def __init__(self):
		QtWidgets.QDialog.__init__(self)
		self.setWindowTitle(_('Make a donation'))
		mainLayout = QtWidgets.QVBoxLayout()
		
		textEdit = QtWidgets.QTextBrowser()
		text = '''<p>If you want to make a donation you can use PayPal to this address :</p><p>Bertrand.Coulombel@gmail.com</p>
<p>or you can also use this link : <a href="https://paypal.me/FondationMAGister?locale.x=en_EN">https://paypal.me/FondationMAGister?locale.x=en_EN</a></p> 
<p>Press "Escape" to close</p> '''
		
		#<p>Credits to the ChronoCrash community.</p>
		#\nicon\nPresentation ChronoCrash community\nLink to ChronoCrash'
		
		textEdit.setText(text)
		textEdit.setReadOnly(True)
		textEdit.setOpenExternalLinks(True)
		textEdit.setMinimumWidth(400)
		textEdit.setMinimumHeight(300)
		mainLayout.addWidget(textEdit)
		
		self.setLayout(mainLayout)
		# self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
		# self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)

	
class TipsDialog(QtWidgets.QDialog):
	def __init__(self):
		QtWidgets.QDialog.__init__(self)
		self.setWindowTitle(_('Some tips about ChronoCrash Modders Tools'))
		self.widgetLayout = QtWidgets.QHBoxLayout()
		
		# mainLayout = QtWidgets.QVBoxLayout()
		
		
		# --- Sections selector
		treeView = QtWidgets.QTreeView(self)
		treeView.setMinimumWidth(200)
		treeView.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
		self.sections = treemodel.SimpleTreeModel()
		def addSection(key, text, iconPath=None, parent=None):
			node = treemodel.SimpleTreeItem(parent, key, iconPath, text)
			self.sections.append(parent, node)
			return node

		addSection('general', _('General'))
		bindingNode = addSection('binding', _('Binding GUI'))
		addSection('binding', _('Basics'), None, bindingNode)
		addSection('binding-adv1', _('Advanced (Mask)'), None, bindingNode)
		addSection('binding-adv2', _('Advanced (code translations)'), None, bindingNode)
		
		treeView.setModel(self.sections)
		treeView.clicked.connect(self.sectionActivated)
		self.widgetLayout.addWidget(treeView, 0)
		
		
		
		
		
		textEdit = QtWidgets.QTextBrowser()
		text = '''<h3>Some info :</h3>

<ul><li>the file selector on the left can list the files "registered" in your mod or list all the files that you actually opened (library mode vs opened mode ; you can change mode through the top icons)</li>
</ul>

<h3>Some tips :</h3>

<ul>
<li>double-clicking on a word will highlight its occurrences in the whole text</li>
<li>If you place the mouse cursor over a "frame data/chars/..." line in the main editor, a tooltip will show a preview of this frame and the number of this frame in the animation (very useful to set landframe, quakeframe and such)</li>
<li>If you select several lines in the main editor, the overing tooltip will indicate the number of frames contained within</li>
<li>F2 key is a shortcut for searching a file in the File Selector (on the left)</li>
<li>Ctrl+D allows you to comment the selected lines (uncomment => Shift+Ctrl+D)</li>
<li>you can expand/collapse treeview nodes by middle-clicking them.</li>
<li>if you put a comment next to the start of an anim block (e.g. "anim attack1 # Light punch") it will be processed and appears as the animation "Label"</li>
</ul>

<p>Press "Escape" to close</p>

		'''
		
		#<p>Credits to the ChronoCrash community.</p>
		#\nicon\nPresentation ChronoCrash community\nLink to ChronoCrash'
		
		textEdit.setText(text)
		textEdit.setReadOnly(True)
		textEdit.setOpenExternalLinks(True)
		textEdit.setMinimumWidth(400)
		textEdit.setMinimumHeight(300)
		
		self.widgets = {}
		
		self.widgets['general'] = textEdit
		self.activeWidget = textEdit
		self.widgetLayout.addWidget(textEdit, 1)
		
		
		self.setUpBinding()
		# w = FontSelector()
		# self.widgetLayout.addWidget(w, 1)
		# w.hide()
		# self.widgets['editor'] = w
		
		
		
		self.setLayout(self.widgetLayout)
		
		
	def loadSection(self, section):
		print(section)
		self.activeWidget.hide()
		self.activeWidget = self.widgets[section]
		self.activeWidget.show()
		
	def sectionActivated(self, index):
		section = index.internalPointer().key
		self.loadSection(section)
		
		
	def setUpBinding(self):
		text = '''<p>There it is, I just finished cooking the first version of the binding GUI, which will be useful in particular for those who want to set up grab animations.</p>

<p>The binding GUI is integrated in the existing entity editor, and includes very useful features such as drag'n'drop positioning with the mouse, real time preview, changing bind entity on the fly, changing animation on the fly, automatic and fully customizable read /write (import/export) from your animations, and more.</p>

<h1>How it works, the basics :</h1>

1 / Open the app, load an entity and go the visual animation editor ("Animation").

2 / In the right panel, there is now a "Bindings" tab. Click on it.

3 / Enter an entity name in the "Entity model" input. When you write a valid model, the input will turn green and the entity will automatically be loaded. If the entity does not show up try to check the box "Show opponent" (not that this checkbox can also be used to hide the bound entity without removing it)

4 / If you want you can also change the animation of the "opponent" entity using the input just below the once you previously changed.

5 / Now you need to create binding settings. Click on the green "+" button to the right of the "Binding settings" group box. This will automatically sync the position of the "opponent" entity with the one of the "player" entity.

6 / Now you can change the position of the "opponent" entity as you please. There is two ways to do it visually : first, you can do it by manipulating the X and Y values on the right. Don't forget that you can use the wheel of your mouse to increase/lower the values. This is great for precise tuning. But you can also drag and drop the "opponent" entity to the desired location. Great for setting up the overall position before fine tuning it.

7 / Direction :
0 = direction stays the same as it was set before.
1 = same as player
-1 = opposite as player
2 = force facing right
-2 = force facing left

8 / Frame = simply the frame within the animation. Not that if you set a number greater that the number of frames within the current animation, it will load the first frame (frame 0) instead.


That's it for the basic stuff. 

<h3>Note that with just this basic stuff, the editor doesn't load or write anything in your files/animations.

That is, without further configuration, the binding GUI is just an independent GUI that doesn't alter or interfere with the files.</h3>

So from there you have to manually copy the values, and manually fill these values in your commands, within the text part.

But of course there is a way to automatize this process and make it way more convenient.

I'll explain it in the next section ;)'''
		
		
		text = '''<div class="bbWrapper">There it is, I just finished cooking the first version of the binding GUI, which will be useful in particular for those who want to set up grab animations.<br>
<br>
The binding GUI is integrated in the existing entity editor, and includes very useful features such as drag'n'drop positioning with the mouse, real time preview, changing bind entity on the fly, changing animation on the fly, automatic and fully customizable read /write (import/export) from your animations, and more.<br>
<br>
<b><span style="font-size: 26px">How it works, the basics :</span></b><br>
<br>
1 / Open the app, load an entity and go the visual animation editor ("Animation").<br>
<br>
2 / In the right panel, there is now a "Bindings" tab. Click on it.<br>
<br>
3 / Enter an entity name in the "Entity model" input. When you write a valid model, the input will turn green and the entity will automatically be loaded. If the entity does not show up try to check the box "Show opponent" (not that this checkbox can also be used to hide the bound entity without removing it)<br>
<br>
4 / If you want you can also change the animation of the "opponent" entity using the input just below the once you previously changed.<br>
<br>
5 / Now you need to create binding settings. Click on the green "+" button to the right of the "Binding settings" group box. This will automatically sync the position of the "opponent" entity with the one of the "player" entity.<br>
<br>
6 / Now you can change the position of the "opponent" entity as you please. There is two ways to do it visually : first, you can do it by manipulating the X and Y values on the right. Don't forget that you can use the wheel of your mouse to increase/lower the values. This is great for precise tuning. But you can also drag and drop the "opponent" entity to the desired location. Great for setting up the overall position before fine tuning it.<br>
<br>
7 / Direction : <br>
0 = direction stays the same as it was set before. <br>
1 = same as player<br>
-1 = opposite as player<br>
2 = force facing right<br>
-2 = force facing left<br>
<br>
8 / Frame = simply the frame within the animation. Not that if you set a number greater that the number of frames within the current animation, it will load the first frame (frame 0) instead.<br>
<br>
<br>
That's it for the basic stuff. <b><span style="font-size: 22px">Note that with just this basic stuff, the editor doesn't load or write anything in your files/animations.<br>
<br>
That is, without further configuration, the binding GUI is just an independent GUI that doesn't alter or interfere with the files. </span></b><br>
<br>
So from there you have to manually copy the values, and manually fill these values in your commands, within the text part. <br>
<br>
But of course there is a way to automatize this process and make it way more convenient.<br>
<br>
I'll explain it in the next post <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" class="smilie smilie--sprite smilie--sprite2" alt=";)" title="Wink    ;)" loading="lazy" data-shortname=";)"></div>'''
		textEdit = QtWidgets.QTextBrowser()
		
		textEdit.setText(text)
		textEdit.setReadOnly(True)
		textEdit.setOpenExternalLinks(True)
		textEdit.setMinimumWidth(400)
		textEdit.setMinimumHeight(300)
		textEdit.hide()
		
		self.widgets['binding'] = textEdit
		self.widgetLayout.addWidget(textEdit, 1)
		
		
		
		text = '''<div class="bbWrapper"><b><span style="font-size: 26px">Binding GUI, How it works, the advanced stuff, part 1 of 2 :</span></b><br>
<br>
Currently the advanced stuff is all about setting up the app so that it can read and write the binding values to and from your custom scripting system (or at the very least read and convert the binding values to and from comments within your animations).<br>
<br>
The main thing for that is to create a mask.<br>
<br>
Let's say you use a system like this :<br>
<br>

	
	


<div class="bbCodeBlock bbCodeBlock--screenLimited bbCodeBlock--code">
	<div class="bbCodeBlock-title">
		Code:
	</div>
	<div class="bbCodeBlock-content" dir="ltr">
		<pre class="bbCodeCode" dir="ltr" data-xf-init="code-block" data-lang=""><code>anim grab
    offset 50 50
    @cmd bindEntity 10 20 0 2 1
    frame data/chars/joe/01.gif
    
    @cmd bindEntity 15 -30 0 5 1
    frame data/chars/joe/02.gif
    
    @cmd bindEntity -7 -20 0 3 1
    frame data/chars/joe/03.gif</code></pre>
	</div>
</div>    <br>
    <br>
where your command bindEntity use params in that order : xPosition, yPosition, zPosition, frameNumber, direction.<br>
<br>
The mask you'll need to create is this :<br>
<br>

	
	


<div class="bbCodeBlock bbCodeBlock--screenLimited bbCodeBlock--code">
	<div class="bbCodeBlock-title">
		Code:
	</div>
	<div class="bbCodeBlock-content" dir="ltr">
		<pre class="bbCodeCode" dir="ltr" data-xf-init="code-block" data-lang=""><code>    @cmd bindEntity {x} {y} {z} {frame} {direction}</code></pre>
	</div>
</div>    <br>
    <br>

<div>And you will have to copy paste this mask in the "Text Mask" input in the right panel of the animation editor in ChronoCrash Modders Tools.<br>
<br>
<b><span style="font-size: 22px">And that's it ! Now the binding GUI will load from and to your animations.</span></b><br>
<br>
<br>
If you just want to log the values the principle is the same. For example you can use this mask<br>
<br>
</div>
	
	


<div class="bbCodeBlock bbCodeBlock--screenLimited bbCodeBlock--code">
	<div class="bbCodeBlock-title">
		Code:
	</div>
	<div class="bbCodeBlock-content" dir="ltr">
		<pre class="bbCodeCode" dir="ltr" data-xf-init="code-block" data-lang=""><code>    # CMT binding values : z = {z}; x = {x} ; y = {y} ; dir = {direction} ; frame number = {frame}</code></pre>
	</div>
</div>    <br><br>
<div>Note that you can set up the values in any order you want. To be loaded properly your mask must contain : {x} {y} {z} {frame} {direction}.<br>
But those can be placed anywhere you want within the mask. They just have to be there somewhere.<br>
<br>
Any of those 5 parameters that is not in the mask won't be recognized anymore by the GUI.<br>
<br>
If you don't use a mask, this warning doesn't apply, as the binding GUI will work independently of any text.<br>
<br>
BTW, if you want to make the binding GUI independent again as it was by default, you'll just have to "delete" the text mask in the previously mentioned input. Just replace it with a completely empty/blank text.</div></div>'''
		
		textEdit = QtWidgets.QTextBrowser()
		
		textEdit.setText(text)
		textEdit.setReadOnly(True)
		textEdit.setOpenExternalLinks(True)
		textEdit.setMinimumWidth(400)
		textEdit.setMinimumHeight(300)
		textEdit.hide()
		
		self.widgets['binding-adv1'] = textEdit
		self.widgetLayout.addWidget(textEdit, 1)
		
		
		text = '''<div class="bbWrapper"><span style="font-size: 26px"><b>Binding GUI, How it works, the advanced stuff, part 2 of 2 :</b></span><br>
<br>
Just by setting up the previously mentioned mask, you can make the binding GUI seamlessly compatible with almost any scripting system.<br>
<br>
The mask was already optional, and the stuff I'll explain in this post is very optional. But if your binding system is more complex, this very optional stuff can help make it compatible.<br>
<br>
Let's say you are using constants names in your system. For example let's say one of your animation look like this :<br>
<br>

	
	


<div class="bbCodeBlock bbCodeBlock--screenLimited bbCodeBlock--code">
	<div class="bbCodeBlock-title">
		Code:
	</div>
	<div class="bbCodeBlock-content" dir="ltr">
		<pre class="bbCodeCode" dir="ltr" data-xf-init="code-block" data-lang=""><code>anim grab
    offset 50 50
    @cmd bindEntity 10 20 0 GRAB_DEF DIR_SAME_AS
    frame data/chars/joe/01.gif
   
    @cmd bindEntity 15 -30 0 GRAB_STOMACH DIR_SAME_AS
    frame data/chars/joe/02.gif
   
    @cmd bindEntity -7 -20 0 GRAB_VERTICAL DIR_OPPOSITE_AS
    frame data/chars/joe/03.gif</code></pre>
	</div>
</div>   <br>
   <br>
<div>
 Where the GRAB_DEF, DIR_SAME, and so on refers to constants pointing to integers.<br>
 <br>
 You can set up the binding GUI so that it is compatible with that, through the "additional translations" input, at the bottom of the binding GUI (right panel).<br>
 <br>
 What you have to write in that is the correspondences of every constant, and which setting they are associated to, in a specific format.<br>
 <br>
 So for example :<br>
 <br>
</div>

	
	


<div class="bbCodeBlock bbCodeBlock--screenLimited bbCodeBlock--code">
	<div class="bbCodeBlock-title">
		Code:
	</div>
	<div class="bbCodeBlock-content" dir="ltr">
		<pre class="bbCodeCode" dir="ltr" data-xf-init="code-block" data-lang=""><code>{
 
 'frame' : { 'GRAB_DEF':0, 'GRAB_STOMACH':1, 'GRAB_VERTICAL': 2},
 'direction' : {'DIR_UNCHANGED':0, 'DIR_SAME_AS':1, 'DIR_OPPOSITE_AS:-1, 'DIR_RIGHT':2, 'DIR_LEFT':-2 }
 
 }</code></pre>
	</div>
</div> <br>
 And with that set, every value matching a correspondence will be converted back and forth to the constant name <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" class="smilie smilie--sprite smilie--sprite6" alt=":cool:" title="Cool    :cool:" loading="lazy" data-shortname=":cool:"><br>
<br>
<br>
<b><span style="font-size: 26px">Final word :</span></b><br>
<br>
While I didn't encounter many bugs or problems while I was personally experimenting with this new feature, be cautious and don't use this on files you do not have recently made a copy of. Again, it probably won't mess around with your files, but you never know, at this point this new system has barely been tested by me, let alone by someone else.</div>'''
		
		
		textEdit = QtWidgets.QTextBrowser()
		
		textEdit.setText(text)
		textEdit.setReadOnly(True)
		textEdit.setOpenExternalLinks(True)
		textEdit.setMaximumWidth(800)
		textEdit.setMinimumWidth(400)
		textEdit.setMinimumHeight(300)
		# textEdit.setFixedWidth(int(textEdit.document().idealWidth() + textEdit.contentsMargins().left() + textEdit.contentsMargins().right()))
		textEdit.hide()
		# textEdit.setStyleSheet("QTextBrowser { max-width:600px; background: rgb(0, 255, 0); selection-background-color: rgb(233, 99, 0); }");
		
		self.widgets['binding-adv2'] = textEdit
		self.widgetLayout.addWidget(textEdit, 1)
		
class CreateFileDialog(QtWidgets.QDialog):
	
	TYPE_FIELDS = (('file', _('File')), ('entity', _('Entity')), ('level', _('Level')), ('script', _('Script')))
	
	TYPE_FIELDMODEL = QtGui.QStandardItemModel()
	for key, label in TYPE_FIELDS:
		TYPE_FIELDMODEL.appendRow([QtGui.QStandardItem(key), QtGui.QStandardItem(label)])
		
	def __init__(self):
		QtWidgets.QDialog.__init__(self)
		self.setWindowTitle(_('Create a new file'))
		mainLayout = QtWidgets.QGridLayout()
		self.setLayout(mainLayout)
	
		
		mainLayout.addWidget(QtWidgets.QLabel(_("Category")), 0, 0)
		
		self.fileTypeCB = QtWidgets.QComboBox()
		self.fileTypeCB.setModel(self.TYPE_FIELDMODEL)
		self.fileTypeCB.setModelColumn(1)
		
		self.fileTypeCB.currentIndexChanged[int].connect(self.fileTypeChanged)
		
		mainLayout.addWidget(self.fileTypeCB, 0, 1)
		
		
		mainLayout.addWidget(QtWidgets.QLabel(_("Template")), 1, 0)
		self.templateCB = QtWidgets.QComboBox()
		self.templateModel = QtGui.QStandardItemModel()
		self.templateCB.setModel(self.templateModel)
		mainLayout.addWidget(self.templateCB, 1, 1)
		
		mainLayout.addWidget(QtWidgets.QLabel(_("Path")), 2, 0)
		lookPath = settings.get_option('general/data_path', '')
		self.filePath = FileInput(self, 'saveFile', '', 'Select a .txt level file', lookPath, 'TXT Files (*.txt)')
		mainLayout.addWidget(self.filePath, 2, 1)
		
		
		buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)
		
		mainLayout.addWidget(buttonBox)
		
	def accept(self):
		
		category = self.TYPE_FIELDS[self.fileTypeCB.currentIndex()][0]
		templateFile = self.templateCB.currentText()
		templatePath = None
		if templateFile != _('Empty'):
			templatePath = os.path.join('templates', category, templateFile)
			
		
		filePath = self.filePath.text()
		if os.path.exists(filePath):
			print('the file is there')
		elif os.access(os.path.dirname(filePath), os.W_OK):
			print('the file does not exists but write privileges are given')
			f = open(filePath, 'w')
			if templatePath != None:
				templateF = open(templatePath, 'r')
				templateContent = templateF.read()
				templateF.close()
				f.write(templateContent)
			f.close()
		else:
			print('can not write there')

		
		self.filePath = filePath
		self.category = category
		QtWidgets.QDialog.accept(self)
		
	def fileTypeChanged(self, pos):
		# Fill templateCB with files from templates folders
		category = self.TYPE_FIELDS[pos][0]
		
		self.templateModel.clear()
		self.templateModel.appendRow([QtGui.QStandardItem(_('Empty'))])
		templateFolder = os.path.join('templates', category)
		if os.path.exists(templateFolder):
			for fName in os.listdir(templateFolder):
				self.templateModel.appendRow([QtGui.QStandardItem(fName)])
		
		if pos == 1:
			self.filePath.lookFolder = os.path.join(settings.get_option('general/data_path', ''), 'chars')
		elif pos == 2:
			self.filePath.lookFolder = os.path.join(settings.get_option('general/data_path', ''), 'levels')
		elif pos == 3:
			self.filePath.lookFolder = os.path.join(settings.get_option('general/data_path', ''), 'scripts')
		else:
			self.filePath.lookFolder = settings.get_option('general/data_path', '')
		pass
		
		

class InsertHeaderDialog(QtWidgets.QDialog):

	def __init__(self, editor, commentPrefix='#'):
		self.editor = editor
		self.commentPrefix = commentPrefix
		QtWidgets.QDialog.__init__(self)
		self.setWindowTitle(_('Insert Heading'))

		lay = QtWidgets.QFormLayout()
		self.setLayout(lay)

		# Title input
		self.titleEntry = QtWidgets.QLineEdit()
		self.titleEntry.setPlaceholderText(_('Enter your title here'))
		self.titleEntry.textChanged.connect(self.updatePreview)
		lay.addRow(_('Title'), self.titleEntry)

		# Style selection
		self.styleCombo = QtWidgets.QComboBox()
		self.styleCombo.addItems(['Unicode (box)', 'Block', 'Block Inverse', 'ASCII'])
		self.styleCombo.setCurrentIndex(settings.get_option('code-editor/heading_style', 0))
		self.styleCombo.currentIndexChanged.connect(self.updatePreview)
		lay.addRow(_('Style'), self.styleCombo)

		# Comment prefix
		self.prefixEntry = QtWidgets.QLineEdit()
		self.prefixEntry.setText(commentPrefix)
		self.prefixEntry.textChanged.connect(self.updatePreview)
		lay.addRow(_('Comment prefix'), self.prefixEntry)

		# Width options
		widthLayout = QtWidgets.QHBoxLayout()
		self.autoWidthRadio = QtWidgets.QRadioButton(_('Auto'))
		self.fixedWidthRadio = QtWidgets.QRadioButton(_('Fixed'))
		widthAuto = settings.get_option('code-editor/heading_width_auto', True)
		self.autoWidthRadio.setChecked(widthAuto)
		self.fixedWidthRadio.setChecked(not widthAuto)
		self.widthSpin = QtWidgets.QSpinBox()
		self.widthSpin.setRange(20, 200)
		self.widthSpin.setValue(settings.get_option('code-editor/heading_width', 60))
		self.widthSpin.setEnabled(not widthAuto)
		self.autoWidthRadio.toggled.connect(lambda checked: self.widthSpin.setEnabled(not checked))
		self.autoWidthRadio.toggled.connect(self.updatePreview)
		self.widthSpin.valueChanged.connect(self.updatePreview)
		widthLayout.addWidget(self.autoWidthRadio)
		widthLayout.addWidget(self.fixedWidthRadio)
		widthLayout.addWidget(self.widthSpin)
		lay.addRow(_('Width'), widthLayout)

		# Padding
		self.paddingSpin = QtWidgets.QSpinBox()
		self.paddingSpin.setRange(1, 20)
		self.paddingSpin.setValue(settings.get_option('code-editor/heading_padding', 6))
		self.paddingSpin.valueChanged.connect(self.updatePreview)
		lay.addRow(_('Padding'), self.paddingSpin)

		# Margin (spaces between comment prefix and box)
		self.marginSpin = QtWidgets.QSpinBox()
		self.marginSpin.setRange(0, 50)
		self.marginSpin.setValue(settings.get_option('code-editor/heading_margin', 0))
		self.marginSpin.valueChanged.connect(self.updatePreview)
		lay.addRow(_('Margin'), self.marginSpin)

		# Vertical spacing (empty lines above and below)
		self.verticalSpacingSpin = QtWidgets.QSpinBox()
		self.verticalSpacingSpin.setRange(0, 10)
		self.verticalSpacingSpin.setValue(settings.get_option('code-editor/heading_vertical_spacing', 0))
		self.verticalSpacingSpin.valueChanged.connect(self.updatePreview)
		lay.addRow(_('Vertical spacing'), self.verticalSpacingSpin)

		# Preview
		self.previewText = QtWidgets.QTextEdit()
		self.previewText.setReadOnly(True)
		self.previewText.setFont(QtGui.QFont('Monospace', 10))
		self.previewText.setMinimumHeight(100)
		self.previewText.setMinimumWidth(400)
		lay.addRow(_('Preview'), self.previewText)

		buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)

		lay.addRow(buttonBox)

		self.updatePreview()

	def getStyleEnum(self):
		from guilib.title_box import BoxStyle
		styles = [BoxStyle.UNICODE, BoxStyle.BLOCK, BoxStyle.BLOCK_INVERSE, BoxStyle.ASCII]
		return styles[self.styleCombo.currentIndex()]

	def updatePreview(self):
		from guilib.title_box import generate_title_box

		title = self.titleEntry.text() or 'Example Title'
		style = self.getStyleEnum()
		prefix = self.prefixEntry.text()
		width = None if self.autoWidthRadio.isChecked() else self.widthSpin.value()
		padding = self.paddingSpin.value()
		margin = self.marginSpin.value()
		verticalSpacing = self.verticalSpacingSpin.value()

		try:
			result = generate_title_box(title, prefix=prefix, style=style, width=width, padding=padding, margin=margin)
			# Add vertical spacing (empty lines above and below)
			if verticalSpacing > 0:
				emptyLines = '\n' * verticalSpacing
				result = emptyLines + result + emptyLines
			self.previewText.setPlainText(result)
		except Exception as e:
			self.previewText.setPlainText(f'Error: {e}')

	def accept(self):
		from guilib.title_box import generate_title_box

		title = self.titleEntry.text()
		if not title:
			QtWidgets.QMessageBox.warning(self, _('Warning'), _('Please enter a title'))
			return

		style = self.getStyleEnum()
		prefix = self.prefixEntry.text()
		widthAuto = self.autoWidthRadio.isChecked()
		width = None if widthAuto else self.widthSpin.value()
		padding = self.paddingSpin.value()
		margin = self.marginSpin.value()
		verticalSpacing = self.verticalSpacingSpin.value()

		# Save settings (except title)
		settings.set_option('code-editor/heading_style', self.styleCombo.currentIndex())
		settings.set_option('code-editor/heading_width_auto', widthAuto)
		settings.set_option('code-editor/heading_width', self.widthSpin.value())
		settings.set_option('code-editor/heading_padding', padding)
		settings.set_option('code-editor/heading_margin', margin)
		settings.set_option('code-editor/heading_vertical_spacing', verticalSpacing)

		result = generate_title_box(title, prefix=prefix, style=style, width=width, padding=padding, margin=margin)

		# Add vertical spacing (empty lines above and below)
		if verticalSpacing > 0:
			emptyLines = '\n' * verticalSpacing
			result = emptyLines + result + emptyLines

		# Insert at cursor position
		cursor = self.editor.textCursor()
		# Add newline before if not at start of line
		if cursor.columnNumber() > 0:
			result = '\n' + result
		# Add newline after
		result = result + '\n'

		self.editor.selectedText = result

		QtWidgets.QDialog.accept(self)


class GeneratePathsDialog(QtWidgets.QDialog):

	def __init__(self, editor):
		self.editor = editor
		QtWidgets.QDialog.__init__(self)
		self.setWindowTitle(_('Generate paths'))
		
		lay = QtWidgets.QFormLayout()
		self.setLayout(lay)
		
		lay.addRow(QtWidgets.QLabel(_('Warning : don\'t forget that you can also drag and drop files directly in text editors')))
		
		self.maskEntry = QtWidgets.QLineEdit()
		self.maskEntry.setText('	frame data/chars/joe-attack{frame}.png')
		
		lay.addRow(_('Mask'), self.maskEntry)
				   
		self.start = QtWidgets.QSpinBox()
		self.end = QtWidgets.QSpinBox()
		self.end.setValue(3)
		
		lay.addRow(_('Start'), self.start)
		lay.addRow(_('End'), self.end)
		
		buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)
		
		
		
		lay.addRow(buttonBox)
		
		
		
		
	def accept(self):
		
		# print("accepting")
		start = self.start.value()
		end = self.end.value()
		
		mask = self.maskEntry.text()
		
		txt = ''
		for i in range(start, end+1):
			txt += mask.replace('{frame}', str(i)) + '\n'
			
		#print(txt)
		
		self.editor.selectedText = txt
		
		QtWidgets.QDialog.accept(self)

		#return txt


class ProjectSettingsDialog(QtWidgets.QDialog):

	def __init__(self, projectName, projectPath):
		QtWidgets.QDialog.__init__(self)
		self.projectName = projectName
		self.projectPath = projectPath
		self.setWindowTitle(_('Project settings') + ' - ' + projectName)
		self.setMinimumWidth(500)

		mainLayout = QtWidgets.QVBoxLayout()
		self.setLayout(mainLayout)

		# --- Search settings ---
		searchGroup = QtWidgets.QGroupBox(_('File search settings'))
		searchLayout = QtWidgets.QVBoxLayout()
		searchGroup.setLayout(searchLayout)

		# Whitelist
		whitelistLabel = QtWidgets.QLabel(_('Whitelist (only search in these directories, relative to project root, one per line) :'))
		whitelistLabel.setWordWrap(True)
		searchLayout.addWidget(whitelistLabel)

		self.whitelistEdit = QtWidgets.QPlainTextEdit()
		self.whitelistEdit.setPlaceholderText(_('e.g. data/chars\ndata/levels\n(leave empty to search everywhere)'))
		self.whitelistEdit.setMaximumHeight(100)
		whitelist = settings.get_option('project/' + projectName + '/search_whitelist', [])
		self.whitelistEdit.setPlainText('\n'.join(whitelist))
		searchLayout.addWidget(self.whitelistEdit)

		# Blacklist
		blacklistLabel = QtWidgets.QLabel(_('Blacklist (ignore files/directories matching these patterns, one per line) :'))
		blacklistLabel.setWordWrap(True)
		searchLayout.addWidget(blacklistLabel)

		self.blacklistEdit = QtWidgets.QPlainTextEdit()
		self.blacklistEdit.setPlaceholderText(_('e.g. .*\n*.1\n*.bak'))
		self.blacklistEdit.setMaximumHeight(100)
		blacklist = settings.get_option('project/' + projectName + '/search_blacklist', [])
		self.blacklistEdit.setPlainText('\n'.join(blacklist))
		searchLayout.addWidget(self.blacklistEdit)

		blacklistHelpLabel = QtWidgets.QLabel(_('Use * as wildcard. Examples: .* (files starting with dot), *.1 (files ending with .1), __pycache__ (exact name)'))
		blacklistHelpLabel.setWordWrap(True)
		blacklistHelpLabel.setStyleSheet("color: gray; font-size: 11px;")
		searchLayout.addWidget(blacklistHelpLabel)

		mainLayout.addWidget(searchGroup)

		mainLayout.addStretch(1)

		# Buttons
		buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)
		mainLayout.addWidget(buttonBox)

	def accept(self):
		# Parse whitelist
		whitelist = [line.strip() for line in self.whitelistEdit.toPlainText().split('\n') if line.strip()]
		settings.set_option('project/' + self.projectName + '/search_whitelist', whitelist)

		# Parse blacklist
		blacklist = [line.strip() for line in self.blacklistEdit.toPlainText().split('\n') if line.strip()]
		settings.set_option('project/' + self.projectName + '/search_blacklist', blacklist)

		settings.MANAGER.save()
		QtWidgets.QDialog.accept(self)

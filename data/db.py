import threading
import os
import sqlite3
from common import settings, util, xdg

from datetime import datetime


# Blabla ff 

class DB():
	NOW = "strftime('%Y-%m-%d %H:%M:%S','now')";
	
	LIMIT_PER_FILE = 100
	
	
	# Type_ID :
	# 1 : 
	# 2 : daily saves
	# 3 : hourly saves
	# 10 : snapshot
	
	def __init__(self, fileName):
		
		self.lock = threading.Lock()
		
		db_path = os.path.join(xdg.get_data_home(), fileName)
		if os.path.exists(db_path):
			self.conn = sqlite3.connect(db_path,  check_same_thread=False)
			self.conn.row_factory = sqlite3.Row
			self.c = self.conn.cursor()
			self.createTables(True)
		else:
			self.conn = sqlite3.connect(db_path,  check_same_thread=False)
			self.conn.row_factory = sqlite3.Row
			self.c = self.conn.cursor()
			self.createTables()
			
	def createTables(self, newOnly=False):
		if not newOnly:
			# ***** Music *****
			self.c.execute('''CREATE TABLE files_backup
			(ID INTEGER PRIMARY KEY AUTOINCREMENT, path text, content text, birth_date datetime NOT NULL, unsaved BOOLEAN DEFAULT 0, Type_ID INTEGER,  file_version text DEFAULT NULL, comment text DEFAULT NULL
			)''')
			self.c.execute('''CREATE TABLE IF NOT EXISTS notes
			(ID INTEGER PRIMARY KEY AUTOINCREMENT, label text, content text, birth_date datetime NOT NULL, edit_date datetime NOT NULL
			)''')
		else:
			query = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('files_backup') WHERE name='file_version'";
			self.c.execute(query)
			

			rows = self.c.fetchall()
			
			
			if(rows[0]['CNTREC'] == 0):
				query2 = "ALTER TABLE files_backup ADD  file_version text DEFAULT NULL;";
				self.c.execute(query2)
				self.conn.commit()
				
			query = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('files_backup') WHERE name='comment'";
			self.c.execute(query)
			

			rows = self.c.fetchall()
			
			
			if(rows[0]['CNTREC'] == 0):
				query2 = "ALTER TABLE files_backup ADD  comment text DEFAULT NULL;";
				self.c.execute(query2)
				self.conn.commit()

			self.c.execute('''CREATE TABLE IF NOT EXISTS notes
			(ID INTEGER PRIMARY KEY AUTOINCREMENT, label text, content text, birth_date datetime NOT NULL, edit_date datetime NOT NULL
			)''')
			self.conn.commit()


		
	def addBackup(self, params):
		
		now = datetime.utcnow()
 
		print("now =", now)

		# dd/mm/YY H:M:S
		
		dt_string_type3 = now.strftime("%Y/%m/%d %H")
		dt_string_type2 = now.strftime("%Y/%m/%d")
		print(dt_string_type3)
		
		path = params[0]
		unsaved = params[2]
		type = params[3]
		version = params[4]
		comment = None
		if(len(params) > 5):
			comment = params[5]
		else:
			params.append(comment)
		
		
		limit_saved = settings.get_option('autobackup/max_number_revisions_saved_per_file', 50)
		
		
		limit_unsaved = settings.get_option('autobackup/max_number_revisions_unsaved_per_file', 50)
		
		if(unsaved == 1):
			DB.LIMIT_PER_FILE = limit_unsaved
		else:
			DB.LIMIT_PER_FILE = limit_saved
			
		
		type1_delete_after = settings.get_option('autobackup/auto_delete_revisions_after_days', 90)
		
		try:
			self.lock.acquire(True)
		
		
			query = '''INSERT INTO files_backup (path, content, birth_date, unsaved, Type_ID, file_version, comment) VALUES (?, ?, ''' + DB.NOW + ''', ?, ?, ?, ?)'''
			self.c.execute(query, params)
			self.conn.commit()
			
			
			if(type == 10):
				self.lock.release()
				return
			
			
			# GLOBAL CLEAN
			
			# delete entries of Type_ID = 1 when older than (type1_delete_after) days
			query = ''' DELETE FROM files_backup WHERE birth_date <  DATETIME('now', ?) AND unsaved = ? AND Type_ID = 1'''
			# self.c.execute(query, ['-' + str(type3_delete_after) + ' day', params[0], 0])
			self.c.execute(query, ['-' + str(type1_delete_after) + ' day', unsaved])
			
			
			# take all entries than are not Type_ID = 2 (that is daily saves)
			query = '''SELECT ID  FROM files_backup WHERE path = ? AND unsaved = ? AND Type_ID = 1 ORDER BY birth_date ASC'''
			self.c.execute(query, [params[0], params[2]])
			
			
			
			
			
			
			
			# ... if there are more than DB.LIMIT_PER_FILE revisions, then delete the oldest excedent
			rows = self.c.fetchall()
			print("number of rows", len(rows))
			if(len(rows) > DB.LIMIT_PER_FILE):
				IDS = []
				for i in range(len(rows) - DB.LIMIT_PER_FILE):
					IDS.append(rows[i]['ID'])
				
				if(len(IDS) > 0):
					self.deleteRevisions(IDS)
					
					
			# TYPE 2 - days
			type2_per_basis = settings.get_option('autobackup/type2_keep_one_revision_per', 1)
			type2_delete_after = settings.get_option('autobackup/type2_auto_delete_revisions_after', 365)
			
			if(unsaved == 0 and type2_per_basis > 0):
				
				# GLOBAL CLEAN - We delete daily revisions that are older than (type2_delete_after) days
				query = ''' DELETE FROM files_backup WHERE birth_date <  DATETIME('now', ?) AND unsaved = ? AND Type_ID = 2'''
				# self.c.execute(query, ['-' + str(type3_delete_after) + ' day', params[0], 0])
				self.c.execute(query, ['-' + str(type2_delete_after) + ' day', 0])
				# self.conn.commit()
				
				
				# Clean previous revisions for this day, so that in practice we overwrite them and only keep one revision per day
				# query = ''' SELECT ID FROM files_backup WHERE strftime('%Y/%m/%d %H', birth_date) = ? AND path = ? AND unsaved = ?'''
				query = ''' DELETE FROM files_backup WHERE strftime('%Y/%m/%d', birth_date) = ? AND path = ? AND unsaved = ? AND Type_ID = 2'''
				self.c.execute(query, [dt_string_type2, params[0], 0])
				self.conn.commit()
				
				# We add the revision
				query = '''INSERT INTO files_backup (path, content, birth_date, unsaved, Type_ID, file_version) VALUES (?, ?, ''' + DB.NOW + ''', ?, ?, ?)'''
				self.c.execute(query, [params[0], params[1], params[2], 2, params[4]])
				self.conn.commit()
					
			
			# TYPE 3 - hours
			type3_per_basis = settings.get_option('autobackup/type3_keep_one_revision_per', 0)
			type3_delete_after = settings.get_option('autobackup/type3_auto_delete_revisions_after', 100)
			
			if(unsaved == 0 and type3_per_basis > 0):
				
				# GLOBAL CLEAN - We delete all entries that are older than (type3_delete_after) hours
				query = ''' DELETE FROM files_backup WHERE birth_date <  DATETIME('now', ?) AND unsaved = ? AND Type_ID = 3'''
				# self.c.execute(query, ['-' + str(type3_delete_after) + ' day', params[0], 0])
				self.c.execute(query, ['-' + str(type3_delete_after) + ' hour', 0])
				# self.conn.commit()
				
				
				# We delete revisions for this hour, so that in practice we overwrite them and only keep one revision per hour
				# query = ''' SELECT ID FROM files_backup WHERE strftime('%Y/%m/%d %H', birth_date) = ? AND path = ? AND unsaved = ?'''
				query = ''' DELETE FROM files_backup WHERE strftime('%Y/%m/%d %H', birth_date) = ? AND path = ? AND unsaved = ? AND Type_ID = 3'''
				self.c.execute(query, [dt_string_type3, params[0], 0])
				self.conn.commit()
				
				# We add the revision
				query = '''INSERT INTO files_backup (path, content, birth_date, unsaved, Type_ID, file_version) VALUES (?, ?, ''' + DB.NOW + ''', ?, ?, ?)'''
				self.c.execute(query, [params[0], params[1], params[2], 3, params[4]])
				self.conn.commit()
				
				
				# p.birth_date > DATETIME(\'now\', \'-30 day\')
		finally:
			self.lock.release()
			
			
			
		
		
		
		
		
		
	def deleteAllRevisions(self):
		self.c.execute('DELETE FROM files_backup')
		self.conn.commit()
		
	def deleteRevisions(self, IDS):
		
		self.c.execute('DELETE FROM files_backup WHERE ID IN (%s)' % ("?," * len(IDS))[:-1], IDS)
		self.conn.commit()
		
		
	def getLastRevision(self, path, unsaved=1):
		
		try:
			self.lock.acquire(True)
			query = '''SELECT content FROM files_backup WHERE path = ? AND unsaved = ? ORDER BY birth_date DESC'''
			params = [path, unsaved]
			self.c.execute(query, params)
			
			row = self.c.fetchone()
		finally:
			self.lock.release()
		
		if row != None:
			return row['content']
			
			
	def getRevisionContent(self, ID):
		query = '''SELECT content FROM files_backup WHERE ID = ?'''
		params = [ID]
		self.c.execute(query, params)
		
		row = self.c.fetchone()
		
		if row != None:
			return row['content']
		
	# ---- Notes ----

	def createNote(self, label, content=''):
		try:
			self.lock.acquire(True)
			query = '''INSERT INTO notes (label, content, birth_date, edit_date) VALUES (?, ?, ''' + DB.NOW + ''', ''' + DB.NOW + ''')'''
			self.c.execute(query, [label, content])
			self.conn.commit()
			return self.c.lastrowid
		finally:
			self.lock.release()

	def getAllNotes(self):
		try:
			self.lock.acquire(True)
			query = '''SELECT ID, label, birth_date, edit_date FROM notes ORDER BY edit_date DESC'''
			self.c.execute(query)
			return self.c.fetchall()
		finally:
			self.lock.release()

	def getNoteContent(self, noteId):
		try:
			self.lock.acquire(True)
			query = '''SELECT content FROM notes WHERE ID = ?'''
			self.c.execute(query, [noteId])
			row = self.c.fetchone()
			if row is not None:
				return row['content'] or ''
			return ''
		finally:
			self.lock.release()

	def updateNote(self, noteId, content):
		try:
			self.lock.acquire(True)
			query = '''UPDATE notes SET content = ?, edit_date = ''' + DB.NOW + ''' WHERE ID = ?'''
			self.c.execute(query, [content, noteId])
			self.conn.commit()
		finally:
			self.lock.release()

	def getAllRevisions(self, pathFilter=[]):
		query = '''SELECT ID, path, birth_date, unsaved, Type_ID, file_version, comment FROM files_backup '''
		
		queryParams = []
		if(len(pathFilter) > 0):
			query += ' WHERE path IN (' + ','.join('?') + ')'
			queryParams = pathFilter
		query += '''ORDER BY birth_date DESC, ID DESC'''
		
		
		print(query, queryParams);
		
		self.c.execute(query, queryParams)
		
		return self.c.fetchall()
		
		
		

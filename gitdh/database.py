# -*- coding: utf-8 -*-

from gitdh.git import GitCommit

class DatabaseBackend(object):
	@staticmethod
	def getDatabaseBackend(config):
		dbEngine = config['Database']['Engine']
		if dbEngine == 'mysql':
			db = MySQL(config)
		elif dbEngine == 'mongodb':
			db = MongoDB(config)
		elif dbEngine == 'sqlite':
			db = SQLite(config)
		else:
			raise Exception("Unknown Database Engine")
		return db

	def __init__(self, config):
		self.config = config

	def getQueuedCommits(self):
		pass

	def getAllCommits(self):
		pass

	def insertCommit(self, commit):
		pass

	def setStatusWorking(self, commit):
		self.setStatus(commit, commit.status[:commit.status.rfind('_')] + '_working')

	def setStatusSkipped(self, commit):
		self.setStatus(commit, commit.status[:commit.status.rfind('_')] + '_skipped')

	def setStatusFinished(self, commit):
		self.setStatus(commit, commit.status[:commit.status.rfind('_')] + '_finished')

	def setStatus(self, commit, status):
		pass


class MySQL(DatabaseBackend):
	def __init__(self, config):
		import pymysql
		DatabaseBackend.__init__(self, config)
		confSection = config['Database']
		self.conn = pymysql.connect(host=confSection['Host'], port=config.getint('Database', 'Port'), user=confSection['User'], passwd=confSection['Password'], db=confSection['Database'])
		self.cur = self.conn.cursor()
		self.tableName = confSection['Table']

	def getQueuedCommits(self):
		self.cur.execute("SELECT `id`, `hash`, `author`, `date`, `message`, `branch`, `repository`, `status` FROM `{0}` WHERE status LIKE '%\_queued' ORDER BY `date` ASC".format(self.tableName))
		commits = []
		for dbCommit in self.cur.fetchall():
			commits.append(GitCommit(dbCommit[1], dbCommit[2], dbCommit[3], dbCommit[4], dbCommit[5], dbCommit[6], id=dbCommit[0], status=dbCommit[7]))
		return commits

	def getAllCommits(self):
		self.cur.execute('SELECT `id`, `hash`, `author`, `date`, `message`, `branch`, `repository`, `status` FROM `{0}` ORDER BY `date` ASC'.format(self.tableName))
		commits = []
		for dbCommit in self.cur.fetchall():
			commits.append(GitCommit(dbCommit[1], dbCommit[2], dbCommit[3], dbCommit[4], dbCommit[5], dbCommit[6], id=dbCommit[0], status=dbCommit[7]))
		return commits

	def insertCommit(self, commit):
		params = (commit.hash, commit.author, commit.date, commit.message, commit.status, commit.repository, commit.branch)
		self.cur.execute('INSERT INTO `{0}` (`hash`, `author`, `date`, `message`, `status`, `repository`, `branch`) VALUES (%s, %s, %s, %s, %s, %s, %s)'.format(self.tableName), params)
		self.cur.connection.commit()
		commit.id = self.cur.lastrowid

	def setStatus(self, commit, status):
		commit.status = status
		if hasattr(commit, 'id') and not commit.id is None:
			params = (status, commit.id)
			self.cur.execute('UPDATE `{0}` SET `status`=%s WHERE `id`=%s'.format(self.tableName), params)
			self.cur.connection.commit()

	def __del__(self):
		try:
			self.cur.close()
		except AttributeError:
			pass
		try:
			self.conn.close()
		except AttributeError:
			pass

class SQLite(MySQL):
	def __init__(self, config):
		import sqlite3
		DatabaseBackend.__init__(self, config)
		confSection = config['Database']
		self.conn = sqlite3.connect(confSection['DatabaseFile'])
		self.cur = self.conn.cursor()
		self.tableName = confSection['Table']
		self._createTable()

	def _createTable(self):
		self.cur.execute("""
CREATE TABLE IF NOT EXISTS {0} (
  `id` INTEGER PRIMARY KEY NOT NULL,
  `hash` TEXT NOT NULL,
  `author` TEXT NOT NULL,
  `date` INTEGER NOT NULL,
  `message` text NOT NULL,
  `status` TEXT NOT NULL,
  `repository` TEXT NOT NULL,
  `branch` TEXT NOT NULL
);""".format(self.tableName))
		self.conn.commit()

	def getQueuedCommits(self):
		self.cur.execute("SELECT `id`, `hash`, `author`, `date`, `message`, `branch`, `repository`, `status` FROM `{0}` WHERE status LIKE '%_queued' ORDER BY `date` ASC".format(self.tableName))
		commits = []
		for dbCommit in self.cur.fetchall():
			commits.append(GitCommit(dbCommit[1], dbCommit[2], dbCommit[3], dbCommit[4], dbCommit[5], dbCommit[6], id=dbCommit[0], status=dbCommit[7]))
		return commits

	def insertCommit(self, commit):
		params = (commit.hash, commit.author, commit.date, commit.message, commit.status, commit.repository, commit.branch)
		self.cur.execute("INSERT INTO `{0}` (`hash`, `author`, `date`, `message`, `status`, `repository`, `branch`) VALUES (?, ?, ?, ?, ?, ?, ?)".format(self.tableName), params)
		self.cur.connection.commit()
		commit.id = self.cur.lastrowid

	def setStatus(self, commit, status):
		commit.status = status
		if hasattr(commit, 'id') and not commit.id is None:
			params = (status, commit.id)
			self.cur.execute('UPDATE `{0}` SET `status`=? WHERE `id`=?'.format(self.tableName), params)
			self.cur.connection.commit()


class MongoDB(DatabaseBackend):
	def __init__(self, config):
		import pymongo
		DatabaseBackend.__init__(self, config)
		confSection = config['Database']
		self.client = pymongo.MongoClient(host=confSection['Host'], port=config.getint('Database', 'Port'))
		self.coll = self.client[confSection['Database']][confSection['Collection']]

	def getQueuedCommits(self):
		jsonCommits = self.coll.find({'status': {'$regex': '_queued$'}}, ['_id', 'hash', 'author', 'date', 'message', 'branch', 'repository', 'status']).sort('date')
		commits = []
		for jsonCommit in jsonCommits:
			commits.append(GitCommit(jsonCommit['hash'], jsonCommit['author'], jsonCommit['date'], jsonCommit['message'], jsonCommit['branch'], jsonCommit['repository'], id=jsonCommit['_id'], status=jsonCommit['status']))
		return commits

	def getAllCommits(self):
		jsonCommits = self.coll.find({}, ['_id', 'hash', 'author', 'date', 'message', 'branch', 'repository', 'status']).sort('date')
		commits = []
		for jsonCommit in jsonCommits:
			commits.append(GitCommit(jsonCommit['hash'], jsonCommit['author'], jsonCommit['date'], jsonCommit['message'], jsonCommit['branch'], jsonCommit['repository'], id=jsonCommit['_id'], status=jsonCommit['status']))
		return commits

	def insertCommit(self, commit):
		keys = {'hash', 'author', 'date', 'message', 'branch', 'repository', 'status'}
		commitDict = {}
		for key in keys:
			commitDict[key] = getattr(commit, key)
		self.coll.insert(commitDict)
		commit.id = commitDict['_id']

	def setStatus(self, commit, status):
		commit.status = status
		if hasattr(commit, 'id') and not commit.id is None:
			self.coll.update({'_id': commit.id}, {'$set': {'status': status}})

	def __del__(self):
		self.client.disconnect()

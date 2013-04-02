#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from configparser import ConfigParser
from copy import copy
from git import GitCommit

class DatabaseConnection(object):
	@staticmethod
	def getDatabaseConnection(config=None):
		if config == None:
			config = ConfigParser()
			config.read("config.ini")
		dbEngine = config["Database"]["Engine"]
		if dbEngine == "mysql":
			db = MySQL(config)
		elif dbEngine == "mongodb":
			db = MongoDB(config)
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

	def setStatusFinished(self, commit):
		self.setStatus(commit, commit.status[:commit.status.rfind('_')] + '_finished')

	def setStatus(self, commit, status):
		pass


class MySQL(DatabaseConnection):
	def __init__(self, config):
		import pymysql
		DatabaseConnection.__init__(self, config)
		confSection = config["Database"]
		self.conn = pymysql.connect(host=confSection["Host"], port=config.getint("Database", "Port"), user=confSection["User"], passwd=confSection["Password"], db=confSection["Database"])
		self.cur = self.conn.cursor()
		self.tableName = config["Database"]["Table"]

	def getQueuedCommits(self):
		self.cur.execute("SELECT `id`, `hash`, `author`, `date`, `message`, `branch`, `repository`, `status` `approver`, `approverdate` FROM `{0}` WHERE status LIKE '%\_queued' ORDER BY `date` ASC".format(self.tableName))
		commits = []
		for dbCommit in self.cur.fetchall():
			commit = GitCommit(dbCommit[1], dbCommit[2], dbCommit[3], dbCommit[4], dbCommit[5], dbCommit[6], id=dbCommit[0], status=dbCommit[7], approver=dbCommit[8], approverDate=dbCommit[9])
		return commits

	def getAllCommits(self):
		self.cur.execute("SELECT `id`, `hash`, `author`, `date`, `message`, `branch`, `repository`, `status` `approver`, `approverdate` FROM `{0}` ORDER BY `date` ASC".format(self.tableName))
		commits = []
		for dbCommit in self.cur.fetchall():
			commit = GitCommit(dbCommit[1], dbCommit[2], dbCommit[3], dbCommit[4], dbCommit[5], dbCommit[6], id=dbCommit[0], status=dbCommit[7], approver=dbCommit[8], approverDate=dbCommit[9])
		return commits

	def insertCommit(self, commit):
		params = (commit.hash, commit.author, commit.date, commit.message, commit.status, commit.repository, commit.branch)
		self.cur.execute("INSERT INTO `{0}` (`hash`, `author`, `date`, `message`, `status`, `repository`, `branch`) VALUES (%s, %s, %s, %s, %s, %s, %s)".format(self.tableName), params)
		commit.id = self.cur.lastrowid

	def setStatus(self, commit, status):
		commit.status = status
		if hasattr(commit, "id") and commit.id != None:
			params = (status, commit.id)
			self.cur.execute("UPDATE `{0}` SET `status`=%s WHERE `id`=%s".format(self.tableName), params)

	def __del__(self):
		self.cur.close()
		self.conn.close()

class MongoDB(DatabaseConnection):
	def __init__(self, config):
		import pymongo
		DatabaseConnection.__init__(self, config)
		confSection = config["Database"]
		self.conn = pymongo.Connection(confSection["Host"], config.getint("Database", "Port"))
		self.coll = self.conn[confSection["Database"]][confSection["Collection"]]

	def getQueuedCommits(self):
		jsonCommits = self.coll.find({"status": {"$regex": "_queued$"}}, ["_id", "hash", "author", "date", "message", "branch", "repository", "status", "approver", "approverDate"]).sort("date")
		commits = []
		for jsonCommit in jsonCommits:
			commits.append(GitCommit(jsonCommit["hash"], jsonCommit["author"], jsonCommit["date"], jsonCommit["message"], jsonCommit["branch"], jsonCommit["repository"], id=jsonCommit["_id"], status=jsonCommit["status"], approver=jsonCommit["approver"], approverDate=jsonCommit["approverDate"]))
		return commits

	def getAllCommits(self):
		jsonCommits = self.coll.find({}, ["_id", "hash", "author", "date", "message", "branch", "repository", "status", "approver", "approverDate"]).sort("date")
		commits = []
		for jsonCommit in jsonCommits:
			commits.append(GitCommit(jsonCommit["hash"], jsonCommit["author"], jsonCommit["date"], jsonCommit["message"], jsonCommit["branch"], jsonCommit["repository"], id=jsonCommit["_id"], status=jsonCommit["status"], approver=jsonCommit["approver"], approverDate=jsonCommit["approverDate"]))
		return commits

	def insertCommit(self, commit):
		commitCopy = copy(commit)
		del commitCopy.id
		jsonCommit = commitCopy.__dict__
		self.coll.insert(jsonCommit)
		commit.id = jsonCommit['_id']

	def setStatus(self, commit, status):
		commit.status = status
		if hasattr(commit, "id") and commit.id != None:
			self.coll.update({"_id": commit.id}, {"$set": {"status": status}})

	def __del__(self):
		self.conn.close()

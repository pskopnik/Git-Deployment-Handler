#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from configparser import ConfigParser


class DatabaseConnection(object):
	@staticmethod
	def getDatabaseConnection(config=None):
		if config == None:
			config = ConfigParser()
			config.read("config.ini")
		dbEngine = config.get("Database", "Engine")
		if dbEngine == "mysql":
			db = MySQL(config)
		elif dbEngine == "mongodb":
			db = MongoDB(config)
		else:
			raise Exception("Unknown Database Engine")
		return db
	
	def __init__(self, config):
		self.config = config

	def getAllAprovedCommits(self):
		pass

	def insertCommit(self, commitHash, commitAuthor, commitDate, commitMessage, branch, status=1):
		pass

	def setStatusWorking(self, commitId, firstStatus):
		pass

	def setStatusFinished(self, commitId, firstStatus):
		pass


class MySQL(DatabaseConnection):
	def __init__(self, config):
		import pymysql
		DatabaseConnection.__init__(self, config)
		self.conn = pymysql.connect(host=config.get("Database", "Host"), port=config.getint("Database", "Port"), user=config.get("Database", "User"), passwd=config.get("Database", "Password"), db=config.get("Database", "Database"))
		self.cur = self.conn.cursor()
		self.tableName = config.get("Database", "Table")

	def getAllAprovedCommits(self):
		self.cur.execute("SELECT `id`, `commit`, `branch`, `status` FROM `{0}` WHERE status='2' OR status='5'".format(self.tableName))
		return self.cur.fetchall()
	
	def insertCommit(self, commitHash, commitAuthor, commitDate, commitMessage, branch, status=1):
		params = (commitHash, commitAuthor , commitDate, commitMessage, status, branch)
		self.cur.execute("INSERT INTO `{0}` (`commit`, `commiter`, `commitdate`, `message`, `status`, `branch`) VALUES (%s, %s, %s, %s, %s, %s)".format(self.tableName), params)

	def setStatusWorking(self, commitId, firstStatus):
		params = (firstStatus + 1, commitId)
		self.cur.execute("UPDATE `{0}` SET `status`=%s WHERE `id`=%s".format(self.tableName), params)

	def setStatusFinished(self, commitId, firstStatus):
		params = (firstStatus + 2, commitId)
		self.cur.execute("UPDATE `{0}` SET `status`=%s WHERE `id`=%s".format(self.tableName), params)

	def __del__(self):
		self.cur.close()
		self.conn.close()

class MongoDB(DatabaseConnection):
	def __init__(self, config):
		import pymongo
		DatabaseConnection.__init__(self, config)
		self.conn = pymongo.Connection(config.get("Database", "Host"), config.getint("Database", "Port"))
		self.coll = self.conn[config.get("Database", "Database")][config.get("Database", "Collection")]

	def getAllAprovedCommits(self):
		jsonCommits = self.coll.find({"$or": [{"status": 2}, {"status": 5}]}, ["commit", "branch", "status"])
		commits = []
		for jsonCommit in jsonCommits:
			commits.append([jsonCommit["_id"], jsonCommit["commit"], jsonCommit["branch"], jsonCommit["status"]])
		return commits

	def insertCommit(self, commitHash, commitAuthor, commitDate, commitMessage, branch, status=1):
		commit = {"commit": commitHash, "commiter": commitAuthor, "commitdate": commitDate, "message": commitMessage, "status": status, "branch": branch}
		self.coll.insert(commit)

	def setStatusWorking(self, commitId, firstStatus):
		self.coll.update({"_id": commitId}, {"$set": {"status": firstStatus + 1}})

	def setStatusFinished(self, commitId, firstStatus):
		self.coll.update({"_id": commitId}, {"$set": {"status": firstStatus + 2}})

	def __del__(self):
		self.conn.close()
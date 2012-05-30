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

	def insertCommit(self, commitHash, commitAuthor, commitDate, commitMessage, project):
		pass

	def setStatusWorking(self, commitId):
		pass

	def setStatusFinished(self, commitId):
		pass


class MySQL(DatabaseConnection):
	def __init__(self, config):
		import pymysql
		DatabaseConnection.__init__(self, config)
		self.conn = pymysql.connect(host=config.get("Database", "Host"), port=config.getint("Database", "Port"), user=config.get("Database", "User"), passwd=config.get("Database", "Password"), db=config.get("Database", "Database"))
		self.cur = self.conn.cursor()

	def getAllAprovedCommits(self):
		self.cur.execute("SELECT `id`, `commit`, `project` FROM `commits` WHERE status='2'")
		return self.cur.fetchall()
	
	def insertCommit(self, commitHash, commitAuthor, commitDate, commitMessage, project):
		params = (commitHash, commitAuthor , commitDate, commitMessage, 1, project)
		self.cur.execute("INSERT INTO `commits` (`commit`, `commiter`, `commitdate`, `message`, `status`, `project`) VALUES (%s, %s, %s, %s, %s, %s)",  params)

	def setStatusWorking(self, commitId):
		self.cur.execute("UPDATE `commits` SET `status`='3' WHERE `id`=%s",  commitId)

	def setStatusFinished(self, commitId):
		self.cur.execute("UPDATE `commits` SET `status`='4' WHERE `id`=%s",  commitId)

	def __del__(self):
		self.cur.close()
		self.conn.close()

class MongoDB(DatabaseConnection):
	def __init__(self, config):
		import pymongo
		DatabaseConnection.__init__(self, config)
		self.conn = pymongo.Connection(config.get("Database", "Host"), config.getint("Database", "Port"))
		self.db = self.conn[config.get("Database", "Database")]

	def getAllAprovedCommits(self):
		jsonCommits = self.db.commits.find({"status": 2}, ["commit", "project"])
		commits = []
		for jsonCommit in jsonCommits:
			commits.append([jsonCommit["_id"], jsonCommit["commit"], jsonCommit["project"]])
		return commits

	def insertCommit(self, commitHash, commitAuthor, commitDate, commitMessage, project):
		commit = {"commit": commitHash, "commiter": commitAuthor, "commitdate": commitDate, "message": commitMessage, "status": 1, "project": project}
		self.db.commits.insert(commit)

	def setStatusWorking(self, commitId):
		self.db.commits.update({"_id": commitId}, {"$set": {"status": 3}})

	def setStatusFinished(self, commitId):
		self.db.commits.update({"_id": commitId}, {"$set": {"status": 4}})
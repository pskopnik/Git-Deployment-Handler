# -*- coding: utf-8 -*-

from gitdh.modules.module import Module
import gitdh.gitdhutils

class DatabaseLog(Module):
	def isEnabled(self, action):
		return (action == "postreceive")

	def preProcessing(self, commits):
		for commit in commits:
			if "DatabaseLog" in self.conf[commit.branch] and self.conf.getboolean(commit.branch, "DatabaseLog"):
				commit.status = "databaselog_queued"

	def processing(self, commits):
		commits = gitdhutils.filterOnStatusBase("databaselog", commits)
		gitdhutils.mInsertCommit(self.dbBe, commits)

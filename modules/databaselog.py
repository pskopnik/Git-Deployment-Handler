from modules.module import Module
import gprhutils

class DatabaseLog(Module):
	def isEnabled(self, action):
		return (action == "postreceive")

	def preProcessing(self, commits):
		for commit in commits:
			if "DatabaseLog" in self.conf[commit.branch] and self.conf.getboolean(commit.branch, "DatabaseLog"):
				commit.status = "databaselog_queued"

	def processing(self, commits):
		commits = gprhutils.filterOnStatusBase("databaselog", commits)
		gprhutils.mInsertCommit(self.dbCon, commits)

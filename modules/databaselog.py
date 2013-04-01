from modules.module import Module
import gprhutils

class DatabaseLog(Module):
	def isEnabled(self, action):
		return (action == "postreceive")

	def preProcessing(self, commmits):
		for commit in commits:
			if "DatabaseLog" in self.conf[branch] and self.conf.getboolean(branch, "DatabaseLog"):
				commit.status = "databaselog_queued"

	def processing(self, commits):
		commits = gprhutils.filterOnStatusBase("databaselog", commits)
		gprhutils.mInsertCommit(self.dbCon, commits)

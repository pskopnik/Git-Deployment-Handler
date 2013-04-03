from modules.module import Module
import gprhutils

class CronDeployment(Module):
	def isEnabled(self, action):
		return (action == "postreceive")

	def preProcessing(self, commits):
		for commit in commits:
			if "CronDeployment" in self.conf[commit.branch] and self.conf.getboolean(commit.branch, "CronDeployment"):
				commit.status = "crondepl_queued"
				commit.preventDepl = False

	def processing(self, commits):
		gprhutils.mInsertOnStatus("crondepl_queued", self.dbCon, commits)

from modules.module import Module
import gprhutils

class Approval(Module):
	def isEnabled(self, action):
		return (action == "postreceive")

	def preProcessing(self, commits):
		for commit in commits:
			if "Approval" in self.conf[branch] and self.conf.getboolean(branch, "Approval"):
				commit.status = "approval"

	def processing(self, commits):
		gprhutils.mInsertOnStatus("approval", self.dbCon, commits)

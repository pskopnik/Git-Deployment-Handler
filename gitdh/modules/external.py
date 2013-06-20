# -*- coding: utf-8 -*-

from gitdh.modules.module import Module
from gitdh.git import Git
from gitdh.gitdhutils import filterOnStatusBase, filterOnSource, getConfigBranchSections, mInsertCommit, generateRandomString
from tempfile import TemporaryDirectory
from subprocess import call, CalledProcessError
from syslog import syslog, LOG_ERR
import re, os, shutil, os.path

class External(Module):
	def __init__(self, config, args, dbBe):
		super().__init__(config, args, dbBe)
		self.tmpDirs = []

	def isEnabled(self, action):
		return (action == "cron" and "Database" in self.config)

	def source(self):
		returnCommits = []
		for configSection in getConfigBranchSections(self.config):
			if "External" in self.config[configSection] and self.config.getboolean(configSection, "External"):
				branch = configSection
				tmpDir = TemporaryDirectory()
				self.tmpDirs.append(tmpDir)
				source = self.config[configSection]["Source"]
				cloneSource = source

				with SSHEnvironment(self.config[configSection]) as sshCloneSource:
					if not sshCloneSource == None: cloneSource = sshCloneSource
					args = ('git', 'clone', '-q', '-b', branch, cloneSource, tmpDir.name)
					try:
						returncode = call(args, cwd=tmpDir.name, stdout=open('/dev/null'), stderr=open('/dev/null'))
					except CalledProcessError as err:
						syslog(LOG_ERR, "CalledProcessError for branch '{0}' '{1}'".format(branch, err))
						continue
					else:
						if returncode != 0:
							syslog(LOG_ERR, "Git return code after pulling is '{0}', branch '{1}'".format(returncode, branch))
							continue

				git = Git(repositoryDir=tmpDir.name)
				gitLog = git.getLog(branch=branch)
				dbLog = filterOnStatusBase("external", filterOnSource(source, self.dbBe.getAllCommits()))
				if len(dbLog) < 1 or gitLog[-1].hash != dbLog[-1].hash:
					if len(dbLog) >= 1: lastDbLog = dbLog[-1]
					reachedNewCommits = len(dbLog) < 1
					for gitLogCommit in gitLog:
						try:
							if reachedNewCommits:
								gitLogCommit.status = "external_queued"
								gitLogCommit.deploymentSource = tmpDir.name
								gitLogCommit.repository = source
								returnCommits.append(gitLogCommit)
							elif gitLogCommit.hash == lastDbLog.hash:
								reachedNewCommits = True
						except NameError:
							pass
		return returnCommits

	def processing(self, commits):
		mInsertCommit(self.dbBe, filterOnStatusBase('external', commits))

	def postProcessing(self, commits):
		for tmpDir in self.tmpDirs:
			tmpDir.cleanup()


class SSHEnvironment(object):
	gitSshUrlPattern = re.compile("^(ssh://)?(?P<user>\w+)@(?P<host>[^:/]+):?(?P<port>\d+)?(:|/)(?P<repositoryPath>.+)$")

	def __init__(self, configSectionObj):
		self.configSectionObj = configSectionObj

	def __enter__(self):
		matchObj = SSHEnvironment.gitSshUrlPattern.match(self.configSectionObj["Source"])

		if matchObj == None:
			self.isSshUrl = False
			return None

		self.isSshUrl = True
		self.sshConfigFileCopied = False
		sshUser = matchObj.group("user")
		sshHost = matchObj.group("host")
		sshPort = matchObj.group("port")
		sshRepositoryPath = matchObj.group("repositoryPath")
		if sshPort == None: sshPort = "22"
		tmpHostName = generateRandomString(20)
		sshConf = "\n\nHost {0}\n\tHostName {1}\n\tUser {2}\n\tPort {3}\n\tStrictHostKeyChecking no\n".format(tmpHostName, sshHost, sshUser, sshPort)
		if "IdentityFile" in self.configSectionObj: sshConf += "\tIdentityFile {0}\n".format(self.configSectionObj["IdentityFile"])
		cloneSource = "ssh://{0}/{1}".format(tmpHostName, sshRepositoryPath)
		sshConfigDirName = os.path.join(os.environ["HOME"], ".ssh")
		self.sshConfigFileName = os.path.join(os.environ["HOME"], ".ssh", "config")
		if not os.path.exists(sshConfigDirName): os.mkdir(sshConfigDirName, mode=0o700)
		if os.path.exists(self.sshConfigFileName):
			self.sshOrigConfigFileName = self.generateOrigConfigFileName(self.sshConfigFileName)
			shutil.copy(self.sshConfigFileName, self.sshOrigConfigFileName)
			self.sshConfigFileCopied = True
		with open(self.sshConfigFileName, "a") as sshConfigFileObj:
			os.chmod(self.sshConfigFileName, 0o600)
			sshConfigFileObj.write(sshConf)
		return cloneSource

	def __exit__(self, type, value, traceback):
		if self.isSshUrl:
			if self.sshConfigFileCopied:
				shutil.move(self.sshOrigConfigFileName, self.sshConfigFileName)
			else:
				os.unlink(self.sshConfigFileName)

	def generateOrigConfigFileName(self, configFilePath):
		origConfigFileName = configFilePath + ".orig"
		while os.path.exists(origConfigFileName):
			origConfigFileName += "_"
		fObj = open(origConfigFileName, "w")
		fObj.close()
		return origConfigFileName

# -*- coding: utf-8 -*-

from gitdh.modules import Module
from gitdh.git import Git
from gitdh.gitdhutils import filterOnStatusBase, filterOnSource, mInsertCommit, generateRandomString
from tempfile import TemporaryDirectory
from subprocess import check_call, check_output, CalledProcessError
from syslog import syslog, LOG_WARNING
import re, os, shutil

class External(Module):
	def __init__(self, config, args, dbBe):
		super().__init__(config, args, dbBe)
		self.tmpDirs = []

	def isEnabled(self, action):
		return action == 'cron' and not self.dbBe is None

	def source(self):
		returnCommits = []
		if not self.config.getboolean('Git', 'External', fallback=False):
			return returnCommits

		with open(os.devnull, 'w') as devNull:
			for confSect in self.config.branches.values():
				branch = confSect.name
				tmpDir = TemporaryDirectory()
				self.tmpDirs.append(tmpDir)
				source = self.config.repoPath
				cloneSource = source

				dbLog = filterOnStatusBase("external", filterOnSource(cloneSource, self.dbBe.getAllCommits()))
				dbLog = sorted(dbLog, key=lambda commit: commit.date)

				with SSHEnvironment(cloneSource, self.config) as sshCloneSource:
					if not sshCloneSource is None:
						cloneSource = sshCloneSource
					try:
						returnCommits += self._doMainClone(source, cloneSource, branch, tmpDir.name, dbLog, devNull)
					except CalledProcessError as err:
						syslog(LOG_WARNING, "CalledProcessError for branch '%s': '%s'"% (branch, err))

			return returnCommits

	def postProcess(self, commits):
		for tmpDir in self.tmpDirs:
			tmpDir.cleanup()

	def store(self, commits):
		mInsertCommit(self.dbBe, filterOnStatusBase('external', commits))

	def _doMainClone(self, source, cloneSource, branch, repo, dbLog, devNull):
		args = ('git', 'ls-remote', cloneSource, branch)
		output = check_output(args, cwd=repo, stderr=devNull)
		if len(output) == 0:
			syslog(LOG_WARNING, "No branch '%s' in '%s'" % (branch, cloneSource))
			return []

		if len(dbLog) == 0:
			args = ('git', 'clone', '-q', '-b', branch, cloneSource, repo)
			depth = None
		else:
			output = output.decode('utf-8')
			if output[:40] == dbLog[-1].hash:
				return []
			depth = 5
			args = ('git', 'clone', '-q', '--depth', str(depth), '-b', branch, cloneSource, repo)

		while True:
			check_call(args, cwd=repo, stdout=devNull, stderr=devNull)
			try:
				return self._catchUp(repo, branch, dbLog, source)
			except NewCommitsNotReachedError:
				try:
					depth += 10
					args = ('git', 'fetch', '--depth', str(depth))
				except TypeError:
					return self._catchUp(repo, branch, [], source)

	def _catchUp(self, repo, branch, dbLog, source):
		returnCommits = []
		git = Git(repo)
		gitLog = git.getLog(branch=branch)
		if len(dbLog) > 0:
			lastDbLog = dbLog[-1]
			reachedNewCommits = False
		else:
			reachedNewCommits = True
		for gitLogCommit in gitLog:
			if reachedNewCommits:
				gitLogCommit.status = 'external_queued'
				gitLogCommit.deploymentSource = repo
				gitLogCommit.repository = source
				returnCommits.append(gitLogCommit)
			elif gitLogCommit.hash == lastDbLog.hash:
				reachedNewCommits = True

		if not reachedNewCommits:
			raise NewCommitsNotReachedError()
		return returnCommits


class SSHEnvironment(object):
	gitSshUrlPattern = re.compile('^(ssh://)?(?P<user>\w+)@(?P<host>[^:/]+):?(?P<port>\d+)?(:|/)(?P<repositoryPath>.+)$')

	def __init__(self, source, config):
		self.source = source
		self.config = config

	def __enter__(self):
		matchObj = SSHEnvironment.gitSshUrlPattern.match(self.source)

		if matchObj is None:
			self.isSshUrl = False
			return None

		self.isSshUrl = True
		self.sshConfigFileCopied = False

		sshUser = matchObj.group('user')
		sshHost = matchObj.group('host')
		sshPort = matchObj.group('port')
		sshRepositoryPath = matchObj.group('repositoryPath')
		if sshPort is None:
			sshPort = '22'

		tmpHostName = generateRandomString(20)
		sshConf = "\n\nHost {0}\n\tHostName {1}\n\tUser {2}\n\tPort {3}\n\tStrictHostKeyChecking no\n".format(tmpHostName, sshHost, sshUser, sshPort)
		try:
			sshConf += "\tIdentityFile {0}\n".format(self.config['Git']['IdentityFile'])
		except KeyError:
			pass
		cloneSource = 'ssh://{0}/{1}'.format(tmpHostName, sshRepositoryPath)

		sshConfigDirName = os.path.join(os.environ['HOME'], '.ssh')
		self.sshConfigFileName = os.path.join(os.environ['HOME'], '.ssh', 'config')
		if not os.path.exists(sshConfigDirName):
			os.mkdir(sshConfigDirName, mode=0o700)
		if os.path.exists(self.sshConfigFileName):
			self.sshOrigConfigFileName = self.generateOrigConfigFileName(self.sshConfigFileName)
			shutil.copy(self.sshConfigFileName, self.sshOrigConfigFileName)
			self.sshConfigFileCopied = True

		with open(self.sshConfigFileName, 'a') as sshConfigFileObj:
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
		origConfigFileName = configFilePath + '.orig'
		while os.path.exists(origConfigFileName):
			origConfigFileName += '_'
		fObj = open(origConfigFileName, 'w')
		fObj.close()
		return origConfigFileName

class NewCommitsNotReachedError(Exception):
	pass

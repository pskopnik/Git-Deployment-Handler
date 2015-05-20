# -*- coding: utf-8 -*-

from gitdh.modules import Module
from gitdh.git import Git
from gitdh.gitdhutils import filterOnStatusBase, filterOnSource, mInsertCommit, generateRandomString
from tempfile import TemporaryDirectory
from subprocess import check_call, check_output, CalledProcessError
from syslog import syslog, LOG_WARNING
from distutils.version import LooseVersion
import re, os, shutil, time

try:
	from subprocess import DEVNULL
except ImportError:
	# < Python 3.3 compatibility
	from gitdh.gitdhutils import getDevNull
	DEVNULL = getDevNull()

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

		for confSect in self.config.branches.values():
			branch = confSect.name
			tmpDir = TemporaryDirectory()
			self.tmpDirs.append(tmpDir)
			source = self.config.repoPath
			cloneSource = source

			dbLog = filterOnStatusBase("external", filterOnSource(source, self.dbBe.getAllCommits()))
			dbLog = sorted(dbLog, key=lambda commit: commit.date)

			with SSHEnvironment(cloneSource, self.config) as sshCloneSource:
				if not sshCloneSource is None:
					cloneSource = sshCloneSource
				try:
					returnCommits += self._doClone(source, cloneSource, branch, tmpDir.name, dbLog)
				except CalledProcessError as err:
					syslog(LOG_WARNING, "CalledProcessError for branch '%s' in '%s': '%s'"% (branch, source, err))

			return returnCommits

	def postProcess(self, commits):
		for tmpDir in self.tmpDirs:
			tmpDir.cleanup()

	def store(self, commits):
		mInsertCommit(self.dbBe, filterOnStatusBase('external', commits))

	def _doClone(self, source, cloneSource, branch, repo, dbLog):
		args = ('git', 'ls-remote', cloneSource, branch)
		output = check_output(args, cwd=repo, stderr=DEVNULL)
		if len(output) == 0:
			syslog(LOG_WARNING, "No branch '%s' in '%s'" % (branch, source))
			return []

		# For Git versions <1.9 clone of a shallow repository will fail, so
		# check the git version and clone the whole repository if it is <1.9
		gitVersOut = check_output(('git', '--version'), stderr=DEVNULL).decode('utf-8')
		if gitVersOut[:12] == "git version ":
			gitVers = LooseVersion(gitVersOut[12:])
		else:
			gitVers = LooseVersion("0")
		if len(dbLog) == 0 or gitVers < LooseVersion("1.9"):
			depth = None
			args = ('git', 'clone', '-q', '-b', branch, cloneSource, repo)
		else:
			output = output.decode('utf-8')
			if output[:40] == dbLog[-1].hash:
				return []
			depth = 5
			args = ('git', 'clone', '-q', '--depth', str(depth), '-b', branch, cloneSource, repo)

		lastGitLogLen = 0
		while True:
			check_call(args, cwd=repo, stdout=DEVNULL, stderr=DEVNULL)
			try:
				return self._catchUp(repo, branch, dbLog, source, lastGitLogLen)
			except NewCommitsNotReachedError as e:
				try:
					lastGitLogLen = e.gitLogLen
					depth += 10
					args = ('git', 'fetch', '--depth', str(depth))
				except TypeError:
					return self._catchUp(repo, branch, [], source, lastGitLogLen)

	def _catchUp(self, repo, branch, dbLog, source, lastGitLogLen):
		returnCommits = []
		git = Git(repo)
		gitLog = git.getLog(branch=branch)
		if len(dbLog) > 0 and len(gitLog) > lastGitLogLen:
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
			raise NewCommitsNotReachedError(len(gitLog))
		return returnCommits


class SSHEnvironment(object):
	gitSshUrlPattern = re.compile('^(ssh://)?(?P<user>\w+)@(?P<host>[^:/]+)(:(?P<port>\d+))?(:|/)(?P<repositoryPath>.+)$')

	def __init__(self, source, config):
		self.source = source
		self.config = config

	def __enter__(self):
		matchObj = SSHEnvironment.gitSshUrlPattern.match(self.source)

		if matchObj is None:
			self.isSshUrl = False
			return None

		self.isSshUrl = True

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

		sshConfigDirPath = os.path.join(os.path.expanduser('~'), '.ssh')
		sshConfigFilePath = os.path.join(sshConfigDirPath, 'config')
		if not os.path.exists(sshConfigDirPath):
			try:
				os.mkdir(sshConfigDirPath, mode=0o700)
			except TypeError:
				# < Python 3.3 compatibility
				os.mkdir(sshConfigDirPath, 0o700)
		if not os.path.exists(sshConfigFilePath):
			with open(sshConfigFilePath, 'w'):
				pass
			os.chmod(sshConfigFilePath, 0o600)

		self.sshOrigConfigFile = TmpOrigFile(sshConfigFilePath, postfix="gitdh")
		self.sshOrigConfigFile.create()

		with open(sshConfigFilePath, 'a') as sshConfigFileObj:
			sshConfigFileObj.write(sshConf)

		return cloneSource

	def __exit__(self, type, value, traceback):
		if self.isSshUrl:
			self.sshOrigConfigFile.remove()

class TmpOrigFile(object):
	def __init__(self, path, postfix="orig"):
		self.path = path
		self.dir = os.path.dirname(path)
		self.postfix = postfix
		self.base = os.path.basename(path) + "." + postfix + "."
		self.lockPath = self.path + "." + postfix + ".lock"
		self.curNum = None
		self.tmpFilePath = None

	def create(self):
		with DirLock(self.lockPath, 0.01, 1):
			confFileNums = self._getFileNums()
			self.curNum = 1
			if len(confFileNums) != 0:
				self.curNum = confFileNums[-1] + 1
			self.tmpFilePath = os.path.join(self.dir, self.base + str(self.curNum))
			shutil.copy(self.path, self.tmpFilePath)

	def remove(self):
		if self.tmpFilePath is None:
			return
		with DirLock(self.lockPath, 0.01, 1):
			confFileNums = self._getFileNums()
			nextFile = self.path
			if confFileNums[-1] != self.curNum:
				nextFile = os.path.join(self.dir, self.base \
					+ str(confFileNums[confFileNums.index(self.curNum) + 1]))
			shutil.move(self.tmpFilePath, nextFile)
			self.tmpFilePath = None
			self.curNum = None

	def __del__(self):
		if not self.tmpFilePath is None:
			self.remove()

	def __enter__(self):
		self.create()

	def __exit__(self, type, value, traceback):
		self.remove()

	def _getFileNums(self):
		base = self.base
		confFileNums = []

		for f in os.listdir(self.dir):
			if f[:len(base)] == base:
				try:
					confFileNums.append(int(f[len(base):]))
				except ValueError:
					pass
		confFileNums.sort()
		return confFileNums

class DirLockTimeoutException(Exception):
	pass

class FileExistsError(Exception):
	def __init__(self, path):
		self.path = path

class DirLock(object):
	def __init__(self, lockDirPath, waitInterval, waitTimeout):
		self.lockDirPath = lockDirPath
		self.waitInterval = waitInterval
		self.waitTimeout = waitTimeout

	def __enter__(self):
		startedAt = time.time()
		while True:
			try:
				if os.path.exists(self.lockDirPath):
					raise FileExistsError(self.lockDirPath)
				os.mkdir(self.lockDirPath)
				break
			except FileExistsError:
				if self.waitTimeout == 0 or time.time() - startedAt < self.waitTimeout:
					time.sleep(self.waitInterval)
				else:
					raise DirLockTimeoutException()

	def __exit__(self, type, value, traceback):
		os.rmdir(self.lockDirPath)
		return False

class NewCommitsNotReachedError(Exception):
	def __init__(self, gitLogLen):
		self.gitLogLen = gitLogLen

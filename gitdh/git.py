# -*- coding: utf-8 -*-

import shlex
from subprocess import check_output, CalledProcessError
import os, re

class Git(object):
	branchPattern = re.compile(r"[\*\s]\s(\S+)$", re.MULTILINE)

	def __init__(self, repositoryPath):
		self.repositoryPath = repositoryPath
		try:
			self._executeGitCommand("rev-parse", suppressStderr=True)
		except CalledProcessError:
			raise GitException("The directory '%s' is not a Git repository" % (repositoryPath))

	def getRepoInfo(self):
		repoInfo = {}
		repoInfo["repositoryPath"] = self.repositoryPath
		repoInfo["repositoryName"] = os.path.basename(self.repositoryPath).split('.git')[0]
		repoInfo["repositoriesDirPath"] = os.path.abspath(os.path.join(self.repositoryPath, os.pardir))
		return repoInfo

	def _executeGitCommand(self, gitCommand, options='', repositoryPath=None, suppressStderr=False):
		if repositoryPath is None:
			repositoryPath = self.repositoryPath
		cmd = 'git ' + gitCommand + ' ' + options
		args = shlex.split(cmd)
		if suppressStderr:
			with open(os.devnull, mode='w') as fd:
				cmdOutput = check_output(args, cwd=repositoryPath, universal_newlines=True, stderr=fd)
			return cmdOutput
		else:
			return check_output(args, cwd=repositoryPath, universal_newlines=True)

	def getLog(self, since=None, until=None, branch=None):
		time = ""
		commits = []
		if since != None or until != None:
			if since is None:
				since = ""
			if until is None:
				until = ""
			time = since + ".." + until

		try:
			log = self._executeGitCommand('log', '--format="#|-#commit %H|tree %T|author %cn <%ce>|date %ct|message %B" {0} ./'.format(time))
		except CalledProcessError:
			raise GitException('Invalid revision range')
		matches = re.findall('^#\|\-#commit (.{40})\|tree (.{40})\|author ([^\|]+)\|date (\d+)\|message ([^(#\|\-#)]*)', log, re.MULTILINE)
		for match in matches:
			commits.append(GitCommit(match[0], match[2], int(match[3]), match[4].strip(), branch, self.repositoryPath))
		commits.reverse()
		return commits

	def getFileContent(self, filePath, branch="master"):
		try:
			fileContent = self._executeGitCommand('cat-file', ' -p {0}:{1}'.format(branch, filePath))
		except CalledProcessError as error:
			if error.returncode == 128:
				raise GitException("The file '%s' does not exist in the branch '%s'" % (filePath, branch))
			else:
				raise GitException("Unknown error")
		return fileContent

	def getFiles(self, directory="", branch="master"):
		files = []
		try:
			fileString = self._executeGitCommand('ls-tree', '{0}:{1} ./'.format(branch, directory))
		except CalledProcessError as error:
			if error.returncode == 128:
				raise GitException("The directory '%s' does not exist in the branch '%s'" % (directory, branch))
			else:
				raise GitException("Unknown error")
		fileLines = fileString.splitlines()
		for fileLine in fileLines:
			fileLineHalfs = fileLine.split("\t")
			fileName = fileLineHalfs[1]
			fileType = fileLineHalfs[0].split(" ")[1]
			files.append(GitTreeNode(fileType, os.path.join(directory, fileName), branch, gitCon=self))
		return files

	def getBranches(self):
		branchOutput = self._executeGitCommand("branch")
		return Git.branchPattern.findall(branchOutput)


class GitTreeNode(object):
	def __init__(self, type, path, branch, gitCon=None, repository=None):
		self.type = type
		self.path = path
		self.branch = branch
		if gitCon is None:
			if repository is None:
				raise GitException("No repository or gitCon given")
			gitCon = Git(repository)
		self.gitCon = gitCon

	def getFileName(self):
		fileName = os.path.basename(self.path)
		if self.type == 2:
			fileName = fileName + "/"
		return fileName

	def getFilePath(self):
		filePath = self.path
		if self.type == 2:
			filePath = filePath + "/"
		return filePath

	def getFileType(self):
		return self.type

	def getFileContent(self):
		if not self.type == 'blob':
			raise GitException("Can only get the content of a 'blob' object, '%s' object given" % self.type)
		return self.gitCon.getFileContent(self.path, self.branch)

	def getChildFiles(self):
		if not self.type ==  'tree':
			raise GitException("Can only get child files from a 'tree' object, '%s' object given" % self.type)
		return self.gitCon.getFiles(self.path + "/", self.branch)


class GitCommit(object):
	def __init__(self, hash, author, date, message, branch, repository, id=None, status=None, approver=None, approverDate=None):
		self.id = id
		self.hash = hash
		self.author = author
		self.date = date
		self.message = message
		self.branch = branch
		self.repository = repository
		self.status = status
		self.approver = approver
		self.approverDate = approverDate

	def getConfSection(self, config):
		try:
			return config.branches[self.branch]
		except KeyError:
			return None


class GitException(Exception):
	pass

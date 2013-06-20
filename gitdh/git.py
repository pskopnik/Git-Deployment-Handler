# -*- coding: utf-8 -*-

import shlex
from subprocess import check_output, CalledProcessError
import os.path, re

class Git(object):
	def __init__(self, repositoryName=None, repositoriesDir='/srv/gitosis/repositories', repositoryDir=None):
		if repositoryName != None:
			self.repositoryName = repositoryName
			self.repositoriesDir = repositoriesDir
			repositoryDir = os.path.join(self.repositoriesDir, repositoryName + '.git')
		elif repositoryDir != None:
			self.repositoryName = os.path.basename(repositoryDir).split('.git')[0]
			self.repositoriesDir = os.path.abspath(os.path.join(repositoryDir, os.pardir))
		else:
			raise GitException("Git.__init__() either needs repositoryName and repositoriesDir or repositoryDir")

		if os.path.isdir(repositoryDir) != True:
			raise GitException("Repository directory does not exist")
		self.repositoryDir = repositoryDir

	def _executeGitCommand(self, gitCommand, options, repositoryDir=None):
		if repositoryDir == None:
			repositoryDir = self.repositoryDir
		cmd = 'git ' + gitCommand + ' ' + options
		args = shlex.split(cmd)
		return check_output(args, cwd=repositoryDir, universal_newlines=True)

	def getLog(self, since=None, until=None, branch=None):
		time = ""
		commits = []
		if since != None or until != None:
			if since == None:
				since = ""
			if until == None:
				until = ""
			time = since + ".." + until
		
		log = self._executeGitCommand('log', '--format="#|-#commit %H|tree %T|author %cn <%ce>|date %ct|message %B" {0} ./'.format(time))
		matches = re.findall('^#\|\-#commit (.{40})\|tree (.{40})\|author ([^\|]+)\|date (\d+)\|message ([^(#\|\-#)]*)', log, re.MULTILINE)
		for match in matches:
			commits.append(GitCommit(match[0], match[2], int(match[3]), match[4].strip(), branch, self.repositoryDir))
		commits.reverse()
		return commits

	def getFileContent(self, file, branch="master"):
		try:
			fileContent = self._executeGitCommand('cat-file', ' -p {0}:{1}'.format(branch, file))
		except CalledProcessError as error:
			if error.returncode == 128:
				raise GitException("The file does not exists in the branch")
			else:
				raise GitException("Unknown error")
		return fileContent

	def getFiles(self, directory="", branch="master"):
		files = []
		try:
			fileString = self._executeGitCommand('ls-tree', '{0}:{1} ./'.format(branch, directory))
		except CalledProcessError as error:
			if error.returncode == 128:
				raise GitException("The file does not exists in the branch")
			else:
				raise GitException("Unknown error")
		fileLines = fileString.splitlines()
		for fileLine in fileLines:
			fileLineHalfs = fileLine.split("\t")
			fileName = fileLineHalfs[1]
			fileType = fileLineHalfs[0].split(" ")[1]
			if fileType == "blob":
				fileType = 1
			elif fileType == "tree":
				fileType = 2
			files.append(GitTreeNode(fileType, os.path.join(directory, fileName), branch, gitCon=self))
		return files

	def getBranches(self):
		branchOutput = self._executeGitCommand("branch", "")
		branchPattern = re.compile(r"[\*\s]\s(\S+)$", re.MULTILINE)
		return branchPattern.findall(branchOutput)




class GitTreeNode(object):
	def __init__(self, type, path, branch, gitCon=None, repository=None):
		self.type = type
		self.path = path
		self.branch = branch
		if gitCon == None:
			if repository == None:
				raise GitException("No repository or gitCon given")
			gitCon = Git(repositoryDir=repository)
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
		if self.type != 1:
			raise GitException("Cannot get the content of a directory")
		return self.gitCon.getFileContent(self.path, self.branch)

	def getChildFiles(self):
		if self.type != 2:
			raise GitException("Cannot get child files from a file")
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
			return config[self.branch]
		except KeyError:
			return None

class GitException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

# -*- coding: utf-8 -*-

import os, string, random
from subprocess import call, CalledProcessError
from syslog import syslog, LOG_ERR

def deleteDirContent(dir):
	for file in os.listdir(dir):
		file_path = os.path.join(dir, file)
		try:
			if os.path.isdir(file_path):
				deleteDir(file_path)
			else:
				os.unlink(file_path)
		except Exception as e:
			print(e)

def deleteDir(dir):
	for file in os.listdir(dir):
		file_path = os.path.join(dir, file)
		try:
			if os.path.isdir(file_path):
				deleteDir(file_path)
			else:
				os.unlink(file_path)
		except Exception as e:
			print(e)
	try:
		os.rmdir(dir)
	except Exception as e:
		print(e)

def deleteUpdateRepo(path, sourceRepository, branch, commit=None, rmIntGitFiles=True):
	path = path.rstrip("/ ")
	if not os.path.exists(path):
		os.mkdir(path)
	else:
		if not os.path.isdir(path):
			raise Exception("'{0}' is not a directory".format(path))
		deleteDirContent(path)
	
	if os.path.exists(sourceRepository):
		args = ('git', 'clone', '-q', '-l', '-s', '-b', branch, 'file://' + sourceRepository, os.path.basename(path))
	else:
		args = ('git', 'clone', '-q', '-b', branch, sourceRepository, os.path.basename(path))

	returncode = call(args, cwd=os.path.dirname(path), stdout=open('/dev/null'), stderr=open('/dev/null'))
	if returncode != 0:
		syslog(LOG_ERR, "Git return code after pulling is '{0}', branch '{1}'".format(returncode, branch))
	if not commit == None:
		args = ('git', 'checkout', commit)
		returncode = call(args, cwd=path, stdout=open('/dev/null'), stderr=open('/dev/null'))
		if returncode != 0:
			syslog(LOG_ERR, "Git return code after checkout of the commit '{0}' is '{1}', branch '{2}'".format(commit, returncode, branch))
		args = ('git', 'reset', '--hard', '-q')
		returncode = call(args, cwd=path, stdout=open('/dev/null'), stderr=open('/dev/null'))
		if returncode != 0:
			syslog(LOG_ERR, "Git return code after resetting to head is '{0}', branch '{1}'".format(returncode, branch))
	if rmIntGitFiles:
		deleteDir(os.path.join(path, '.git'))
		if os.path.isfile(os.path.join(path, '.gitignore')):
			os.unlink(os.path.join(path, '.gitignore'))


def mInsertCommit(dbBe, commits):
	for commit in commits:
		insertCommit(dbBe, commit)


def insertCommit(dbBe, commit):
	if not hasattr(commit, "id") or commit.id == None:
		dbBe.insertCommit(commit)


def mInsertOnStatus(status, dbBe, commits):
	for commit in commits:
		insertOnStatus(status, dbBe, commit)


def insertOnStatus(status, dbBe, commit):
		if commit.status == status:
			insertCommit(dbBe, commit)


def filterOnStatus(status, commits):
	return [commit for commit in commits if commit.status == status]

def filterOnStatusBase(statusBase, commits):
	return [commit for commit in commits if '_' in commit.status and commit.status[:commit.status.rfind('_')] == statusBase]

def filterOnStatusExt(statusExt, commits):
	return [commit for commit in commits if '_' in commit.status and commit.status[commit.status.rfind('_') + 1:] == statusExt]

def filterOnSource(source, commits):
	return [commit for commit in commits if commit.repository == source]


def getExePath(file):
	"""Similar to the UNIX command `which`, but returns the whole file path, not just the directory."""
	for directory in os.environ["PATH"].split(':'):
		filePath = os.path.join(directory, file)
		if os.path.exists(filePath) and os.path.isfile(filePath):
			return filePath
	raise Exception("File not found")

def getConfigBranchSections(config):
	returnSections = []
	f = lambda section: not section in ["Git", "DEFAULT", "Database"] and not ("-" in section and section[section.rfind('-') + 1:] == "command")
	for section in filter(f, config):
		returnSections.append(section)
	return returnSections

def generateRandomString(length, characters=string.ascii_lowercase):
	return ''.join(random.choice(characters) for i in range(length))

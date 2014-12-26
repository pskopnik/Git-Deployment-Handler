# -*- coding: utf-8 -*-

import os, string, random

_devNull = None

def getDevNull():
	global _devNull
	if _devNull is None:
		_devNull = open(os.devnull, 'wb')
	return _devNull

def deleteDirContent(dir):
	for file in os.listdir(dir):
		file_path = os.path.join(dir, file)
		if os.path.isdir(file_path):
			deleteDir(file_path)
		else:
			os.unlink(file_path)

def deleteDir(dir):
	deleteDirContent(dir)
	os.rmdir(dir)

def mInsertCommit(dbBe, commits):
	for commit in commits:
		insertCommit(dbBe, commit)


def insertCommit(dbBe, commit):
	if not hasattr(commit, "id") or commit.id is None:
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
	"""Similar to the UNIX command `which`"""
	for directory in os.environ["PATH"].split(':'):
		filePath = os.path.join(directory, file)
		if os.path.exists(filePath) and os.path.isfile(filePath):
			return filePath
	raise Exception("File not found")

def generateRandomString(length, characters=string.ascii_lowercase):
	return ''.join(random.choice(characters) for i in range(length))

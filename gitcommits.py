#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from subprocess import call, CalledProcessError
from syslog import syslog, LOG_ERR
from configparser import ConfigParser
import shlex
import re

def deleteDirContent(dir):
    for the_file in os.listdir(dir):
        file_path = os.path.join(dir, the_file)
        try:
            if os.path.isdir(file_path):
                deleteDir(file_path)
            else:
                os.unlink(file_path)
        except Exception as e:
            print(e)

def deleteDir(dir):
    for the_file in os.listdir(dir):
        file_path = os.path.join(dir, the_file)
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

def deleteUpdateRepo(path, repositoryname, branch, commit=None):
    path = path.rstrip("/ ")
    deleteDirContent(path)
    args = ('git', 'clone', '-q', '-l', '-s', '-b', branch, 'file:///srv/gitosis/repositories/' + repositoryname + '.git', os.path.basename(path))
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


def getAllFiles(path):
    allFiles = list()
    pathcontent = os.walk(path)
    for root, dirs, files in pathcontent:
        for file in files:
            allFiles.append(os.path.join(root, file))
    return allFiles

def filterFiles(files, regexp):
    filteredFiles = list()
    regexp = re.compile(regexp)
    for file in files:
        if regexp.match(file):
            filteredFiles.append(file)
    return filteredFiles

def executePathCommand(command, path):
    command = command.replace("%f", '"' + path + '"')
    args = shlex.split(command)
    return call(args, stdout=open('/dev/null'), stderr=open('/dev/null'))

def runPostprocessing(path, type, config, sectionname):
    if config.has_option(sectionname, "Postprocessing-" + type):
        postprocCommandString = config.get(sectionname, "Postprocessing-" + type)
        postprocCommands = postprocCommandString .split(" ")
        for postprocCommand in postprocCommands:
            if not config.has_section(postprocCommand + "-command"):
                syslog(LOG_ERR, "Command '{0}' doesn't exist".format(postprocCommand))
            else:
                configMode = config.get(postprocCommand + "-command", "Mode")
                if configMode == "once":
                    executePathCommand(config.get(postprocCommand + "-command", "Command"), path)
                elif configMode == "perfile":
                    files = getAllFiles(path)
                    if config.has_option(postprocCommand + "-command", "RegExp"):
                        files = filterFiles(files, config.get(postprocCommand + "-command", "RegExp"))
                    for file in files:
                        executePathCommand(config.get(postprocCommand + "-command", "Command"), file)

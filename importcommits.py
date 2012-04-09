#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql, git, sys, os
from syslog import syslog, LOG_ERR, LOG_INFO
from configparser import ConfigParser
from gitcommits import deleteDirContent, deleteDir, deleteUpdateRepo,  runPostprocessing

config = ConfigParser()
config.read("config.ini")

project = sys.argv[1]
firstcommit = sys.argv[2]
lastcommit = sys.argv[3]
ref = sys.argv[4]

if not config.has_section(project):
    syslog(LOG_ERR, "No section in config for project '{0}'".format(project))
    exit(1)

if ref.find("refs/heads/") == 0:
    branch = ref[11:]
else:
    syslog(LOG_ERR,  "Branch name could not be parsed in '{0}'".format(ref))
    exit(1)

if branch == project + "-stable":
    syslog(LOG_INFO, "Inserting in the database for the stable website '{0}'".format(project))
    conn = pymysql.connect(host=config.get("DataBase", "Host"), port=config.getint("DataBase", "Port"), user=config.get("DataBase", "User"), passwd=config.get("DataBase", "Password"), db=config.get("DataBase", "Database"))
    cur = conn.cursor()
    
    gC = git.Git(config.get(project, "Repositoryname"))
    commits = gC.getLog(firstcommit, lastcommit)
    for commit in commits:
        commitMessage = commit.getMessage()
        if len(commitMessage) > 300:
            commitMessage = commitMessage[:297] + "..."
        
        params = (commit.getHash(), commit.getAuthor() , commit.getDate(), commitMessage,  1,  project)
        cur.execute("INSERT INTO `commits` (`commit`, `commiter`, `commitdate`, `message`, `status`, `project`) VALUES (%s, %s, %s, %s, %s, %s)",  params)
    
    cur.close()
    conn.close()
elif branch == project+ "-dev":
    syslog(LOG_INFO, "Pulling git for dev website '{0}'".format(project))
    deleteUpdateRepo(config.get(project, "DevPath"), config.get(project, "Repositoryname"), project + "-dev")
    runPostprocessing(config.get(project, "DevPath"), "dev", config, project)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql, git, sys, os
from syslog import syslog, LOG_ERR, LOG_INFO
from configparser import ConfigParser
from gitcommits import deleteDirContent, deleteDir, deleteUpdateRepo,  runPostprocessing

config = ConfigParser()
config.read("config.ini")

conn = pymysql.connect(host=config.get("DataBase", "Host"), port=config.getint("DataBase", "Port"), user=config.get("DataBase", "User"), passwd=config.get("DataBase", "Password"), db=config.get("DataBase", "Database"))
cur = conn.cursor()

cur.execute("SELECT `id`, `commit`, `project` FROM `commits` WHERE status='2'")
commits = cur.fetchall()
for commit in commits:
    cur.execute("UPDATE `commits` SET `status`='3' WHERE `id`=%s",  commit[0])
    if not config.has_section(commit[2]):
        syslog(LOG_ERR, "No section in the config for project '{0}' fetched with id '{1}'".format(commit[2],  commit[0]))
    else:
        path = config.get(commit[2], "StablePath")
        branch = commit[2] + "-stable"
        repositoryname = config.get(commit[2], "Repositoryname")
        syslog(LOG_INFO, "Pulling git for stable website '{0}'".format(commit[2]))
        deleteUpdateRepo(path,  repositoryname,  branch,  commit=commit[1])
        runPostprocessing(path, "stable", config, commit[2])
        cur.execute("UPDATE `commits` SET `status`='4' WHERE `id`=%s",  commit[0])

cur.close()
conn.close()

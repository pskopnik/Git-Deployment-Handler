#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, databaseconnection
from syslog import syslog, LOG_ERR, LOG_INFO
from configparser import ConfigParser
from gitcommits import deleteUpdateRepo, runPostprocessing, getAndInsertCommits

configFile = "config.ini"
if len(sys.argv) > 4:
    configFile = sys.argv[4]

firstcommit = sys.argv[1]
lastcommit = sys.argv[2]
ref = sys.argv[3]

config = ConfigParser()
config.read(configFile)

if ref.find("refs/heads/") == 0:
    branch = ref[11:]
else:
    syslog(LOG_ERR,  "Branch name could not be parsed in '{0}'".format(ref))
    exit(1)

if not config.has_section(branch):
    syslog(LOG_ERR, "No section in config for branch '{0}'".format(branch))
    exit(1)


if config.has_option(branch, "Approval") and config.getboolean(branch, "Approval"):
    syslog(LOG_INFO, "Inserting into the database (approval) for '{0}'".format(branch))
    dbCon = databaseconnection.DatabaseConnection.getDatabaseConnection(config=config)
    getAndInsertCommits(config, branch, firstcommit, lastcommit, dbCon)

elif config.has_option(branch, "DatabaseOnly") and config.getboolean(branch, "DatabaseOnly"):
    syslog(LOG_INFO, "Inserting into the database (pulling) for '{0}'".format(branch))
    dbCon = databaseconnection.DatabaseConnection.getDatabaseConnection(config=config)
    getAndInsertCommits(config, branch, firstcommit, lastcommit, dbCon, 5)

else:
    syslog(LOG_INFO, "Pulling git for '{0}'".format(branch))
    deleteUpdateRepo(config.get(branch, "Path"), config.get(branch, "Repositoryname"), branch, config.get("Git", "RepositoriesDir"))
    runPostprocessing(config.get(branch, "Path"), config, branch)
    if config.has_option(branch, "DatabaseLog") and config.getboolean(branch, "DatabaseLog"):
        syslog(LOG_INFO, "Inserting into the database (logging) for '{0}'".format(branch))
        dbCon = databaseconnection.DatabaseConnection.getDatabaseConnection(config=config)
        getAndInsertCommits(config, branch, firstcommit, lastcommit, dbCon, 8)
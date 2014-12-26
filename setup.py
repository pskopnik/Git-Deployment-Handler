#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
import sys

with open('README.rst') as file:
	long_description = file.read()

extras = {}
if sys.version_info < (3,3):
	extras['tests_require'] = ['mock']

setup(
		name = 'gitdh',
		version = '0.7.1',
		description = 'A python tool to deploy git commits using post-receive hooks and cron',
		long_description = long_description,
		author = 'Seoester',
		author_email = 'seoester@googlemail.com',
		license = 'MIT',
		url = 'https://github.com/seoester/Git-Deployment-Handler',
		provides = ['argh'],
		packages = ['gitdh', 'gitdh.modules'],
		install_requires = [
			"argh>=0.25"
		],
		entry_points = {
			'console_scripts': [
				'git-dh=gitdh.cli:main'
			]
		},
		extras_require = {
			'mongodb': ['pymongo'],
			'mysql': ['pymysql']
		},
		test_suite = "gitdh.tests",
		keywords = "git deploy deployment commit database remote approval cron post-receive hook",
		classifiers = [
			'Development Status :: 4 - Beta',
			'License :: OSI Approved :: MIT License',
			'Operating System :: POSIX :: Linux',
			'Programming Language :: Python :: 3',
			'Programming Language :: Python :: 3.2',
			'Programming Language :: Python :: 3.3',
			'Programming Language :: Python :: 3.4',
			'Topic :: Software Development :: Version Control',
		],
		**extras
	)

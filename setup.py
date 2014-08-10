#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as file:
	long_description = file.read()

setup(
		name='gitdh',
		version='0.7.dev3',
		description='A python tool to deploy git commits using post-receive hooks and cron',
		long_description=long_description,
		author='Seoester',
		author_email='seoester@googlemail.com',
		license='MIT',
		url='https://github.com/seoester/Git-Deployment-Handler',
		packages=['gitdh', 'gitdh.modules'],
		install_requires=[
			"argh>=0.25"
		],
		entry_points={
			'console_scripts': [
				'git-dh=gitdh.cli:main'
			]
		},
		extras_require={
			'mongodb': ['pymongo'],
			'mysql': ['pymysql']
		},
		classifiers=[
			'Development Status :: 4 - Beta',
			'License :: OSI Approved :: MIT License',
			'Operating System :: POSIX :: Linux',
			'Programming Language :: Python :: 3',
			'Programming Language :: Python :: 3.2',
			'Programming Language :: Python :: 3.3',
			'Programming Language :: Python :: 3.4',
			'Topic :: Software Development :: Version Control',
		],
	)

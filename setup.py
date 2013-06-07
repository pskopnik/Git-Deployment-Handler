#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

with open('README.rst') as file:
    long_description = file.read()

setup(
		name='gitdh',
		version='0.5',
		description='Git Deployment Handler using post-receive hooks, supports approval and logging of commits',
		long_description=long_description,
		author='Seoester',
		author_email='seoester@googlemail.com',
		license='MIT',
		url='https://github.com/seoester/Git-Deployment-Handler',
		packages=['gitdh', 'gitdh.modules'],
		scripts=['git-dh', 'git-dh-pr'],
		classifiers=[
			'Development Status :: 4 - Beta',
			'License :: OSI Approved :: MIT License',
			'Operating System :: POSIX :: Linux',
			'Programming Language :: Python :: 3.2',
			'Topic :: Software Development :: Version Control',
		],
	 )

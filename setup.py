#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
		name='gitdh',
		version='0.5',
		description='Git Deployment Handler',
		author='Seoester',
		author_email='seoester@googlemail.com',
		url='https://github.com/seoester/Git-Deployment-Handler',
		package_dir={'gitdh': 'src', 'gitdh.modules': 'src/modules'},
		packages=['gitdh', 'gitdh.modules'],
		scripts=['git-dh', 'git-dh-pr'],
	 )

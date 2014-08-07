import unittest, tempfile, os.path, re
from gitdh.config import Config, ConfigBranches
from gitdh.git import Git
from configparser import SectionProxy
from subprocess import check_output

# unittest.mock is available in python >= 3.3
# A backport exists: 'mock' on PyPi
try:
	import unittest.mock as mock
except ImportError:
	import mock

class GitdhConfigTestCase(unittest.TestCase):

	def setUp(self):
		self.cStr = """
[Git]
RepositoryPath = /var/lib/gitolite/repositories/test.git

[Database]
Engine = sqlite
DatabaseFile = /var/lib/gitolite/data.sqlite
Table = commits

[master]
Path=/home/www/production

[development]
Path=/home/www/development

[crunch-command]
Mode = perfile
RegExp = \.php$
Command = eff_php_crunch ${f}
"""

	@mock.patch('gitdh.module.ModuleLoader.getConfRegEx', new=mock.MagicMock(return_value=re.compile('^(.*\\-command|Git|DEFAULT|Database)$')))
	def test_branches(self):
		c = Config()
		c.read_string(self.cStr)

		self.assertTrue(isinstance(c.branches, ConfigBranches))

		self.assertEqual(len(c.branches), 2)

		self.assertNotIn('feature-xyz', c.branches)
		self.assertNotIn('Git', c.branches)
		self.assertNotIn('Database', c.branches)
		self.assertNotIn('DEFAULT', c.branches)
		self.assertNotIn('crunch-command', c.branches)
		self.assertIn('development', c.branches)
		self.assertIn('master', c.branches)

		self.assertRaises(KeyError, lambda: c.branches['feature-xyz'])
		self.assertRaises(KeyError, lambda: c.branches['Git'])
		self.assertRaises(KeyError, lambda: c.branches['Database'])
		self.assertRaises(KeyError, lambda: c.branches['DEFAULT'])
		self.assertRaises(KeyError, lambda: c.branches['crunch-command'])

		self.assertSetEqual(set((i for i in c.branches)), set(('development', 'master')))

		self.assertIsInstance(c.branches['development'], SectionProxy)
		self.assertIn('Path', c.branches['development'])

		self.assertNotIn('External', c.branches['development'])
		c['development']['External'] = 'False'
		self.assertIn('External', c.branches['development'])

	def test_command(self):
		c = Config()
		c.read_string(self.cStr)

		self.assertTrue('crunch-command' in c)
		sct = c['crunch-command']
		self.assertIsInstance(sct, SectionProxy)
		self.assertEqual(sct['Mode'], 'perfile')
		self.assertEqual(sct['RegExp'], '\.php$')
		self.assertEqual(sct['Command'], 'eff_php_crunch ${f}')

	def test_file(self):
		f = tempfile.TemporaryFile(mode='w+')
		f.write(self.cStr)
		f.flush()
		f.seek(0)
		c = Config.fromFile(f)

		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, '/var/lib/gitolite/repositories/test.git')

		f.close()

	def test_filePath(self):
		f = tempfile.NamedTemporaryFile()
		f.write(self.cStr.encode())
		f.flush()
		c = Config.fromFilePath(f.name)

		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, '/var/lib/gitolite/repositories/test.git')

		c = Config.fromPath(f.name)

		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, '/var/lib/gitolite/repositories/test.git')

		f.close()

	def test_gitRepo(self):
		path = "/home/git/repositories/test.git"

		isdir = mock.MagicMock(return_value=True)
		git = mock.MagicMock()
		git.return_value = git
		git.getBranches.return_value = ["master", "development", "gitdh"]
		confFile = mock.MagicMock()
		confFile.getFileName.return_value = "gitdh.conf"
		confFile.getFileContent.return_value = self.cStr
		git.getFiles.return_value = [confFile]

		with mock.patch('gitdh.git.Git', new=git):
			c = Config.fromGitRepo(path)
			self.assertTrue('Database' in c)
			self.assertTrue('master' in c)
			self.assertEqual(c['Database']['Engine'], 'sqlite')
			self.assertEqual(c.repoPath, path)

			git.assert_called_once_with(path)
			git.getBranches.assert_called_once_with()
			git.getFiles.assert_called_once_with(branch='gitdh')
			confFile.getFileName.assert_called_once_with()
			confFile.getFileContent.assert_called_once_with()

			git.reset_mock()
			confFile.reset_mock()

			with mock.patch('os.path.isdir', new=isdir):
				c = Config.fromPath(path)
				self.assertTrue('Database' in c)
				self.assertTrue('master' in c)
				self.assertEqual(c['Database']['Engine'], 'sqlite')
				self.assertEqual(c.repoPath, path)

				git.assert_called_once_with(path)
				git.getBranches.assert_called_once_with()
				git.getFiles.assert_called_once_with(branch='gitdh')
				confFile.getFileName.assert_called_once_with()
				confFile.getFileContent.assert_called_once_with()
				isdir.assert_called_once_with(path)

import unittest, tempfile, os.path
from gitdh.config import Config, ConfigBranches
from gitdh.git import Git
from configparser import SectionProxy
from subprocess import check_output

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
		d = tempfile.TemporaryDirectory()
		self._createGitRepo(d.name)

		c = Config.fromGitRepo(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, d.name)

		c = Config.fromPath(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, d.name)

		d.cleanup()

	def test_bareGitRepo(self):
		d = tempfile.TemporaryDirectory()
		self._createBareGitRepo(d.name)

		c = Config.fromGitRepo(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, d.name)

		c = Config.fromPath(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, d.name)

		d.cleanup()


	def _createGitRepo(self, path):
		check_output(('git', 'init'), cwd=path)

		gC = Git(path)
		gC._executeGitCommand('config', 'user.email test@localhost')
		gC._executeGitCommand('config', 'user.name Test')

		with open(os.path.join(path, 'README'), 'w') as f:
			f.write('On master')
		gC._executeGitCommand('add', '.')
		gC._executeGitCommand('commit', '-m "Initial Import"')
		gC._executeGitCommand('branch', 'development')
		gC._executeGitCommand('checkout', 'development', suppressStderr=True)
		with open(os.path.join(path, 'README'), 'w') as f:
			f.write('On development')
		gC._executeGitCommand('add', '.')
		gC._executeGitCommand('commit', '-m "Development branch added"')

		gC._executeGitCommand('branch', 'gitdh')
		gC._executeGitCommand('checkout', 'gitdh', suppressStderr=True)
		with open(os.path.join(path, 'gitdh.conf'), 'w') as f:
			f.write(self.cStr)
		gC._executeGitCommand('add', '.')
		gC._executeGitCommand('commit', '-m "Gitdh conf added"')

		return gC

	def _createBareGitRepo(self, path):
		d = tempfile.TemporaryDirectory()
		self._createGitRepo(d.name)

		check_output(('git', 'clone', '--bare', d.name, path))

		d.cleanup()



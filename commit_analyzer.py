import logging
import os


class IsBugCommitAnalyzer(object):

	def __init__(self, commit, repo):
		self._commit = commit
		self._repo = repo
		self.associated_tests_paths = None

	@property
	def commit(self):
		return self._commit

	def analyze(self):
		if len(self.commit.parents) == 0: return self
		self.associated_tests_paths = self.get_tests_paths_from_commit()
		return self

	def is_bug_commit(self):
		return self.associated_tests_paths != None and len(self.associated_tests_paths) > 0

	def get_test_paths(self):
		return self.associated_tests_paths

	def get_tests_paths_from_commit(self):
		ans = []
		diff_index = self.commit.parents[0].diff(self.commit)
		for file in self.commit.stats.files.keys():
			if self.is_test_file(file):
				try:
					diff = list(filter(lambda d: d.a_path == file, diff_index))[0]
				except IndexError as e:
					logging.info('No diff for ' + file + ' in commit ' + self.commit.hexsha)
					return ans
				if not diff.deleted_file:
					ans.append(os.path.join(self._repo.working_dir, file))
		return ans

	def is_test_file(self, file):
		name = os.path.basename(file.lower())
		if not name.endswith('.java'):
			return False
		if name.endswith('test.java'):
			return True
		if name.endswith('tests.java'):
			return True
		if name.startswith('test'):
			return True
		return False

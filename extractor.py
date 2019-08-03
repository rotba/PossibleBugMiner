import logging
import os

from utils import is_test_file


class Extractor(object):

	def __init__(self, repo, inspected_branch):
		self.repo = repo
		self.inspected_branch = inspected_branch

	# Returns tupls of (issue,commit,tests) that may contain bugs
	def extract_possible_bugs(self):
		ans = []
		for bug_issue in bug_issues:
			logging.info("extract_possible_bugs(): working on issue " + bug_issue.key)
			issue_commits = self.get_issue_commits(bug_issue)
			if len(issue_commits) == 0:
				logging.info('Couldn\'t find commits associated with ' + bug_issue.key)
				continue
			for commit in issue_commits:
				issue_tests = self.get_tests_paths_from_commit(commit)
				if len(issue_tests) == 0:
					logging.info(
						'Didn\'t associate ' + bug_issue.key + ' and commit ' + commit.hexsha + ' with any test')
					continue
				ans.append((bug_issue.key, commit.hexsha, issue_tests))
		return ans

	# Returns the commits relevant to bug_issue
	def get_issue_commits(self, issue):
		ans = []
		for commit in all_commits:
			if self.is_associated_to_commit(issue, commit):
				ans.append(commit)
		return ans

	# Returns true if the commit message contains the issue key exclusively
	def is_associated_to_commit(self, issue, commit):
		if issue.key in commit.message:
			index_of_char_after_issue_key = commit.message.find(issue.key) + len(issue.key)
			if index_of_char_after_issue_key == len(commit.message):
				return True
			char_after_issue_key = commit.message[commit.message.find(issue.key) + len(issue.key)]
			return not char_after_issue_key.isdigit()
		else:
			return False

	# Returns tests that have been changed in the commit in the current state of the project
	def get_tests_paths_from_commit(self, commit):
		ans = []
		diff_index = commit.parents[0].diff(commit)
		for file in commit.stats.files.keys():
			if is_test_file(file):
				try:
					diff = list(filter(lambda d: d.a_path == file, diff_index))[0]
				except IndexError as e:
					logging.info('No diff for ' + file + ' in commit ' + commit.hexsha)
					return ans
				if not diff.deleted_file:
					ans.append(os.path.join(self.repo.working_dir, file))
		return ans

	def get_all_commits(self):
		return list(self.repo.iter_commits(self.inspected_branch))

import datetime
import re

from aidnd_diff.filediff import FileDiff
from commit_analyzer import IsBugCommitAnalyzer
from extractor import Extractor
from termcolor import colored


class SourceforgeExtractor(Extractor):
	MAX_ISSUES_TO_RETRIEVE = 2000

	# USE_CASH = False

	# def __init__(self, repo_dir, branch_inspected, jira_url, issue_key=None, query = None, use_cash = False):
	def __init__(self, repo_dir, branch_inspected):
		super(SourceforgeExtractor, self).__init__(repo_dir, branch_inspected)

	# Returns tupls of (issue,commit,tests) that may contain bugs
	def extract_possible_bugs(self):
		ans = []
		for commit in self.get_all_commits():
			print(colored('### START HANDLING ###', 'red') + commit.hexsha + ' ' + str(datetime.datetime.now().time()))
			analyzer = SourcforgeCommitAnalyzer(commit=commit, repo=self.repo).analyze()
			if analyzer.is_bug_commit():
				ans.append((analyzer.get_bug_number(), analyzer.commit.hexsha, analyzer.get_test_paths()))
				print(colored('### APPENDED !###', 'blue'))
			print(colored('### END HANDLING ###', 'green') + commit.hexsha + ' ' + str(datetime.datetime.now().time()))
		return ans

	def is_bug_fix_commit(self, commit):
		if len(commit.parents) == 0:
			return False
		# return self.is_associated_to_test_diffs(commit) or self.contains_bug_fix_in_code_diffs(commit)
		return self.contains_bug_fix_in_code_diffs(commit)

	def contains_bug_fix_in_code_diffs(self, commit):
		for diff in commit.parents[0].diff(commit):
			positive_delta = FileDiff(diff).get_positive_delta()
			if any(map(lambda x: self.is_bug_fix_documentation(x), positive_delta)):
				return True
		return False

	def is_bug_fix_documentation(self, line):
		return re.search("bug ([0-9])+", line)


class SourcforgeCommitAnalyzer(IsBugCommitAnalyzer):

	def __init__(self, commit, repo):
		super(SourcforgeCommitAnalyzer, self).__init__(commit, repo)
		self._bug_number = None

	def analyze(self):
		super(SourcforgeCommitAnalyzer, self).analyze()
		self._bug_number = self.find_bug_number()
		return self

	def is_bug_commit(self):
		return super(SourcforgeCommitAnalyzer, self).is_bug_commit() and self._bug_number != None

	def get_bug_number(self):
		return self._bug_number

	def find_bug_number(self):
		for diff in self._commit.parents[0].diff(self._commit):
			positive_delta = FileDiff(diff).get_positive_delta()
			return reduce(
				lambda acc, curr: acc if acc != None or self.get_bug_id_from_doc(curr) == None
				else self.get_bug_id_from_doc(curr),
				positive_delta,
				None)

	def get_bug_id_from_doc(self, line):
		match = re.search("bug ([0-9])+", line)
		if match != None:
			bug_space_id = match.group(0)
			space_id = re.search(" ([0-9])+", bug_space_id).group(0)
			return space_id.strip(' ')

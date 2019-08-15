import datetime
import multiprocessing

from git import Repo
# from jira_extractor import JiraExtractor
# from sourceforge_extractor import SourceforgeExtractor
from termcolor import colored


class Extractor(object):

	def __init__(self, repo_dir, inspected_branch):
		self.repo = Repo(repo_dir)
		self.inspected_branch = inspected_branch
		self.manager = multiprocessing.Manager()

	# Returns tupls of (issue,commit,tests) that may contain bugs
	def extract_possible_bugs(self):
		ans = []
		for hey in self.get_all_commits():

			print(colored('### START HANDLING ###', 'red') + hey.hexsha + ' ' + str(datetime.datetime.now().time()))
			if self.is_bug_fix_commit(hey):
				ans.append(hey)
				print(colored('### APPENDED !###', 'blue'))
			print(colored('### END HANDLING ###', 'green') + hey.hexsha + ' ' + str(datetime.datetime.now().time()))

		x = 1

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

	def get_all_commits(self):
		return list(self.repo.iter_commits(self.inspected_branch))



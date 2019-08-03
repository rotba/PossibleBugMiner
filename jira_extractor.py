import logging
import os
from urlparse import urlparse

from jira import JIRA
from jira import exceptions as jira_exceptions

from extractor import Extractor
from utils import is_test_file


class JiraExtractor(Extractor):
	MAX_ISSUES_TO_RETRIEVE = 2000

	def __init__(self, repo, branch_inspected, jira_url, issue_key=None):
		super(JiraExtractor, self).__init__(repo, branch_inspected)
		self.jira_url = urlparse(jira_url)
		self.jira_proj_name = os.path.basename(self.jira_url.path)
		self.issue_key = issue_key
		self.jira = JIRA(options={'server': 'https://issues.apache.org/jira'})

	# Returns tupls of (issue,commit,tests) that may contain bugs
	def extract_possible_bugs(self):
		ans = []
		for bug_issue in self.get_bug_issues():
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
				ans.append((bug_issue, commit.hexsha, issue_tests))
		return ans

	# Returns the commits relevant to bug_issue
	def get_issue_commits(self, issue):
		return filter(
			lambda x: self.is_associated_to_commit(issue, x),
			self.get_all_commits()
		)

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

	def get_bug_issues(self):
		FIND_BUGS_JQL_QUERY = self.generate_jql_find_bugs()
		# 	'project = {} AND issuetype = Bug AND createdDate <= "2018/10/03" ORDER BY  createdDate ASC'.format(self.jira_proj_name)
		# if self.issue_key != None:
		# 	FIND_BUGS_JQL_QUERY = '''\
		# 	issuekey = {} AND \
		# 	'''.format(self.issue_key) + FIND_BUGS_JQL_QUERY
		try:
			return self.jira.search_issues(FIND_BUGS_JQL_QUERY, maxResults=JiraExtractor.MAX_ISSUES_TO_RETRIEVE)
		except jira_exceptions.JIRAError as e:
			raise JiraErrorWrapper(msg=e.text, jira_error=e)

	def generate_jql_find_bugs(self):
		ans = 'project = {} ' \
		      'AND issuetype = Bug ' \
		      'AND createdDate <= "2018/10/03" ' \
		      'ORDER BY  createdDate ASC' \
			.format(
			self.jira_proj_name)
		if self.issue_key != None:
			ans = 'issuekey = {} AND ' \
				      .format(self.issue_key) + ans
		return ans


class JiraExtractorException(Exception):
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return repr(self.msg)


class JiraErrorWrapper(JiraExtractorException):
	def __init__(self, msg, jira_error):
		super(JiraErrorWrapper, self).__init__(msg)
		self.jira_error = jira_error

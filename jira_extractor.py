import logging
import os
import re
from urlparse import urlparse

import settings
from commit_analyzer import IsBugCommitAnalyzer
from extractor import Extractor
from jira import JIRA
from jira import exceptions as jira_exceptions
from utils import get_from_cache


class JiraExtractor(Extractor):
	MAX_ISSUES_TO_RETRIEVE = 1000
	WEAK_ISSUE_COMMIT_BINDING = False

	# def __init__(self, repo_dir, branch_inspected, jira_url, issue_key=None, query = None, use_cash = False):
	def __init__(self, repo_dir, branch_inspected, jira_url, issue_key=None, query=None):
		super(JiraExtractor, self).__init__(repo_dir, branch_inspected)
		self.jira_url = urlparse(jira_url)
		self.jira_proj_name = os.path.basename(self.jira_url.path)
		self.issue_key = issue_key
		self.query = query if query != None else self.generate_jql_find_bugs()
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
				if not self.has_parent(commit): continue
				analyzer = IsBugCommitAnalyzer(commit=commit, parent=self.get_parent(commit), repo=self.repo).analyze()
				if analyzer.is_bug_commit():
					ans.append((bug_issue, analyzer.commit.hexsha, analyzer.get_test_paths(), analyzer.get_diffed_components()))
				else:
					logging.info(
						'Didn\'t associate ' + bug_issue.key + ' and commit ' + commit.hexsha + ' with any test')
		return ans

	# Returns the commits relevant to bug_issue
	def get_issue_commits(self, issue):
		return filter(
			lambda x: self.is_associated_to_commit(issue, x),
			self.get_all_commits()
		)

	# Returns true if the commit message contains the issue key exclusively
	def is_associated_to_commit(self, issue, commit):
		if settings.DEBUG:
			if commit.hexsha == 'af6fe141036d30bfd1613758b7a9fb413bf2bafc':
				return True
		if issue.key in commit.message:
			if JiraExtractor.WEAK_ISSUE_COMMIT_BINDING:
				if 'fix' in commit.message.lower():
					return True
			index_of_char_after_issue_key = commit.message.find(issue.key) + len(issue.key)
			if index_of_char_after_issue_key == len(commit.message):
				return True
			char_after_issue_key = commit.message[commit.message.find(issue.key) + len(issue.key)]
			return not char_after_issue_key.isdigit()
		elif re.search("This closes #{}".format(issue.key), commit.message):
			return True
		elif re.search("\[{}\]".format(issue.key), commit.message):
			return True
		else:
			return False

	def get_bug_issues(self):
		try:
			return self.jira.search_issues(self.query, maxResults=JiraExtractor.MAX_ISSUES_TO_RETRIEVE)
		except jira_exceptions.JIRAError as e:
			raise JiraErrorWrapper(msg=e.text, jira_error=e)

	def generate_jql_find_bugs(self):
		ans = 'project = {} ' \
		      'AND issuetype = Bug ' \
		      'AND createdDate <= "2019/10/03" ' \
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

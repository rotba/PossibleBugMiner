import logging
import settings
from diff.CommitsDiff import CommitsDiff
from mvnpy import mvn
from pathlib import Path
import os
from javadiff.diff import get_changed_exists_methods, get_changed_methods
from diff.CommitsDiff import CommitsDiff

class IsBugCommitAnalyzer(object):
    TESTS_DIFFS_IS_CRITERIA = False

    def __init__(self, commit, parent, repo):
        self._commit = commit
        self._parent = parent
        self._repo = repo
        self.associated_tests_paths = None
        self.diffed_components = None
        self.changed_exists_methods = None
        self.changed_methods = None

    @property
    def commit(self):
        return self._commit

    @property
    def parent(self):
        return self._parent

    def analyze(self):
        if len(self.commit.parents) == 0: return self
        self.associated_tests_paths = self.get_tests_paths_from_commit()
        self.diffed_components = self.get_diffed_components()
        self.changed_exists_methods = get_changed_exists_methods(self._repo.working_dir, self._commit)
        self.changed_methods = get_changed_methods(self._repo.working_dir, self._commit)
        return self

    def is_bug_commit(self, check_trace=False):
        if settings.DEBUG:
            if self.commit.hexsha == 'af6fe141036d30bfd1613758b7a9fb413bf2bafc':
                return True
        check = self.has_associated_tests_paths() and self.has_associated_diffed_components() and not self.has_added_methods()
        if check and check_trace:
            from mvnpy.Repo import Repo
            repo = Repo(self._repo)
            if repo.has_surefire():
                return True
        return False

    def get_test_paths(self):
        return self.associated_tests_paths

    def has_added_methods(self):
        # check of there are new non-test methods
        return len(filter(lambda m: "test" not in m.id.lower() and m not in self.changed_exists_methods, self.changed_methods)) > 0

    def get_tests_paths_from_commit(self):
        ans = []
        diff_index = self._parent.diff(self.commit)
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

    def has_associated_tests_paths(self):
        if not IsBugCommitAnalyzer.TESTS_DIFFS_IS_CRITERIA: return True
        return self.associated_tests_paths is not None and len(self.associated_tests_paths) > 0

    def has_associated_diffed_components(self):
        return self.diffed_components is not None and len(self.diffed_components) > 0

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
        if 'test' in os.path.basename(file).lower() and 'test' in Path(file).parts:
            return True
        return False


    def get_diffed_components(self):
        ans = []
        try:
            commit_diff = CommitsDiff(
                commit_a=self.commit,
                commit_b=self.parent)
        except AssertionError as e:
            return []
        for file_diff in commit_diff.diffs:
            if file_diff.file_name.endswith('.java') and not self.is_test_file(file_diff.file_name):
                ans.append(file_diff)
        return ans

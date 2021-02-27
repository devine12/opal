from typing import List
from pathlib import Path
from git.objects import Commit

from opal.common.git.repo_utils import GitActions, DirActions
from opal.common.logger import get_logger
from opal.common.git.repo_watcher import RepoWatcher
from opal.server.config import (
    POLICY_REPO_URL,
    POLICY_REPO_CLONE_PATH,
    POLICY_REPO_MAIN_BRANCH,
    POLICY_REPO_MAIN_REMOTE,
    POLICY_REPO_POLLING_INTERVAL,
    OPA_FILE_EXTENSIONS,
)
from opal.server.gitwatcher.publisher import policy_publisher

logger = get_logger("opal.git.watcher")


def policy_topics(paths: List[Path]) -> List[str]:
    return ["policy:{}".format(str(path)) for path in paths]


async def publish_full_manifest(
    old_commit: Commit, new_commit: Commit, file_extensions: List[str] = OPA_FILE_EXTENSIONS):
    """
    publishes policy topics matching all relevant directories in tracked repo,
    prompting the client to ask for *all* contents of these directories (and not just diffs).
    """
    all_paths = GitActions.all_files_in_repo(new_commit, file_extensions)
    directories = DirActions.parents(all_paths)
    logger.info("Publishing policy update", directories=[str(d) for d in directories])
    topics = policy_topics(directories)
    policy_publisher.publish_updates(topics=topics, data=new_commit.hexsha)


policy_watcher = RepoWatcher(
    repo_url=POLICY_REPO_URL,
    clone_path=POLICY_REPO_CLONE_PATH,
    branch_name=POLICY_REPO_MAIN_BRANCH,
    remote_name=POLICY_REPO_MAIN_REMOTE,
    polling_interval=POLICY_REPO_POLLING_INTERVAL,
)

policy_watcher.on_new_commits(publish_full_manifest)
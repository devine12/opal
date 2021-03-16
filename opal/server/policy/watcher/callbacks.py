from typing import List, Optional
from pathlib import Path
from functools import partial
from git.objects import Commit

from opal.common.paths import PathUtils
from opal.common.logger import get_logger
from opal.common.git.commit_viewer import CommitViewer, has_extension
from opal.common.git.diff_viewer import DiffViewer
from opal.common.topics.publisher import TopicPublisher
from opal.common.topics.utils import policy_topics


async def publish_all_directories_in_repo(
    old_commit: Commit,
    new_commit: Commit,
    publisher: TopicPublisher,
    file_extensions: Optional[List[str]] = None
):
    """
    publishes policy topics matching all relevant directories in tracked repo,
    prompting the client to ask for *all* contents of these directories (and not just diffs).
    """
    logger = get_logger("opal.git.watcher")
    with CommitViewer(new_commit) as viewer:
        filter = partial(has_extension, extensions=file_extensions)
        all_paths = list(viewer.files(filter))
        directories = PathUtils.intermediate_directories(all_paths)
        logger.info("Publishing policy update", directories=[str(d) for d in directories])
        topics = policy_topics(directories)
        publisher.publish(topics=topics, data=new_commit.hexsha)


async def publish_changed_directories(
    old_commit: Commit,
    new_commit: Commit,
    publisher: TopicPublisher,
    file_extensions: Optional[List[str]] = None
):
    """
    publishes policy topics matching all relevant directories in tracked repo,
    prompting the client to ask for *all* contents of these directories (and not just diffs).
    """
    logger = get_logger("opal.git.watcher")
    if new_commit == old_commit:
        return await publish_all_directories_in_repo(
            old_commit,
            new_commit,
            publisher=publisher,
            file_extensions=file_extensions
        )

    with DiffViewer(old_commit, new_commit) as viewer:
        def has_extension(path: Path) -> bool:
            if not file_extensions:
                return True
            return path.suffix in file_extensions
        all_paths = list(viewer.affected_paths(has_extension))
        if not all_paths:
            logger.warn(
                "new commits detected but no files are affected",
                old_commit=old_commit,
                new_commit=new_commit
            )
            return
        directories = PathUtils.intermediate_directories(all_paths)
        logger.info("Publishing policy update", directories=[str(d) for d in directories])
        topics = policy_topics(directories)
        publisher.publish(topics=topics, data=new_commit.hexsha)
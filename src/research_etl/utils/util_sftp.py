import os
import stat
from typing import List

import paramiko

from research_etl.utils.util_logging import ProcessLogger


def walk_sftp_dirs(sftp: paramiko.SFTP, remote_dir: str = ".") -> List[str]:
    """
    return list of all files found by walking sftp dirs
    """
    logger = ProcessLogger("walk_sftp_dirs", remote_dir=remote_dir)
    file_list = []
    for entry in sftp.listdir_attr(remote_dir):
        if entry.st_mode is None:
            continue
        remote_path = os.path.join(remote_dir, entry.filename)
        if stat.S_ISDIR(entry.st_mode):
            file_list += walk_sftp_dirs(sftp, remote_path)
        elif stat.S_ISREG(entry.st_mode):
            file_list.append(remote_path)

    logger.add_metadata(files_found=len(file_list))
    logger.log_complete()

    return file_list

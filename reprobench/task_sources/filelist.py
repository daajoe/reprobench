from loguru import logger
import os

from pathspec import PathSpec
from pathlib import Path
from .base import BaseTaskSource


class FileListSource(BaseTaskSource):
    TYPE = "filelist"

    def __init__(self, path=None, filelist="", resolve=False, **kwargs):
        super().__init__(path)
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                logger.error(f"Failed to create directory at {path}")
        if not os.path.exists(path):
            logger.error(f"Path does not exist: '{path}'")
            raise FileNotFoundError(path)
        self.filelist = filelist
        self.__resolve = resolve

    def setup(self):
        spec = []
        with open(self.filelist, 'r') as files_fh:
            for line in files_fh.readlines():
                if line.startswith('#'):
                    continue
                spec.append(line.split("\n")[0])
        logger.info(f"Sending {len(spec)} instances for exectution to server.")
        if self.__resolve:
            return map(lambda match: (Path(self.path).resolve(), match), spec)
        else:
            return map(lambda match: (Path(self.path), match), spec)

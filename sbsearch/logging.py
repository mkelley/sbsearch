# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys
import time
import logging
import numpy as np
from astropy.time import Time


class ElapsedFormatter(logging.Formatter):
    """Based on https://stackoverflow.com/questions/25194864/python-logging-time-since-start-of-program"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t0 = time.time()
        self.t_last = self.t0

    def format(self, record):
        record.dt0 = record.created - self.t0
        record.dt = record.created - self.t_last
        self.t_last = record.created
        return super().format(record)


def setup(filename='sbsearch.log', name='SBSearch', level=None):
    logger = logging.Logger(name)
    if level:
        logger.setLevel(level)
    else:
        logger.setLevel(logging.DEBUG)

    # This test allows logging to work when it is run multiple times
    # from ipython
    if len(logger.handlers) == 0:
        formatter = ElapsedFormatter(
            '%(asctime)10s (%(dt).2f/%(dt0).2f) %(levelname)s: '
            '[%(funcName)s] %(message)s', "%Y-%m-%d %H:%M:%S")

        console = logging.StreamHandler(sys.stdout)
        if not level:
            console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        logger.addHandler(console)

        logfile = logging.FileHandler(filename)
        if not level:
            logfile.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: - %(message)s')
        logfile.setFormatter(formatter)
        logger.addHandler(logfile)

    return logger


class ProgressWidget:
    pass


class ProgressBar(ProgressWidget):
    """Progress bar widget for logging.

    Parameters
    ----------
    n : int
        Total number of steps.

    logger : logging.Logger, optional
        The `Logger` object to which to report progress.

    Examples
    --------
    with ProgressBar(1000, logger) as bar:
      for i in range(1000):
        bar.update()

    """

    def __init__(self, n, logger=None):
        self.n = n
        self.logger = logger

    def __enter__(self):
        self.i = 0
        self.last_tenths = 0
        self._logger(tenths=0)
        return self

    def __exit__(self, *args):
        pass

    def _logger(self, msg=None, tenths=0):
        if not msg:
            msg = '#' * tenths + '-' * (10 - tenths)

        if self.logger:
            self.logger.info(msg)
        else:
            print(msg)

    def update(self):
        self.i += 1
        tenths = int(self.i / self.n * 10)
        if tenths != self.last_tenths:
            self.last_tenths = tenths
            self._logger(tenths=tenths)


class ProgressTriangle(ProgressWidget):
    """Progress triangle widget for logging.

    Parameters
    ----------
    n : int
        Total number of steps per dot.

    logger : logging.Logger, optional
        The `Logger` object to which to report progress.

    base : int, optional
        Use logarithmic steps with this base: 2 or 10.

    Examples
    --------
    with ProgressTriangle(1000, logger) as tri:
        for i in range(1000):
            tri.update()

    tri = ProgressTriangle(1, logger=logger, base=2)
    tri.update()

    """

    def __init__(self, n, logger=None, base=None):
        self.n = n
        self.logger = logger
        self.base = base
        if base:
            if base == 2:
                self._log = np.log2
                self.logger.info('Base-2 dots')
            elif base == 10:
                self._log = np.log10
                self.logger.info('Base-10 dots')
            else:
                raise ValueError('base must be 2 or 10')
        self.reset()

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, *args):
        self.done()

    @property
    def dt(self):
        return (Time.now() - self.t0).sec

    def _logger(self, msg=None, dots=0):
        if not msg:
            msg = '.' * dots

        if self.logger:
            self.logger.info(msg)
        else:
            print(msg)

    def reset(self):
        self.i = 0
        self.t0 = Time.now()

    def update(self, n=1):
        last = self.i
        self.i += n

        msg = None
        if self.base:
            if last == 0:
                return

            logi = self._log(self.i)
            if (self._log(last) % self.n) >= (logi % self.n):
                self._logger(dots=int(logi // self.n))
        else:
            if (last % self.n) >= (self.i % self.n):
                self._logger(dots=int(self.i // self.n))

    def done(self):
        self._logger('{:.0f} seconds elapsed.'.format(self.dt))

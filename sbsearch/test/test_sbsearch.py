# Licensed with the 3-clause BSD license.  See LICENSE for details.
import sqlite3
import pytest
from logging import Logger

import numpy as np
from astropy.coordinates import SkyCoord
import astropy.time as Time

from .. import util
from ..sbsearch import SBSearch
from ..config import Config

# tile 1/2 the sky
N_tiles = 10
ra_steps = np.linspace(0, 2 * np.pi, N_tiles + 1)
dec_steps = np.linspace(-np.pi / 2, np.pi / 2, N_tiles + 1)
sky_tiles = np.zeros((10, N_tiles**2))
for i in range(N_tiles):
    for j in range(N_tiles):
        sky_tiles[:, i * N_tiles + j] = (
            np.mean(ra_steps[i:i+2]),
            np.mean(dec_steps[j:j+2]),
            ra_steps[i], dec_steps[j],
            ra_steps[i], dec_steps[j+1],
            ra_steps[i+1], dec_steps[j+1],
            ra_steps[i+1], dec_steps[j])
del ra_steps, dec_steps, i, j


@pytest.fixture
def sbs():
    config = Config(database=':memory:')
    with SBSearch(config) as sbs:
        sbs.db.add_object('C/1995 O1')
        objid = sbs.db.add_object('2P')

        obsids = range(N_tiles**2)
        start = 2458119.5 + np.arange(N_tiles**2) * 30 / 86400
        stop = start + 30 / 86400

        sbs.db.add_observations(
            columns=[obsids, start, stop] + list(sky_tiles))
        sbs.update_eph(objid, 2458119.5, 2458121.5, step='1d', cache=True)

        yield sbs


class TestSBSearch:
    def test_update_eph(self, sbs):
        objid = sbs.db.resolve_object('2P')[0]
        start, stop = 2458119.5, 2458121.5
        count = len(sbs.db.get_ephemeris(objid, None, None))
        assert count == 3

        sbs.update_eph(objid, start, stop, clean=True)
        count = len(sbs.db.get_ephemeris(objid, None, None))
        assert count == 0

        sbs.update_eph(objid, start, stop, step='1d', cache=True)
        count = len(sbs.db.get_ephemeris(objid, None, None))
        assert count == 3

    def test_find_obs(self, sbs):
        objid = sbs.db.resolve_object('2P')[0]
        obsids = sbs.find_obs(objid)
        assert len(obsids) == 1
from __future__ import division

import numpy as np

from experiment.util import old_div


# transform from absolute pixel (col,row) to frame-relative (x,y)
def px2xy(px, size, SC):
    return [
        [old_div((_[0] - size[0] / 2.0), SC), old_div((_[1] - size[1] / 2.0), SC)]
        for _ in px
    ]


# transform from frame-relative (x,y) to absolute pixel (col,row)
def xy2px(xy, size, SC):
    # return [[int(SC*_[0]+size[0]/2.),int(size[1]/2.-SC*_[1])] for _ in xy]
    return [
        [int(SC * _[0] + size[0] / 2.0), int(size[1] / 2.0 - SC * _[1])] for _ in xy
    ]


def datestring(t=None, sec=False):
    """
    Datestring

    Inputs:
      (optional)
      t - time.localtime()
      sec - bool - whether to include sec [SS] in output

    Outputs:
      ds - str - date in YYYYMMDD-HHMM[SS] format

    by Sam Burden 2012
    """
    if t is None:
        import time

        t = time.localtime()

    ye = "%04d" % t.tm_year
    mo = "%02d" % t.tm_mon
    da = "%02d" % t.tm_mday
    ho = "%02d" % t.tm_hour
    mi = "%02d" % t.tm_min
    se = "%02d" % t.tm_sec
    if not sec:
        se = ""

    return ye + mo + da + "-" + ho + mi + se


# size = (1200,800)
size = (1000, 250)
RATIO = 4
HEIGHT = 400
HEIGHT = 200
size = (RATIO * HEIGHT, HEIGHT)


# global constants
FPS_ = 30
FPS = FPS_

SLIDER_MIN = 0.0
SLIDER_MAX = 4096.0
SLIDER_SPT = 2  # number of slider samples per pygame tick
SLIDER_SCALE = 5.0

STEP = 1.0 / (FPS * SLIDER_SPT)

PAUSE = False
# PAUSE = True

TRIAL_DONE = False

TRIAL_STATE = None

FADE = -1

ALLOW_DUPLICATES = False
# ALLOW_DUPLICATES = True

PLOT = False
# PLOT = True

SHOW_GRID = True
SHOW_GRID = False

SHOW_REF = True
# SHOW_REF = False

SHOW_INPUT = True
SHOW_INPUT = False

SHOW_DISTURBANCE = True
SHOW_DISTURBANCE = False

SC = float(HEIGHT)  # modify SC to change lookahead
RANGE = np.asarray(px2xy([[0.0, 0.0], size], size, SC))
X_RANGE = RANGE[:, 0]
Y_RANGE = RANGE[:, 1]
ACCEL = 1.0
RAD_SYS, THICKNESS_SYS = 5e-2, 0.0
THICK_REFERENCE = 2 * RAD_SYS
THICKNESS_INPUT = RAD_SYS
THICKNESS_DISTURBANCE = RAD_SYS
# GRID_SPACE = 4*RAD_SYS
GRID_SPACE = 1.0
SHIP_SHIFT = -0.0
INPUT_SHIFT = -0.5  # SHIP_SHIFT-4*RAD_SYS
DISTURBANCE_SHIFT = -0.25  # SHIP_SHIFT-4*RAD_SYS
TIMES = np.linspace(
    X_RANGE[0] - 2 * THICK_REFERENCE, X_RANGE[1] + THICK_REFERENCE, old_div(size[0], 10)
)

HZ = 0.2


# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

GREY = (247, 247, 247)
DARKGREY = (47, 47, 47)
PURPLE = (153, 142, 195)
GOLD = (241, 163, 64)

_GREY = np.array((247, 247, 247)) / 255.0
_DARKGREY = np.array((47, 47, 47)) / 255.0
_PURPLE = np.array((153, 142, 195)) / 255.0
_GOLD = np.array((241, 163, 64)) / 255.0

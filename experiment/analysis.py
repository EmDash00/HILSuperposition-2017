from __future__ import print_function

import glob
import importlib
import os
import sys
from builtins import range

#
import numpy as np
from matplotlib import rc

#
# Say, "the default sans-serif font is Helvetica"
rc("font", **{"sans-serif": "Helvetica", "family": "sans-serif"})
rc("text", usetex=False)

args = sys.argv

help = """
usage:
  analysis subjects protocol [formats]

separate subjects by commas to pool data:
  analysis subj1,subj2 protocol

separate protocols by commas to pool data:
  analysis subject proto1,proto2

add filename formats to save files in those formats:
  analysis subjects protocol png,pdf
"""

if len(args) < 2:
    print("\nABORT -- no subject specified")
    print(help)
    sys.exit(0)

if len(args) < 3:
    print("\nABORT -- no protocol specified")
    print(help)
    sys.exit(0)


def dbg(s):
    print(s)
    pass


do_title = True
do_title = False

font = dict(fontname="sans-serif", fontsize=16)


def format_axes(
    ax,
    title=None,
    do_title=do_title,
    grid="on",
    xlabel=None,
    ylabel=None,
    xticks=None,
    yticks=None,
    xlim=None,
    ylim=None,
    xticklabels=None,
    yticklabels=None,
    xfont=font,
    yfont=font,
):
    if title is not None and do_title:
        ax.set_title(title, **xfont)
    if grid is not None:
        ax.grid(grid)
    if xlabel is not None:
        ax.set_xlabel(xlabel, **xfont)
    if ylabel is not None:
        ax.set_ylabel(ylabel, **yfont)
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)
    if xticks is not None:
        ax.set_xticks(xticks)
    if yticks is not None:
        ax.set_yticks(yticks)
    if xticklabels is not None:
        ax.set_xticklabels(xticklabels)
    if yticklabels is not None:
        ax.set_yticklabels(yticklabels)
    # if xfont is not None:
    #  ax.set_xticklabels(ax.get_xticklabels(),fontdict=xfont)
    #  lbls = ax.get_xticklabels()
    #  for lbl in lbls:
    #    if 'fontname' in xfont:
    #      lbl.set_fontname(xfont['fontname'])
    #    if 'fontsize' in xfont:
    #      lbl.set_fontsize(xfont['fontsize'])
    #  ax.set_xticklabels(lbls)
    # if yfont is not None:
    #  for label in ax.get_yticklabels():
    #    if 'fontname' in yfont:
    #      label.set_fontname(yfont['fontname'])
    #    if 'fontsize' in yfont:
    #      label.set_fontsize(yfont['fontsize'])
    # 1/0


def bootstrap_trials(d, N=None, M=None):
    # TODO allow other axes
    axis = 0
    #
    d = np.asarray(d)
    sh = list(d.shape)
    # indices to bootstrap
    i = np.arange(sh[axis])
    # default number of resamplings is 10 * number of trials
    if N is None:
        N = 10 * sh[axis]
    # default number of samples per resampling is number of trials
    if M is None:
        M = sh[axis]
    sh[axis] = M * N
    D = np.nan * np.ones(sh)
    for n in range(N):
        D[n * M : (n + 1) * M] = d[np.random.choice(i, M)]
    return D


def bootstrap_mean(d, N=None, M=None):
    # TODO allow other axes
    axis = 0
    #
    d = np.asarray(d)
    sh = list(d.shape)
    # indices to bootstrap
    i = np.arange(sh[axis])
    # default number of resamplings is 10 * number of trials
    if N is None:
        N = 10 * sh[axis]
    # default number of samples per resampling is number of trials
    if M is None:
        M = sh[axis]
    sh[axis] = N
    D = np.nan * np.ones(sh)
    for n in range(N):
        D[n] = np.mean(d[np.random.choice(i, M)], axis=axis)
    return D


subjects = args[1].split(",")
protocols = args[2].split(",")

fmts = []
if len(args) >= 4:
    fmts = args[3].split(",")

try:
    trials
    dbg('FOUND trials -- not loading data; run without "-i" to reload data')
except:
    dbg("LOADING")
    fis = []
    for subject in subjects:
        for protocol in protocols:
            fis += glob.glob(os.path.join("data", subject, "*_" + protocol + "*"))
    ids = sorted(list(set([fi.strip(".npz").split("_", 2)[2] for fi in fis])))
    ids = [id for id in ids if id[-3:] not in ["rej", "oob", "rst", "max"]]
    ids = [id for id in ids if id[-4:] not in ["rst1", "rst2"]]

    # dbg(fis)
    # dbg(ids)

    if not len(fis) == len(ids):
        dbg("WARNING -- repeated trials; using only most recent")

    # load data
    trials = dict()
    for subject in subjects:
        for protocol in protocols:
            for i, id in enumerate(ids):
                fis = sorted(
                    glob.glob(
                        os.path.join(
                            "data", subject, "*_" + protocol + "_" + id + ".npz"
                        )
                    )
                )
                if len(fis) > 1:
                    dbg("WARNING -- repeated trials for id =" + id)
                if len(fis) == 0:
                    dbg("WARNING -- no data for id =" + id)
                    continue
                # dbg(fis)
                fi = fis[-1]
                print("LOAD " + fi)
                trial = dict(np.load(fi))
                trials[subject + "_" + protocol + "_" + id] = trial
                # dbg(trial['time_'][:10])
                # dbg(trial['time_'][-10:])

for protocol in protocols:
    proto = importlib.import_module("protocols." + protocol)

    # title = u'subj:'+subject+' proto:'+protocol
    title = "" + ",".join(subjects) + " " + protocol
    figs = proto.analysis(
        trials,
        title=title,
        bootstrap_trials=bootstrap_trials,
        bootstrap_mean=bootstrap_mean,
        format_axes=format_axes,
    )
    if len(fmts) > 0:
        #
        subjs = ",".join(subjects)
        subject_dir = os.path.join("visuals", subjs)
        if not os.path.exists(subject_dir):
            os.mkdir(subject_dir)
        for fmt in fmts:
            plot_dir = os.path.join("visuals", subjs, fmt)
            if not os.path.exists(plot_dir):
                os.mkdir(plot_dir)
            for lbl, fig in list(figs.items()):
                fig.savefig(
                    os.path.join(
                        "visuals", subjs, fmt, protocol + "_" + lbl + "." + fmt
                    ),
                    format=fmt,
                    pad_inches=0.0,
                    dpi=300,
                )

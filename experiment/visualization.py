from __future__ import absolute_import, division, print_function

import glob
import importlib
import os
import sys
from builtins import zip

#
import numpy as np
import pylab as plt
from matplotlib import rc
from past.utils import old_div

#
# Say, "the default sans-serif font is Helvetica"
rc("font", **{"sans-serif": "Helvetica", "family": "sans-serif"})
rc("text", usetex=False)

help = """
usage:
  visualization subject protocol [formats]

add filename formats to save files in those formats:
  visualization subject protocol png,mp4
"""


def dbg(s):
    print(s)


args = sys.argv

if len(args) < 2:
    dbg("\nABORT -- no subject specified")
    dbg(help)
    sys.exit(0)

if len(args) < 3:
    dbg("\nABORT -- no protocol specified")
    dbg(help)
    sys.exit(0)

subject = args[1]
protocol = args[2]

fmts = []
if len(args) >= 4:
    fmts = args[3].split(",")

do_anim = True
do_anim = False
do_stills = True
# do_stills = False

proto = importlib.import_module("protocols." + protocol)

fis = glob.glob(os.path.join("data", subject, "*_" + protocol + "*"))
ids = sorted(list(set([fi.strip(".npz").split("_", 2)[2] for fi in fis])))
ids = [id for id in ids if id[-3:] not in ["rej", "oob", "rst", "max"]]

viz = proto.visualization(subject, protocol)
ids = viz["ids"]
scales = viz["scales"]
jumps = viz["jumps"]

# print ids

# sys.exit(0)

from util import *

from .protocols.globals import (
    GRID,
    GRID_SPACE,
    INPUT_SHIFT,
    SHIP_SHIFT,
    X_RANGE,
    Y_RANGE,
    size,
)

INPUT_SHIFT = INPUT_SHIFT - SHIP_SHIFT
SHIP_SHIFT = SHIP_SHIFT - SHIP_SHIFT  # 0.
X_RANGE = (-0.5, 2.5)

trials = dict()

for id in ids:
    fis = sorted(
        glob.glob(os.path.join("data", subject, "*_" + protocol + "_" + id + ".npz"))
    )
    if len(fis) > 1:
        dbg("WARNING -- repeated trials for id =" + id)
    assert len(fis) > 0, "ERROR -- no data for id =" + id
    fi = fis[-1]
    print("LOAD " + fi)
    trial = dict(np.load(fi))
    trials[id] = trial

# sys.exit(0)

times_ = [trials[ids[0]]["time_"]]
refs_ = [trials[ids[0]]["ref_"]]
outs_ = [trials[ids[0]]["out_"]]
inps_ = [old_div(trials[ids[0]]["inp_"], (scales[0] * 3.0))]

for id, scale in zip(ids[1:], scales[1:]):
    times_.append([np.nan])
    refs_.append([np.nan])
    outs_.append([np.nan])
    inps_.append([np.nan])
    times_.append(trials[id]["time_"] + times_[-2][-1])
    refs_.append(trials[id]["ref_"])
    outs_.append(trials[id]["out_"])
    inps_.append(old_div(trials[id]["inp_"], (scale * 3.0)))

times = np.hstack(times_)
refs = np.hstack(refs_)
outs = np.hstack(outs_)
inps = np.hstack(inps_)

samp0 = 60

Hzmp4 = 30
Hzdata = int(np.median(1.0 / np.diff(times)))
xrealtime = 1
step = old_div(xrealtime * Hzdata, Hzmp4)

samp = 0
time = times[samp]

xticks = np.hstack(
    (
        -np.arange(-(SHIP_SHIFT - GRID_SPACE), -(X_RANGE[0] - GRID_SPACE), GRID_SPACE)[
            ::-1
        ],
        np.arange(SHIP_SHIFT, X_RANGE[1] + GRID_SPACE, GRID_SPACE),
    )
) - np.mod(time, GRID_SPACE)

col_out = "indigo"
col_ref = "darkorange"
col_inp = 0.15 * np.ones(3)

if do_anim:
    lw = 20
    ms = 40
    al = 1.0  # 0.66

    plt.ion()
    #
    fig = plt.figure(1, figsize=(old_div(2 * size[0], 100), old_div(size[1], 100)))
    plt.clf()
    ax = plt.subplot(1, 1, 1)
    ax.grid("on")
    ax.axis("equal")
    # plots
    l_ref = ax.plot(
        times - time, refs, "-", lw=lw, color=col_ref, alpha=al, solid_capstyle="butt"
    )[0]
    l_out = ax.plot(
        times[:samp] - time,
        outs[:samp],
        "-",
        lw=0.5 * lw,
        color=col_out,
        alpha=0.5 * al,
        solid_capstyle="butt",
    )[0]
    l_inp = ax.plot(
        times[:samp] - time + INPUT_SHIFT,
        inps[:samp],
        "-",
        lw=0.5 * lw,
        color=col_inp,
        alpha=0.5 * al,
        solid_capstyle="butt",
    )[0]
    m_inp = ax.plot(
        INPUT_SHIFT * np.ones(2),
        [0.0, inps[samp]],
        "-",
        lw=0.5 * lw,
        color=col_inp,
        solid_capstyle="butt",
    )[0]
    # m_ref = ax.plot(SHIP_SHIFT,refs[samp],'.',ms=ms,color=col_ref,alpha=al)[0]
    m_out = ax.plot(SHIP_SHIFT, outs[samp], ".", ms=ms, color=col_out, alpha=al)[0]
    # ticks
    if GRID:
        ax.set_xticks(xticks)
        ax.set_xticklabels([])
    ax.set_yticks([])
    # limits
    ax.set_xlim(X_RANGE)
    ax.set_ylim(Y_RANGE)
    #
    for i, samp in enumerate(np.arange(0, times.size, step)):
        time = times[samp]
        l_ref.set_xdata(times - times[samp])
        l_out.set_xdata(times[:samp] - time)
        l_out.set_ydata(outs[:samp])
        l_inp.set_xdata(times[:samp] - time + INPUT_SHIFT)
        l_inp.set_ydata(inps[:samp])
        # m_ref.set_ydata(refs[samp])
        m_out.set_ydata(outs[samp])
        m_inp.set_ydata([0.0, inps[samp]])
        #
        plt.draw()
        if "mp4" in fmts:
            subject_dir = os.path.join("visuals", subject)
            if not os.path.exists(subject_dir):
                os.mkdir(subject_dir)
            subject_protocol_dir = os.path.join("visuals", subject, protocol)
            if not os.path.exists(subject_protocol_dir):
                os.mkdir(subject_protocol_dir)
            fn = os.path.join("visuals", subject, protocol, "%05d.png" % i)
            print("SAVE " + fn)
            fig.savefig(fn, pad_inches=0.0, dpi=300, bbox_inches="tight", frameon=False)
    #
    if "mp4" in fmts:
        try:
            fn = os.path.join("visuals", subject, protocol, "%05d.png")
            vn = os.path.join("visuals", subject, protocol + "_x%d" % xrealtime)
            cmd = 'ffmpeg -i "%s" -c:v libx264 -r 30 -pix_fmt yuv420p %s.mp4' % (fn, vn)
            print(cmd)
            os.system(cmd)
        except:
            print("VIDEO FAIL -- do you have ffmpeg and libx264 installed?")
    #
    plt.ioff()

if "mp4" in fmts:
    fmts.remove("mp4")

if do_stills:
    lw = 20
    ms = 40
    al = 1.0  # 0.66
    la = 0.2
    #
    figs = dict()
    #
    figs["2"] = plt.figure(
        2, figsize=(old_div(2 * size[0], 100), old_div(size[1], 100))
    )
    plt.clf()
    ax = plt.subplot(1, 1, 1)
    ax.grid("on")
    ax.axis("equal")
    for time, ref, out in zip(times_[::2], refs_[::2], outs_[::2]):
        # plots
        ax.plot(
            time - time[Hzdata],
            ref,
            "-",
            lw=lw,
            color=col_ref,
            alpha=al,
            solid_capstyle="butt",
            zorder=-10,
        )[0]
        ax.plot(
            time - time[Hzdata],
            out,
            "-",
            lw=0.25 * lw,
            color=col_out,
            alpha=la,
            solid_capstyle="butt",
            zorder=+10,
        )[0]
    # ticks
    if GRID:
        ax.set_xticks(xticks)
        ax.set_xticklabels([])
    ax.set_yticks([])
    # limits
    ax.set_xlim(X_RANGE)
    ax.set_ylim(Y_RANGE)
    #
    figs["3"] = plt.figure(
        3, figsize=(old_div(2 * size[0], 100), old_div(size[1], 100))
    )
    plt.clf()
    ax = plt.subplot(1, 1, 1)
    ax.grid("on")
    ax.axis("equal")
    for time, ref, out in zip(times_[::2], refs_[::2], outs_[::2]):
        # plots
        ax.plot(
            time - time[Hzdata],
            np.sign(ref[-1]) * (ref - ref[0]),
            "-",
            lw=lw,
            color=col_ref,
            alpha=al,
            solid_capstyle="butt",
            zorder=-10,
        )[0]
        ax.plot(
            time - time[Hzdata],
            np.sign(ref[-1]) * (out - ref[0]),
            "-",
            lw=0.25 * lw,
            color=col_out,
            alpha=la,
            solid_capstyle="butt",
            zorder=+10,
        )[0]
    # ticks
    if GRID:
        ax.set_xticks(xticks)
        ax.set_xticklabels([])
    ax.set_yticks([])
    # limits
    ax.set_xlim(X_RANGE)
    ax.set_ylim(Y_RANGE)
    #
    figs["4"] = plt.figure(
        4, figsize=(old_div(2 * size[0], 100), old_div(size[1], 100))
    )
    plt.clf()
    ax = plt.subplot(1, 1, 1)
    ax.grid("on")
    ax.axis("equal")
    for time, ref, out in zip(times_[::2], refs_[::2], outs_[::2]):
        # plots
        ax.plot(
            time - time[Hzdata] + 1,
            np.sign(ref[-1]) * (ref - ref[0]),
            "-",
            lw=lw,
            color=col_ref,
            alpha=al,
            solid_capstyle="butt",
            zorder=-10,
        )[0]
        ax.plot(
            time - time[Hzdata] + 1,
            np.sign(ref[-1]) * (out - ref[0]),
            "-",
            lw=0.25 * lw,
            color=col_out,
            alpha=la,
            solid_capstyle="butt",
            zorder=+10,
        )[0]
    # limits
    format_axes(
        ax,
        xlim=(1.0, 3.0),
        ylim=(-0.1, 0.5),
        xlabel="time (sec)",
        ylabel=r"output ($y$)",
    )
    #
    lw = 1
    figs["5"] = plt.figure(
        5, figsize=(old_div(2 * size[0], 100), old_div(size[1], 100))
    )
    plt.clf()
    ax = plt.subplot(1, 1, 1)
    ax.grid("on")
    ax.axis("equal")
    #
    time = times_[0][: 3 * Hzdata + 1]
    refs = []
    outs = []
    inps = []
    for ref, out, inp in zip(refs_[::2], outs_[::2], inps_[::2]):
        refs.append(np.sign(ref[-1]) * (ref[: 3 * Hzdata + 1] - ref[0]))
        outs.append(np.sign(ref[-1]) * (out[: 3 * Hzdata + 1] - ref[0]))
        inps.append(np.sign(ref[-1]) * (inp[: 3 * Hzdata + 1]))
    refs = np.vstack(refs)
    outs = np.vstack(outs)
    inps = np.vstack(inps)
    #
    prc = 25
    prcs = [50, old_div(prc, 2), 100 - old_div(prc, 2)]
    alpha_fill = 0.2
    for jump in np.unique(np.abs(jumps)):
        ref = np.percentile(refs[jumps == jump], prcs, axis=0)
        out = np.percentile(outs[jumps == jump], prcs, axis=0)
        inp = np.percentile(inps[jumps == jump], prcs, axis=0)
        #
        ax.plot(time, ref[0], "-", lw=2 * lw, color=col_ref, zorder=-10)
        ax.fill_between(
            time, out[1], out[2], color=col_out, zorder=10, alpha=alpha_fill
        )
        ax.plot(time, out[1:].T, "--", lw=1 * lw, color=col_out, zorder=10)
        ax.plot(time, out[0], "-", lw=2 * lw, color=col_out, zorder=10)
    # limits
    format_axes(
        ax,
        xlim=(1.0, 3.0),
        ylim=(-0.1, 0.5),
        xlabel="time (sec)",
        ylabel=r"output ($y$)",
    )

    for fmt in fmts:
        plot_dir = os.path.join("visuals", subject, fmt)
        if not os.path.exists(plot_dir):
            os.mkdir(plot_dir)
        for lbl, fig in list(figs.items()):
            fn = os.path.join(plot_dir, protocol + "_" + lbl + "." + fmt)
            print("SAVE " + fn)
            fig.savefig(fn, pad_inches=0.0, dpi=300, bbox_inches="tight", format=fmt)

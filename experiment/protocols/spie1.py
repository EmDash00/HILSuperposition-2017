from __future__ import division
from __future__ import absolute_import
from builtins import str
from builtins import range
from past.utils import old_div
import numpy as np
import pylab as plt
import matplotlib 
from matplotlib import rc

from .dynamics import fo, so, zd11, zd12

from .references import spline as ref
from .references import spline_interp

from disturbances import zero as dis

# vector fields
#vfs = ['fo','so','zd12']
vfs = ['fo','zd12']
#vfs = ['zd12']
# reference goes from -jump to jump for each jump in jump
jumps = [0.1,0.2]
# number of replicates
I = 10 
# time to complete task
dt = 1.
#
scale = dict()
scale['fo'] = spline_interp(.5,0.,1.,-max(jumps),+max(jumps),0.,0.,return_dy=True)[1]
scale['so'] = 0.25*spline_interp(0,0.,1.,-max(jumps),+max(jumps),0.,0.,return_ddy=True)[1]
scale['zd11'] = 0.25*spline_interp(0,0.,1.,-max(jumps),+max(jumps),0.,0.,return_ddy=True)[1]
scale['zd12'] = 0.25*spline_interp(0,0.,1.,-max(jumps),+max(jumps),0.,0.,return_ddy=True)[1]
#
def trial_gen(subject,protofile):
  for vf in vfs:
    for jump in jumps:
      for i in range(I):
        for s in [+1,-1]:
          id = '%s_j%+0.1f_i%d' % (vf,s*jump,i)
          if vf == 'fo':
            state = [-s*jump]
            out = lambda x : x[0]
          elif vf == 'so':
            state = [-s*jump,0.]
            out = lambda x : x[0]
          elif vf == 'zd11':
            state = [-s*jump,-s*jump]
            out = lambda x : .5*(x[0]+x[1])
          elif vf == 'zd12':
            state = [-s*jump,-s*jump,0.]
            out = lambda x : .5*(x[0]+x[1])
          #
          pts = np.vstack(([-np.inf,1.*dt, -s*jump,-s*jump],
                           [1.*dt,  2.*dt, -s*jump,+s*jump],
                           [2.*dt,  np.inf,+s*jump,+s*jump],
                         ))
          #
          trial = dict(id=id,pts=pts,init=state,vf=vf,ref=ref,dis=dis,out=out,
                       scale=scale[vf])
          yield trial

# plotting globals
lw = 1
col_out = 'indigo'
col_ref = 'darkorange'
col_inp = col_out
col_p_gain = 'dodgerblue'
col_pd_gain = 'dodgerblue'
alpha_trials = 0.0
alpha_fill = 0.2
#
xlim = (1.,3.)
#ylim_out = (-.3,+.3)
ylim_out = (-0.1,+.5)
#
prc = 25
prcs = [50,old_div(prc,2),100-old_div(prc,2)] 
do_bootstrap_means = False
#
aggro = 1.
do_gains = True
#do_gains = False
#
if do_gains:
  from .spie2 import gain_sim
  p_gains = eval(''.join(open('p_gains.txt','r').readlines()).replace('array',''))
  pd_gains = eval(''.join(open('pd_gains.txt','r').readlines()).replace('array',''))
# pure feedback simulation
def pred_zd12(time,state0,ref):
  state = np.nan*np.zeros((time.size,state0.size))
  state[0] = state0
  inp = np.nan*time
  for ti in range(0,time.size-1):
    dt = time[ti+1] - time[ti]
    t = time[ti]
    xi,zeta,dzeta = state[ti]
    inp[ti] = 2 * ( old_div((ref[ti+1]-ref[ti]), dt) - .5 * dzeta )
    state[ti+1] = state[ti] + dt * zd12(t,state[ti],inp[ti])
  inp[-1] = inp[-2]
  return state,inp
#
def analysis(trials,title='',rescale=False,**util):
  #
  ids = sorted(trials.keys())
  #
  time_ = trials[ids[0]]['time_']
  samps = np.arange((time_ <= xlim[0]).nonzero()[0][-1], (time_ >= xlim[1]).nonzero()[0][0])
  times = time_[samps]
  # 
  figs = dict()
  axs = dict()
  lines = dict()
  for vi,vf in enumerate(vfs):
    inps,outs = dict(),dict()
    #
    #ylim_inp = scale[vf] * (3./2.) * np.array([-0.75,+0.75])
    #ylim_inp = scale[vf] * (3./2.) * np.array([-1.,+1.])
    ylim_inp = scale[vf] * (3./2.) * np.array([-.25,+1.])
    #
    figs[vf] = plt.figure(vi,figsize=(12,6)); plt.clf()
    axs[vf] = dict()
    axs[vf]['+'] = [plt.subplot(2,3,1),plt.subplot(2,3,4)]
    axs[vf]['-'] = [plt.subplot(2,3,2),plt.subplot(2,3,5)]
    axs[vf]['+/-'] = [plt.subplot(2,3,3),plt.subplot(2,3,6)]
    for s in list(axs[vf].keys()):
      for i,id in enumerate(ids):
        subj,proto,_ = id.split('_',2)
        if not proto == 'spie1':
          continue
        subj,proto,v,j,i = id.split('_')
        if not v == vf or not j[1] in s:
          continue
        sgn = float(j[1]+'1')
        jump = float(j[2:])
        if vf == 'zd12' and jump > .15:
          continue
        sc = 1.
        if rescale:
          sc = old_div(max(jumps),jump)
        trial = trials[id]
        ax0,ax1 = axs[vf][s]
        #
        ylabel_inp = ''; ylabel_out = ''
        if s == '+':
          ylabel_inp = r'input ($u$)'
          ylabel_out = r'output ($y$)'
        if vf == 'fo' and do_gains:
          nln = lambda y : y
          p_gain_state,p_gain_inp = gain_sim(
                                         [p_gains['all'],0.],
                                         eval(vf),
                                         nln,
                                         nln,
                                         trial['time_'],
                                         trial['state_'][0],
                                         trial['ref_'])
          pd_gain_state,pd_gain_inp = gain_sim(
                                         pd_gains['all'],
                                         eval(vf),
                                         nln,
                                         nln,
                                         trial['time_'],
                                         trial['state_'][0],
                                         trial['ref_'])
          lines['p_out']  = ax0.plot(trial['time_'],sgn*sc*(p_gain_state)+jump,'-',lw=2*lw,color=col_p_gain,zorder=-10)
          lines['pd_out'] = ax0.plot(trial['time_'],sgn*sc*(pd_gain_state)+jump,'--',lw=2*lw,color=col_pd_gain,zorder=-10)
        # out
        #ax0.plot(trial['time_'],sc*2*jump,'k--',lw=lw,zorder=-10,alpha=alpha_trials)
        lines['ref'] = ax0.plot(trial['time_'],sgn*sc*trial['ref_']+jump,lw=2*lw,color=col_ref,zorder=-10)
        lines['out'] = ax0.plot(trial['time_'],sgn*sc*trial['out_']+jump,'-',lw=lw,color=col_out,zorder=0,alpha=alpha_trials)
        if s == '+':
          xlabel_out = 'up'
          yticklabels = None
        elif s == '-':
          xlabel_out = 'down'
          yticklabels = []
        else:
          xlabel_out = 'pooled up/down'
          yticklabels = []
        util['format_axes'](ax0,title=u''+title+' '+vf+' '+s,
                            xlim=xlim,ylim=ylim_out,
                            xlabel=xlabel_out,ylabel=ylabel_out,
                            xticklabels=[],yticklabels=yticklabels)
        if j[1:] not in outs:
          outs[j[1:]] = []
        outs[j[1:]].append(sgn*sc*trial['out_'][samps]+jump)
        # inp
        if vf == 'fo':
          pred = old_div(np.diff(sgn*sc*trial['ref_']), np.diff(trial['time_']))
          pred = np.hstack((pred,[0.]))
        elif vf == 'zd12':
          if jump > .15:
            continue
          _,pred = pred_zd12(trial['time_'],trial['state_'][0],trial['ref_'])
          pred *= sgn
          #plt.clf()
          #plt.subplot(3,1,1);
          #plt.plot(_)
          #plt.subplot(3,1,2)
          #plt.plot(trial['ref_'],lw=4,color=col_ref)
          #plt.plot(np.dot(_[:,:2],[.5,.5]))
          #plt.subplot(3,1,3)
          #plt.plot(pred)
          #1/0
        elif vf == 'so':
          pred = old_div(np.diff(np.diff(sgn*sc*trial['ref_'])), np.diff(trial['time_'])[1:]**2)
          pred = np.hstack((pred,[0.,0.]))
        if vf == 'fo' and do_gains:
          lines['p_inp']  = ax1.plot(trial['time_'],sgn*sc*p_gain_inp,'-',lw=2*lw,color=col_p_gain,zorder=-10)
          lines['pd_inp'] = ax1.plot(trial['time_'],sgn*sc*pd_gain_inp,'--',lw=2*lw,color=col_pd_gain,zorder=-10)
        lines['pred'] = ax1.plot(trial['time_'],pred,'-',lw=2*lw,color=col_ref,zorder=-10)
        lines['inp']  = ax1.plot(trial['time_'],sgn*sc*trial['inp_'],'-',lw=lw,color=col_out,zorder=0,alpha=alpha_trials)
        if s == '+':
          xlabel_inp = ''
          yticklabels = None
        elif s == '-':
          xlabel_inp = 'time (sec)'
          yticklabels = []
        else:
          xlabel_inp = ''
          yticklabels = []
        util['format_axes'](ax1,xlabel=xlabel_inp,
                            xlim=xlim,ylim=ylim_inp,
                            ylabel=ylabel_inp,
                            yticklabels=yticklabels)
        if j[1:] not in inps:
          inps[j[1:]] = []
        inps[j[1:]].append(sgn*sc*trial['inp_'][samps])
        #
      # distributions
      ax0,ax1 = axs[vf][s]
      for jump in jumps:
        if vf == 'zd12' and jump > 0.15:
          continue
        outs_ = []; inps_ = []
        for sgn in ['+','-']:
          if sgn in s:
            outs_.append(outs[sgn+str(jump)])
            inps_.append(inps[sgn+str(jump)])
        outs_ = np.vstack(outs_)
        inps_ = np.vstack(inps_)
        if len(outs_) == 0:
          continue
        #
        if do_bootstrap_means:
          bootstrap_means = util['bootstrap_mean'](outs_)
          out = np.percentile(bootstrap_means,prcs,axis=0)
          #bootstrap_trials = util['bootstrap_trials'](outs[str(jump)])
          #out = np.percentile(bootstrap_trials,[50,1,99],axis=0)
        else:
          out = np.percentile(outs_,prcs,axis=0)
        lines['out_fill'] = ax0.fill_between(times,out[1],out[2],color=col_out,zorder=10,alpha=alpha_fill)
        lines['out_bd']   = ax0.plot(times,out[1:].T,'--',lw=1*lw,color=col_out,zorder=10)
        lines['out_mean'] = ax0.plot(times,out[0],   '-', lw=2*lw,color=col_out,zorder=10)
        #
        if do_bootstrap_means:
          bootstrap_means = util['bootstrap_mean'](inps_)
          inp = np.percentile(bootstrap_means,prcs,axis=0)
        else:
          inp = np.percentile(inps_,prcs,axis=0)
        lines['inp_fill'] = ax1.fill_between(times,inp[1],inp[2],color=col_inp,zorder=10,alpha=alpha_fill)
        lines['inp_bd']   = ax1.plot(times,inp[1:].T,'--',lw=1*lw,color=col_inp,zorder=10)
        lines['inp_mean'] = ax1.plot(times,inp[0],   '-', lw=2*lw,color=col_inp,zorder=10)
      # legend
      if s == '-':
        lines['ref'][0].set_label('reference')
        lines['out_mean'][0].set_label('operator average')
        #lines['out_fill'].set_label('operator 50%')
        lines['out_bd'][0].set_label('operator quartiles')
        if vf == 'fo' and do_gains:
          lines['p_inp'][0].set_label('P feedback')
          lines['pd_inp'][0].set_label('PD feedback')
          ls = (lines['ref'][0],lines['out_mean'][0],lines['out_bd'][0],lines['p_inp'][0],lines['pd_inp'][0])
          lb = ['reference','operator average','operator quartiles','P feedback','PD feedback']
        else:
          ls = (lines['ref'][0],lines['out_mean'][0],lines['out_bd'][0])
          lb = ['reference','operator average','operator quartiles']
        leg_pos = (0.5,1.05)
        ax0.legend(ls,lb,ncol=6,loc='lower center',bbox_to_anchor=leg_pos)
  #
  return figs

def visualization(subject,protofile):
  ids = []; scales = []; jumps = []
  gen = trial_gen(subject,protofile)
  for trial in gen:
    id = trial['id']
    scale = trial['scale']
    sys,jump,i = id.split('_')
    if i[1:] in '0123456789' and sys in ['fo'] and jump[-1] in '12':
      ids.append(id)
      scales.append(scale)
      jumps.append(float(jump[1:]))
  #
  return dict(ids=ids,scales=scales,jumps=jumps)

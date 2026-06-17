from __future__ import division
from __future__ import absolute_import
from past.utils import old_div
import sys

import numpy as np
import pylab as plt
import matplotlib 
from matplotlib import rc

from . import globals

from .dynamics import fo, so, zd11, zd12

from .references import sum_of_sines_ramp as sos
from .references import zero as zero
refs = dict(sos=sos,zero=zero)

# vector fields
vfs = ['so']
#vfs = ['fo']
#vfs = ['fo','so']
#vfs = ['fo']
#
states = dict(fo=[0.],so=[0.,0.])
#states = dict(fo=[0.],so=[1.,0.]) # DEBUG
# time to complete task
dt = 1.
seed = 49
np.random.seed(seed)
#
period = 20 # sec
f_base = 1./period # Hz
# TODO go up to 3--5Hz -- check that Sam can track, and check when becomes sub-pixel
primes = np.asarray([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199])
f_max = 2 # max Hz of signal # fo
f_max = 1 # max Hz of signal # so
p_max = np.nonzero(primes*f_base <= f_max)[0][-1]
#p_max = 1 # DEBUG
f_primes = np.asarray(primes[:p_max]) # prime multiples of f_base frequency
#
frequencies = f_primes*f_base
frequencies_r = frequencies.copy()
frequencies_d = frequencies.copy()
#
#print 'p_max = ',p_max,', primes[p_max] = ',primes[p_max]
amplitudes = 1./f_primes; amplitudes /= amplitudes.sum() # confine signal to [-1,+1]
amplitudes_r = amplitudes.copy()
amplitudes_d = amplitudes.copy()
#
num_refs = 4
phase_shifts_r = np.random.rand(num_refs,len(f_primes)) # phase ranges from 0 to 1
# only first disturbance signal differs from reference signals
phase_shifts_d = phase_shifts_r.copy()
phase_shifts_d[0] = np.random.rand(len(f_primes))
#
ramp = 0.25*period
duration = 2*period + ramp
#
trial = dict(ramp=ramp,duration=duration)
t = np.arange(ramp,ramp+period,globals.STEP)
dt = np.gradient(t)
# DEBUG 
#phase_shifts_r[0] = 0 # fo
#phase_shifts_r[0] = 0.25 # so
#amplitudes_d = 2*np.pi*frequencies*amplitudes_r # fo
#amplitudes_d = -((2*np.pi*frequencies)**2)*amplitudes_r # so
#phase_shifts_d[0] = phase_shifts_r[0] + 0.25 # fo
#phase_shifts_d[0] = phase_shifts_r[0] # so
# PLOT
#r = sos(t,trial,None,frequencies_r,amplitudes_r,phase_shifts_r[0])
#dr = np.gradient(r)/dt
#ddr = np.gradient(dr)/dt
#d = sos(t,trial,None,frequencies_d,amplitudes_d,phase_shifts_d[0])
#plt.figure(1); plt.clf()
#plt.plot(t,r,label='r')
#plt.plot(t,np.cumsum(d)*dt,'--',lw=6,label='cumsum(d)') # fo
##plt.plot(np.cumsum(dt),1+np.cumsum(np.cumsum(d)*dt)*dt,'--',lw=6,label='1+cumsum**2(d)') # so
##plt.plot(t,1.+np.cumsum(np.cumsum(ddr)*dt)*dt,'-.',lw=6,label='1+cumsum**2(ddr)')
#plt.plot(t,d,'--',lw=6,label='d')
#plt.plot(t,dr,label='dr') # fo
##plt.plot(t,ddr,label='ddr') # so
#plt.legend()
#sys.exit(0)
#
scale = dict(fo=0.,so=0.)
for _,phase_shift in enumerate(phase_shifts_r):
  t = np.arange(ramp,ramp+period,globals.STEP)
  dt = np.diff(t)
  r = sos(t,trial,None,frequencies_r,amplitudes_r,phase_shift)
  dr = old_div(np.diff(r),dt)
  ddr = old_div(np.diff(dr),dt[1:])
  #
  scale['fo'] = max(scale['fo'],np.abs(dr).max())
  scale['so'] = max(scale['so'],np.abs(ddr).max())
#for phase_shift in phase_shifts_d:
#  trial = dict(ramp=ramp,duration=duration)
#  t = np.arange(ramp,ramp+period,globals.STEP)
#  d = np.abs(sos(t,trial,None,frequencies_d,amplitudes_d,phase_shift))
#  scale['fo'] = max(scale['fo'],d.max())
#  scale['so'] = max(scale['so'],d.max())
#
def trial_gen(subject,protofile):
  for vf in vfs:
    for assay,num_reps,ref_,dis_ in [(0,0,'sos','zero'),
                                     (1,num_refs,'zero','sos'),
                                     (2,0,'sos','sos'),
                                     (3,num_refs,'sos','zero'),
                                     (4,0,'sos','sos'),
                                     ]:
      for s in [+1,-1]:
        for shift_id in np.hstack((np.random.permutation(np.arange(1,num_reps)),0)):
          # alternate frequencies when reference and disturbance are both active
          if ref_ == 'sos' and dis_ == 'sos':
            if s > 0:
              sines_r = np.arange(p_max)[0::2]
              sines_d = np.arange(p_max)[1::2]
            elif s < 0:
              sines_r = np.arange(p_max)[1::2]
              sines_d = np.arange(p_max)[0::2]
          else:
            sines_r = np.arange(p_max) 
            sines_d = np.arange(p_max) 
          #
          ref = lambda t,trial,x=None : refs[ref_](t,trial,x,
                                                   frequencies_r[sines_r],
                                                   s*amplitudes_r[sines_r],
                                                   phase_shifts_r[shift_id][sines_r])
          dis = lambda t,trial,x=None : refs[dis_](t,trial,x,
                                                   frequencies_d[sines_r],
                                                   s*amplitudes_d[sines_r],
                                                   phase_shifts_d[shift_id][sines_r])
          #
          id = '%s_r-%s_d-%s_s%d_p%da%d_%+d' % (vf,ref_,dis_,seed,shift_id,assay,s)
          state = states[vf]
          out = lambda x : x[0]
          #
          trial.update(dict(id=id,init=state,vf=vf,ref=ref,dis=dis,out=out,scale=scale[vf]))
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
ylim_out = (-1.,+1.)
#
prc = 0
prcs = [50,old_div(prc,2),100-old_div(prc,2)] 
do_bootstrap_means = False
#
def analysis(trials,title='',rescale=False,**util):
  #
  ids = sorted(trials.keys())
  #
  time_ = trials[ids[0]]['time_']
  samps = np.arange((time_ >= ramp).nonzero()[0][0], (time_ <= time_[-1]).nonzero()[0][-1])
  times = time_[samps]
  xlim = (times[0],times[-1])
  # 
  figs = dict()
  axs = dict()
  lines = dict()
  #
  for vi,vf in enumerate(vfs):
    inps,outs,refs = dict(),dict(),dict()
    #
    ylim_inp = scale[vf] * (3./2.) * np.array([-1.,+1.])
    #
    figs[vf] = plt.figure(vi,figsize=(20,12)); plt.clf()
    axs[vf] = dict()
    axs[vf]['r-sos_d-zero'] = [plt.subplot(4,3,1),plt.subplot(4,3,4),plt.subplot(4,3,7),plt.subplot(4,3,10)]
    axs[vf]['r-zero_d-sos'] = [plt.subplot(4,3,2),plt.subplot(4,3,5),plt.subplot(4,3,8),plt.subplot(4,3,11)]
    axs[vf]['r-sos_d-sos']  = [plt.subplot(4,3,3),plt.subplot(4,3,6),plt.subplot(4,3,9),plt.subplot(4,3,12)]
    for _ in [None]:#s in axs[vf].keys():
      for i,id in enumerate(ids):
        subj,proto,_ = id.split('_',2)
        if not proto == 'su17':
          continue
        subj,proto,v,r,d,seed,p,sgn = id.split('_')
        if not v == vf:
          continue
        rd = r+'_'+d
        trial = trials[id]
        ax0,ax1,ax2,ax3 = axs[vf][rd]
        #
        # out
        #ax0.plot(trial['time_'],sc*2*jump,'k--',lw=lw,zorder=-10,alpha=alpha_trials)
        if p[:2] == 'p0':
          sgn = int(sgn)
          lines['ref'] = ax0.plot(trial['time_'],sgn*trial['ref_'],lw=2*lw,color=col_ref,zorder=-10)
          lines['out'] = ax0.plot(trial['time_'],sgn*trial['out_'],'-',lw=lw,color=col_out,zorder=0,alpha=alpha_trials)
          if r == 'r-sos' and d == 'd-zero':
            title_out = 'tracking'
            yticklabels = None#[]
            ylabel_inp = r'input ($u$)'
            ylabel_out = r'output ($y$)'
          elif r == 'r-zero' and d == 'd-sos':
            title_out = 'disturbance'
            yticklabels = None#[]
            ylabel_inp = r''
            ylabel_out = r''
          elif r == 'r-sos' and d == 'd-sos':
            title_out = 'tracking + disturbance'
            yticklabels = None#[]
            ylabel_inp = r''
            ylabel_out = r''
          util['format_axes'](ax0,do_title=True,
                              #title=u''+title+' '+vf+' -- '+title_out,                              
                              title=u''+vf+' -- '+title_out,                              
                              xlim=xlim,ylim=ylim_out,
                              xlabel='',ylabel=ylabel_out,
                              xticklabels=[],yticklabels=yticklabels)
          # collect outputs to create distribution later
          if rd not in outs:
            outs[rd] = []
          outs[rd].append(sgn*trial['out_'][samps])
          if rd not in refs:
            refs[rd] = []
          if rd == 'r-sos_d-zero':
            refs[rd].append(sgn*trial['ref_'][samps])
            if vf == 'fo':
              pred = sgn*(old_div(np.diff(trial['ref_']), np.diff(trial['time_'])))[samps]
            elif vf == 'so':
              pred = sgn*(old_div(np.diff(np.diff(trial['ref_'])), np.diff(trial['time_'])[1:]**2))[samps[:-1]]
              pred = np.hstack((pred,pred[-1]))
          elif rd == 'r-zero_d-sos':
            refs[rd].append(-sgn*trial['dis_'][samps])
            pred = -sgn*trial['dis_'][samps]
          elif rd == 'r-sos_d-sos':
            refs[rd].append(sgn*trial['ref_'][samps])
            if vf == 'fo':
              pred = (sgn*(old_div(np.diff(trial['ref_']), np.diff(trial['time_'])))[samps] 
                      - sgn*trial['dis_'][samps])
            elif vf == 'so':
              pred = (sgn*(old_div(np.diff(np.diff(trial['ref_'])), np.diff(trial['time_'])[1:]**2))[samps[:-1]]
                      - sgn*trial['dis_'][samps[:-1]])
              pred = np.hstack((pred,pred[-1]))

          # inp
          lines['pred'] = ax1.plot(times,pred,'-',lw=2*lw,color=col_ref,zorder=-10)
          xlabel_inp = 'time (sec)'
          util['format_axes'](ax1,xlabel=xlabel_inp,
                              xlim=xlim,ylim=ylim_inp,
                              ylabel=ylabel_inp,
                              yticklabels=yticklabels)
          # collect inputs to create distribution later
          if rd not in inps:
            inps[rd] = []
          inps[rd].append(sgn*trial['inp_'][samps])
          #
      for rd in ['r-sos_d-zero','r-zero_d-sos','r-sos_d-sos']:
        # distributions
        ax0,ax1,ax2,ax3 = axs[vf][rd]
        outs_ = np.vstack(outs[rd])
        refs_ = np.vstack(refs[rd])
        inps_ = np.vstack(inps[rd])
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
        # frequencies
        L = times.size
        xlabel_freq = r'frequency ($\times$ base)'
        if rd == 'r-sos_d-zero':
          ylabel_abs = 'magnitude'
          ylabel_ang = 'phase'
          yticklabels = None
          usr_fft_ = np.fft.fft(outs_)[:,:old_div(L,2)]
          sys_fft_ = np.fft.fft(refs_)[:,:old_div(L,2)]
        elif rd == 'r-sos_d-sos':
          ylabel_abs = ''
          ylabel_ang = ''
          yticklabels = None
          usr_fft_ = np.fft.fft(outs_)[:,:old_div(L,2)]
          sys_fft_ = np.fft.fft(refs_)[:,:old_div(L,2)]
        elif rd == 'r-zero_d-sos':
          ylabel_abs = ''
          ylabel_ang = ''
          yticklabels = None
          usr_fft_ = np.fft.fft(inps_)[:,:old_div(L,2)]
          sys_fft_ = np.fft.fft(refs_)[:,:old_div(L,2)]
        freqs = old_div(old_div(np.arange(old_div(L,2)),(np.median(np.diff(times))*L)),f_base)
        if do_bootstrap_means:
          bootstrap_means = util['bootstrap_mean'](old_div(np.abs(usr_fft_),L))
          usr_fft_abs = np.percentile(bootstrap_means,prcs,axis=0)
        else:
          usr_fft_abs = old_div(np.percentile(np.abs(usr_fft_),prcs,axis=0),L)
        # abs
        if rd == 'r-sos_d-sos':
          sys_fft_abs = old_div(np.abs(sys_fft_).sum(axis=0),L)
          ax2.plot(freqs,old_div(np.abs(usr_fft_).T,L),color=col_out,zorder=10)
          ax2.plot(freqs,sys_fft_abs,lw=2*lw,color=col_ref)
        else:
          sys_fft_abs = old_div(np.abs(sys_fft_.mean(axis=0)),L)
          ax2.fill_between(freqs,usr_fft_abs[1],usr_fft_abs[2],color=col_out,zorder=10,alpha=alpha_fill)
          ax2.plot(freqs,usr_fft_abs[1:].T,'--',lw=1*lw,color=col_out,zorder=10)
          ax2.plot(freqs,usr_fft_abs[0],   '-', lw=2*lw,color=col_out,zorder=10)
          ax2.plot(freqs,sys_fft_abs,lw=2*lw,color=col_ref)
        xticks = [0] + f_primes
        xlim_freq = (0,35)
        ylim_abs = ax2.get_ylim()
        util['format_axes'](ax2,xlabel='',ylabel=ylabel_abs,
                            xlim=xlim_freq,ylim=ylim_abs,
                            xticks=xticks,
                            yticklabels=yticklabels)
        # ang
        # TODO look up how to compute dispersion using circular statistics
        _ = (old_div(usr_fft_,sys_fft_)); _ /= np.abs(_)
        usr_fft_ang = np.angle(_.mean(axis=0))
        _ = sys_fft_; _ /= np.abs(_)
        sys_fft_ang = np.angle(_.mean(axis=0))
        #1/0
        #ax3.fill_between(freqs,usr_fft_ang[1],usr_fft_ang[2],color=col_out,zorder=10,alpha=alpha_fill)
        #ax3.plot(freqs,usr_fft_ang[1:].T,'--',lw=1*lw,color=col_out,zorder=10)
        #ax3.plot(freqs,usr_fft_ang[0],   '-', lw=2*lw,color=col_out,zorder=10)
        ax3.plot(freqs[2*f_primes],usr_fft_ang[2*f_primes],'.-', lw=2*lw,ms=10,color=col_out,zorder=10)
        #ax3.plot(freqs,sys_fft_ang,lw=2*lw,color=col_ref)
        ylim_ang = (-np.pi,+np.pi)
        util['format_axes'](ax3,xlabel=xlabel_freq,ylabel=ylabel_ang,
                            xlim=xlim_freq,ylim=ylim_ang,
                            xticks=xticks,
                            yticklabels=yticklabels)
      # legend
      #if s == '-':
      #  lines['ref'][0].set_label('reference')
      #  lines['out_mean'][0].set_label('operator average')
      #  #lines['out_fill'].set_label('operator 50%')
      #  lines['out_bd'][0].set_label('operator quartiles')
      #  if vf == 'fo' and do_gains:
      #    lines['p_inp'][0].set_label('P feedback')
      #    lines['pd_inp'][0].set_label('PD feedback')
      #    ls = (lines['ref'][0],lines['out_mean'][0],lines['out_bd'][0],lines['p_inp'][0],lines['pd_inp'][0])
      #    lb = ['reference','operator average','operator quartiles','P feedback','PD feedback']
      #  else:
      #    ls = (lines['ref'][0],lines['out_mean'][0],lines['out_bd'][0])
      #    lb = ['reference','operator average','operator quartiles']
      #  leg_pos = (0.5,1.05)
      #  ax0.legend(ls,lb,ncol=6,loc='lower center',bbox_to_anchor=leg_pos)
  plt.tight_layout()
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

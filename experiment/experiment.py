#!/usr/bin/python

import warnings
warnings.filterwarnings("error")

import sys
import os
import glob
import time
import serial
import serial.tools.list_ports
import importlib

import numpy as np
#import pylab as plt
from matplotlib import pyplot as plt
import pygame

from protocols.globals import *

from lib.slider import sliderUSB as slider

args = sys.argv

help = """
usage:
  experiment subject protocol [port]

data will be stored in
  data/subject

print available serial ports by running
  lib/print_serial
"""

if len(args) < 2:
  print '\nABORT -- no subject specified'
  print help
  sys.exit(0)

if len(args) < 3:
  print '\nABORT -- no protocol specified'
  print help
  sys.exit(0)

subject = args[1]
protocol = args[2]

subject_dir = os.path.join('data',subject)

# debugging
def dbg(s):
  print(s)

#COM_PORT = 'COM9'
#COM_PORT = '/dev/cu.usbmodem141131' # Sam home
#COM_PORT = '/dev/cu.usbmodem141111' # Sam office
COM_PORT = None
if len(args) >= 4:
  COM_PORT = args[3]
elif 0:
  arduinoPorts = [p.device
    for p in serial.tools.list_ports.comports()
    if 'Arduino' in p.description
  ]
  COM_PORT = arduinoPorts[0]


if COM_PORT is None:
  print 'WARN -- COM_PORT is None, using keyboard for input'
else:
  try:
    joy = slider(port=COM_PORT)
  except:
    print 'ABORT -- slider not detected at COM_PORT =',COM_PORT
    sys.exit(0)

  dbg('COM_PORT='+COM_PORT)
  joy.startArduino()

if not os.path.exists(subject_dir):
  os.mkdir(subject_dir)

from protocols import dynamics
proto = importlib.import_module('protocols.'+protocol)

trial_gen = proto.trial_gen(subject,protocol)

# --- helper functions for output to command line and graphical display

# draw rectangle using frame-relative (x,y) coordinates
def draw_rect(scr, col, (x,y,w,h), thk):
  c,r = xy2px([[x,y]],size,SC)[0]
  return pygame.draw.rect(scr,col,(c,r,int(SC*w),int(SC*h)),int(SC*thk))

def draw_circle(scr, col, (x,y), r, thk):
  px = xy2px([[x,y]],size,SC)[0]
  return pygame.draw.circle(scr,col,px,int(SC*r),int(SC*thk))

def draw_lines(scr, col, clo, pts, thk):
  pxs = xy2px(pts,size,SC)
  return pygame.draw.lines(scr,col,clo,pxs,int(SC*thk))

#def draw_line(scr, col, start_pos, end_pos, thk):
#  pxs = xy2px(pts,size,SC)
#  return pygame.draw.line(scr,col,start_pos,end_pos,pxs,int(SC*thk))

def draw_polygon(scr, col, pts, thk):
  pxs = xy2px(pts,size,SC)
  return pygame.draw.polygon(scr,col,pxs,int(SC*thk))

def draw_ref(scr, col, pts, thk):
  pts = np.array(pts)
  diff = np.diff(pts,axis=0)
  perp = np.dot(diff,np.asarray([[0,1],[-1,0]]))
  nml = perp / np.sqrt(np.sum(perp**2,axis=1))[:,np.newaxis]
  pts_u = pts[:-1] + .2*thk * nml
  pts_d = pts[:-1] - .2*thk * nml
  pxs = xy2px(np.vstack((pts_u,pts_d[::-1])),size,SC)
  return pygame.draw.polygon(scr,col,pxs,0)
  #return pygame.draw.lines(scr,GOLD,False,xy2px(pts,size,SC),10)

class Point:
  # constructed using a normal tuple
  def __init__(self, point_t = (0,0)):
    self.x = float(point_t[0])
    self.y = float(point_t[1])
  # define all useful operators
  def __add__(self, other):
    return Point((self.x + other.x, self.y + other.y))
  def __sub__(self, other):
    return Point((self.x - other.x, self.y - other.y))
  def __mul__(self, scalar):
    return Point((self.x*scalar, self.y*scalar))
  def __div__(self, scalar):
    return Point((self.x/scalar, self.y/scalar))
  def length(self):
    return int(np.sqrt(self.x**2 + self.y**2))
  # get back values in original tuple format
  def get(self):
      return (self.x, self.y)

def draw_dashed_line(surf, color, start_pos, end_pos, width=1, dash_length=10):
  origin = Point(xy2px([start_pos],size,SC)[0])
  target = Point(xy2px([end_pos],size,SC)[0])
  displacement = target - origin
  length = displacement.length()
  slope = displacement/length

  for index in range(0, length/dash_length, 2):
    start = origin + (slope *    index    * dash_length)
    end   = origin + (slope * (index + 1) * dash_length)
    pygame.draw.line(surf, color, start.get(), end.get(), width)

def datestring(t=None,sec=False):
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

  ye = '%04d'%t.tm_year
  mo = '%02d'%t.tm_mon
  da = '%02d'%t.tm_mday
  ho = '%02d'%t.tm_hour
  mi = '%02d'%t.tm_min
  se = '%02d'%t.tm_sec
  if not sec:
    se = ''

  return ye+mo+da+'-'+ho+mi+se




# --- set up graphical display window

# global variables
FULLSCREEN = False
#FULLSCREEN = True

if FULLSCREEN:
  flags = pygame.FULLSCREEN #| pygame.DOUBLEBUF
else:
  os.environ['SDL_VIDEO_CENTERED'] = '1'
  os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d'%(0,0)
  flags = pygame.RESIZABLE | pygame.NOFRAME #| pygame.DOUBLEBUF
screen = pygame.display.set_mode(size,flags)
screen.set_alpha(None)
HEIGHT = size[0] / RATIO
SC = float(HEIGHT)
fader = pygame.Surface(size, pygame.SRCALPHA)
RANGE = np.asarray(px2xy([[0.0, 0.0], size], size, SC))
fader = pygame.Surface(size, pygame.SRCALPHA)
pygame.display.set_caption("hcps v0.1")
pygame.event.set_allowed([pygame.QUIT,
                          pygame.KEYDOWN,
                          pygame.KEYUP,
                          pygame.VIDEORESIZE,
                          pygame.MOUSEBUTTONDOWN,
                          pygame.MOUSEBUTTONUP,
                         ])
done = False
clock = pygame.time.Clock()

# --- variables and functions for ship and reference


oldrects = []

def rescale_inp(inp,MIN=SLIDER_MIN,MAX=SLIDER_MAX):
  return 2 * ( (inp - MIN) / (MAX - MIN) - .5) * trial['scale'] * (3./2.)

try:
  trial = trial_gen.next()
  if not ALLOW_DUPLICATES:
    while len(glob.glob(os.path.join(subject_dir,'*'+protocol+'_'+str(trial['id'])+'.npz'))) > 0:
      dbg('SKIP subject='+subject_dir+'; protocol='+protocol+'_'+str(trial['id']))
      trial = trial_gen.next()
    dbg('RUN subject='+subject_dir+'; protocol='+protocol+'_'+str(trial['id']))
except StopIteration:
  done = True

trial_run = trial

trial_reset = dict(duration=np.inf,
                   id=trial['id'],
                   scale=.5,
                   init=[0.],
                   dis=lambda t,x,_ : 0.,
                   out=lambda x : x[0],
                   ref=lambda t,_ : 0.*np.asarray(t),
                   vf='fo')

def init(trial):
  state = trial['init']
  steps = 0
  frame = 0
  _time = steps * STEP
  time_ = [_time]
  realtime_ = [time.time()]
  state_ = [state]
  inp_ = [inp(time_[-1],state_[-1])]
  dis_ = [trial['dis'](time_[-1],trial,state_[-1])]
  out_ = [trial['out'](state)]
  ref_ = [trial['ref'](time_[-1],trial)*(RNG[1,1]-RNG[0,1])]
  return state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_

def save(sfx='',csv=True,**trial_data):
  di = subject_dir
  id = str(trial['id'])
  fi = protocol+'_'+id+sfx
  if glob.glob(os.path.join(di,'*'+fi+'.npz')):
    dbg('WARN -- trial repeated')
  ds = datestring(sec=True)
  fi = ds+'_'+fi
  dbg('SAVE '+os.path.join(di,fi))
  np.savez(os.path.join(di,fi),filename=fi,**trial_data)
  #err = np.sqrt(np.mean((trial_data['ref_']-trial_data['state_'])**2))
  #dbg('RMSE: '+ err)
  if csv:
    time = trial_data['time_']
    realtime = trial_data['realtime_']
    ref = trial_data['ref_']
    inp = trial_data['inp_']
    dis = np.asarray(trial_data['dis_']).flatten()
    state = np.asarray(trial_data['state_'])
    d = np.vstack((time,realtime,ref,inp,dis,state.T)).T
    np.savetxt(os.path.join(di,fi)+'.csv',d,delimiter=',',
               header='\n'.join(10*['']+['time,realtime,ref,inp,dis,state...']))


# -- initialize system
if COM_PORT is None:
  inp = lambda time,state : 0.
else:
  inp = lambda time,state : rescale_inp(joy.grabData()[1])
#
TRIAL_STATE = 'reset1'
trial = trial_reset
# DEBUG
#TRIAL_STATE = 'run'
#trial = trial_run
#
state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_ = init(trial)

# runge-kutta numerical integration assuming constant input
def rk_(vf,t,x,u,d=None,dt=1.):
  dx1 = vf( t, x, u, d ) * dt
  dx2 = vf( t+.5*dt, x+.5*dx1, u, d ) * dt
  dx3 = vf( t+.5*dt, x+.5*dx2, u, d ) * dt
  dx4 = vf( t+dt, x+dx3, u, d ) * dt
  dx = (1./6.)*( dx1 + 2*dx2 + 2*dx3 + dx4 )
  return x + dx


if PLOT:
  plt.ion()

  fig = plt.figure(1,figsize=(size[0]/100,size[1]/100))
  plt.clf()
  plt.grid('on'); plt.axis('equal')
  plt.xlim(RNG[:,0])
  plt.ylim(RNG[:,1])


# ---- game loop
frame = 0
t0 = time.time()
while not done:
  # only handle events every SLIDER_SPT ticks
  if steps % SLIDER_SPT == 0:
    # --- handle events (keyboard / mouse input)
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        dbg("QUIT")
        done = True
      elif event.type == pygame.VIDEORESIZE:
        size = list(event.size)
        HEIGHT = size[0]/RATIO
        size = (RATIO*HEIGHT,HEIGHT)
        SC = float(HEIGHT)
        screen = pygame.display.set_mode(size,pygame.RESIZABLE)
        fader = pygame.Surface(size, pygame.SRCALPHA)
        RNG = np.asarray(px2xy([[0.,0.],size],size,SC))
        dbg("RESIZE %s"%str(size))
      elif event.type == pygame.KEYDOWN:
        #dbg("KEYDOWN")
        if event.key in [pygame.K_SPACE,pygame.K_p]:
          if PAUSE:
            dbg("UNPAUSE")
          if not PAUSE:
            dbg("PAUSE")
          PAUSE = not PAUSE
        elif event.key == pygame.K_k:  # Skip current trial
            dbg("SKIP - moving to next trial")
            # Save the skipped trial data with a skip marker
            # Move to next trial
            try:
                trial = next(trial_gen)
                if not ALLOW_DUPLICATES:
                    while (
                        len(
                            glob.glob(
                                os.path.join(
                                    subject_dir,
                                    "*" + protocol + "_" + str(trial["id"]) + ".npz",
                                )
                            )
                        )
                        > 0
                    ):
                        dbg(
                            "SKIP subject="
                            + subject_dir
                            + "; protocol="
                            + protocol
                            + "_"
                            + str(trial["id"])
                        )
                        trial = next(trial_gen)
                dbg(
                    "RUN subject="
                    + subject_dir
                    + "; protocol="
                    + protocol
                    + "_"
                    + str(trial["id"])
                )
                TRIAL_STATE = "reset1"
                trial_run = trial
                trial_reset["init"] = [0.0]  # Reset with zero input
                trial = trial_reset
                (
                    state,
                    steps,
                    _time,
                    time_,
                    realtime_,
                    state_,
                    inp_,
                    dis_,
                    out_,
                    ref_,
                ) = init(trial)
                FADE = -1
            except StopIteration:
                dbg("No more trials - quitting")
                done = True
        elif event.key == pygame.K_RIGHT:
          dbg("RIGHT")
          inp = lambda time,state : +ACCEL
        elif event.key == pygame.K_LEFT:
          dbg("LEFT")
          inp = lambda time,state : -ACCEL
        elif event.key == pygame.K_DOWN:
          dbg("DOWN")
          inp = lambda time,state : 0.
        elif event.key == pygame.K_g:
          pass
        elif event.key == pygame.K_f:
          if FULLSCREEN:
            screen = pygame.display.set_mode(size,pygame.RESIZABLE)
            FULLSCREEN = False
          else:
            screen = pygame.display.set_mode(size,pygame.FULLSCREEN)
            FULLSCREEN = True
        elif event.key == pygame.K_s and COM_PORT is not None:
          inp = lambda time,state : rescale_inp(joy.grabData()[1])
        elif event.key == pygame.K_r:
          cmt = raw_input("> why reject? ")
          save(time_=time_,realtime_=realtime_,state_=state_,
               inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,
               sfx="_rej",cmt=cmt)
          trial = trial_reset
          state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_ = init(trial)
        elif event.key in [pygame.K_q,pygame.K_ESCAPE]:
          dbg("QUIT")
          done = True
      #elif event.type == pygame.KEYUP:
      #  #dbg("KEYUP")
      #  if event.key in [pygame.K_LEFT,pygame.K_RIGHT]:
      #    dbg("0.")
      #    inp = lambda time,state : 0.
      elif event.type == pygame.MOUSEBUTTONDOWN:
        pass
        #dbg("MOUSEBUTTONDOWN")
      elif event.type == pygame.MOUSEBUTTONUP:
        pass
        #dbg("MOUSEBUTTONUP")

  _inp = inp(time_[-1],state_[-1])
  _dis = trial['dis'](time_[-1],trial,state_[-1])

  if not PAUSE:
    # duration
    if TRIAL_STATE == 'run' and _time + SHIP_SHIFT > trial['duration']:
      save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_)
      try:
        trial = trial_gen.next()
        if not ALLOW_DUPLICATES:
          while len(glob.glob(os.path.join(subject_dir,'*'+protocol+'_'+str(trial['id'])+'.npz'))) > 0:
            dbg('SKIP subject='+subject_dir+'; protocol='+protocol+'_'+str(trial['id']))
            trial = trial_gen.next()
        dbg('RUN subject='+subject_dir+'; protocol='+protocol+'_'+str(trial['id']))
        TRIAL_STATE = 'reset1'
        trial_reset['init'] = [_inp]
        trial = trial_reset
        state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_ = init(trial)
        FADE = -1
      except StopIteration:
        done = True

    if TRIAL_STATE == 'reset1':
      if (np.abs(out_[-FPS*SLIDER_SPT:]).max() > .5):
        save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,sfx="_rst1")
        TRIAL_STATE = 'reset2'
        trial_reset['init'] = [_inp]
        trial = trial_reset
        state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_ = init(trial)
        FADE = -1

    if TRIAL_STATE == 'reset2':
      if (np.abs(out_[-FPS*SLIDER_SPT:]).max() < RAD_SYS):
        save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,sfx="_rst2")
        TRIAL_STATE = 'run'
        trial = trial_run
        state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_ = init(trial)
        FADE = -1

    ## out of bounds
    #if np.abs(out_[-1]) > 0.5:
    #  save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,sfx="_oob")
    #  state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_ = init(trial)
    #  PAUSE = True

    ## saturated input
    #if np.abs(_inp/(trial['scale']*3./2.)) > .95:
    #  save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,sfx="_max")
    #  state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_ = init(trial)
    #  PAUSE = True

    if TRIAL_STATE in ['run','reset1','reset2']:
      steps += 1
      _time = steps * STEP
      # --- update game state
      if TRIAL_STATE in ['run']:
        state = rk_(eval('dynamics.'+trial['vf']),_time,state,_inp,_dis,STEP)
      else:
        state = [_inp]
      # --- record game state
      realtime_.append(time.time())
      time_.append(_time)
      state_.append(state)
      inp_.append(_inp)
      dis_.append(_dis)
      out_.append(trial['out'](state))
      ref_.append(trial['ref']([SHIP_SHIFT + _time,_time],trial)[0]*(RNG[1,1]-RNG[0,1]))

  # only draw every SLIDER_SPT ticks -- SPT = samples per tick
  if steps % SLIDER_SPT == 0 and not done:

    if TRIAL_STATE in ['run']:
      bg_color = BLACK
      ref_color = GOLD
      out_color = PURPLE
    elif TRIAL_STATE in ['reset1','reset2']:
      bg_color = BLACK
      ref_color = GOLD
      out_color = PURPLE

    # --- draw
    screen.fill(bg_color) # this will occlude any drawing above


    if SHOW_GRID:
      xticks = np.arange(-RATIO/2,RATIO/2,.5)
      for g in xticks:
        draw_dashed_line(screen, DARKGREY, (g,YRNG[0]), (g,YRNG[1]),
                         width=1, dash_length=10)
      #yticks = np.hstack((-np.arange(-(SHIP_SHIFT-GRID_SPACE),-(XRNG[0]-GRID_SPACE),GRID_SPACE)[::-1],np.arange(SHIP_SHIFT,XRNG[1]+GRID_SPACE,GRID_SPACE)))# - np.mod(_time,GRID_SPACE)
      yticks = np.arange(-1,1,.5)
      for g in yticks:
        draw_dashed_line(screen, DARKGREY, (XRNG[0],g), (XRNG[1],g),
                         width=1, dash_length=10)
    #
    rects = []
    if TRIAL_STATE in ['run']:
      #TIMES = np.linspace(XRNG[0]-2*THK_REF,XRNG[1]+THK_REF,size[0]/10)
      TIMES = np.linspace(-0.5-THK_REF,0.5+THK_REF,size[0]/10)
      pts = np.vstack((trial['ref'](TIMES + _time,trial),TIMES)).T
      #pts = pts[np.all(np.logical_not(np.isnan(pts),),axis=1)]
      pts = pts[np.all(np.isfinite(pts),axis=1)]
      # reference curve
      if SHOW_REF:
        rects.append(draw_ref(screen, ref_color, pts, THK_REF))
      # reference glyph
      rects.append(draw_rect(screen, ref_color, (ref_[-1]+SHIP_SHIFT-RAD_SYS,RAD_SYS, 2*RAD_SYS, 2*RAD_SYS), THK_SYS))
    elif TRIAL_STATE in ['reset1']:
      rects.append(draw_rect(screen, ref_color, (-RATIO/2,0.5,RATIO/2-.5,1.),THK_SYS))
      rects.append(draw_rect(screen, ref_color, (.5,1.,RATIO/2-.5,+RATIO/2),THK_SYS))
    elif TRIAL_STATE in ['reset2','done']:
      rects.append(draw_rect(screen, ref_color, (-RAD_SYS,1.,2*RAD_SYS,+2.),THK_SYS))
    # output glyph
    #rects.append(draw_rect(screen, out_color, (out_[-1]+SHIP_SHIFT-.5*RAD_SYS,1.5*RAD_SYS, 1*RAD_SYS, 3*RAD_SYS), THK_SYS))
    pts = [out_[-1],0] + np.asarray([[-RAD_SYS,0],[0,RAD_SYS],[RAD_SYS,0],[0,-RAD_SYS]])
    rects.append(draw_polygon(screen, out_color, pts, THK_SYS))
    if SHOW_INP:
      # input
      rects.append(draw_lines(screen, WHITE, False, [[0.,INP_SHIFT],[_inp/(trial['scale']),INP_SHIFT]], THK_INP))
    if SHOW_DIS:
      # input
      rects.append(draw_lines(screen, WHITE, False, [[0.,DIS_SHIFT],[_dis/(trial['scale']),DIS_SHIFT]], THK_DIS))

    activerects = rects + oldrects
    activerects = filter(bool, activerects)

    if PLOT:
      plt.clf()
      plt.grid('on'); plt.axis('equal')
      plt.plot(TIMES,trial['ref'](TIMES + _time,trial)*(RNG[1,1]-RNG[0,1]),'.-',lw=10,color=_GOLD)
      plt.plot(SHIP_SHIFT,state[0],'.',ms=40,color=_PURPLE)
      if SHOW_GRID:
        plt.xticks(xticks)
      plt.xlim(XRNG)
      plt.ylim(YRNG)
      plt.yticks([])
      plt.draw()

    if FADE > 0:
      fader.fill((0.,0.,0.,FADE))
      screen.blit(fader,(0,0))
      FADE += 20
      if FADE >= 255:
        FADE = 0

    if FADE < 0:
      fader.fill((0.,0.,0.,255+FADE))
      screen.blit(fader,(0,0))
      FADE -= 20
      if FADE < -255:
        FADE = 0

    # --- update screen
    pygame.display.flip()

    #dbg('t = %0.1f, FPS = %0.1f' % (clock.get_time(),
    #                                clock.get_fps()))

  while (time.time() - t0 < frame / float(FPS)):
      pass

  # --- limit update rate to FPS
  frame += 1
  clock.tick_busy_loop()

  if (steps+1) % 60 == 0:
    dbg('%d t = %0.1f, FPS = %0.1f, inp = %0.1f, state = %s' %
        (len(inp_), time_[-1], clock.get_fps(), _inp, state))

if COM_PORT is not None:
  joy.stopArduino()
pygame.display.quit()
pygame.quit()
sys.exit(0)

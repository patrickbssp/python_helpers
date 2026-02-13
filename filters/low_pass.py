#!/bin/python3

import numpy as np
import matplotlib.pyplot as plt
import control

dB=True
Hz=True
deg=True

#G = 0.2*control.tf([0.5,1],[1.5,0.5,1])
G = control.tf([1],[0.5,1])
print(G)

w = np.logspace(-1.5,1,200)

control.bode(G,w,Hz=Hz,dB=dB,deg=deg)

plt.tight_layout()

ax1,ax2 = plt.gcf().axes     # get subplot axes

plt.sca(ax1)                 # magnitude plot
#plt.plot(plt.xlim(),[Kcu,Kcu],'r--')
#plt.plot([wc,wc],plt.ylim(),'r--')
plt.title("Gain at Crossover = {0:.3g}".format(1))

plt.sca(ax2)                 # phase plot
#plt.plot(plt.xlim(),[-180,-180],'r--')
#plt.plot([wc,wc],plt.ylim(),'r--')
plt.title("Crossover Frequency = {0:.3g} rad/sec".format(1))
plt.show()

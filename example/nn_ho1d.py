import torch
from torch.autograd import Variable
from pyCHAMP.wavefunction.neural_wf_base import NEURAL_WF, WaveNet1D
from pyCHAMP.solver.neural_net import NN, QMCLoss
from pyCHAMP.sampler.metropolis import METROPOLIS_TORCH as METROPOLIS
import matplotlib.pyplot as plt

import numpy as np

def plot_wf(net,X):
    pos = net.sample(ntherm=-1)
    vals = net.wf(X)
    kin = net.wf.kinetic_autograd(X)
    vn = vals.detach().numpy().flatten()
    xn = X.detach().numpy().flatten()
    g = np.gradient(vn,xn)
    h = np.gradient(g,xn)
    plt.hist(pos.detach().numpy())
    plt.plot(xn,vn)
    plt.plot(xn,kin.detach().numpy())
    plt.plot(xn,h)
    plt.show()



X = Variable(torch.linspace(-5,5,100).view(100,1))
X.requires_grad = True

wf = NEURAL_WF(ndim=1,nelec=1)

sampler = METROPOLIS(nwalkers=100, nstep=1000, 
                     step_size = 3., nelec = wf.nelec, 
                     ndim = wf.ndim, domain = {'min':-5,'max':5})

net = NN(wf=wf,sampler=sampler)
#pos = net.sample(ntherm=-1)
net.train(10,ntherm=-1)






# net.train(50,ntherm=-1)
# vals = net.wf(X)
# plt.plot(X.detach().numpy(),vals.detach().numpy())
# plt.show()


# pos = net.sample(ntherm=0)
# pos = pos.reshape(sampler.nwalkers,-1,wf.ndim_tot)
# var = net.observalbe(net.wf.variance,pos)
# plt.plot(var)
# plt.show()




# pos = net.sample(ntherm=0)
# pos = pos.reshape(100,100,6)
# var_ = net.observalbe(net.wf.variance,pos)
# plt.plot(var_)
# plt.show()

# net.train(50,pos=pos,ntherm=-1)
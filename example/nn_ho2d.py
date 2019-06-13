import torch
from torch import nn
from torch.autograd import Variable
import torch.nn.functional as F
from torch.nn.utils.weight_norm import weight_norm
import torch.optim as optim

from pyCHAMP.wavefunction.neural_wf_base import NEURAL_WF_BASE
from pyCHAMP.wavefunction.rbf import RBF
from pyCHAMP.solver.deepqmc import DeepQMC

from pyCHAMP.sampler.metropolis import METROPOLIS_TORCH as METROPOLIS
from pyCHAMP.solver.mesh import regular_mesh_2d as regmesh2d

from pyCHAMP.solver.plot import plot_wf_2d

import numpy as np


class RBF_HO2D(NEURAL_WF_BASE):

    def __init__(self,nelec=1,ndim=2,ncenter=[3,3]):
        super(RBF_HO2D,self).__init__(nelec,ndim)

        # get the RBF centers
        points = regmesh2d(xmin=-5,xmax=5,nx=ncenter[0],
                           ymin=-5,ymax=5,ny=ncenter[1]) 

        self.centers = torch.tensor(points)
        self.ncenter = len(self.centers)

        # define the RBF layer
        self.rbf = RBF(self.ndim_tot, self.ncenter,centers=self.centers,opt_centers=False)
        
        # define the fc layer
        self.fc = nn.Linear(self.ncenter, 1, bias=False)

        # initiaize the fc layer
        self.fc.weight.data.fill_(0.)
        self.fc.weight.data[0,4] = 1.
        #nn.init.uniform_(self.fc.weight,0,1)

    def forward(self,x):
        ''' Compute the value of the wave function.
        for a multiple conformation of the electrons

        Args:
            parameters : variational param of the wf
            pos: position of the electrons

        Returns: values of psi
        '''

        batch_size = x.shape[0]
        x = x.view(batch_size,self.ndim)
        x = self.rbf(x)
        x = self.fc(x)
        return x.view(-1,1)

    def nuclear_potential(self,pos):
        '''Compute the potential of the wf points
        Args:
            pos: position of the electron

        Returns: values of V * psi
        '''
        return (0.5*pos**2).sum(1).view(-1,1)

    def electronic_potential(self,pos):
        '''Compute the potential of the wf points
        Args:
            pos: position of the electron

        Returns: values of Vee * psi
        '''
        return 0

def ho2d_sol(pos):
    '''Analytical solution of the 1D harmonic oscillator.'''
    vn = torch.exp(-0.5*pos**2).prod(1).view(-1,1)
    return vn/torch.norm(vn)

# wavefunction
wf = RBF_HO2D(ndim=2,nelec=1,ncenter=[3,3])

#sampler
sampler = METROPOLIS(nwalkers=250, nstep=1000, 
                     step_size = 3., nelec = wf.nelec, 
                     ndim = wf.ndim, domain = {'min':-5,'max':5})

# optimizer
opt = optim.Adam(wf.parameters(),lr=0.005)

# network
net = DeepQMC(wf=wf,sampler=sampler,optimizer=opt)
pos = None
obs_dict = None

plot_wf_2d(net,sol=ho2d_sol,nx=25,ny=25)

# plt.ion()
# fig = plt.figure()

# for i in range(1):

#     net.wf.fc.weight.requires_grad = True
#     net.wf.rbf.centers.requires_grad = False

#     pos,obs_dict = net.train(250,
#              batchsize=250,
#              pos = pos,
#              obs_dict = obs_dict,
#              resample=100,
#              ntherm=-1,
#              loss = 'variance',
#              sol=ho2d_sol,
#              fig=fig)

    # net.wf.fc.weight.requires_grad = False
    # net.wf.rbf.centers.requires_grad = True

    # pos,obs_dict = net.train(10,
    #          batchsize=250,
    #          pos = pos,
    #          obs_dict = obs_dict,
    #          resample=100,
    #          ntherm=-1,
    #          loss = 'variance',
    #          sol=ho1d_sol,
    #          fig=fig)

#net.plot_results(obs_dict,ho1d_sol,e0=0.5)






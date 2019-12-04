import torch
from torch import nn
import torch.nn.functional as F
from torch.autograd import grad, Variable

import numpy as np
from pyscf import scf, gto, mcscf

from tqdm import tqdm
from time import time

def btrace(M):
    return torch.diagonal(M,dim1=-2,dim2=-1).sum(-1)

def bproj(M,P):
    return P.transpose(1,2) @ M @ P

class KineticPooling(nn.Module):

    """Comutes the kinetic energy of each configuration using the trace trick."""

    def __init__(self,configs,nup,ndown):
        super(KineticPooling, self).__init__()

        self.configs = configs
        self.nconfs = len(configs[0])
        

        self.nup = nup
        self.ndown = ndown
        self.nelec = nup+ndown

        self.index_up = torch.arange(nup)
        self.index_down = torch.arange(nup,nup+ndown)

    def forward(self,MO, d2MO, return_local_energy=False):

        ''' Compute the kinetic energy using the trace trick
        for a product of spin up/down determinant
        .. math::

            T \Psi  =  T Dup Ddwn 
                    = -1/2 Dup * Ddown  *( \Delta_up Dup  + \Delta_down Ddwn)

            using the trace trick with D = |A| :
                O(D) = D trace(A^{-1} O(A))
                and Delta_up(D_down) = 0

        Args:
            A : matrix of MO vals (Nbatch, Nelec, Nmo)
            d2A : matrix of \Delta MO vals (Nbatch, Nelec, Nmo)
        Return:
            K : T Psi (Nbatch, Ndet)
        '''

        nbatch = MO.shape[0]
        out = torch.zeros(nbatch,self.nconfs)
                
        for ic,(cup,cdown) in enumerate(zip(self.configs[0],self.configs[1])):

            Aup = MO.index_select(1,self.index_up).index_select(2,cup)
            Adown = MO.index_select(1,self.index_down).index_select(2,cdown)
            
            iAup = torch.inverse(Aup)
            iAdown = torch.inverse(Adown)
            
            d2Aup = d2MO.index_select(1,self.index_up).index_select(2,cup)
            d2Adown = d2MO.index_select(1,self.index_down).index_select(2,cdown)
            out[:,ic] = (btrace(iAup@d2Aup) + btrace(iAdown@d2Adown))

            if not return_local_energy:
                pd = torch.det(Aup) * torch.det(Adown)
                out[:,ic] *= pd

        return -0.5*out

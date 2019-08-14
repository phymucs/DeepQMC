import torch
from torch import nn
import torch.nn.functional as F
from torch.autograd import grad, Variable

import numpy as np
from pyscf import scf, gto, mcscf

from tqdm import tqdm
from time import time


class BatchDeterminant(torch.autograd.Function):

    @staticmethod
    def forward(ctx,input):

        # LUP decompose the matrices
        inp_lu, pivots = input.lu()
        perm, inpl, inpu = torch.lu_unpack(inp_lu,pivots)
        
        # get the number of permuations
        s = (pivots != torch.tensor(range(1,input.shape[1]+1)).int()).sum(1).float()

        # get the prod of the diag of U
        d = torch.diagonal(inpu,dim1=-2,dim2=-1).prod(1)

        # assemble
        det = ((-1)**s * d)
        ctx.save_for_backward(input,det)

        return det

    @staticmethod
    def backward(ctx, grad_output):
        '''using jaobi's formula 
            d det(A) / d A_{ij} = adj^T(A)_{ij} 
        using the adjunct formula
            d det(A) / d A_{ij} = ( (det(A) A^{-1})^T )_{ij}
        '''
        input, det = ctx.saved_tensors
        return (grad_output * det).view(-1,1,1) * torch.inverse(input).transpose(1,2)

class SlaterPooling(nn.Module):

    """Applies a slater determinant pooling in the active space."""

    def __init__(self,configs,nup,ndown):
        super(SlaterPooling, self).__init__()

        self.configs = configs
        self.nconfs = len(configs[0])

        self.index_up = torch.arange(nup)
        self.index_down = torch.arange(nup,nup+ndown)

    def forward(self,input):

        ''' Compute the product of spin up/down determinants
        Args:
            input : MO values (Nbatch, Nelec, Nmo)
        Returnn:
            determiant (Nbatch, Ndet)
        '''
        nbatch = input.shape[0]
        out = torch.zeros(nbatch,self.nconfs)
                
        for ic,(cup,cdown) in enumerate(zip(self.configs[0],self.configs[1])):

            mo_up = input.index_select(1,self.index_up).index_select(2,cup)
            mo_down = input.index_select(1,self.index_down).index_select(2,cdown)

            # a batch version of det is on its way (end July 2019)
            # https://github.com/pytorch/pytorch/issues/7500
            # we'll move to that asap but in the mean time we loop
            #for isample in range(nbatch):
            #    out[isample,ic] = (torch.det(mo_up[isample]) * torch.det(mo_down[isample]))

            # using my own BatchDeterminant
            out[:,ic] = BatchDeterminant.apply(mo_up) * BatchDeterminant.apply(mo_down)

        return out


class ElectronDistance(nn.Module):
    
    def __init__(self,nelec,ndim):
        super(ElectronDistance,self).__init__()
        self.nelec = nelec
        self.ndim = ndim
        
    def forward(self,input):
        '''compute the pairwise distance between two sets of electrons.
        Args:
            input1 (Nbatch,Nelec1*Ndim) : position of the electrons
            input2 (Nbatch,Nelec2*Ndim) : position of the electrons if None -> input1
        Returns:
            mat (Nbatch,Nelec1,Nelec2) : pairwise distance between electrons
        '''

        input = input.view(-1,self.nelec,self.ndim)
        norm = (input**2).sum(-1).unsqueeze(-1)
        dist = norm + norm.transpose(1,2) -2.0 * torch.bmm(input,input.transpose(1,2))

        return dist

class TwoBodyJastrowFactor(nn.Module):

    def __init__(self,nup,ndown):
        super(TwoBodyJastrowFactor, self).__init__()

        self.nup = nup
        self.ndown = ndown
        self.nelec = nup+ndown

        self.weight = Variable(torch.tensor([1.0]))
        self.weight.requires_grad = True

        bup = torch.cat( (0.25*torch.ones(nup,nup),0.5*torch.ones(nup,ndown) ),dim=1)
        bdown = torch.cat( (0.5*torch.ones(ndown,nup),0.25*torch.ones(ndown,ndown) ),dim=1)
        self.static_weight = torch.cat( (bup,bdown),dim=0)

    def forward(self,input):
        
        factors = torch.exp(self.static_weight * input / (1.0 + self.weight * input))
        factors = factors[:,torch.tril(torch.ones(self.nelec,self.nelec))==0].prod(1)
        return factors.view(-1,1)

        #return JastrowFunction.apply(input,self.weight,self.static_weight)

        
class JastrowFunction(torch.autograd.Function):

    @staticmethod
    def forward(ctx,input,weight,static_weight):
        '''Compute the Jastrow factor.
        Args:
            input : Nbatch x Nelec x Nelec (elec distance)
            weight : Nelec, Nelec
            static weight : Float
        Returns:
            jastrow : Nbatch x 1
        '''

        # save the tensors
        ctx.save_for_backward(input,weight,static_weight)

        # all jastrow for all electron pairs
        factors = torch.exp(static_weight * input / (1.0 + weight * input))
        
        # product of the off diag terms 
        nr,nc = input.shape[1], input.shape[2]
        factors = factors[:,torch.tril(torch.ones(nr,nc))==0].prod(1)
        
        return factors.view(-1,1)


    # @staticmethod
    # def backward(ctx,grad_output):
    #     input, weight, static_weight = ctx.saved_tensors
    #     grad_input = (static_weight / (1+weight*input) *( 1 -  input * weight / (1+weight*input) ) )
    #     grad_weight = -(static_weight * input**2 * (1+weight*input)**(-2) )
    #     return grad_output * grad_input, grad_output * grad_weight, None


if __name__ == "__main__":

    # pos = torch.rand(10,12)
    # edist = ElectronDistance.apply(pos)
    # jastrow = TwoBodyJastrowFactor(2,2)
    # val = jastrow(edist)

    x = Variable(torch.rand(10,3,3))
    x.requires_grad = True
    det = BatchDeterminant.apply(x)
    det.backward(torch.ones(10))

    # # LUP decompose the matrices
    # x_lu, pivots = x.lu()
    # perm, xl, xu = torch.lu_unpack(x_lu,pivots)
    
    # # get the number of permuations
    # #s = perm.sum((1,2)) - torch.diagonal(perm,dim1=-2,dim2=-1).sum(1)
    # s = (pivots != torch.tensor(range(1,x.shape[1]+1)).int()).sum(1).float()
    # #s = perm.diagonal(dim1=-2,dim2=-1).fill_(0).sum((1,2))

    # # get the prod of the diag of U
    # d = torch.diagonal(xu,dim1=-2,dim2=-1).prod(1)

    # # assemble
    # det = (-1)**(s) * d

    det_true = torch.tensor([torch.det(xi).item() for xi in x])
    print(det-det_true)
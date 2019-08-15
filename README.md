# DeepQMC

Deep Learning for Quantum Monte Carlo Simulations

## Introduction

DeepQMC allows to leverage deep learning to optimize QMC wave functions. The package offers solutions to optimize particle in a box model and molecular systems. It relies heavily on pytorch for the deep learning part and on pyscf to obtain the first guess of the molecular orbitals. Several MC samplers are implemented :

  * Metropolis-Hasting
  * Hamiltonian Monte-Carlo

and more will be added. Beyond facilitating the optimization of the wave fuction parameters, `autograd` is also leveraged for example to apply the kinetic operator on the wave function.



## Example : Harmonic Oscillator in 1D

We illustrate here how to optimize a simple harmonic oscillator in 1D using DeepQMC. The `pot_func` function defines the potential that is here a simple harmonic oscillator. The `sol_func` function gives the analytical solution of the problem and is only use for plotting purposes.



```python
import torch
import torch.optim as optim

from deepqmc.wavefunction.wf_potential import Potential
from deepqmc.sampler.metropolis import  Metropolis
from deepqmc.solver.deepqmc import DeepQMC
from deepqmc.solver.plot import plot_results_1d, plotter1d

def pot_func(pos):
    '''Potential function desired.'''
    return  0.5*pos**2

def sol_func(pos):
    '''Analytical solution of the 1D harmonic oscillator.'''
    return torch.exp(-0.5*pos**2)

# box
domain, ncenter = {'xmin':-5.,'xmax':5.}, 5

# wavefunction
wf = Potential(pot_func,domain,ncenter,nelec=1)

#sampler
sampler = Metropolis(nwalkers=250, nstep=1000, 
                     step_size = 1., nelec = wf.nelec, 
                     ndim = wf.ndim, domain = {'min':-5,'max':5})

# optimizer
opt = optim.Adam(wf.parameters(),lr=0.01)

# define solver
qmc = DeepQMC(wf=wf,sampler=sampler,optimizer=opt)

# train the wave function
pos,obs_dict = qmc.train(100, loss = 'variance',
                         plot = plotter1d(wf,domain,50,sol=sol_func) )

# plot the final wave function 
plot_results_1d(qmc,obs_dict,domain,50,sol_func,e0=0.5)
```


After defining the domain in `domain` and the number of basis function in `ncenter`, we instantialte the `Potential` wave function class. This class defines a very simple neural network that, given a position computes the value of the wave function at that point. This neural network is composed of a layer of radial basis functions followed by a fully conneted layer to sum them up:

![alt-text](./pics/rbf_nn.png)

The final form of the wave function is then given by :

$$ \Psi(x) = \sum_n \mathcal{G}_n(\theta,x)$$
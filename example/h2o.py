import sys
import torch
from torch import optim
from torch.autograd import Variable
from torch.optim import Adam

from deepqmc.wavefunction.wf_orbital_split import OrbitalSplit
from deepqmc.wavefunction.wf_orbital import Orbital 
from deepqmc.solver.solver_orbital import SolverOrbital
#from deepqmc.solver.solver_orbital_distributed import DistSolverOrbital  as SolverOrbital

from deepqmc.sampler.metropolis import Metropolis
from deepqmc.wavefunction.molecule import Molecule

from deepqmc.solver.plot_orbital import plot_molecule
from deepqmc.solver.plot_orbital import plot_molecule_mayavi as plot_molecule
from deepqmc.solver.plot_data import plot_observable


# define the molecule
#mol = Molecule(atom='water.xyz', basis_type='sto', basis='sz')
mol = Molecule(atom='water_line_small.xyz', unit='angs', 
			   basis_type='gto', basis='sto-3g')

# define the wave function
wf = Orbital(mol,kinetic_jacobi=True,configs='singlet(1,1)')

#sampler
sampler = Metropolis(nwalkers=1000, nstep=50, step_size = 0.5, 
                     ndim = wf.ndim, nelec = wf.nelec, move = 'one')

# optimizer
opt = Adam(wf.parameters(),lr=0.1)

# scheduler
scheduler = optim.lr_scheduler.StepLR(opt,step_size=20,gamma=0.75)

# solver
solver = SolverOrbital(wf=wf,sampler=sampler,optimizer=opt,scheduler=scheduler)
solver.configure(task='wf_opt')
pos = solver.sample()
#pos, e, v = solver.single_point()

# # optimize the geometry
# solver.configure(task='geo_opt')
# solver.observable(['local_energy','atomic_distances'])
# solver.run(5,loss='energy')
# solver.save_traj('h2o_traj.xyz')

# # plot the data
# plot_observable(solver.obs_dict)
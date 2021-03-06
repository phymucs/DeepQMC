from torch import optim
from torch.optim import Adam

from deepqmc.wavefunction.wf_orbital import Orbital
from deepqmc.solver.solver_orbital import SolverOrbital


from deepqmc.sampler.metropolis import Metropolis
#from deepqmc.sampler.metropolis_all_elec import Metropolis
from deepqmc.sampler.generalized_metropolis import GeneralizedMetropolis
from deepqmc.wavefunction.molecule import Molecule

from deepqmc.solver.plot_data import plot_energy

# define the molecule
mol = Molecule(atom='water.xyz', unit='angs',
               calculator='pyscf', basis='sto-3g')

# define the wave function
wf = Orbital(mol, kinetic='jacobi',
             configs='single(2,2)',
             use_jastrow=True)

# sampler
sampler = Metropolis(nwalkers=1000, nstep=2000, step_size=0.5,
                     nelec=wf.nelec, ndim=wf.ndim,
                     init=mol.domain('normal'),
                     move={'type': 'one-elec', 'proba': 'normal'})

# optimizer
opt = Adam(wf.parameters(), lr=0.005)

# scheduler
scheduler = optim.lr_scheduler.StepLR(opt, step_size=20, gamma=0.75)

# solver
solver = SolverOrbital(wf=wf,
                       sampler=sampler,
                       optimizer=opt,
                       scheduler=scheduler)


# # single point
pos, e, v = solver.single_point(ntherm=1500, ndecor=100)

# # sampling traj
# pos = solver.sample(ntherm=500, ndecor=10)
# obs = solver.sampling_traj(pos)
# plot_energy(obs, e0=-74, ax=None)

# # optimize the wave function
# solver.configure(task='wf_opt', freeze=['mo', 'bas_exp'])
# solver.observable(['local_energy'])
# solver.run(15, loss='energy')
# plot_energy(solver.obs_dict, e0=-76.)

# # optimize the geometry
# solver.configure(task='geo_opt')
# solver.observable(['local_energy','atomic_distances'])
# solver.run(5,loss='energy')
# solver.save_traj('h2o_traj.xyz')

# # plot the data
# plot_energy(solver.obs_dict)

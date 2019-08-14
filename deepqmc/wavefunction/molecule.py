import os
import numpy as np
from mendeleev import element
from pyscf import gto,scf
import basis_set_exchange as bse 
import json 

class Molecule(object):

    def __init__(self,atom=None,basis_type='sto',basis='sz'):

        self.atoms_str = atom
        self.basis_type = basis_type.lower()
        self.basis = basis.lower()

        if self.basis_type not in ['sto','gto']:
            raise ValueError("basis_type must be sto or gto")

        # process the atom name/pos
        self.atoms = []
        self.atom_coords = []
        self.nelec = 0
        self.process_atom_str()

        # get the basis folder
        self.basis_path = os.path.dirname(os.path.realpath(__file__))
        self.basis_path = os.path.join(self.basis_path,'atomicdata')
        self.basis_path = os.path.join(self.basis_path,self.basis_type)
        self.basis_path = os.path.join(self.basis_path, basis.upper())

        # init the basis data
        self.nshells = [] # number of shell per atom
        self.index_ctr = [] # index of the contraction
        self.bas_exp = []
        self.bas_coeffs = []
        self.bas_n = []
        self.bas_l = []
        self.bas_m = []

        # utilities dict for extracting data
        self.get_label = {0:'S',1:'P',2:'D'}
        self.get_l = {'S':0,'P':1,'D':2}
        self.mult_bas = {'S':1,'P':3,'D':5}
        self.get_m = {'S':[0],'P':[-1,0,1],'D':[-2,-1,0,1,2]}

        # for cartesian 
        self.get_lmn_cart = {'S': [0,0,0],
                             'P':[[1,0,0],
                                  [0,1,0],
                                  [0,0,1]],
                             'D':[[2,0,0],
                                  [0,2,0],
                                  [0,0,2],
                                  [1,1,0],
                                  [1,0,1],
                                  [0,1,1] ]}

        # read/process basis info
        self.process_basis()

    def process_atom_str(self):

        atoms = self.atoms_str.split(';')
        for a in atoms:
            atom_data = a.split()
            self.atoms.append(atom_data[0])
            x,y,z = float(atom_data[1]),float(atom_data[2]),float(atom_data[3])
            self.atom_coords.append([x,y,z])
            self.nelec += element(atom_data[0]).electrons
        self.natom = len(self.atoms)

    def process_basis(self):
        if self.basis_type == 'sto':
            self._process_sto()

        elif self.basis_type == 'gto':
            self._process_gto()

    def _get_sto_atomic_data(self,at):

        atomic_data = { 'electron_shells':{} }

        # read the atom file
        fname = os.path.join(self.basis_path,at)
        with open(fname,'r') as f:
            data = f.readlines()

        # loop over all the basis
        for ibas in  range(data.index('BASIS\n')+1,data.index('END\n')):

            # split the data
            bas = data[ibas].split()
            
            if len(bas) == 0:
                continue

            bas_name = bas[0]
            zeta = float(bas[1])

            # get the primary quantum number
            n = int(bas_name[0])-1

            if n not in atomic_data['electron_shells']:
                atomic_data['electron_shells'][n] = {'angular_momentum':[],
                                                     'exponents':[],
                                                     'coefficients':[] }

            # secondary qn and multiplicity
            l = self.get_l[bas_name[1]]
            
            # store it
            if l not in atomic_data['electron_shells'][n]['angular_momentum']:
                atomic_data['electron_shells'][n]['angular_momentum'].append(l)
                atomic_data['electron_shells'][n]['coefficients'].append([])
                atomic_data['electron_shells'][n]['exponents'].append([])

            atomic_data['electron_shells'][n]['coefficients'][-1].append(1.)
            atomic_data['electron_shells'][n]['exponents'][-1].append(zeta)

        return atomic_data

    def _process_sto(self):

        # number of orbs
        self.norb = 0

        # loop over all the atoms
        for at in self.atoms:

            data = self._get_sto_atomic_data(at)
            self.nshells.append(0)

            for ishell, shell in data['electron_shells'].items():

                # primary quantum number
                n = ishell

                # loop over the angular momentum
                for iangular, angular in enumerate(shell['angular_momentum']):

                    # secondary qn and multiplicity
                    l = angular
                    mult = self.mult_bas[self.get_label[angular]]
                    nbas = len(shell['coefficients'][0])
                    mvals = self.get_m[self.get_label[angular]]

                    for imult in range(mult):

                        self.norb += 1

                        # store coeffs and exps of the bas
                        self.bas_exp += shell['exponents'][iangular]
                        self.bas_coeffs += shell['coefficients'][iangular]

                        # index of the contraction
                        self.index_ctr += [ self.norb-1 ] * nbas

                        # store the quantum numbers
                        self.bas_n += [n]*nbas
                        self.bas_l += [l]*nbas
                        self.bas_m += [mvals[imult]]*nbas

                    # number of shells
                    self.nshells[-1] += nbas*mult

                
    def _process_gto(self):

        # number of orbs
        self.norb = 0

        # loop over all the atoms
        for at in self.atoms:

            at_num = element(at).atomic_number
            self.nshells.append(0)
            all_bas_names = []

            # import data
            data = json.loads(bse.get_basis(self.basis,elements=[at_num],fmt='JSON'))

            # loop over the electronic shells
            for ishell,shell in enumerate(data['elements'][str(at_num)]['electron_shells']):

                # get the primary number
                n = ishell

                # loop over the angular momentum
                for iangular, angular in enumerate(shell['angular_momentum']):

                    # secondary qn and multiplicity
                    l = angular
                    mult = self.mult_bas[self.get_label[angular]]
                    nbas = len(shell['exponents'])
                    mvals = self.get_m[self.get_label[angular]]

                    for imult in range(mult):

                        self.norb += 1

                        # store coeffs and exps of the bas
                        self.bas_exp += np.array(shell['exponents']).astype('float').tolist()
                        self.bas_coeffs += np.array(shell['coefficients'][iangular]).astype('float').tolist()

                        # index of the contraction
                        self.index_ctr += [ self.norb-1 ] * nbas

                        # store the quantum numbers
                        self.bas_n += [n]*nbas
                        self.bas_l += [l]*nbas
                        self.bas_m += [mvals[imult]]*nbas

                    # number of shells
                    self.nshells[-1] += mult*nbas


    def get_mo_coeffs(self,code='pyscf'):

        if self.basis_type == 'gto':

            if code.lower() not in ['pyscf']:
                raise ValueError(code + 'not currently supported for GTO orbitals')

            if code.lower() == 'pyscf':
                mo = self._get_mo_pyscf()

        elif self.basis_type == 'sto': 

            if code.lower() not in ['pyscf']:
                raise ValueError(code + 'not currently supported for STO orbitals')

            if code.lower() == 'pyscf':
                mo = self._get_mo_pyscf()

        return mo

    def _get_mo_pyscf(self):

        if self.basis_type == 'sto':
            bdict = {'sz':'sto-3g','dz':'sto-3g'}
            pyscf_basis = bdict[self.basis]
        else:
            pyscf_basis = self.basis

        mol = gto.M(atom=self.atoms_str,basis=pyscf_basis)
        rhf = scf.RHF(mol).run()
        return self._normalize_columns(rhf.mo_coeff)

    @staticmethod
    def _normalize_columns(mat):
        norm = np.sqrt( (mat**2).sum(0) )
        return mat / norm


if __name__ == "__main__":

    m1 = Molecule(atom='H 0 0 0; O 0 0 1',basis_type='gto',basis='sto-3g')
    m2 = Molecule(atom='H 0 0 0; O 0 0 1',basis_type='sto',basis='dzp')

    
    


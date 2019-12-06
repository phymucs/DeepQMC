import torch


def SphericalHarmonics(xyz, l, m, derivative=0):
    '''Compute the Real Spherical Harmonics of the AO.
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, distance component of each
              point from each RBF center
        l : array(Nrbf) l quantum number
        m : array(Nrbf) m quantum number
    Returns:
        Y array (Nbatch,Nelec,Nrbf) : value of each SH at each point
    '''

    Y = torch.zeros(xyz.shape[:-1])

    # l=0
    ind = (l == 0).nonzero().view(-1)
    if derivative == 0:
        Y[:, :, ind] = _spherical_harmonics_l0(xyz[:, :, ind, :])
    if derivative == 1:
        Y[:, :, ind] = _nabla_spherical_harmonics_l0(xyz[:, :, ind, :])

    # l=1
    indl = (l == 1)
    if torch.any(indl):
        for mval in [-1, 0, 1]:
            indm = (m == mval)
            ind = (indl*indm).nonzero().view(-1)
            if len(ind > 0):
                if derivative == 0:
                    Y[:, :, ind] = _spherical_harmonics_l1(
                        xyz[:, :, ind, :], mval)
                if derivative == 1:
                    Y[:, :, ind] = _nabla_spherical_harmonics_l1(
                        xyz[:, :, ind, :], mval)
                if derivative == 2:
                    Y[:, :, ind] = _lap_spherical_harmonics_l1(
                        xyz[:, :, ind, :], mval)

    # l=2
    indl = (l == 2)
    if torch.any(indl):
        for mval in [-2, -1, 0, 1, 2]:
            indm = (m == mval)
            ind = (indl*indm).nonzero().view(-1)
            if len(ind > 0):
                if derivative == 0:
                    Y[:, :, ind] = _spherical_harmonics_l2(
                        xyz[:, :, ind, :], mval)
                if derivative == 1:
                    Y[:, :, ind] = _nabla_spherical_harmonics_l2(
                        xyz[:, :, ind, :], mval)
                if derivative == 2:
                    Y[:, :, ind] = _lap_spherical_harmonics_l2(
                        xyz[:, :, ind, :], mval)

    return Y


def _spherical_harmonics_l0(xyz):
    ''' Compute the l=0 Spherical Harmonics
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, of (Point - Center)
    Returns
        Y00 = 1/2 \sqrt(1 / \pi)
    '''

    return 0.2820948 * torch.ones(xyz.shape[:-1])


def _nabla_spherical_harmonics_l0(xyz):
    ''' Compute the nabla of l=0 Spherical Harmonics
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, of (Point - Center)
    Returns
        \nabla * Y00 = 0
    '''
    return torch.zeros(xyz.shape[:-1])


def _lap_spherical_harmonics_l0(xyz):
    ''' Compute the laplacian of l=0 Spherical Harmonics
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, of (Point - Center)
    Returns
        \nabla^2 * Y00 = 0
    '''
    return torch.zeros(xyz.shape[:-1])


def _spherical_harmonics_l1(xyz, m):
    ''' Compute the 1-1 Spherical Harmonics
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, of (Point - Center)
        m : second quantum number (-1,0,1)
    Returns
        Y0-1 = \sqrt(3 / (4\pi)) y/r. (m=-1)
        Y00  = \sqrt(3 / (4\pi)) z/r (m=0)
        Y01  = \sqrt(3 / (4\pi)) x/r. (m=1)
    '''
    index = {-1: 1, 0: 2, 1: 0}
    r = torch.sqrt((xyz**2).sum(3))
    c = 0.4886025119029199
    return c * xyz[:, :, :, index[m]] / r


def _nabla_spherical_harmonics_l1(xyz, m):
    ''' Compute the nabla of 1-1 Spherical Harmonics
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, of (Point - Center)
        m : second quantum number (-1,0,1)
    Returns
        \nabla Y0-1 = \sqrt(3 / (4\pi)) ( 1/r - y (x+y+z)/r^3 ) (m=-1)
        \nabla Y00  = \sqrt(3 / (4\pi)) ( 1/r - z (x+y+z)/r^3 ) (m= 0)
        \nabla Y01  = \sqrt(3 / (4\pi)) ( 1/r - x (x+y+z)/r^3 ) (m= 1)
    '''
    index = {-1: 1, 0: 2, 1: 0}
    r = torch.sqrt((xyz**2).sum(3))
    r3 = r**3
    c = 0.4886025119029199
    return c * (1./r - xyz[:, :, :, index[m]] * xyz.sum(3) / r3)


def _lap_spherical_harmonics_l1(xyz, m):
    ''' Compute the laplacian of 1-1 Spherical Harmonics
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, of (Point - Center)
        m : second quantum number (-1,0,1)
    Returns
        Y0-1 = \sqrt(3 / (4\pi)) ( -2y/r^3 ) (m=-1)
        Y00  = \sqrt(3 / (4\pi)) ( -2z/r^3 ) (m= 0)
        Y01  = \sqrt(3 / (4\pi)) ( -2x/r^3 ) (m= 1)
    '''
    index = {-1: 1, 0: 2, 1: 0}
    r = torch.sqrt((xyz**2).sum(3))
    r3 = r**3
    c = 0.4886025119029199
    return c * (- 2*xyz[:, :, :, index[m]] / r3)


def _spherical_harmonics_l2(xyz, m):
    ''' Compute the l=2 Spherical Harmonics
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, of (Point - Center)
        m : second quantum number (-2,-1,0,1,2)
    Returns
        Y2-2 = 1/2\sqrt(15/\pi) xy/r^2
        Y2-1 = 1/2\sqrt(15/\pi) yz/r^2
        Y20  = 1/4\sqrt(5/\pi) (-x^2-y^2+2z^2)/r^2
        Y21  = 1/2\sqrt(15/\pi) zx/r^2
        Y22  = 1/4\sqrt(15/\pi) (x*x-y*y)/r^2
    '''

    r2 = (xyz**2).sum(-1)

    if m == 0:
        c0 = 0.31539156525252005
        return c0 * (-xyz[:, :, :, 0]**2 - xyz[:, :, :, 1]**2 + 2*xyz[:, :, :, 2]**2) / r2
    if m == 2:
        c2 = 0.5462742152960396
        return c2 * (xyz[:, :, :, 0]**2 - xyz[:, :, :, 1]**2) / r2
    else:
        cm = 1.0925484305920792
        index = {-2: [0, 1], -1: [1, 2], 1: [2, 0]}
        return cm * xyz[:, :, :, index[m][0]] * xyz[:, :, :, index[m][1]] / r2


def _nabla_spherical_harmonics_l2(xyz, m):
    ''' Compute the nabla of l=2 Spherical Harmonics
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, of (Point - Center)
        m : second quantum number (-2,-1,0,1,2)
    Returns
        Y2-2 = 1/2\sqrt(15/\pi) (x+y)/r^2 - 2 * xy (x+y+z)/r^3
        Y2-1 = 1/2\sqrt(15/\pi) (y+z)/r^2 - 2 * yz (x+y+z)/r^3
        Y20  = 1/4\sqrt(5/\pi) ( (-2x-2y+4z)/r^2 - 2 *(-xx - yy + 2zz) * (x+y+z)/r3 )
        Y21  = 1/2\sqrt(15/\pi) (x+z)/r^2 - 2 * xz (x+y+z)/r^3
        Y22  = 1/4\sqrt(15/\pi)  ( 2(x-y)/r^2 - 2 *(xx-yy)(x+y+z)/r^3  )
    '''

    r = torch.sqrt((xyz**2).sum(3))
    r2 = r**2
    r3 = r**3

    if m == 0:
        c0 = 0.31539156525252005
        return c0 * ((-2 * xyz[:, :, :, 0] - 2 * xyz[:, :, :, 1] + 4 * xyz[:, :, :, 2]) / r2
                     - 2 * (-xyz[:, :, :, 0]**2 - xyz[:, :, :, 1]**2 + 2*xyz[:, :, :, 2]**2) * xyz.sum(3) / r3)
    if m == 2:
        c2 = 0.5462742152960396
        return c2 * (2 * (xyz[:, :, :, 0]-xyz[:, :, :, 1])/r2
                     - 2 * (xyz[:, :, :, 0]**2-xyz[:, :, :, 1]**2) * xyz.sum(3) / r3)
    else:
        cm = 1.0925484305920792
        index = {-2: [0, 1], -1: [1, 2], 1: [2, 0]}
        return cm * ((xyz[:, :, :, index[m][0]] + xyz[:, :, :, index[m][1]]) / r2
                     - 2 * xyz[:, :, :, index[m][0]]*xyz[:, :, :, index[m][1]] * xyz.sum(3) / r3)


def _lap_spherical_harmonics_l2(xyz, m):
    ''' Compute the nabla of l=2 Spherical Harmonics
    Args:
        xyz : array (Nbatch,Nelec,Nrbf,Ndim) x,y,z, of (Point - Center)
        m : second quantum number (-2,-1,0,1,2)
    Returns
        Y2-2 = 1/2\sqrt(15/\pi) -6xy/r^4
        Y2-1 = 1/2\sqrt(15/\pi) -6yz/r^4

        Y20  = 1/4\sqrt(5/\pi) ( 6/r6 * (xx+yy)^2 - zz * (xx + yy -2zz))

        Y21  = 1/2\sqrt(15/\pi) -6zx/r^4
        Y22  = 1/4\sqrt(15/\pi)  ( 6/r6 * ( zz*(yy-xx)  +y^4 - x^4  )  )
    '''

    r = torch.sqrt((xyz**2).sum(3))
    r4 = r**4
    r6 = r**6

    if m == 0:
        c0 = 0.31539156525252005
        xyz2 = xyz**2
        return c0 * (6/r6 * (xyz2[:, :, :, :2].sum(-1))**2 - xyz2[:, :, :, 2] * (xyz2[:, :, :, 0]+xyz2[:, :, :, 1]-2*xyz2[:, :, :, 2]))
    if m == 2:
        c2 = 0.5462742152960396
        xyz2 = xyz**2
        return c2 * (6/r6 * xyz2[:, :, :, 2]*(xyz2[:, :, :, 1]-xyz2[:, :, :, 0]) + xyz2[:, :, :, 1]**2-xyz2[:, :, :, 0]**2)
    else:
        cm = 1.0925484305920792
        index = {-2: [0, 1], -1: [1, 2], 1: [2, 0]}
        return cm * (- 6 * xyz[:, :, :, index[m][0]] * xyz[:, :, :, index[m][1]] / r4)


if __name__ == "__main__":

    Nbatch = 10
    Nelec = 5
    Nrbf = 10
    Ndim = 3

    xyz = torch.rand(Nbatch, Nelec, Nrbf, Ndim)
    l = torch.randint(0, 3, (Nrbf,))
    m = torch.zeros(Nrbf)
    for i in range(Nrbf):
        li = l[i]
        m[i] = torch.randint(-li, li+1, (1,))

    Y = SphericalHarmonics(xyz, l, m)

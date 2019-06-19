import os
import math
import numpy as np
import UVspec3

home = os.environ['HOME']+'/'


#LSST_Altitude = 2.750  # in k meters from astropy package (Cerro Pachon)
#OBS_Altitude = str(LSST_Altitude)


#CTIO_Altitude = 2.200  # in k meters from astropy package (Cerro Pachon)
#OBS_Altitude = str(CTIO_Altitude)

#OHP_Altitude = 0.65   # in km
#OBS_Altitude=str(OHP_Altitude)

PDM_Altitude= 2.8905 # in km
OBS_Altitude=str(PDM_Altitude)

############################################################################
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(f):
        os.makedirs(f)
#########################################################################


def read_uu_map(fo, nphi, numu):

    # The reading of radiances is a bit complicated. They all come on one line for each
    # wavelength and altitude when "output_user uu" is specified. In addition, the first
    # number is for the phi[0], the second for phi[1] and so on. Since we have many umu
    # and two phis (0 and 180 to get the fill principal plane for umu between 0 and 90)
    # in the input file the following will unpack, sort and get the right viewing angles.
    

    f = open(fo,'r')
    uu = np.zeros((numu,nphi))

    for line in f:
        l   = line.split()
        uur = l[6:len(l)]
    f.close()

    #    print len(uur)

    i  = 0
    iu = 0
    while iu < numu:
        j  = 0
        while j < nphi:
            #            print i, iu, j
            uu[iu][j] = uur[i]
            i = i + 1
            j = j + 1
        iu = iu + 1

    return uu

def write_uu_map(fo, uu, nphi, numu):

    f = open(fo,'w')
    i  = 0
    iu = 0
    while iu < numu:
        j  = 0
        while j < nphi:
            f.write( ' {0:13.6e}'.format(uu[iu][j]))
            j = j + 1
        f.write( '\n')
        iu = iu + 1
    f.close()


#####################################################################

if __name__ == "__main__":

    ensure_dir('input')
    ensure_dir('output')

    # Set up type of run
    runtype='clearsky' #'aerosol_default' #
    sza=30
    
    if runtype=='clearsky':
        outtext='clearsky'
    elif runtype=='aerosol_default':
        outtext='aerosol_default'

    # LibRadTran installation directory
    home = os.environ['HOME']+'/'
    libradtranpath = os.getenv('LIBRADTRANDIR')+'/'

    print(libradtranpath)

        
    #libradtranpath = home+'MacOSX/External/libRadtran'
    libradtranpathbin = libradtranpath
    libradtranpathdata = libradtranpath+'/share/libRadtran/data'
    libradtranpathatm = libradtranpathdata+'/atmmod'

    # Rough estimate of center wavlengths of LSST filters. Should use filter functions
    # instead.
    wavelengths = np.array([350, 450, 620, 750, 880, 980])

    for wavelength in wavelengths:
        verbose=True
        uvspec = UVspec3.UVspec()

        uvspec.inp["data_files_path"] = libradtranpath + 'data'
        uvspec.inp["atmosphere_file"] = libradtranpath + 'data/atmmod/' + 'afglus' + '.dat'


        #uvspec.inp["data_files_path"]  =  libradtranpathdata
        #uvspec.inp["atmosphere_file"] = libradtranpathatm+'/afglus.dat'
        uvspec.inp["albedo"]           = '0.2'
        uvspec.inp["rte_solver"] = 'disort'

        phis = ''
        angle = 0.0
        nphi=0
        while angle <=360.0:
            phis = phis+' '+str(angle)
            angle = angle + 10.0
            nphi=nphi+1

        umus = ''
        angle = 180.0
        numu=0
        while angle > 90:
            umu   = math.cos(angle*math.pi/180)
            umus  = umus+' '+str(umu)
            angle = angle -2.5
            numu=numu+1
        

        if runtype=='aerosol_default':
            uvspec.inp["aerosol_default"] = ''
        uvspec.inp["umu"] = umus
        uvspec.inp["phi"] = phis
        uvspec.inp["output_user"] = 'lambda zout eglo edir edn eup uu'
        uvspec.inp["zout"] = 'boa'
        #uvspec.inp["altitude"] = '0.600'
        uvspec.inp["altitude"] =OBS_Altitude
        #uvspec.inp["source"] = 'solar '+libradtranpathdata+'/solar_flux/kurudz_1.0nm.dat'
        uvspec.inp["source"] = 'solar ' + libradtranpath + 'data/solar_flux/kurudz_1.0nm.dat'
        uvspec.inp["sza"]        = str(sza)
        uvspec.inp["phi0"]       = '0'
        uvspec.inp["wavelength"]       = str(wavelength)
        uvspec.inp["output_quantity"] = 'reflectivity' #'transmittance' #
        uvspec.inp["quiet"] = ''

        if "output_quantity" in uvspec.inp.keys():
            outtextfinal=outtext+'_'+uvspec.inp["output_quantity"]

        inp = 'input/uvspec_{:5.1f}_{:4.1f}'.format(wavelength,sza)+'_'+outtextfinal+'.inp'
        out = 'output/uvspec_{:5.1f}_{:4.1f}'.format(wavelength,sza)+'_'+outtextfinal+'.out'

        uvspec.write_input(inp)
        uvspec.run(inp,out,verbose,path=libradtranpathbin)

        # Read output
        uu0 = read_uu_map(out,nphi,numu)
        #
        out0uu = out+'_uu'
        write_uu_map(out0uu,uu0,nphi,numu)


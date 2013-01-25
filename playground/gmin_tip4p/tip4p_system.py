import numpy as np

from pygmin.potentials import GMINPotential
import gmin_ as GMIN
from pygmin.angleaxis import RBSystem
from copy import deepcopy
import tip4p
from pygmin.utils import rotations
from pygmin.takestep import RotationalDisplacement
from pygmin.systems import BaseSystem, dict_copy_update, BaseParameters
from pygmin.transition_states import NEB, InterpolatedPathDensity

from pygmin.optimize import fire, mylbfgs
from pygmin import defaults

from pygmin.angleaxis.aamindist import *
from pygmin.angleaxis import MinPermDistAACluster, ExactMatchAACluster
from pygmin.angleaxis.aautils import TakestepAA
from pygmin.landscape import smoothPath

class TIP4PSystem(BaseSystem):
    def __init__(self):
        BaseSystem.__init__(self)
        
        GMIN.initialize()
        pot = GMINPotential(GMIN)
        coords = pot.getCoords()        
        nrigid = coords.size / 6

        print "I have %d water molecules in the system"%nrigid
        print "The initial energy is", pot.getEnergy(coords)

        water = tip4p.water()
        #water.S *= 2
        
        system = RBSystem()
        system.add_sites([deepcopy(water) for i in xrange(nrigid)])
        
        self.aasystem = system
        self.potential = pot
        self.nrigid = nrigid
                
        self.params.basinhopping["temperature"]=8.
        self.params.takestep["translate"]=0.0
        self.params.takestep["rotate"]=1.6
        
        self.params.double_ended_connect.local_connect_params.nrefine_max = 5
        
        NEBparams = self.params.double_ended_connect.local_connect_params.NEBparams
        NEBparams.max_images=200
        NEBparams.image_density=3.0
        NEBparams.iter_density=10
        NEBparams.k = 400.
        NEBparams.adjustk_freq = 5
        NEBparams.reinterpolate = 50
        NEBparams.adaptive_nimages = True
        NEBparams.adaptive_niter = True
        NEBparams.interpolator=self.aasystem.interpolate
        NEBparams.verbose = -1
        NEBparams.quenchRoutine = mylbfgs
        quenchParams = NEBparams.NEBquenchParams
        #quenchParams["nsteps"] = 1000
        quenchParams["iprint"] = -1
        quenchParams["maxstep"] = 0.1
        quenchParams["maxErise"] = 1000
        quenchParams["tol"] = 1e-6
        
        
        tsSearchParams = self.params.double_ended_connect.local_connect_params.tsSearchParams

        tsSearchParams["nfail_max"]=20
        self.params.double_ended_connect.local_connect_params.NEBparams.distance=self.aasystem.neb_distance


    def get_potential(self):
        return self.potential
    
    def get_random_configuration(self):
        coords = 5.*np.random.random(6*self.nrigid)
        ca = self.aasystem.coords_adapter(coords)
        for p in ca.rotRigid:
            p = rotations.random_aa()
        return coords
    
    def get_takestep(self, **kwargs):
        """return the takestep object for use in basinhopping, etc.
        
        default is random displacement with adaptive step size 
        adaptive temperature
        
        See Also
        --------
        pygmin.takestep
        """
        kwargs = dict_copy_update(self.params["takestep"], kwargs)
        return TakestepAA(self.aasystem, **kwargs)
    
    def get_compare_exact(self, **kwargs):
        return ExactMatchAACluster(self.aasystem, accuracy=0.1, **kwargs)
    
    def get_mindist(self, **kwargs):
        return MinPermDistAACluster(self.aasystem,accuracy=0.1, **kwargs)
    
    def get_orthogonalize_to_zero_eigenvectors(self):
        return self.aasystem.orthogopt
#    
#    def createNEB(self, coords1, coords2):
#        minima = self.database.minima()
#        dc = self.get_double_ended_connect(minima[0], minima[1], self.database)
#        
#        local_connect = dc._getLocalConnectObject()
#        return local_connect._getNEB(self.get_potential(), coords1, coords2,
#                                     **local_connect.NEBparams)
#    
#        pot = self.get_potential()
#        #dist = np.linalg.norm(coords1- coords2)
#        #if dist < 1.: dist = 1
#        #image_density = 15.
#        
#        #path = InterpolatedPathDensity(coords1, coords2, 
#        #                               distance=dist, density=image_density)
#        path = tip4p.get_path(self.aasystem, coords1, coords2, self.params.neb.nimages)
#                              
#        if(self.params.neb.aadist):
#            return NEB(path, pot, k = self.params.neb.k, distance=self.aasystem.neb_distance)
#        else:
#            return NEB(path, pot, k = self.params.neb.k)
    
    def drawCylinder(self, X1, X2):
        from OpenGL import GL,GLUT, GLU
        z = np.array([0.,0.,1.]) #default cylinder orientation
        p = X2-X1 #desired cylinder orientation
        r = np.linalg.norm(p)
        t = np.cross(z,p)  #angle about which to rotate
        a = np.arccos( np.dot( z,p) / r ) #rotation angle
        a *= (180. / np.pi)  #change units to angles
        GL.glPushMatrix()
        GL.glTranslate( X1[0], X1[1], X1[2] )
        GL.glRotate( a, t[0], t[1], t[2] )
        g=GLU.gluNewQuadric()
        GLU.gluCylinder(g, .1,0.1,r,30,30)  #I can't seem to draw a cylinder
        GL.glPopMatrix()
        
    def draw(self, rbcoords, index):
        from OpenGL import GL,GLUT
        coords = self.aasystem.to_atomistic(rbcoords)
        com=np.mean(coords, axis=0)
        i=0                  
        for xx in coords:
            if(i%3 == 0):
                color = [1.0, 0.0, 0.0]
                radius = 0.35
            else:
                color = [1.0, 1.0, 1.0]
                radius = 0.3
            if index == 2:
                color = [0.5, 1.0, .5]                
            
            i+=1
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_DIFFUSE, color)
            
            x=xx-com
            GL.glPushMatrix()            
            GL.glTranslate(x[0],x[1],x[2])
            GLUT.glutSolidSphere(radius,30,30)
            GL.glPopMatrix()
        
        for i in xrange(self.nrigid):
            color = [1.0, 0.0, 0.0]
            if index == 2:
                color = [0.5, 1.0, .5]                
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_DIFFUSE, color)
            self.drawCylinder(coords[3*i]-com, coords[3*i+1]-com)
            self.drawCylinder(coords[3*i]-com, coords[3*i+2]-com)
            
    def smooth_path(self, path, **kwargs):
        mindist = self.get_mindist()
        return smoothPath(path, mindist, interpolator=self.aasystem.interpolate, **kwargs)
    
    
if __name__ == "__main__":
    import pygmin.gui.run as gr
    gr.run_gui(TIP4PSystem, db="tip4p_8.sqlite")
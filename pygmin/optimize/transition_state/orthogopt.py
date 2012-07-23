import numpy as np


def subcross(vec3, redcoords, n):
    if n == 0:
        pm = 1.0
        i = 1
        j = 2
    elif n == 1:
        pm = -1.0
        i = 0
        j = 2
    else:
        pm = 1.0
        i = 0
        j = 1
    dummy1 = pm * np.sum( vec3[:,i] * redcoords[:,j] - vec3[:,j] * redcoords[:,i] )
    dummy2 = np.sum( (redcoords[:,i])**2 + (redcoords[:,j])**2)
    vdot = 0.
    if dummy2 > 0.:
        vdot = np.abs(dummy1) / np.sqrt(dummy2)
        dummy3 = dummy1 / dummy2
        #print "dummy1, dummy2", dummy1, dummy2, dummy3
        vec3[:,i] -= pm* dummy3 * redcoords[:,j]
        vec3[:,j] +=  pm* dummy3 * redcoords[:,i]
    return vdot
    

def orthogopt(vec, coords, otest):
    """
    make vec orthogonal to eigenvectors of the Hessian corresponding to overall 
    translations and rotations.  
    """
    
    coords = np.reshape(coords, [-1,3])
    natoms = len(coords[:,0])
    com = coords.sum(0) / natoms
    
    vec3 = np.reshape( vec, [-1,3] )
    redcoords = coords - com
    
    vdot = np.zeros(3)
    vdottol = 1e-6


    for ncheck in xrange(100):
        vdot[:] = 0.
        ncheck += 1
        
        for i in range(3):
            veccom = vec3[:,i].sum() / natoms
            vdot[i] = veccom * np.sqrt(float(natoms))  
            #print "vdot translation", vdot[i], i    
            vec3[:,i] -= veccom
            if otest: vec3 /= np.linalg.norm(vec3)
        
        if np.max(vdot) > vdottol:
            continue
        
        for i in range(3):
            vdot[i] = subcross(vec3, redcoords, i)
            #print "vdot rotation   ", vdot[i], i    
            if otest: vec3 /= np.linalg.norm(vec3)
        
        if np.max(vdot) <= vdottol:
            break

    if np.max(vdot) > vdottol:
        print "WARNING, cannot orthogonalise to known eigenvectors in ORTHOGOPT"
        print "         max(vdot)", np.max(vdot)
    
    vec = np.reshape(vec3, [-1])
    return vec
    
        
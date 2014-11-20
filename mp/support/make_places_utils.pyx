#imports
# cython: profile=True
#cimport cython

#from libc.math cimport log
#from libc.math cimport sin as sin
#from libc.math cimport cos as cos
#from math import sin as sin
#from math import cos as cos
# from libc.math cimport fmax
# from math import log

#import random
import numpy as np

#from numpy import pi

cpdef float distance_xy(list v1,list v2):
    cdef float dx
    cdef float dy
    cdef float ds
    dx = v2[0] - v1[0]
    dy = v2[1] - v1[1]
    ds = (dx**2 + dy**2)**(0.5)
    return ds

cpdef list center_of_mass(list coords):
    xs,ys,zs = zip(*coords)
    #xme = np.round(np.mean(xs),8)
    xme = np.mean(xs, dtype = np.float32)
    yme = np.mean(ys, dtype = np.float32)
    zme = np.mean(zs, dtype = np.float32)
    return [xme,yme,zme]

cpdef float dot(list v1, list v2):
    cdef float xp
    cdef float yp
    cdef float zp
    xp = v1[0]*v2[0]
    yp = v1[1]*v2[1]
    zp = v1[2]*v2[2]
    return xp + yp + zp

cpdef tuple project(list verts, list axis):
    cdef float min_ = dot(verts[0],axis)
    cdef float max_ = min_
    cdef int vcnt = len(verts)
    cdef int vdx
    cdef float val
    for vdx in range(1,vcnt):
    #for v in verts[1:]:
        v = verts[vdx]
        val = dot(v,axis)
        if val < min_: min_ = val
        if val > max_: max_ = val
    return (min_,max_)

cpdef bint overlap(rng1,rng2):
    if max(rng1) < min(rng2): return 0
    elif max(rng2) < min(rng1): return 0
    else: return 1

cpdef bint separating_axis(bb1,bb2):
    #ns1 = get_norms(bb1.corners)
    #ns2 = get_norms(bb2.corners)
    cdef list ns1 = bb1.edgenorms
    cdef list ns2 = bb2.edgenorms
    cdef list edgenorms = ns1 + ns2
    cdef list edgenorm
    cdef int egcnt = len(edgenorms)
    cdef int egdx
    cdef tuple proj1
    cdef tuple proj2
    for egdx in range(egcnt):
        edgenorm = edgenorms[egdx]
        proj1 = project(bb1.corners,edgenorm)
        proj2 = project(bb2.corners,edgenorm)
        if not overlap(proj1,proj2): return 0
    return 1

cpdef list get_norms(list verts):
    cdef list norms = []
    #zhat = [0,0,1]
    cdef int vcnt = len(verts)
    cdef int vdx
    cdef list v1
    cdef list v2
    cdef float dx
    cdef float dy
    cdef float dv
    cdef list norm
    for vdx in range(1,vcnt):
        v1,v2 = verts[vdx-1],verts[vdx]
        #v1_v2_ = normalize(v1_v2(v1,v2))
        #norm = normalize(cross(v1_v2_,zhat))
        dx = v2[0] - v1[0]
        dy = v2[1] - v1[1]
        dv = sqrt(dx**2 + dy**2)
        norm = [dy/dv,-dx/dv,0]
        norms.append(norm)
    return norms

cpdef tuple find_closest_xy(list one,list bunch):
    cdef int bcnt = len(bunch)
    cdef int bdx
    cdef float nearest 100000000.0
    for bdx in range(bcnt)
        ds = distance_xy(one,bunch[bdx])
        if ds < nearest:
            nearest = ds
            ndx = bdx
    return bunch[ndx],nearest,ndx























'''#
#System State Variables
cdef SIM_COUNTS
cdef int SIM_COUNTS_LENGTH
cdef int SIM_FUNCTION_INDEX
cdef SIM_COUNT_TARGETS


############################################################################
############################################################################

#############
### Rates ###
#############

cpdef double heaviside(double value):
	return 1.0 if value > 0.0 else 0.0

cpdef double gauss_noise(double value, double SNR):
	noise = random.gauss(0.0, 1.0)
	return value + value*noise/SNR

#TODO consider using __call__ instead of calculate
cdef class Rate:
	"""
	Rate that represents a lambda function
	"""
	cdef lam

	def __init__(self, lam):
		self.lam = lam

	cpdef double calculate(self):
		global SIM_COUNTS
		return self.lam(SIM_COUNTS)

#################
### End Rates ###
#################

############################################################################
############################################################################

####################
### Propensities ###
####################


#############################################################################
# a very long list of propensity classes, depending on the form of reaction #
#############################################################################


# a fast rounding function used by the below classes
cdef inline double zero_if_below_minimum(double value):
	return value if value > 1e-30 else 0.0


# classes for propensities:
# potentially uses / contains:
#		-cnt_dexes: memoryview of reactant count indices
#		-rate: double precision or Rate object
#		-reagents: entries are like (amt, spec_dex)


################
################

# base class for propensities
cdef class PropensityBase:
	cdef int [:] cnt_dexes
	cdef reagents

	# abstract class, cannot calculate propensity
	cpdef double calculate(self):
		raise NotImplementedError

################
################

cdef class Propensity(PropensityBase):
	cdef double rate

	def __init__(self, reagents, rate):
		#print '=== Propensity constructor called ==='
		self.reagents = reagents
		self.rate = rate

	# rate was a float and some stochiometric coefficient > 1
	cpdef double calculate(self):
		global SIM_COUNTS
		
		# index labels for the "agent" tuple
		cdef int cnt_dex, act_dex
		cnt_dex = 1
		act_dex = 0
		
		# working variables
		cdef double population, propensity
		population = 1.0		# the mass action term piece of propensity
		propensity = 1.0		# the final total propensity
		

		for agent in self.reagents:

			cnt = SIM_COUNTS[agent[cnt_dex]]
			act = agent[act_dex]

			# for multiple molecules of same species type, compute mass action term
			# e.g. X*(X-1), or just X			
			for k in range(act): population *= cnt - k

			# POTENTIAL ISSUE HERE - needed??
			# divides by the stoichiometric coefficient
			population /= act

		# compute final propensity
		propensity = population * self.rate
		return zero_if_below_minimum(propensity)

################
################
'''#






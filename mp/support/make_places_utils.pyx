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
#import numpy as np

#from numpy import pi

def distance_xy(v1,v2):
    dx = v2[0] - v1[0]
    dy = v2[1] - v1[1]
    ds = (dx**2 + dy**2)**(0.5)
    return ds

cpdef center_of_mass(list coords):
    cdef float xsum = 0.0
    cdef float ysum = 0.0
    cdef float zsum = 0.0
    cdef int ccnt = len(coords)
    cdef float ccntf = float(ccnt)
    cdef int dx
    cdef float xcm 
    cdef float ycm 
    cdef float zcm 
    for dx in range(ccnt):
        coo = coords[dx]
        xsum += coo[0]
        ysum += coo[1]
        zsum += coo[2]
    xcm = xsum/ccntf
    ycm = ysum/ccntf
    zcm = zsum/ccntf
    return [xcm,ycm,zcm]



























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






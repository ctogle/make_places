import make_places.core.scenegraph as sg
import make_places.core.primitives as pr
import make_places.core.blueprints as mbp

import mp_vector as cv
import mp_utils as mpu

class waters(sg.node):
    def __init__(self, *args, **kwargs):
        self._default_('grit_renderingdistance',10000,**kwargs)
        self._default_('length',100,**kwargs)
        self._default_('width',100,**kwargs)
        self._default_('sealevel',0.0,**kwargs)
        self._default_('depth',100.0,**kwargs)
        self.primitives = self.make_waters(*args,**kwargs)
        sg.node.__init__(self, *args, **kwargs)

    def make_waters(self, *args, **kwargs):
        bp = mbp.blueprint()
        cs = mpu.make_corners(cv.zero(),self.length,self.width,0)
        cv.translate_coords_z(cs,self.sealevel)
        nfs = []
        nfs.extend(bp._quad(*cs,m = 'ocean',pm = 'skip'))
        cv.translate_coords_z(cs,-self.depth)
        nfs.extend(bp._quad(*cs,m = 'gridmat'))
        bp._project_uv_xy(nfs)
        wcube = bp._primitives()

        #wcube = mbp.ucube()
        #wcube.scale(cv.vector(self.length,self.width,self.depth))
        #wcube.translate_z(self.sealevel-self.depth)
        #wcube.assign_material('ocean')
        return [wcube]






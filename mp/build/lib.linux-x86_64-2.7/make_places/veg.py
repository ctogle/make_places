import make_places.fundamental as fu
import mp_utils as mpu
import make_places.primitives as pr
from make_places.primitives import arbitrary_primitive
from make_places.scenegraph import node

import random as rm
import os

class tree(arbitrary_primitive):
    treexml = os.path.join(pr.primitive_data_path, 'Tree_aelm.mesh.xml')
    treelodxml = os.path.join(pr.primitive_data_path, 'Tree_aelm_LOD.mesh.xml')

    def __init__(self, *args, **kwargs):
        self._default_('is_lod', False)
        self._default_('has_lod', False)
        if not 'data' in kwargs.keys():
            if self.is_lod:
                ptreedata = pr.primitive_data_from_xml(self.treelodxml)
            else: ptreedata = pr.primitive_data_from_xml(self.treexml)
        else: ptreedata = kwargs['data']
        arbitrary_primitive.__init__(self, *args, **ptreedata)
        self.tag = '_tree_'
        self._scale_uvs_ = False

tree_data = pr.primitive_data_from_xml(tree.treexml)
tree_lod_data = pr.primitive_data_from_xml(tree.treelodxml)

class veg_batch(node):                                

    def __init__(self, *args, **kwargs):
        self._default_('consumes_children',True,**kwargs)
        self._default_('grit_renderingdistance',250,**kwargs)
        self._default_('grit_lod_renderingdistance',10000,**kwargs)
        node.__init__(self, *args, **kwargs)

def vegetate(verts, norms, faces):
    # vegetate should create veg_batch for faces, using norms for orientation
    # should return node for all veg on faces
    # verts are expected to be in world space
    #pt = mpu.center_of_mass(verts)
    treeprims = []
    treelodprims = []
    pts = []
    mintcnt = 1
    maxtcnt = 3
    for fa in faces:
        vs = verts[fa]
        pt = mpu.center_of_mass(vs)
        pts.append(pt)
        #for ntdx in rm.sample([0,1,2],rm.randrange(mintcnt,maxtcnt)):
        for ntdx in rm.sample([0,1,2],1):
            npt = mpu.midpoint(pt,vs[ntdx])
            #treeprims.append(tree(has_lod = True))
            treeprims.append(tree(data = tree_data, has_lod = True))
            #treelodprims.append(tree(is_lod = True))
            treelodprims.append(tree(data = tree_lod_data, is_lod = True))
            treeprims[-1].translate(npt)
            treelodprims[-1].translate(npt)

    vegs = veg_batch(
        position = [0.0,0.0,0.0], 
        primitives = treeprims, 
        lod_primitives = treelodprims)
    return vegs


import make_places.fundamental as fu
import make_places.scenegraph as sg
import make_places.primitives as pr
import make_places.materials as mpm
import make_places.blueprints as mbp
import make_places.gritty as gritgeo

import make_places.stairs as st
import make_places.floors as fl
import make_places.walls as wa
import make_places.portals as po

import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

import matplotlib.pyplot as plt
import random as rm
import os





class newtree(mbp.blueprint):

    def __init__(self):
        mbp.blueprint.__init__(self)
    
    def _build(self):
        com = cv.zero()
        poleb = [p.translate(com) for p in mbp.polygon(8)]
        poleb.append(poleb[0])
        polet = [p.copy().translate_z(2) for p in poleb]
        self._bridge(polet,poleb,m = 'gridmat')

class bush(mbp.blueprint):

    def __init__(self):
        mbp.blueprint.__init__(self)

    def _build(self):
        cs = mpu.make_corners(cv.vector(0,0,1),2,2,0)
        cv.rotate_x_coords(cs,fu.to_rad(90))
        self._quad(*cs,m = 'bmat1')
        cv.translate_coords(cs,cv.vector(2,0,0))
        self._quad(*cs,m = 'bmat2')
        




class tree(pr.arbitrary_primitive):
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
        pr.arbitrary_primitive.__init__(self, *args, **ptreedata)
        self.tag = '_tree_'
        self._scale_uvs_ = False

def demo_ground():
    bp = mbp.blueprint()
    cs = mpu.make_corners(cv.zero(),40,40,0)
    nfs = bp._quad(*cs,m = 'grass1')
    bp._project_uv_xy(nfs)
    demoground = bp._primitive_from_slice()
    return demoground

def demo_foliage():
    demoground = demo_ground()
    gritgeo.create_primitive(demoground)

    ntree = newtree()
    ntree._build()
    demoprim = ntree._primitive_from_slice()
    gritgeo.create_primitive(demoprim)

    bsh = bush()
    bsh._build()
    demoprim = bsh._primitive_from_slice()
    gritgeo.create_primitive(demoprim)

    gritgeo.create_primitive(tree().translate(cv.vector(10,10,0)))











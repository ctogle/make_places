import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.gritty as gritgeo

import mp_utils as mpu
import mp_vector as cv
from mp_vector import vector

from copy import deepcopy as dcopy
import numpy as np

import pdb





class tform(fu.base):
    def true(self):
        # should return a tform to world space
        np = self.position.copy()
        nr = self.rotation.copy()
        ns = self.scales.copy()
        if self.parent:
            tpar = self.parent.true()
            np.rotate_z(tpar.rotation.z)
            np.translate(tpar.position)
            nr.translate(tpar.rotation)
            ns.scale(tpar.scales)
        new = tform(self.owner,position = np,rotation = nr,scales = ns)
        return new

    def __init__(self, *args, **kwargs):
        self.owner = args[0]
        self._default_('position',vector(0,0,0),**kwargs)
        self._default_('rotation',vector(0,0,0),**kwargs)
        self._default_('scales',vector(1,1,1),**kwargs)
        self._default_('parent',None,**kwargs)
        self._default_('children',[],**kwargs)
        #for ch in self.children: ch.parent = self

    def __str__(self, bump = 0):
        strr  = '\t'*bump + 'tform' + '\n'
        strr += '\t'*bump + 'pos: ' + str(self.position) + '\n'
        strr += '\t'*bump + 'rot: ' + str(self.rotation) + '\n'
        strr += '\t'*bump + 'scl: ' + str(self.scales)
        return strr

class uv_tform(tform):
    pass

class sgraph(fu.base):
    def __init__(self, *args, **kwargs):
        self._default_('nodes',[],**kwargs)

    def add_node(self, nd):
        self.nodes.append(nd)

    def __str__(self):
        strr = '\n' + self.__str__() + '\t'
        strr += '\tscenegraph:\n'
        if not self.nodes:strr += '\tEMPTY\n'
        else:
            strr += '\t\ttop-level-nodes:'
            strr += ','.join([n.name for n in self.nodes])
            strr += '\n'.join([n.__str__() for n in self.nodes])
        return strr

    def make_scene(self, center = False):
        for nd in self.nodes:
            nd.make(center = center)

_node_count_ = 0
class node(fu.base):
    def __str__(self,bump = -1):
        bump += 1
        tf = self.tform
        pcnt = str(len(self.primitives))
        ccnt = str(len(tf.children))
        strr = '\t'*bump + 'node:' + str(self.name) + '\n'
        strr += tf.__str__(bump) + '\n'
        strr += '\t'*bump + 'with ' + pcnt + ' primitives '
        strr += 'and ' + ccnt + ' children'
        childstr = [c.owner.__str__(bump) for c in tf.children]
        strr += '\n' + '\n'.join(childstr)
        return strr

    def translate(self, v):
        self.tform.position.translate(v)

    def rotate(self, v):
        print 'is node.rotate being used??'
        self.tform.rotation.translate(v)

    def def_tform(self,*args,**kwargs):
        def _def(ke,de):
            if ke in kwargs.keys(): return kwargs[ke]
            else: return de
        # should only instantiate these vectors if needed
        pos = _def('position',vector(0,0,0))
        rot = _def('rotation',vector(0,0,0))
        scl = _def('scales',vector(1,1,1))
        if 'parent' in kwargs.keys():
            tpar = kwargs['parent'].tform
        else: tpar = None
        chi = _def('children',[])
        ntf = tform(self, parent = tpar, 
            children = [ch.tform for ch in chi], 
            position = pos, rotation = rot, scales = scl)
        return ntf

    def def_uv_tform(self,*args,**kwargs):
        def _def(ke,de):
            if ke in kwargs.keys(): return kwargs[ke]
            else: return de
        pos = _def('uv_position',vector(0,0,0))
        rot = _def('uv_rotation',vector(0,0,0))
        scl = _def('uv_scales',vector(1,1,1))
        if 'uv_parent' in kwargs.keys():
            tpar = kwargs['uv_parent'].uv_tform
        else: tpar = None
        chi = _def('uv_children',[])
        ntf = uv_tform(self, parent = tpar, 
            children = [ch.uv_tform for ch in chi], 
            position = pos, rotation = rot, scales = scl)
        return ntf

    def add_child(self, *chil):
        for ch in chil:
            ch.tform.parent = self.tform
            if not ch in self.tform.children:
                self.tform.children.append(ch.tform)
    
    def remove_child(self, *chil):
        for ch in chil:
            ch.tform.parent = None
            if ch.tform in self.tform.children:
                self.tform.children.remove(ch.tform)

    def set_parent(self, parent):
        self.tform.parent = parent.tform
        if not self.tform in parent.tform.children:
            parent.tform.children.append(self.tform)

    def worldly_primitive(self, prim, ttf, uv_ttf, **kwargs):
        tpm = prim
        tpm.scale(ttf.scales)
        tpm.worldly_uvs(uv_ttf)
        tpm.rotate_z(ttf.rotation.z)
        tpm.translate(ttf.position)
        kwargs['name'] = self.name
        kwargs['rdist'] = self.grit_renderingdistance
        kwargs['lodrdist'] = self.grit_lod_renderingdistance
        return tpm, kwargs

    def worldly_children(self, **kwargs):
        ttf = self.tform.true()
        uv_ttf = self.uv_tform.true()
        newpms = []
        for pm in self.primitives:
            tpm,kwargs = self.worldly_primitive(pm,ttf,uv_ttf,**kwargs)
            newpms.append(tpm)
        for ch in self.tform.children:
            chpms = ch.owner.worldly_children()
            newpms.extend(chpms)
        return newpms

    def lod_worldly_children(self, **kwargs):
        ttf = self.tform.true()
        uv_ttf = self.uv_tform.true()
        newpms = []
        for pm in self.lod_primitives:
            tpm, kwargs = self.worldly_primitive(pm,ttf,uv_ttf,**kwargs)
            newpms.append(tpm)
        for ch in self.tform.children:
            chpms = ch.owner.lod_worldly_children()
            newpms.extend(chpms)
        return newpms

    def consume(self):

        #if self.converts_to_lod:
        #    self.convert_to_lod()

        chps = []
        chlps = []
        for ch in self.tform.children:
            ch.owner.consume()
            ch.parent = None
            chps.extend(ch.owner.worldly_children())
            chlps.extend(ch.owner.lod_worldly_children())
        self.tform.children = []
        self.primitives.extend(chps)
        self.lod_primitives.extend(chlps)
        if self.primitives:
            final_prim = pr.sum_primitives(self.primitives)
            self.primitives = [final_prim]
        if self.lod_primitives:
            final_lod_prim = pr.sum_primitives(self.lod_primitives)
            self.lod_primitives = [final_lod_prim]

            if self.primitives:
                self.primitives[0].has_lod = True
            self.lod_primitives[0].is_lod = True

    def convert_to_lod(self):
        # convert every primitive to lod
        for ch in self.tform.children:
            ch.owner.convert_to_lod()
        for p in self.primitives:
            p.is_lod = True
            self.lod_primitives.append(p)
            self.primitives.remove(p)

    def terrain_points(self):
        return []

    def assign_material(self, mat, propagate = True):
        if propagate:
            for ch in self.tform.children:
                ch.owner.assign_material(mat)
        for p in self.primitives: p.assign_material(mat)
        for p in self.lod_primitives: p.assign_material(mat)

    def get_name(self):
        global _node_count_
        nam = 'node ' + str(_node_count_)
        _node_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        if not hasattr(self,'name'):
            self.name = self.get_name()
        #self._default_('name',defname,**kwargs)
        self._default_('grit_renderingdistance',250,**kwargs)
        self._default_('grit_lod_renderingdistance',2500,**kwargs)
        self._default_('consumes_children',False,**kwargs)
        self._default_('converts_to_lod',False,**kwargs)
        self._default_('primitives',[],**kwargs)
        self._default_('lod_primitives',[],**kwargs)

        if not hasattr(self,'tform'):
            if kwargs.has_key('tform'): self.tform = kwargs['tform']
            else: self.tform = self.def_tform(*args,**kwargs)
        #self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)

        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)

    def make_primitives_in_scene(self, scene_type, **kwargs):
        ttf = self.tform.true()
        uv_ttf = self.uv_tform.true()

        pcnt = len(self.primitives)
        lodcnt = len(self.lod_primitives)

        if pcnt < lodcnt:
            self.primitives.extend([None]*(lodcnt-pcnt))
            apcnt = lodcnt
        elif pcnt > lodcnt:
            self.lod_primitives.extend([None]*(pcnt-lodcnt))
            apcnt = pcnt
        else: apcnt = pcnt

        for pmdx in range(apcnt):
            pm = self.primitives[pmdx]
            lpm = self.lod_primitives[pmdx]
            if not pm is None:
                tpm,kwargs = self.worldly_primitive(pm,ttf,uv_ttf)
                scene_type.create_primitive(tpm,**kwargs)
            if not lpm is None:
                tpm,kwargs = self.worldly_primitive(lpm,ttf,uv_ttf)
                tpm.is_lod = True
                scene_type.create_primitive(tpm,**kwargs)

    def make(self, *args, **kwargs):

        #if self.converts_to_lod:
        #    self.convert_to_lod()

        if self.consumes_children: self.consume()
        else: [ch.owner.make(*args, **kwargs) for ch in self.tform.children]

        self.make_primitives_in_scene(gritgeo)













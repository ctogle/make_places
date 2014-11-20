import make_places.fundamental as fu
import mp_utils as mpu
from make_places.fundamental import base
import make_places.primitives as pr
import make_places.blend_in as blgeo
import make_places.gritty as gritgeo

from copy import deepcopy as dcopy
import numpy as np

import pdb





class tform(base):
    def true(self):
        # should return a tform to world space
        nr = self.rotation[:]
        if self.parent:
            tpar = self.parent.true()
            np = mpu.rotate_z_coord(self.position[:],tpar.rotation[2])
            mpu.translate_vector(np,tpar.position)
            mpu.translate_vector(nr,tpar.rotation)
            ns = mpu.scale_vector(self.scales[:],tpar.scales)
        else:
            np = self.position[:]
            ns = self.scales[:]
        new = tform(self.owner,position = np,rotation = nr,scales = ns)
        return new

    def __init__(self, *args, **kwargs):
        self.owner = args[0]
        self._default_('position',[0,0,0],**kwargs)
        self._default_('rotation',[0,0,0],**kwargs)
        self._default_('scales',[1,1,1],**kwargs)
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

class sgraph(base):
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

    def make_scene_b(self, center = False):
        for nd in self.nodes:
            nd.make_b(center = center)

    def make_scene_g(self, center = False):
        for nd in self.nodes:
            nd.make_g(center = center)

_node_count_ = 0
class node(base):
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
        mpu.translate_vector(self.tform.position, v)

    def rotate(self, v):
        mpu.translate_vector(self.tform.rotation, v)

    def def_tform(self,*args,**kwargs):
        def _def(ke,de):
            if ke in kwargs.keys(): return kwargs[ke]
            else: return de
        pos = _def('position',[0,0,0])
        rot = _def('rotation',[0,0,0])
        scl = _def('scales',[1,1,1])
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
        pos = _def('uv_position',[0,0,0])
        rot = _def('uv_rotation',[0,0,0])
        scl = _def('uv_scales',[1,1,1])
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
        tpm.scale(ttf.scales)
        tpm.rotate_z(ttf.rotation[2])
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
        # returns a single primitives, the sum of self and childrens prims
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

    '''#
    def consume_children(self):
        final = self.consume()
        print 'consumed!', len(self.primitives), self.name
        newpms = []
        newlodpms = []
        for ch in self.tform.children:
            old_rent = self.tform.parent
            #old_pos = self.tform.position
            self.tform.parent = None
            #self.tform.position = [0,0,0]
            newpms.extend(ch.owner.worldly_children())
            newlodpms.extend(ch.owner.lod_worldly_children())
            #newpms.extend(self.worldly_children())
            #newlodpms.extend(self.lod_worldly_children())
            self.tform.parent = old_rent
            #self.tform.position = old_pos
        self.primitives.extend(newpms)
        #self.primitives = self.worldly_children()
        if self.primitives:
            final_prim = pr.sum_primitives(self.primitives)
            self.primitives = [final_prim]
        self.lod_primitives.extend(newlodpms)
        if self.lod_primitives:
            lod_final_prim = pr.sum_primitives(self.lod_primitives)
            self.lod_primitives = [lod_final_prim]
            if self.primitives: self.primitives[0].has_lod = True
        print 'consumed!', len(self.primitives), self.name
    '''#

    def terrain_points(self):
        return []

    def assign_material(self, mat, propagate = True):
        if propagate:
            for ch in self.tform.children: ch.owner.assign_material(mat)
        for p in self.primitives: p.assign_material(mat)
        for p in self.lod_primitives: p.assign_material(mat)

    def get_name(self):
        global _node_count_
        nam = 'node ' + str(_node_count_)
        _node_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self._default_('name',self.get_name(),**kwargs)
        self._default_('grit_renderingdistance',250,**kwargs)
        self._default_('grit_lod_renderingdistance',2500,**kwargs)
        self._default_('consumes_children',False,**kwargs)
        self._default_('primitives',[],**kwargs)
        self._default_('lod_primitives',[],**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
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

        #for pm,lpm in zip(self.primitives,self.lod_primitives):
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

    def make_b(self, *args, **kwargs):
        for ch in self.tform.children: ch.make_b(*args, **kwargs)
        self.make_primitives_in_scene(blgeo)

    def make_g(self, *args, **kwargs):
        if self.consumes_children: self.consume()
        #if self.consumes_children: self.consume_children()
        else: [ch.owner.make_g(*args, **kwargs) for ch in self.tform.children]
        self.make_primitives_in_scene(gritgeo)







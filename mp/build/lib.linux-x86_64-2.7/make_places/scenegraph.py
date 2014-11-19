import make_places.fundamental as fu
from make_places.fundamental import base
import make_places.primitives as pr
import make_places.blend_in as blgeo
import make_places.gritty as gritgeo

from copy import deepcopy as dcopy
import numpy as np

import pdb





class tform(base):
    def true(self):
        if self.parent:
            tpar = self.parent.true()
            #fu.rotate_z_coords([self.position],tpar.rotation[2])
            #self.position = fu.rotate_z_coords(
            #    [self.position], tpar.rotation[2])[0]
            return tpar + self
        else: return self

    def __init__(self, *args, **kwargs):
        self._default_('position',[0,0,0],**kwargs)
        self._default_('rotation',[0,0,0],**kwargs)
        self._default_('scales',[1,1,1],**kwargs)
        self._default_('parent',None,**kwargs)
        self._default_('children',[],**kwargs)

    def __str__(self):
        strr = 'tform\n\tpos:\t'
        strr += str(self.position)
        strr += '\n\trot:\t'
        strr += str(self.rotation)
        strr += '\n\tscl:\t'
        strr += str(self.scales)
        strr += '\n'
        return strr

    def __add__(self, other):
        np = fu.translate_vector(self.position[:],other.position)
        nr = fu.translate_vector(self.rotation[:],other.rotation)
        ns = fu.scale_vector(self.scales[:],other.scales)
        new = tform(parent = self.parent, children = self.children, 
            position = np, rotation = nr, scales = ns)
        return new

class uv_tform(tform):
    pass

class sgraph(base):
    def __init__(self, *args, **kwargs):
        self._default_('nodes',[],**kwargs)

    def add_node(self, nd):
        self.nodes.append(nd)

    def make_scene_b(self, center = False):
        for nd in self.nodes:
            nd.make_b(center = center)

    def make_scene_g(self, center = False):
        for nd in self.nodes:
            nd.make_g(center = center)

class node(base):
    def translate(self, v):
        fu.translate_vector(self.tform.position, v)

    def rotate(self, v):
        fu.translate_vector(self.tform.rotation, v)

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
        return tform(parent = tpar, position = pos, 
            rotation = rot, scales = scl)

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
        return uv_tform(parent = tpar, position = pos, 
            rotation = rot, scales = scl)

    def add_child(self, *chil):
        for ch in chil:
            ch.tform.parent = self.tform
            if not ch in self.children:
                self.children.append(ch)

    def worldly_primitive(self, prim, ttf, uv_ttf, **kwargs):
        #tpm = dcopy(prim)
        tpm = prim
        tpm.scale(ttf.scales)
        tpm.worldly_uvs(uv_ttf)
        #tpm.rotate_z(ttf.rotation[2])
        tpm.translate(ttf.position)
        #tpm.rotate_z(ttf.rotation[2])

        kwargs['world_rotation'] = ttf.rotation
        kwargs['name'] = self.name
        kwargs['rdist'] = self.grit_renderingdistance
        kwargs['lodrdist'] = self.grit_lod_renderingdistance
        return tpm, kwargs

    def worldly_children(self, **kwargs):
        ttf = self.tform.true()
        uv_ttf = self.uv_tform.true()
        newpms = []
        for pm in self.primitives:
            tpm, kwargs = self.worldly_primitive(pm,ttf,uv_ttf,**kwargs)
            newpms.append(tpm)
        for ch in self.children:
            chpms = ch.worldly_children()
            newpms.extend(chpms)
        return newpms

    def lod_worldly_children(self, **kwargs):
        ttf = self.tform.true()
        uv_ttf = self.uv_tform.true()
        newpms = []
        for pm in self.lod_primitives:
            tpm, kwargs = self.worldly_primitive(pm,ttf,uv_ttf,**kwargs)
            newpms.append(tpm)
        for ch in self.children:
            chpms = ch.lod_worldly_children()
            newpms.extend(chpms)
        return newpms

    def consume_children(self):
        newpms = []
        newlodpms = []
        for ch in self.children:
            old_rent = self.tform.parent
            old_pos = self.tform.position
            self.tform.parent = None
            self.tform.position = [0,0,0]
            newpms.extend(self.worldly_children())
            newlodpms.extend(self.lod_worldly_children())
            self.tform.parent = old_rent
            self.tform.position = old_pos
        self.primitives.extend(newpms)
        if self.primitives:
            final_prim = pr.sum_primitives(self.primitives)
            self.primitives = [final_prim]
        self.lod_primitives.extend(newlodpms)
        if self.lod_primitives:
            lod_final_prim = pr.sum_primitives(self.lod_primitives)
            self.lod_primitives = [lod_final_prim]
            if self.primitives: self.primitives[0].has_lod = True

    def terrain_points(self):
        return []

    def assign_material(self, mat, propagate = True):
        if propagate:
            for ch in self.children: ch.assign_material(mat)
        for p in self.primitives: p.assign_material(mat)
        for p in self.lod_primitives: p.assign_material(mat)

    #if your xy position matches that of your parent, you can inherit your parents rotation in lua safely?
    def __init__(self, *args, **kwargs):
        self._default_('name',None,**kwargs)
        self._default_('grit_renderingdistance',250,**kwargs)
        self._default_('grit_lod_renderingdistance',2500,**kwargs)
        self._default_('consumes_children',False,**kwargs)
        self._default_('children',[],**kwargs)
        self._default_('primitives',[],**kwargs)
        self._default_('lod_primitives',[],**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)

    # THIS IS INCOMPLETE
    def ______________add__(self, other):
        # change the origin of others children/prims to selfs
        nargs = {
            'name':self.name + other.name,
            'grit_renderingdistance':self.grit_renderingdistance,
            'grit_lod_renderdistance':self.grit_lod_renderingdistance,
            'consumes_children':self.consumes_children, 
            'children':self.children + other.children, 
            'primitives':self.primitives + other.primitives, 
            'lod_primitives':self.lod_primitives + other.lod_primitives, 
            'tform':self.tform, 
                }
        return node(**nargs)

    def make_primitives_in_scene(self, scene_type, **kwargs):
        ttf = self.tform.true()
        uv_ttf = self.uv_tform.true()

        pcnt = len(self.primitives)
        lodcnt = len(self.lod_primitives)
        if pcnt < lodcnt:
            self.primitives.extend([None]*(lodcnt-pcnt))
        elif pcnt > lodcnt:
            self.lod_primitives.extend([None]*(pcnt-lodcnt))
        for pm,lpm in zip(self.primitives,self.lod_primitives):
            if not pm is None:
                tpm, kwargs = self.worldly_primitive(pm, ttf, uv_ttf)
                scene_type.create_primitive(tpm, **kwargs)
            if not lpm is None:
                tpm, kwargs = self.worldly_primitive(lpm, ttf, uv_ttf)
                tpm.is_lod = True
                scene_type.create_primitive(tpm, **kwargs)

    def make_b(self, *args, **kwargs):
        for ch in self.children: ch.make_b(*args, **kwargs)
        self.make_primitives_in_scene(blgeo)

    def make_g(self, *args, **kwargs):
        if self.consumes_children: self.consume_children()
        else: [ch.make_g(*args, **kwargs) for ch in self.children]
        self.make_primitives_in_scene(gritgeo)






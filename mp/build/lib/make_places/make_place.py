import make_places.fundamental as fu
import make_places.scenegraph as sg
import make_places.primitives as pr
import make_places.cities as cities
import make_places.buildings as blg
import make_places.roads as roads
import make_places.floors as floors
import make_places.walls as walls
import make_places.profiler as prf

import make_places.blend_in as blgeo
import make_places.gritty as gritgeo

import os
import numpy as np

def ucube_b():
    pcube = pr.ucube()
    blgeo.create_primitive(pcube)

def ucube_g():
    pcube = pr.ucube()
    gritgeo.create_primitive(pcube)

def uoctagon_b():
    poct = pr.uoctagon()
    blgeo.create_primitive(poct)

def uoctagon_g():
    poct = pr.uoctagon()
    gritgeo.create_primitive(poct)

def ulineup_b():
    pcube = pr.ucube()
    poct = pr.uoctagon()
    pcube.translate([1,0,0])
    poct.translate([-1,0,0])
    blgeo.create_primitive(pcube,poct)

def ulineup_g():
    pcube = pr.ucube()
    poct = pr.uoctagon()
    pcube.translate([1,0,0])
    poct.translate([-1,0,0])
    gritgeo.create_primitive(pcube,poct)

def cube_oct_elem(pos, scl, rot, children = []):
    uc = pr.ucube()
    uo = pr.uoctagon()
    uc.scale([2,2,3])
    uc.translate([1,0,0])
    uo.translate([-1,0,0])
    eprims = [uc, uo]
    elem = fu.element(children = children, 
        position = pos, scales = scl, 
        rotation = rot, primitives = eprims)
    return elem

def uelements_b():
    el1 = cube_oct_elem([-2,-2,2], [2,2,1], [0,0,np.pi/2])
    el2 = cube_oct_elem([2,2,-2], [3,3,2], [0,0,3*(np.pi/2)])
    blgeo.create_element(el1,el2)

def uelements_g():
    el1 = cube_oct_elem([-2,-2,2], [2,2,1], [0,0,np.pi/2])
    el2 = cube_oct_elem([2,2,-2], [3,3,2], [0,0,3*(np.pi/2)])
    gritgeo.create_element(el1,el2)

def uelement_child_b():
    el1 = cube_oct_elem([2,4,1], [1,2,2], [0,0,np.pi/6])
    el2 = cube_oct_elem([0,0,-1], [2,2,1], [0,0,np.pi/2], children = [el1])
    blgeo.create_element(el2)

def uelement_child_g():
    el1 = cube_oct_elem([2,4,1], [1,2,2], [0,0,np.pi/2])
    el2 = cube_oct_elem([0,0,-1], [2,2,1], [0,0,np.pi/2], children = [el1])
    gritgeo.create_element(el2)

def intersection_b():
    iarg = {
        'position':[10,10,0], 
        'road_width':30, 
        'road_height':5, 
            }
    elem = roads.intersection(**iarg)
    blgeo.create_element(elem)

def intersection_g():
    iarg = {
        'position':[10,10,0], 
        'road_width':30, 
        'road_height':5, 
            }
    elem = roads.intersection(**iarg)
    gritgeo.create_element(elem)

def road_b():
    rarg = {
        'start':[0,10,0],
        'end':[100,110,-10],
        'directions':['north','west'],
        'road_height':1,
        'road_width':10,
            }
    elem = roads.road(**rarg)
    for ke in elem.__dict__.keys():
        print('elem',ke,elem.__dict__[ke])
    blgeo.create_element(elem)

def road_g():
    rarg = {
        'start':[0,10,0],
        'end':[100,110,-10],
        'directions':['north','west'],
        'road_height':1,
        'road_width':10,
            }
    elem = roads.road(**rarg)
    for ke in elem.__dict__.keys():
        print('elem',ke,elem.__dict__[ke])
    gritgeo.create_element(elem)

def roady_b():
    r1 = {
        'start':[0,0,0], 
        'end':[0,100,10], 
        'directions':['north','south'],
        'road_height':2, 
        'road_width':20, 
            }
    rargs = [r1]
    blgeo.create_element([roads.road(**rg) for rg in rargs])

def roady_g():
    r1 = {
        'start':[0,0,0], 
        'end':[0,100,10], 
        'directions':['north','south'],
        'road_height':2, 
        'road_width':20, 
            }
    rargs = [r1]
    gritgeo.create_element([roads.road(**rg) for rg in rargs])

def road_network_b():
    rnarg = {}
    elem = roads.road_system(**rnarg)
    blgeo.create_element(elem)

def road_network_g():
    rnarg = {}
    elem = roads.road_system(**rnarg)
    gritgeo.create_element(elem)

def afloor():
    elem = floors.floor()
    blgeo.create_element(elem)

def awall():
    v1,v2 = [10,10,0], [50,30,0]
    v3,v4 = [0,0,0], [0,30,0]
    w1 = walls.wall(v1,v2)
    w2 = walls.wall(v3,v4,gaped = True)
    blgeo.create_element(w1,w2)

def abox():
    fl = floors.floor()
    pe = walls.perimeter(floor = fl)
    elems = [fl,pe]
    blgeo.create_element(elems)

def astory():
    st = blg.story(1, position = [1,1,1])
    blgeo.create_element(st)

def ashaft():
    sh = blg.shaft()
    blgeo.create_element(sh)

def someshafts():
    sh1 = blg.shaft(position = [-10,0,0],direction = 'north')
    sh2 = blg.shaft(position = [10,0,0], direction = 'east')
    blgeo.create_element(sh1,sh2)

def build():
    built = blg.building()
    blgeo.create_element(built)

def buildfew_b():
    ang = np.pi/24
    bargs = [{
        'position':[10,50,10], 
            }, {
        'position':[-10,-10,0], 
        'rotation':[0,0,ang], 
            }]
    built = [blg.building(**ba) for ba in bargs]
    blgeo.create_element(built)

def buildfew_g():
    ang = np.pi/6
    bargs = [{
        'position':[10,50,10], 
            }, {
        'position':[-10,-10,0], 
        'rotation':[0,0,ang], 
            }]
    built = [blg.building(**ba) for ba in bargs]
    gritgeo.create_element(built)

def block_b():
    iargs = [{
        'position':[0,0,0], 
            }, {
        'position':[0,300,-10], 
            }, {
        'position':[300,100,10], 
            }]
    rsargs = {
        'interargs':iargs, 
            }
    rsys = roads.road_system(**rsargs)
    rd = rsys.roads[1]
    b1 = {
        'road':rd, 
        'bboxes':rd.get_bbox(),
        'side':'right',
            }
    b2 = {
        'road':rd, 
        'bboxes':rd.get_bbox(),
        'side':'left',
            }
    bl1 = cities.block(**b1)
    bl2 = cities.block(**b2)
    blgeo.create_element(rsys,bl1,bl2)

def profile_block_b():
    prf.profile_function(block_b)

def city_b():
    elem = cities.city()
    blgeo.create_element(elem)

def city_g():
    elem = cities.city()
    gritgeo.create_element(elem)

def profile_city_b():
    prf.profile_function(city_b)








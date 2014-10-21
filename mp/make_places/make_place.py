import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.cities as cities
import make_places.buildings as blg
import make_places.roads as roads
import make_places.floors as floors
import make_places.walls as walls

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

def uoctagon():
    poct = pr.uoctagon()
    blgeo.create_primitive(poct)

def ulineup():
    pcube = pr.ucube()
    poct = pr.uoctagon()
    pcube.translate([1,0,0])
    poct.translate([-1,0,0])
    blgeo.create_primitive(pcube,poct)

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

def uelements():
    el1 = cube_oct_elem([-2,-2,2], [2,2,1], [0,0,np.pi/2])
    el2 = cube_oct_elem([2,2,-2], [3,3,2], [0,0,3*(np.pi/2)])
    blgeo.create_element(el1,el2)

def uelement_child():
    el1 = cube_oct_elem([2,4,1], [1,2,2], [0,0,np.pi/2])
    el2 = cube_oct_elem([0,0,-1], [2,2,1], [0,0,np.pi/2], children = [el1])
    blgeo.create_element(el2)

def intersection():
    iarg = {
        'position':[10,10,0], 
        'road_width':30, 
        'road_height':5, 
            }
    elem = roads.intersection(**iarg)
    blgeo.create_element(elem)

def road():
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

def roady():
    r1 = {
        'start':[0,0,0], 
        'end':[0,100,10], 
        'directions':['north','south'],
        'road_height':2, 
        'road_width':20, 
            }
    rargs = [r1]
    blgeo.create_element([roads.road(**rg) for rg in rargs])

def road_directions():
    rargs = [
        #    {
        #'start':[0,10,0],
        #'end':[100,110,-10],
        #'directions':['north','west'],
        #'road_height':1,
        #'road_width':10,
        #    }, 
        #    {
        #'start':[0,10,0],
        #'end':[-100,110,-10],
        #'directions':['north','east'],
        #'road_height':1,
        #'road_width':10,
        #    }, 
        #    {
        #'end':[0,10,10],
        #'start':[-100,110,0],
        #'directions':['east','north'],
        #'road_height':1,
        #'road_width':20,
        #    }, 
        #    {
        #'end':[0,-10,10],
        #'start':[-100,-110,0],
        #'directions':['east','south'],
        #'road_height':1,
        #'road_width':20,
        #    },
        #    {
        #'start':[0,-10,0],
        #'end':[-100,-110,-10],
        #'directions':['south','east'],
        #'road_height':1,
        #'road_width':20,
        #    },
        #    {
        #'end':[0,10,10],
        #'start':[-100,110,0],
        #'directions':['south','west'],
        #'road_height':1,
        #'road_width':20,
        #    },
        #    {
        #'start':[0,10,0],
        #'end':[-100,110,-10],
        #'directions':['west','south'],
        #'road_height':1,
        #'road_width':20,
        #    },
            {
        'end':[0,10,10],
        'start':[100,110,0],
        'directions':['west','north'],
        'road_height':1,
        'road_width':20,
            },
        #    {
        #'start':[0,10,0],
        #'end':[100,110,-10],
        #'directions':['east','south'],
        #'road_height':1,
        #'road_width':10,
        #    }, 
        #    {
        #'end':[0,10,30],
        #'start':[100,110,0],
        #'directions':['south','east'],
        #'road_height':1,
        #'road_width':10,
        #    }, 
            {
        'start':[0,0,0], 
        'end':[-200,100,50],
        'directions':['north', 'east'], 
        'road_height':2, 
        'road_width':30, 
            }] 
    '''#
    rargs = [
            {
        'end':[0,10,10],
        'start':[100,110,0],
        'directions':['west','north'],
        'road_height':1,
        'road_width':20,
            }] 
    '''#
    elems = [roads.road(**ra) for ra in rargs]
    blgeo.create_element(elems)

def road_network():
    rnarg = {}
    elem = roads.road_system(**rnarg)
    blgeo.create_element(elem)

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

def buildfew():
    bargs = [{
        'position':[10,50,10], 
            }, {
        'position':[-10,-10,0], 
            }]
    built = [blg.building(**ba) for ba in bargs]
    blgeo.create_element(built)

def city():
    elem = cities.city()
    blgeo.create_elements(elem)
    





def intersect_bb():
    #ucube3 = fu.element(materials = ['imgtex'], 
    #    primitives = [pr.unit_cube()])
    #ucube2 = fu.element(position = [0.5,0.5,0], 
    #        primitives = [pr.unit_cube()])

    #flcnt = 4
    #ucube3 = blg.building(name = 'ucube3', 
    #    position = [0,0,0],length = 40,width = 30,
    #    floor_height = 0.4, wall_width = 0.4, wall_height = 4.0, 
    #    floors = flcnt, rotation = [0,0,30])
    #ucube2 = blg.building(name = 'ucube2', 
    #    position = [5,5,0],length = 10,width = 10,
    #    floor_height = 0.2, wall_width = 0.2, wall_height = 2.0, 
    #    floors = flcnt, rotation = [0,0,0])

    #ucube1 = roads.intersection(position = [20,20,20])
    #ucube2 = roads.intersection(position = [30,20,20])

    #flcnt = 3
    #ucube1 = roads.road_system(interargs = [
    rsys = roads.road_system(interargs = [
        {'position':[0,0,0]}, 
        {'position':[0,200,0]}, 
    #    #{'position':[200,200,0]}, 
        ])
    #ucube2 = blg.building(name = 'ucube2', 
    #    position = [0,50,0],length = 40,width = 40,
    #    floor_height = 0.2, wall_width = 0.2, wall_height = 2.0, 
    #    floors = flcnt, rotation = [0,0,0])
    ucube1 = cities.city(road_system = rsys)
    #ucube2 = cities.city()

    elems = ucube1.children
    #bldgs = fu.break_elements(ucube1.blocks)
    #pieces = fu.break_elements(bldgs)
    #elems = pieces + [rsys]
    #elems = ucube3.children
    #elems = [ucube3]
    blgeo.create_elements(elems)

def unit_cube():
    ucube = [fu.element(primitives = [pr.unit_cube()])]
    blgeo.create_elements(ucube)

def make_building():
    flcnt = 4
    bldg = blg.building(name = 'building', 
        position = [0,0,0],length = 40,width = 30,
        floor_height = 0.4, wall_width = 0.4, wall_height = 4.0, 
        floors = flcnt, rotation = [0,0,30])
    elems = bldg.children
    blgeo.create_elements(elems)

def make_roads():
    rsys = roads.road_system(
        seeds = [[0,0,0], [100,0,20]], 
        intersection_count = 2)
    elems = rsys.children
    blgeo.create_elements(elems)

def make_city():
    elements = cities.city().children
    blgeo.create_elements(elements)




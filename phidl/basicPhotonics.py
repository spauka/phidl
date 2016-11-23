from __future__ import division # Makes it so 1/4 = 0.25 instead of zero


from phidl import Device, quickplot
import numpy as np
import phidl.geometry as pg
import gdspy
from scipy.interpolate import interp1d

## parameters for rings
#radius = 10
#gaps = [0.1, 0.2, 0.3]
#wRing = 0.5
#wWg = 0.4
#dR = 0.015
#period = radius*3

def polygon(xcoords=[-1,-1, 0, 0],
            ycoords = [0, 1, 1, 0],
            layer = 0):
    # returns a polygon with ports on all edges
    P = Device('polygon')
    P.add_polygon([xcoords, ycoords], layer = layer)
    n = len(xcoords)
    xcoords.append(xcoords[0])
    ycoords.append(ycoords[0]) 
 #determine if clockwise or counterclockwise
    cc = 0     
    for i in range(0,n):
        cc += ((xcoords[i+1]-xcoords[i])*(ycoords[i+1]+ycoords[i]))
            
    for i in range(0,n):
        midpoint_n = [(xcoords[i+1]+xcoords[i])/2, (ycoords[i+1]+ycoords[i])/2]
        orientation_n = np.arctan2(np.sign(cc)*(xcoords[i+1]-xcoords[i]),np.sign(cc)*(ycoords[i]-ycoords[i+1]))*180/np.pi           
        width_n = np.abs(np.sqrt((xcoords[i+1]-xcoords[i])**2+(ycoords[i+1]-ycoords[i])**2))    
        P.add_port(name = str(i), midpoint = midpoint_n, width = width_n, orientation = orientation_n)
    
    return P
    
def grating(nperiods = 20, period = 0.75, ff = 0.5, wGrating = 20, lTaper = 10, wWg = 0.4, partialetch = 0):
    #returns a fiber grating
    G = Device('grating')

# make the deep etched grating
    if partialetch is 0:
        # make the grating teeth
        for i in range(nperiods):
            cgrating = G.add_ref(pg.compass(size=[period*ff,wGrating]), layer = 0)
            cgrating.x+=i*period
            
        # make the taper
        tgrating = G.add_ref(pg.taper(length = lTaper, width1 = wGrating, width2 = wWg, port = None, layer = 0))
        tgrating.xmin = cgrating.xmax
        # define the port of the grating
        p = G.add_port(port = tgrating.ports[2], name = 1)
# make a partially etched grating
    if partialetch is 1:
        # hard coded overlap
            partetch_overhang = 5
            # make the etched areas (opposite to teeth)
            for i in range(nperiods):
                cgrating = G.add_ref(pg.compass(size=[period*(1-ff),wGrating+partetch_overhang*2]), layer = 1)
                cgrating.x+=i*period
                        # define the port of the grating
            p = G.add_port(port = cgrating.ports['E'], name = 1)
            p.midpoint=p.midpoint+np.array([(1-ff)*period,0])
                
        #draw the deep etched square around the grating
            deepbox = G.add_ref(pg.compass(size=[nperiods*period, wGrating]), layer=0)    
    return G

def ccRings(radius = 10, gaps = [0.1, 0.2, 0.3], wRing = 0.5, wWg = 0.4, dR = 0.15, period = 30, GratingDevice = gdspy.Cell):
# number of rings defined by the length of the gaps vector    
    nrings = len(gaps)
    lWg = (nrings + 1)*period
    
    D = Device('critically coupled rings')
# make the main bus
    wg = D.add_ref(pg.compass(size=[lWg, wWg]))
    R = Device();
 # make the rings with different gaps and radii   
    for i, g in enumerate(gaps):
        r = R.add_ref(pg.ring(radius = radius + dR*i, width = wRing, angle_resolution = 1, layer = 0)) 
        r.move([period*i,0])
        r.ymax = wg.ymin - g
# put the rings in the main device    
    R.x = D.x
    D.add_ref(R)
# add the gratings    
    g = D.add_ref(GratingDevice)
    g2 = D.add_ref(GratingDevice)
# define port connections   
    g.connect(port = 1, destination = wg.ports['W'])
    g.xmax = wg.xmin
    g2.connect(port = 1, destination = wg.ports['E'])
    g2.xin = wg.xmax
    
# route between connected ports with tapers  
    D.add_ref(pg.route(port1 = g.ports[1], port2 = wg.ports['W']))
    D.add_ref(pg.route(port1 = g2.ports[1], port2 = wg.ports['E']))
    
    return D
    
def lossRings(radius = 10, gaps = [0.1, 0.2, 0.3], wRing = 0.5, wWg = 0.4, dR = 0.15, period = 30, GratingDevice = gdspy.Cell):
    
    D = Device("loss rings")
    nrings = len(gaps)
    lWg = (nrings + 1)*period
    
    wg = D.add_ref(pg.compass(size=[lWg, wWg]))
    
    g = D.add_ref(GratingDevice)
    g2 = D.add_ref(GratingDevice)
    
    g.connect(port = 1, destination = wg.ports['W'])
    g.xmax = wg.xmin
    g2.connect(port = 1, destination = wg.ports['E'])
    g2.xmin = wg.xmax
    
    D.add_ref(pg.route(port1 = g.ports[1], port2 = wg.ports['W']))
    D.add_ref(pg.route(port1 = g2.ports[1], port2 = wg.ports['E']))
    
    R = Device();
    
    for i, g in enumerate(gaps):
        r = R.add_ref(pg.ring(radius = radius + dR*i, width = wRing, angle_resolution = 1, layer = 0)) 
        r.move([period*i,0])
        r.ymax = wg.ymin - g
        rwg = R.add_ref(pg.compass(size=[10, wWg]))
        rwg.move([period*i, 0])
        rwg.ymax = r.ymin-g
        rarc = R.add_ref(pg.arc(radius = 10, width = wWg, theta = 180, start_angle = 90, angle_resolution = 2.5, layer = 0))
        rarc.xmax = rwg.xmin
        rarc.ymax = rwg.ymax
        rtap = R.add_ref(pg.taper(length = 10, width1 = wWg, width2 = 0.1, port = None, layer = 0))
        rtap.xmin = rwg.xmax
        rtap.ymax = rwg.ymax
        
        rwg2 = R.add_ref(pg.compass(size=[10, wWg]))
        rwg2.xmin = rarc.xmax
        rwg2.ymin = rarc.ymin
        
        g3 = R.add_ref(GratingDevice)
        g3.xmin = rwg2.xmax
        g3.connect(port = 1, destination = rwg2.ports['E'])
          
    R.x = D.x
    D.add_ref(R)
    
    return D
    
def adiabaticBeamsplitter(interaction_length = 10, gap1 = 1, gap2 = 0.1, 
                          port1 = 0.4, port2 = 0.5, port3 = 0.4, port4 = 0.4,
                          hSines = 3, rMin = 10):

    lSines = np.sqrt((np.pi**2)*hSines*rMin/2)
    #
    D = Device("adiabatic beam splitter")
    #
    # start with the actual beamsplitter part
    xpts_upper = [0, 0, interaction_length, interaction_length]
    ypts_upper = [0, port1, port3, 0]
    
    wg_upper = D.add_ref(polygon(xcoords = xpts_upper, ycoords = ypts_upper, layer = 0))
    #
    xpts_lower = [0, 0, interaction_length, interaction_length]
    ypts_lower = [-gap1, -gap1-port2, -gap2-port4, -gap2]
    wg_lower = D.add_ref(polygon(xcoords = xpts_lower, ycoords = ypts_lower, layer = 0))
    
    #locate the straight sections after the sine bends
    P = Device('ports')
    P.add_port(name = 'port 1', midpoint = [wg_upper.xmin-lSines, wg_upper.center[1]+hSines], width = port1, orientation = 0)
    P.add_port(name = 'port 2', midpoint = [wg_lower.xmin-lSines, wg_lower.center[1]-hSines], width = port1, orientation = 0)
    P.add_port(name = 'port 3', midpoint = [wg_upper.xmax+lSines, wg_upper.center[1]+hSines], width = port1, orientation = 180)
    P.add_port(name = 'port 4', midpoint = [wg_lower.xmax+lSines, wg_lower.center[1]-hSines], width = port1, orientation = 180)
    route1 = D.add_ref(pg.route(port1 = P.ports['port 1'], port2 = wg_upper.ports['0'], path_type = 'sine'))
    route2 = D.add_ref(pg.route(port1 = P.ports['port 2'], port2 = wg_lower.ports['0'], path_type = 'sine'))
    route3 = D.add_ref(pg.route(port1 = P.ports['port 3'], port2 = wg_upper.ports['2'], path_type = 'sine'))
    route4 = D.add_ref(pg.route(port1 = P.ports['port 4'], port2 = wg_lower.ports['2'], path_type = 'sine'))
    
    D.add_port(port = route1.ports[1], name = 1)
    D.add_port(port = route2.ports[1], name = 2)
    D.add_port(port = route3.ports[1], name = 3)
    D.add_port(port = route4.ports[1], name = 4)
    
    return D

def beamTap(interaction_length = 10, hSines = 5, rMin = 10, gap = 0.5, wWg= 0.4): 
                                   
    lSines = np.sqrt(hSines*np.pi**2*rMin/2)    
    D = Device()
    
    WG = pg.compass(size=[interaction_length, wWg])
    wg1 = D.add_ref(WG)
    wg2 = D.add_ref(WG)
    
    wg1.center = wg2.center
    wg1.ymin = wg1.ymax + gap
    
    P = Device()
    port1 = P.add_port(name = 1, midpoint = wg1.ports['W'].midpoint+[-1*lSines, hSines], width = wWg, orientation = 0)
    port2 = P.add_port(name = 2, midpoint = wg2.ports['W'].midpoint+[-1*lSines, 0], width = wWg, orientation = 0)
    port3 = P.add_port(name = 3, midpoint = wg1.ports['E'].midpoint+[lSines,hSines], width = wWg, orientation = 180)
    port4 = P.add_port(name = 4, midpoint = wg2.ports['E'].midpoint+[lSines, 0], width = wWg, orientation = 180)
    
    route1 = D.add_ref(pg.route(port1 = wg1.ports['W'], port2 = port1))
    route2 = D.add_ref(pg.route(port1 = wg2.ports['W'], port2 = port2))
    route3 = D.add_ref(pg.route(port1 = wg1.ports['E'], port2 = port3))
    route4 = D.add_ref(pg.route(port1 = wg2.ports['E'], port2 = port4))
    D.add_ref(P)
    
    D.add_port(port = route1.ports[2], name = 1)
    D.add_port(port = route2.ports[2], name = 2)
    D.add_port(port = route3.ports[2], name = 3)
    D.add_port(port = route4.ports[2], name = 4)
    quickplot(D)

def MZI(FSR = 0.05, ng = 4, rMin = 10, wavelength = 1.55, BS = gdspy.Cell, **kwargs):
    # MZI. input the FSR and ng and it calculates the largest hSines for a given minimum radius of curvature.
# optionally you can input devices for the four ports of the MZI. If you leave them empty it will just put ports on.


    # for a given ratio of hSines and lSines we can analytically estimate the FSR based 
    #on the length of a sine from 2*pi to 0 = 7.64. For some reason here we have a scale factor to 6.66
    dL = wavelength**2/ng/FSR
    # ok, but we still have to make our best initial guess at lSines
    lSines_approx = dL/(9/2/np.pi-1)
    # based on that guess + the rMin we calculate the ratio of hSines/lSines
    r = 2*lSines_approx/np.pi**2/rMin
    # now using that ratio we actually calculate the factor F, which is an elliptic integral
    MZI_factors = np.load('MZI_factors.npy')
    f = interp1d(MZI_factors[:,0],MZI_factors[:,1],kind='cubic')
    F = f(r)
    # now we can recalculate lSines and hSines
    lSines = dL/(F/(2*np.pi)-1)
    hSines = r*lSines
    
    # build the device
    D = Device()
    bS1 = D.add_ref(BS)
    bS2 = D.add_ref(BS)
    bS1.reflect(p1 = bS1.ports[3], p2 = bS1.ports[4])
    P = Device()
    P.add_port(name = 1, midpoint = bS1.ports[3].midpoint+[lSines/2,hSines], width = bS1.ports[3].width, orientation = 180)
    P.add_port(name = 2, midpoint = bS1.ports[3].midpoint+[lSines/2,hSines], width = bS1.ports[3].width, orientation = 0)
    D.add_ref(P)
    bS1.movex(lSines)
    route1 = D.add_ref(pg.route(port1 = P.ports[1], port2 = bS2.ports[3], path_type = 'sine'))
    route2 = D.add_ref(pg.route(port1 = P.ports[2], port2 = bS1.ports[3], path_type = 'sine'))
    route3 = D.add_ref(pg.route(port1 = bS1.ports[4], port2 = bS2.ports[4]))
    calc_length = route1.meta['length']+route2.meta['length']-route3.meta['length']
    calc_fsr = wavelength**2/ng/calc_length
    D.meta['Calculated FSR'] = calc_fsr
    # now we put either devices or ports on the 4 outputs of the MZI
    n = len(kwargs)
    dest = {0: bS2.ports[1], 1: bS2.ports[2], 2: bS1.ports[1], 3: bS1.ports[2]}
    
    for i in range(0, len(kwargs)):
        dP = D.add_ref(kwargs[kwargs.keys()[i]])
        dP.connect(port = dP.ports[1], destination = dest[i])
        D.add_ref(dP)
    for i in range(len(kwargs), 4):
        D.add_port(port = dest[i], name = i+1)

    return D

def wgSNSPD():
    pass

def LED(wWg=1, lWg=10, wDopeOffset=0.2, wDope=5, wE=1, metalInset = 0.2, 
        padsShiftLat = 0, wTaper = 0.4, lTaper = 10, wgLayer = 0, pLayer = 1, 
        nLayer = 2, wLayer = 3):
 
    D = Device("LED")
    
    wg = D.add_ref(pg.compass(size=[lWg,wWg],layer=wgLayer))
    wRegion = D.add_ref(pg.compass(size=[lWg,wE],layer=wLayer))
    pRegion = D.add_ref(pg.compass(size=[lWg,wDope],layer=pLayer))
    nRegion = D.add_ref(pg.compass(size=[lWg,wDope],layer=nLayer))
    taper = D.add_ref(pg.taper(length = lTaper, width1 = wWg, width2 = wTaper))
    
    taper.xmin = wg.xmax
    wg.connect(port = 'W', destination = taper.ports[1])
    wg.center = wRegion.center
    pRegion.ymin = wRegion.ymax + wDopeOffset
    pRegion.center[0] = wRegion.center[0]
    nRegion.ymax = wRegion.ymin - wDopeOffset
    nRegion.center[0] = wRegion.center[0]
    D.add_port(port = taper.ports[2], name = 'LED')
    return D
    
def hidra():
    pass

def hexapod():
    pass
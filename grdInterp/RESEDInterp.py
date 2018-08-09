from __future__ import print_function
from descartes import PolygonPatch
from shapely.ops import cascaded_union, polygonize
from scipy.spatial import Delaunay
from shapely.geometry import Polygon, Point

import string
import os
import sys
import base64
import math

import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
import numpy.random as rnd
import matplotlib.mlab as mlab
import time
import pylab as pl
import shapely.geometry as geometry



def get_max(x):
	max = 0
	for i in range(0, len(x)):
		if(i==0):
			max = x[0]
		else:
			if(max < x[i]):
				max = x[i]
	return max

def get_min(x):
	min = 0
	for i in range(0, len(x)):
		if(i==0):
			min = x[0]
		else:
			if(min > x[i]):
				min = x[i]
	return min

def plot_polygon(polygon):
    fig = pl.figure(figsize=(10,10))
    ax = fig.add_subplot(111)
    margin = .3

    x_min, y_min, x_max, y_max = polygon.bounds

    ax.set_xlim([x_min-margin, x_max+margin])
    ax.set_ylim([y_min-margin, y_max+margin])
    patch = PolygonPatch(polygon, fc='#999999', ec='#000000', fill=True, zorder=-1)
    ax.add_patch(patch)
    return fig

def alpha_shape(points, alpha):
    """
    Compute the alpha shape (concave hull) of a set of points.

    @param points: Iterable container of points.
    @param alpha: alpha value to influence the gooeyness of the border. Smaller
                  numbers don't fall inward as much as larger numbers. Too large,
                  and you lose everything!
    """
    if len(points) < 4:
        # When you have a triangle, there is no sense in computing an alpha
        # shape.
        return geometry.MultiPoint(list(points)).convex_hull

    def add_edge(edges, edge_points, coords, i, j):
        """Add a line between the i-th and j-th points, if not in the list already"""
        if (i, j) in edges or (j, i) in edges:
            # already added
            return
        edges.add( (i, j) )
        edge_points.append(coords[ [i, j] ])

    coords = np.array([point.coords[0] for point in points])

    tri = Delaunay(coords)
    edges = set()
    edge_points = []
    # loop over triangles:
    # ia, ib, ic = indices of corner points of the triangle
    for ia, ib, ic in tri.vertices:
        pa = coords[ia]
        pb = coords[ib]
        pc = coords[ic]

        # Lengths of sides of triangle
        a = math.sqrt((pa[0]-pb[0])**2 + (pa[1]-pb[1])**2)
        b = math.sqrt((pb[0]-pc[0])**2 + (pb[1]-pc[1])**2)
        c = math.sqrt((pc[0]-pa[0])**2 + (pc[1]-pa[1])**2)

        # Semiperimeter of triangle
        s = (a + b + c)/2.0

        # Area of triangle by Heron's formula
        area = math.sqrt(s*(s-a)*(s-b)*(s-c))
        try:
            circum_r = a*b*c/(4.0*area)
        except:
            circum_r = 0

        # Here's the radius filter.
        #print circum_r
        if circum_r < 1.0/alpha:
            add_edge(edges, edge_points, coords, ia, ib)
            add_edge(edges, edge_points, coords, ib, ic)
            add_edge(edges, edge_points, coords, ic, ia)

    m = geometry.MultiLineString(edge_points)
    triangles = list(polygonize(m))
    return cascaded_union(triangles), edge_points

def within_polygon(grid_point, concave_hull, buffer):
    intw = 0
    if grid_point.within(concave_hull.buffer(buffer)):
        intw = 1
    return intw
	
def isNum(value):
    try:
        value + 1
    except TypeError:
        return False
    else:
        return True

IFName = sys.argv[1]
OFName = sys.argv[2]
reso = float(sys.argv[3])
convex_buff = reso/100.0 
IDATA = open(IFName,"r")
Nx = 0
Ny = 0

P1 = IDATA.readline().strip('\n').split()
projName = P1[0].split(".")[0]

for i in range (0,20):
	P1 = IDATA.readline().strip('\n').split()
	if(i==0):#get Nx Ny
		Nx = int(P1[0])
		Ny = int(P1[1])
LnY = math.ceil(Ny/10)

N = Nx*Ny
Xc = N*[0]
Yc = N*[0]

print(projName,Nx,Ny,LnY)
c = 0
for x in range(0,Nx):
	for ly in range(0,LnY):
		P1 = IDATA.readline().strip('\n').split()
		for l in range(0,len(P1)):
			Xc[c] = float(P1[l])
			c = c+1
c = 0
for x in range(0,Nx):
	for ly in range(0,LnY):
		P1 = IDATA.readline().strip('\n').split()
		for l in range(0,len(P1)):
			Yc[c] = float(P1[l])
			c = c+1
print (len(Xc))
print (len(Yc))
#print (Xc)
#print (Yc)

#依照模擬網格點取凹多邊形 concave_hull2
points2 = geometry.MultiPoint(list(zip(Xc, Yc)))
concave_hull2, edge_points2 = alpha_shape(points2 ,alpha=0.01)
_ = plot_polygon(concave_hull2)

#計算基本數據
xmax = get_max(Xc)
xmin = get_min(Xc)
ymax = get_max(Yc)
ymin = get_min(Yc)
print(xmin,xmax,ymin,ymax)
IntNx = (xmax-xmin)/reso
IntNy = (ymax-ymin)/reso
IDATA.close()

#讀變數資料
ODATA = open(OFName,"r")
var_string = ['U-VELOCITY','V-VELOCITY','DEPTH','ABS-UV-VELOCITY']
v_string = []
zb_string = ['INI-ZB']
Time = []
lines = []
Time_lno = []
Var_lno = []
Var_type = []

temp_arr = N*[0]
Zb = N*[0]
UV = N*[0]
VV = N*[0]
DEP = N*[0]
ABSUV = N*[0]
Zbln = 0

datalines = ODATA.readlines()
ln = 0
for linedata in datalines:
	P1 = linedata.strip('\n').split()
	if(P1[0]=="TIME="):
		Time_lno.append(ln)
		Time.append(P1[1])
		lines.append(int(P1[2]))
	ln = ln+1
for nl in range(1,Time_lno[1]-1,Nx+1):
	P1 = datalines[nl].strip('\n').split()
	v_string.append(P1[0])
ln = 0
for linedata in datalines:
	P1 = linedata.strip('\n').split()
	if P1[0] in v_string:
		Var_lno.append(ln)
		idx = v_string.index(P1[0])
		Var_type.append(v_string[idx])
	ln = ln+1
print (Var_lno)
print (Var_type)

c = 0
if(Var_lno[0]>Time_lno[0]):#read ZB-ini
	for effln in range(Var_lno[0]+1,Var_lno[0]+1+Nx):
		for d in range(0,Ny*10,10):
			Zb[c] = float(datalines[effln][d:d+10])
			c = c+1

#內插用的正交網格點
xi = np.linspace(xmin, xmax, IntNx)
yi = np.linspace(ymin, ymax, IntNy)
#判斷及輸出用的座標

xo = len(xi)*len(yi)*[0]
yo = len(xi)*len(yi)*[0]
zo = len(xi)*len(yi)*[0]
widx = len(xi)*len(yi)*[0]#0表示在polygon外側
for j in range(0,len(yi)):
	for i in range(0,len(xi)):
		idx = j*len(xi)+i
		if(idx%1000==0):
			print ("judge",idx)
		xo[idx] = xi[i]
		yo[idx] = yi[j]
		widx[idx] = within_polygon(Point(xo[idx], yo[idx]),concave_hull2, 0)
print ("judge OK")

for t in range(0,len(Time_lno)):
	ALLDATA = []
	ALLDATA.append(Xc)
	ALLDATA.append(Yc)
	ALLDATA.append(Zb)
	OUTPUTDATA = []
	OUTPUTDATA.append(xo)
	OUTPUTDATA.append(yo)
	OUTPUTDATA.append(widx)
	
	OutFileName = projName+"_"+Time[t]+"_q.csv"
	OutDATA = open(OutFileName,"w")
	#OutDATA.write('{0}\n'.format(projName))
	#OutDATA.write('{0} {1}\n'.format(Nx*Ny,Time[t]))
	OutDATA.write('X Y idx {0}'.format(v_string[0]))
	for i in range (1,len(v_string)):
		OutDATA.write(' {0}'.format(v_string[i]))
	OutDATA.write('\n')
	
	print (OutFileName)
	lmin = Time_lno[t]
	if(t<len(Time_lno)-1):
		lmax = Time_lno[t+1]
	else:
		lmax = len(datalines)
	
	for var in range(1,len(Var_lno)):
		temp_arr = N*[0]
		if (Var_lno[var]>lmin and Var_lno[var]<lmax):
			c = 0
			for effln in range(Var_lno[var]+1,Var_lno[var]+1+Nx):
				for d in range(0,Ny*10,10):
					temp_arr[c] = float(datalines[effln][d:d+10])
					c = c+1
			ALLDATA.append(temp_arr)

	Zc = N*[0]
	for j in range (2,len(ALLDATA)):
		zo = len(xi)*len(yi)*[0] 
		for i in range(0,Nx*Ny):
			Zc[i] = float(ALLDATA[j][i])#將某個物理變數，放到Zc裡
		zi = mlab.griddata(Xc, Yc, Zc, xi, yi, interp='linear')
		for jj in range(0,len(yi)):
			for ii in range(0,len(xi)):
				idx = jj*len(xi)+ii
				zo[idx] = zi[jj][ii]
		OUTPUTDATA.append(zo)
	
	for k in range(0,len(xo)):
		for v in range (0,len(OUTPUTDATA)):
			#print (type(OUTPUTDATA[4][k]))
			#if(OUTPUTDATA[4][k] == "--"):
			#	pass
			if((widx[k]==1)and(type(OUTPUTDATA[4][k])!=np.ma.core.MaskedConstant)):
				#print (OUTPUTDATA[v][k])
				if(v!=len(OUTPUTDATA)-1):
					OutDATA.write('{0} '.format(OUTPUTDATA[v][k]))
				else:
					OutDATA.write('{0}\n'.format(OUTPUTDATA[v][k]))
			else:
				pass
	OutDATA.close()
	
'''
	for i in range(0,Nx*Ny):
		for j in range (0,len(ALLDATA)):
			if(j!=len(ALLDATA)-1):
				OutDATA.write('{0} '.format(ALLDATA[j][i]))
			else:
				OutDATA.write('{0}\n'.format(ALLDATA[j][i]))
	OutDATA.close()
'''
	#ALLDATA.clear()
	#output
#print (ALLDATA)
#print (zi)

#xp = []
#yp = []


		
#plt.contour(xi, yi, zi, 15, linewidths=0.5, colors='k')
#plt.contourf(xi, yi, zi, 15,
#			norm=plt.Normalize(vmax=abs(zi).max(), vmin=-abs(zi).max()))
#plt.colorbar()  # draw colorbar
#plt.plot(xp, yp, 'ko', ms=3)
#plt.xlim(xmin, xmax)
#plt.ylim(ymin, ymax)
##plt.title('griddata and contour (%d points, %d grid points)' %
##		(N, IntNx*IntNy))
###print('griddata and contour seconds: %f' % (time.clock() - start))
##
#plt.show()




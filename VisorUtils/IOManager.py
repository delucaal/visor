#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 18:29:50 2020

@author: albdl
"""

from pymatreader import read_mat
import numpy as np
import time

class VisorIO(object):
    
    @staticmethod
    def LoadMATTractography(filename,max_tracts=1e10):
        t = time.time()
        MatFile = read_mat(filename,variable_names=['Tracts','TractMask','VDims']);
        elapsed = time.time() - t
        print('Loading of MAT took ' + str(elapsed) + 's')
        t = time.time()
        
        Tracts = MatFile['Tracts']#np.asarray(MatFile['Tracts']);
        TractMask = MatFile['TractMask']
        VD = MatFile['VDims']        
        
        # for i in range(0,min(Tracts.shape[0],max_tracts)):
        for i in range(0,min(len(Tracts),max_tracts)):
            P = Tracts[i]
            # P[:,0] = TractMask.shape[0]*VD[1]-P[:,0]
            # P[:,1] = TractMask.shape[1]*VD[0]-P[:,1]
            P[:,0] = TractMask.shape[1]-P[:,0]/VD[0]
            P[:,1] = TractMask.shape[0]-P[:,1]/VD[1]
            P[:,2] = P[:,2]/VD[2]
            Tracts[i] = P
        
        return Tracts
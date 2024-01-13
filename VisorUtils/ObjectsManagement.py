#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 18:04:40 2020

@author: albdl
"""

class ObjectsManager(object):
    tracts_list = [];
    fod_list = [];
    images_list = [];
    rois_list = []

    @staticmethod
    def RemoveTractographyObjects():
        ObjectsManager.fod_list = []
        ObjectsManager.actors_list = []
        ObjectsManager.rois_list = []
        ObjectsManager.tracts_list = []

    @staticmethod
    def AddFODObject(theObject):
        ObjectsManager.fod_list.append(theObject)
       
    @staticmethod
    def RemoveFODObject():
        ObjectsManager.fod_list = []
    
    @staticmethod
    def AddTractographyObject(theActor):
        ObjectsManager.tracts_list.append(theActor)
        
    @staticmethod
    def RemoveTractographyObject(zin):
        ObjectsManager.tracts_list.remove(ObjectsManager.tracts_list[zin])

    @staticmethod
    def IndexOfTractographyObject(theActor):
        idx = -1
        for i in range(0,len(ObjectsManager.tracts_list)):
            if(ObjectsManager.tracts_list[i].actor == theActor):
                idx = i
                break
        return idx
            
    @staticmethod
    def AddImageObject(theImage):
        ObjectsManager.images_list.append(theImage)
    
    @staticmethod
    def RemoveImageObject(zin):
        ObjectsManager.images_list.remove(ObjectsManager.images_list[zin])
    
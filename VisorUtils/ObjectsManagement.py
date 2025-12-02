#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 18:04:40 2020

@author: albdl
"""

class ObjectsManager(object):
    tracts_list = []
    fod_list = []
    images_list = []
    rois_list = []
    rois_groups_list = []
    surfaces_list = []

    @staticmethod
    def AddSurfaceObject(theSurface):
        ObjectsManager.surfaces_list.append(theSurface)
        
    @staticmethod
    def RemoveSurfaceObject(zin):
        ObjectsManager.surfaces_list.remove(ObjectsManager.surfaces_list[zin])
        
    @staticmethod
    def IndexOfSurfaceObject(theActor):
        idx = -1
        for i in range(0,len(ObjectsManager.surfaces_list)):
            if(ObjectsManager.surfaces_list[i].actor == theActor):
                idx = i
                break
        return idx

    @staticmethod
    def RemoveTractographyObjects():
        ObjectsManager.fod_list = []
        #ObjectsManager.actors_list = []
        ObjectsManager.rois_list = []
        ObjectsManager.tracts_list = []
        ObjectsManager.rois_groups_list = []

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
    def IndexOfROIObject(theActor):
        idx = -1
        for i in range(0,len(ObjectsManager.rois_list)):
            if(ObjectsManager.rois_list[i].actor == theActor):
                idx = i
                break
        return idx
    
    @staticmethod
    def IndexOfROIGroupObject(theName):
        idx = -1
        for i in range(0,len(ObjectsManager.rois_groups_list)):
            if(ObjectsManager.rois_groups_list[i].name == theName):
                idx = i
                break
        return idx
            
    @staticmethod
    def AddImageObject(theImage):
        ObjectsManager.images_list.append(theImage)
    
    @staticmethod
    def RemoveImageObject(zin):
        ObjectsManager.images_list.remove(ObjectsManager.images_list[zin])
    
    @staticmethod
    def AddROIObject(theROI):
        ObjectsManager.rois_list.append(theROI)
    
    @staticmethod
    def RemoveROIObject(zin):
        ObjectsManager.rois_list.remove(ObjectsManager.rois_list[zin])
        
    @staticmethod
    def IndexOfROIObject(theActor):
        idx = -1
        for i in range(0,len(ObjectsManager.rois_list)):
            if(ObjectsManager.rois_list[i].actor == theActor):
                idx = i
                break
        return idx
    
    @staticmethod
    def AddROIGroupObject(theGroup):
        ObjectsManager.rois_groups_list.append(theGroup)
        
    @staticmethod
    def RemoveROIGroupObject(zin):
        ObjectsManager.rois_groups_list.remove(ObjectsManager.rois_groups_list[zin])
    

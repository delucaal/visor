# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 08:30:05 2020

@author: user
"""


import threading
import time

class ThreadProps:
    Busy = False
    AskedAgain = False
    ScheduledArguments = ()

class MethodInBackground(object):
    
    def __init__(self,target_method,args):
        print('Arguments would be')
        print(args)
        if(ThreadProps.Busy == False):
            print('Thread not busy - can start')
            ThreadProps.Busy = True
            ThreadProps.AskedAgain = False
            self.target_method = target_method
            self.thread = threading.Thread(target=self.run,args=[args,])
            self.thread.daemon = True
            self.thread.start()
        else:
            print('Cannot start another thread - scheduling')
            ThreadProps.AskedAgain = True
            ThreadProps.ScheduledArguments = args
            
        # self.thread.join()
        
    def run(self,args):
        print('Thread run arguments ')
        print(args)
        if(self.target_method != 0):
            self.target_method(args)
        # self.thread.join()
        time.sleep(0.1)
        if(ThreadProps.AskedAgain == True):
            print('Asked to run again')
            ThreadProps.AskedAgain = False
            self.target_method(ThreadProps.ScheduledArguments)        
        ThreadProps.Busy = False
        # self.thread.join()        
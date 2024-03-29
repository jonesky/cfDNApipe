# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 15:58:34 2019

@author: zhang
"""


from .StepBase import StepBase
from .cfDNA_utils import commonError
import os, re
from .Configure import Configure


__metaclass__ = type


class adapterremoval(StepBase):
    def __init__(self, 
                 fqInput1 = None, # list
                 fqInput2 = None, # list
                 outputdir = None, # str
                 threads = 1,
                 adapter1 = ['AGATCGGAAGAGCACACGTCTGAACTCCAGTCA'],
                 adapter2 = ['AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT'],
                 other_params = {'--qualitybase': 33, '--gzip': True},
                 upstream = None,
                 formerrun = None,
                 **kwargs):
        if upstream is None:
            super(adapterremoval, self).__init__()
            self.setInput('fq1', fqInput1)
            self.setInput('fq2', fqInput2)
            self.checkInputFilePath()
            
            if outputdir is None:
                self.setOutput('outputdir', os.path.dirname(os.path.abspath(self.getInput('fq1')[1])))
            else:
                self.setOutput('outputdir', outputdir)
                
            self.setParam('threads', threads)
            self.setParam('adapter1', adapter1)
            self.setParam('adapter2', adapter2)
            
        else:
            # here to check upstream source!!!!!!!!!!!!!!!!!!!!!!!!!!
            # upstream can come from inputprocess and identifyAdapter
            
            # super init
            if formerrun is None:
                super(adapterremoval, self).__init__(upstream.getStepID())
            else:
                super(adapterremoval, self).__init__(formerrun.getStepID())
            
            # check Configure for running pipeline
            Configure.configureCheck()
            
            upstream.checkFilePath()
            
            self.setInput('fq1', upstream.getOutput('fq1'))
            self.setInput('fq2', upstream.getOutput('fq2'))
            
            self.setOutput('outputdir', self.getStepFolderPath())
            
            if upstream.__class__.__name__ not in ['identifyAdapter', 'inputprocess']:
                raise commonError('Parameter upstream must from inputprocess or identifyAdapter.')
            
            if upstream.__class__.__name__ == 'identifyAdapter':
                # using identified adapters
                adapter1 = []
                adapter2 = []
                for fq1, fq2 in zip(self.getInput('fq1'), self.getInput('fq2')):
                    basename = self.getMaxFileNamePrefix(fq1, fq2)
                    adapter_file = upstream.getOutput(basename + '-adapterFile')
                    adapters = self.getAdapetrFromFile(adapter_file)
                    adapter1.append(adapters[0])
                    adapter2.append(adapters[1])

            self.setParam('adapter1', adapter1)
            self.setParam('adapter2', adapter2)
            
            self.setParam('threads', Configure.getThreads())
            
        # generate base name
        basenames = []
        for fq1, fq2 in zip(self.getInput('fq1'), self.getInput('fq2')):
            basenames.append(self.getMaxFileNamePrefix(fq1, fq2))
        self.setParam('basename', basenames)
        
        self.setParam('outPrefix', [os.path.join(self.getOutput('outputdir'), x) for x in self.getParam('basename')])
            
        if other_params is None:
            self.setParam('other_params', '')
        else:
            self.setParam('other_params',  other_params)
        
        if len(self.getInput('fq1')) == len(self.getInput('fq2')):
            multi_run_len = len(self.getInput('fq1'))
        else:
            raise commonError('Paired end Input files are not consistent.')
            
        self.setOutput('discarded', [(os.path.join(self.getOutput('outputdir'), x) + '.discarded.gz') for x in self.getParam('basename')])
        self.setOutput('settings', [(os.path.join(self.getOutput('outputdir'), x) + '.settings') for x in self.getParam('basename')])
        self.setOutput('pair1', [(os.path.join(self.getOutput('outputdir'), x) + '.pair1.truncated.gz') for x in self.getParam('basename')])
        self.setOutput('pair2', [(os.path.join(self.getOutput('outputdir'), x) + '.pair2.truncated.gz') for x in self.getParam('basename')])
        self.setOutput('singleton', [(os.path.join(self.getOutput('outputdir'), x) + '.singleton.truncated.gz') for x in self.getParam('basename')])
        
        all_cmd = []
        
        for i in range(multi_run_len):
            tmp_cmd = self.cmdCreate(["AdapterRemoval", 
                                       '--threads', self.getParam('threads'),
                                       '--file1', self.getInput('fq1')[i],
                                       '--file2', self.getInput('fq2')[i],
                                       '--adapter1', self.getParam('adapter1')[i],
                                       '--adapter2', self.getParam('adapter2')[i],
                                       '--basename', self.getParam('outPrefix')[i],
                                       self.getParam('other_params')])
            all_cmd.append(tmp_cmd)
            
        self.setParam('cmd', all_cmd)
        
        finishFlag = self.stepInit(upstream)
        
        self.excute(finishFlag)

            
            
            
            
    # get adapter from file
    def getAdapetrFromFile(self, file):
        adapter = []
        with open(file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if re.search(r'Consensus:', line):
                    tmp_line = line.split()
                    adapter.append(tmp_line[1])
        
        return(adapter)





            
            
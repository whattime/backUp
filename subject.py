# -*- coding: utf-8 -*-
from __future__ import division
import os
import dicom
import re
import pandas as pd
import getpass

from progressbar import AnimatedMarker,ProgressBar,Percentage,Bar
class subject(object):
    def __init__(self, subjectDir, dbLoc):
        self.location = subjectDir


        dicomDirDict = {}

        pbar = ProgressBar()
        for root, dirs, files in os.walk(self.location):
            dicoms = []
            for oneFile, i in zip(files, pbar(range(6000))):
                if re.search('(dcm|ima)', oneFile, re.IGNORECASE):
                    dicoms.append(os.path.join(root,oneFile))
            if not dicoms == [] : dicomDirDict[root] = dicoms

        self.dicomDirs = dicomDirDict
        self.dirs = dicomDirDict.keys()
        self.allDicoms = reduce(lambda x, y: x + y, dicomDirDict.values())
        self.allDicomNum = len(self.allDicoms)
        self.dirDicomNum = [(x,len(y)) for (x,y) in dicomDirDict.iteritems()]
        self.firstDicom = self.allDicoms[0]
        self.modalityMapping = [modalityMapping(x) for x in self.dirs]
        self.modalityDicomNum = dict(zip(self.modalityMapping, [x[1] for x in self.dirDicomNum]))

        ds = dicom.read_file(self.firstDicom)
        self.age = re.search('^0(\d{2})Y',ds.PatientAge).group(1)
        self.dob = ds.PatientBirthDate
        self.id = ds.PatientID
        self.surname = ds.PatientName.split('^')[0]
        self.name = ds.PatientName.split('^')[1]
        try:
            self.fullname = ''.join([x[0].upper()+x[1:].lower() for x in [self.surname, self.name.split(' ')[0], self.name.split(' ')[1]]])
            self.initial = self.surname[0]+''.join([x[0] for x in self.name.split(' ')])
        except:
            self.fullname = ''.join([x[0].upper()+x[1:].lower() for x in [self.surname, self.name]])
            self.initial = self.surname[0]+self.name[0]
        
        self.sex = ds.PatientSex
        self.date = ds.StudyDate
        self.experimenter = getpass.getuser()

        print 'Now collecting information for'
        print '=============================='
        print '\n\t'.join([self.location, self.fullname, self.initial, self.id, self.dob, 
                           self.date, self.sex, ', '.join(self.modalityMapping),
                           'by ' + self.experimenter])
        print '=============================='

        self.koreanName = raw_input('Korean name  ? eg. 김민수: ')
        self.note = raw_input('Any note ? : ')
        self.group = raw_input('Group ? : ')
        self.numberForGroup = maxGroupNum(os.path.join(dbLoc, self.group))
        self.study = raw_input('Study name ? : ')

        self.timeline = raw_input('baseline or follow up ? eg) baseline or followup : ')#unicodeDecodeError.2yfu
        if self.timeline != 'baseline':
            df = pd.ExcelFile(os.path.join(dbLoc,'database','database.xls')).parse(0)
            self.folderName = df.ix[(df.timeline=='baseline') & (df.patientNumber == int(self.id)), 
                                     'folderName'].get_values().tostring()

            if self.folderName == '':
                self.folderName = self.group + self.numberForGroup + '_' + self.initial
        else:
            self.folderName = self.group + self.numberForGroup + '_' + self.initial

        self.targetDir = os.path.join(dbLoc,
                self.group,
                self.group + self.numberForGroup + '_' + self.initial,
                self.timeline)

def modalityMapping(directory):
    t1 = re.compile(r'tfl|[^s]t1',re.IGNORECASE)
    dti = re.compile(r'dti\S*\(.\)_\d+\S*',re.IGNORECASE)
    dtiFA = re.compile(r'dti.*[^l]fa',re.IGNORECASE)
    dtiEXP = re.compile(r'dti.*exp',re.IGNORECASE)
    dtiCOLFA = re.compile(r'dti.*colfa',re.IGNORECASE)
    dki = re.compile(r'dki\S*\(.\)_\d+\S*',re.IGNORECASE)
    dkiFA = re.compile(r'dki.*[^l]fa',re.IGNORECASE)
    dkiEXP = re.compile(r'dki.*exp',re.IGNORECASE)
    dkiCOLFA = re.compile(r'dki.*colfa',re.IGNORECASE)
    rest = re.compile(r'rest|rest\S*4060',re.IGNORECASE)
    t2flair = re.compile(r'flair',re.IGNORECASE)
    t2tse = re.compile(r'tse',re.IGNORECASE)
    scout = re.compile(r'scout',re.IGNORECASE)

    for modality in (t1,'T1'),(rest,'REST'),(dki,"DKI"),(dti,'DTI'),(t2flair,'T2FLAIR'),(t2tse,'T2TSE'),(dtiFA,'DTI_FA'),(dtiEXP,   'DTI_EXP'),(dtiCOLFA,'DTI_COLFA'),(dkiFA,'DKI_FA'),(dkiEXP,'DKI_EXP'),(dkiCOLFA,'DKI_COLFA'), (scout, 'SCOUT'):
        basename = os.path.basename(directory)
        try:
            matchingSource = modality[0].search(basename).group(0)
            return modality[1]
        except:
            pass
    return directory


def maxGroupNum(backUpTo):
    maxNumPattern=re.compile('\d+')

    mx = 0
    for string in maxNumPattern.findall(' '.join(os.listdir(backUpTo))):
        if int(string) > mx:
            mx = int(string)

    highest = mx +1

    if highest<10:
        highest ='0'+str(highest)
    else:
        highest = str(highest)

    return highest


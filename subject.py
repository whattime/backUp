import os
import dicom
import re
import getpass

class subject(object):
    def __init__(self, input):
        self.location = input

        dicomDirDict = {}
        for root, dirs, files in os.walk(self.location):
            dicoms = []
            for oneFile in files:
                if re.search('(dcm|ima)', oneFile, re.IGNORECASE):
                    dicoms.append(os.path.join(root,oneFile))
            if not dicoms == [] : dicomDirDict[root] = dicoms

        self.dicomDirs = dicomDirDict
        self.dirs = dicomDirDict.keys()
        self.allDicoms = reduce(lambda x, y: x + y, dicomDirDict.values())
        self.allDicomNum = len(self.allDicoms)
        self.firstDicom = self.allDicoms[0]

        ds = dicom.read_file(self.firstDicom)
        self.age = re.search('^0(\d{2})Y',ds.PatientAge).group(1)
        self.dob = ds.PatientBirthDate
        self.id = ds.PatientID
        self.fullname = ds.PatientName
        self.surname = ds.PatientName.split('^')[0]
        self.name= ds.PatientName.split('^')[1]
        self.sex = ds.PatientSex
        self.date = ds.StudyDate
        self.experimenter = getpass.getuser()

        self.note = raw_input('Any note ? : ')

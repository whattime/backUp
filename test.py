#from backUp import *
#import backUp
import os
import argparse
import textwrap
import pickle
import backUp
import pandas as pd
import motion_extraction
import freesurfer
import freesurfer_summary


import subject as subj
if os.path.isfile('subjectPickle'):
    with open('subjectPickle', 'r') as f:
        subjClass = pickle.load(f)
else:
    with open('subjectPickle', 'w') as f:
        subjClass = subj.subject('/Users/kangik/KIM_SE_UK_46676612', '/Volumes/promise/nas_BackUp/CCNC_MRI_3T/')
        pickle.dump(subjClass, f)


#execute copy test
try:
    backUp.executeCopy(subjClass)
except:
    pass
print subjClass.folderName
subjDf = backUp.saveLog(subjClass)
print subjDf
DataBaseAddress = 'database.xls'

dbDf = backUp.processDB(DataBaseAddress)
newDf = pd.concat([dbDf, subjDf])
#print newDf
newDf.koreanName = newDf.koreanName.str.decode('utf-8')
newDf.note = newDf.note.str.decode('utf-8')
print 'haha'

newDf.to_excel(DataBaseAddress, 'Sheet1')
os.chmod(DataBaseAddress, 0o2770)




print subjClass.targetDir
#try:
    ##motion_extraction.main(subjClass.targetDir, True, False, False)
#except:
    #pass

#backUp.server_connect('147.47.228.192', os.path.dirname(subjClass.targetDir))

#freesurfer.main(True, False, False, subjClass.targetDir,
        #os.path.join(subjClass.targetDir, 'FREESURFER'))


freesurfer_summary.main('/Volumes/promise/nas_BackUp/CCNC_MRI_3T/CHR/CHR45_JYS/followUp/2yfu', None, "ctx_lh_G_cuneus", True, True, True, True)


#os.popen('sudo rm -rf /Volumes/promise/nas_BackUp/CCNC_MRI_3T/CHR/CHR95_KSU')

#savedList = 
#if 'ha' in os.listdir(os.getcwd()):
    #with open('ha','r') as f:
        #[newDirectoryList, logDf] = pickle.load(f)

## copied directory check test

#else:
    #logDf = copiedDirectoryCheck('pracDir/from', 'pracDir/from/log.xlsx')


    ## newDirectoryGrep
    #newDirectoryList,logDf = newDirectoryGrep(False, 'pracDir/from', logDf)


    #with open('ha', 'w') as f:
        #pickle.dump([newDirectoryList, logDf], f)


#if 'foundDict' in os.listdir(os.getcwd()):
    #with open('foundDict', 'r') as f:
        #foundDict = pickle.load(f)

#else:
    #foundDict=findDtiDkiT1restRest2(newDirectoryList)
    #with open('foundDict', 'w') as f:
        #pickle.dump(foundDict, f)

#backUpTo = './pracDir/to'
#backUpFrom = '.pracDir/from'
#DataBaseAddress = '.pracDir/database.xlsx'

#allInfo,df,newDfList=verifyNumbersAndLog(foundDict,backUpTo,backUpFrom,DataBaseAddress)






#print a.fullname
#print a.name
#print a.initial
#print a.number_for_group
#print a.dirDicomNum


#print a.modalityMapping
#print a.dicomDirs
#print a.dirDicomNum
#print a.modalityMapping
#print a.dirs
#print a.targetDir
#print a.dob
#print a.date



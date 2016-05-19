#from backUp import *
#import backUp
import os
import argparse
import textwrap
import pickle



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



import subject as subj

a = subj.subject('/Users/kangik/KIM_SE_UK_46676612', '/Volumes/promise/nas_BackUp/CCNC_MRI_3T/')
print len(a.allDicoms)



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


import backUp

backUp.checkFileNumbers(a)


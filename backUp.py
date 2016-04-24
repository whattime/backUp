#!/ccnc_bin/venv/bin/python
# -*- coding: utf-8 -*-
import re
import time
from datetime import date
import sys
import os
import tree
import shutil
import getpass
import pickle
from progressbar import AnimatedMarker,ProgressBar,Percentage,Bar
import glob
import argparse
import textwrap
import collections
import pandas as pd
import dicom
import updateSpreadSheet
import motion_extraction
import freesurfer
import freesurfer_summary

# scp modules for network dual back up
import getpass
from paramiko import SSHClient
from scp import SCPClient




def main(args):
    #--------------------------#
    # Initial information      #
    #--------------------------#
    backUpFrom = args.hddLocation
    backUpTo = args.backupDir
    DataBaseAddress = args.database

    # External HDD log
    if args.USBlogFile:
        logFileInUSB = args.USBlogFile
    else args.USBlogFile:
        logFileInUSB = os.path.join(backUpFrom,"log.xlsx")

    #--------------------------------------------------------------------------------
    # Load previously copied directories
    #--------------------------------------------------------------------------------
    #     logDf : log saved in external hard drive
    #     newDirectoryList : recently added directory to the external hard drive
    #
    #     If user wants a directory not to be called again,
    #         logDf is updated with the directory
    #
    #     If there is no new directory --> sys.exit
    #================================================================================
    logDf=copiedDirectoryCheck(backUpFrom,logFileInUSB)
    newDirectoryList,logDf=newDirectoryGrep(args.inputDirs, backUpFrom,logDf)
    
    logDf.to_excel(logFileInUSB,'Sheet1')
    if newDirectoryList==[]:
        sys.exit('Everything have been backed up !')


    #--------------------------------------------------------------------------------
    # check the number of images in the new directories
    #--------------------------------------------------------------------------------
    #     foundDict : {newDirName:{modalityName:modalitySource,fileNumber}}
    #
    #     allInfo : {newDirName:[group,followUp,birthday,note,target,
    #                            subjInitial,fullname,subjNum,targetDirectory,sex,
    #                            allModalityWithLocation,maxNum,backUpTo,backUpFrom,
    #                            koreanName]
    #
    #     df : pandas dataframe made with the function 'log'
    #          including information about the new subjects
    #================================================================================
    foundDict=findDtiDkiT1restRest2(newDirectoryList)

    #if args.prac:
    allInfo,df,newDfList=verifyNumbersAndLog(foundDict,backUpTo,backUpFrom,DataBaseAddress)
    #================================================================================


    #--------------------------------------------------------------------------------
    # check the number of images in the new directories
    #================================================================================
    if args.executeCopy:
        executeCopy(allInfo,df,newDfList)
    #individualLog(allInfo,df)
    #================================================================================


    #--------------------------------------------------------------------------------
    # Update the database excel and log in the external hard-drive
    #================================================================================

    #df = changeencode(df,['koreanName','note'])
    #writer = pd.ExcelWriter(DataBaseAddress)
    #df.to_excel(DataBaseAddress,sheet_name='rearrangeWithId',engine='xlsxwriter')
    #writer.save()

    #df.to_excel(DataBaseAddress,sheet_name='rearrangeWithId',engine='xlsxwriter')
    if args.executeCopy:
        df.to_excel(DataBaseAddress,sheet_name='rearrangeWithId')

        for dirName,value in allInfo.iteritems():
            logDf = noCall(logDf,backUpFrom,dirName)
            logDf.to_excel(logFileInUSB,'Sheet1')
    #================================================================================


    #--------------------------------------------------------------------------------
    # Update the database excel for CCNC
    #================================================================================

    if args.executeCopy:
        class spreadsheetInput():
            def __init__(self):
                self.database = args.database
                self.outExcel = args.spreadsheet
        us_input = spreadsheetInput()
        updateSpreadSheet.main(us_input)

    print '-----------------'
    print 'Completed\n'

    print allInfo
    print df
    print newDfList

    #--------------------------------------------------------------------------------
    # link motion_extraction
    # allInfo[subject]=[group,followUp,birthday,note,target,
    #                   subjInitial,fullname,subjNum,targetDirectory,
    #                   sex,allModalityWithLocation,maxNum,
    #                   backUpTo,backUpFrom,koreanName]
    # ['NOR', 'baseline', '1988-09-16', 'ha', 
    # '/Volumes/promise/CCNC_MRI_3T/NOR', 'CKI', 'ChoKangIk', 
    # '88091612', 'NOR96_CKI', 'M', 
    # {'DTI': ['/Volumes/20141013/CHO_KANG_IK_88091612/RESEARCH_STUDY_RESEARCH_STUDY_20150807_173318_875000/DTI_64D_B1K(2)_0006', 65], 
    # 'REST': ['/Volumes/20141013/CHO_KANG_IK_88091612/RESEARCH_STUDY_RESEARCH_STUDY_20150807_173318_875000/REST_FMRI_PHASE_116_(1)_0005', 4060], 
    # 'T1': ['/Volumes/20141013/CHO_KANG_IK_88091612/RESEARCH_STUDY_RESEARCH_STUDY_20150807_173318_875000/TFL3D_208_SLAB_0004', 208]},
    # '96', '/Volumes/promise/CCNC_MRI_3T', 
    # '/Volumes/20141013', u'\uc870\uac15\uc775']
    #================================================================================

    if args.motion:
        print 'Now, running motion_extraction'
        for subject,infoList in allInfo.iteritems():
            #copiedDir=os.path.join(infoList[4],infoList[8],infoList[1])
            copiedDir=infoList[8]
            motion_extraction.to_nifti(copiedDir,False)
            motion_extraction.to_afni_format(copiedDir)
            motion_extraction.slice_time_correction(copiedDir)
            motion_extraction.motion_correction(copiedDir)
            motion_extraction.make_graph(copiedDir)

        print 'Completed\n'

    #--------------------------------------------------------------------------------
    # link freesurfer
    # allInfo[subject]=[group,followUp,birthday,note,target,
    #                   subjInitial,fullname,subjNum,targetDirectory,
    #                   sex,allModalityWithLocation,maxNum,
    #                   backUpTo,backUpFrom,koreanName]
    # ['NOR', 'baseline', '1988-09-16', 'ha', 
    # '/Volumes/promise/CCNC_MRI_3T/NOR', 'CKI', 'ChoKangIk', 
    # '88091612', 'NOR96_CKI', 'M', 
    # {'DTI': ['/Volumes/20141013/CHO_KANG_IK_88091612/RESEARCH_STUDY_RESEARCH_STUDY_20150807_173318_875000/DTI_64D_B1K(2)_0006', 65], 
    # 'REST': ['/Volumes/20141013/CHO_KANG_IK_88091612/RESEARCH_STUDY_RESEARCH_STUDY_20150807_173318_875000/REST_FMRI_PHASE_116_(1)_0005', 4060], 
    # 'T1': ['/Volumes/20141013/CHO_KANG_IK_88091612/RESEARCH_STUDY_RESEARCH_STUDY_20150807_173318_875000/TFL3D_208_SLAB_0004', 208]},
    # '96', '/Volumes/promise/CCNC_MRI_3T', 
    # '/Volumes/20141013', u'\uc870\uac15\uc775']
    #================================================================================
    if args.freesurfer:
        class fs_args():
            pass

        class fs_summary_args():
            pass
        
        for subject,infoList in allInfo.iteritems():
            #copiedDir=os.path.join(infoList[4],infoList[8],infoList[1])
            copiedDir=infoList[8]
            print copiedDir
            fs.directory = copiedDir
            fs.nifti = True
            fs.file_input = False
            fs.cwd = False
            fs.output = os.path.join(copiedDir,'FREESURFER')

            freesurfer(fs_args)


            fs_summary_args.subject_loc = copiedDir
            fs_summary_args.backgrounds = None
            fs_summary_args.roi_list = "ctx_lh_G_cuneus"
            fs_summary_args.meanDfLoc = True
            fs_summary_args.verbose = True
            fs_summary_args.brain = True

            
            freesurfer_summary.main(fs_summary_args.subject_loc,
                    fs_summary_args.backgrounds,
                    fs_summary_args.roi_list,
                    fs_summary_args.meanDfLoc,
                    fs_summary_args.verbose,
                    fs_summary_args.brain)

    print 'Completed\n'

    


    #========================#
    # dual back up to nas    #
    #========================#
    if args.nasBackup:
        server = 147.47.228.192    
        for subject,infoList in allInfo.iteritems():
            #copiedDir=os.path.join(infoList[4],infoList[8],infoList[1])
            copiedDir=infoList[8]
            server_connect(server, copiedDir)

    print completed



def noCall(logDf,backUpFrom,folderName):
    logDf = pd.concat([logDf,pd.DataFrame.from_dict({'directoryName':folderName,'backedUpBy':getpass.getuser(),'backedUpAt':time.ctime()},orient='index').T])
    return logDf

def changeencode(data, cols):
    for col in cols:
        data[col] = data[col].str.decode('iso-8859-1').str.encode('utf-8')
    return data

def getDicomInfoAuto(firstDicomAddress):
    try:
        df = dicom.read_file(firstDicomAddress)
        dob = df.PatientBirthDate
        sex = df.PatientSex
        pID = df.PatientID
        date = df.StudyDate
        age,dob,date = calculate_age2(dob,date)
        name = df.PatientName
        return {'name':name,'dob':dob,
                'sex':sex, 'patientId':pID,
                'scanDate':date, 'age':age,'dicomRead':df}
    except:
        dicom.read_file(firstDicomAddress,force=True)
        print 'cannot properly read dicom file'

# In[324]:

def copiedDirectoryCheck(backUpFrom,logFileInUSB):
    if os.path.isfile(logFileInUSB):
        df = pd.read_excel(logFileInUSB,'Sheet1')
        print 'Log loaded successfully'
    else:
        df = pd.DataFrame.from_dict({'directoryName':None,'backedUpBy':None,'backedUpAt':None},orient='index').T

    return df


# In[325]:

def newDirectoryGrep(inputDirs, backUpFrom,logDf):
    '''
    show the list of folders under the backUpFrom
    if it is confirmed by the user
    excute backup
    '''
    toBackUp = []

    if inputDirs:
        for subjFolder in inputDirs:
            toBackUp.append(subjFolder)

    else:

        #grebbing directories in the target
        allFiles = os.listdir(backUpFrom)
        directories = [item for item in allFiles if os.path.isdir(os.path.join(backUpFrom,item))
                       and not item.startswith('$')
                       and not item.startswith('.')]

        newDirectories = [item for item in directories if not item in [str(x).encode("ascii") for x in logDf.directoryName]]


        for folderName in newDirectories:
            subjFolder = os.path.join(backUpFrom,folderName)
            stat = os.stat(subjFolder)
            created = os.stat(subjFolder).st_ctime
            asciiTime = time.asctime( time.gmtime( created ) )
            print '''
            ------------------------------------
            ------{0}
            created on ( {1} )
            ------------------------------------
            '''.format(folderName,asciiTime)
            response = raw_input('\nIs this the name of the subject you want to back up? [Yes/No/Quit/noCall] :')
            if re.search('[yY]|[yY][Ee][Ss]',response):
                toBackUp.append(subjFolder)
            elif re.search('[Dd][Oo][Nn][Ee]|stop|[Qq][Uu][Ii][Tt]|exit',response):
                break
            elif re.search('[Nn][Oo][Cc][Aa][Ll][Ll]',response):
                logDf = noCall(logDf,backUpFrom,folderName)
            else:
                continue

    print toBackUp
    return toBackUp,logDf


def noCall(logDf,backUpFrom,folderName):
    logDf = pd.concat([logDf,pd.DataFrame.from_dict({'directoryName':folderName,'backedUpBy':getpass.getuser(),'backedUpAt':time.ctime()},orient='index').T])
    return logDf


# In[326]:

def findDtiDkiT1restRest2(newDirectoryList):
    '''
    dictionary {subject:{t1:t1location,DTI:DTIlocation,...}}
    '''

    # Regrex compilers
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


    foundDict={}
    #nameDictionary={t1:'T1',rest:'REST',t2flair:'T2FLAIR',t2tse:'T2TSE',dtiFA:'DTI_FA',dtiEXP:'DTI_EXP',dtiCOLFA:'DTI_COLFA',dkiFA:'DKI_FA',dkiEXP:'DKI_EXP',dkiCOLFA:'DKI_COLFA'}
    for sourceSubjectDIR in newDirectoryList:
        subjectName=os.path.basename(sourceSubjectDIR)
        #looping through the os.walk
        foundDirectories={}

        #os.walk directory output
        osWorkOut={}
        print('\n\t{0} : going to search & match'.format(subjectName))

        num=1
        pbar=ProgressBar().start()
        for root, dirs, files in os.walk(sourceSubjectDIR):
            pbar.update(num)
            num+=5
            if len(dirs)==0:
                osWorkOut[root]=len(files)
        pbar.finish()
        print '\n\n'

        matchCheck=[]
        #osWorkOut = {modalityLocation:fileNumber,...}
        for modality in (t1,'T1'),(rest,'REST'),(dki,"DKI"),(dti,'DTI'),(t2flair,'T2FLAIR'),(t2tse,'T2TSE'),(dtiFA,'DTI_FA'),(dtiEXP,'DTI_EXP'),(dtiCOLFA,'DTI_COLFA'),(dkiFA,'DKI_FA'),(dkiEXP,'DKI_EXP'),(dkiCOLFA,'DKI_COLFA'):


            matchingSource=''.join([item for item in osWorkOut.iterkeys() if modality[0].search(item)])
            fileNumber=osWorkOut.get(matchingSource)


            if fileNumber:
                #print '\t{modality}  --> {found} with {fileNumber} files'.format(modality=modality[1],
                        #found=os.path.basename(matchingSource),
                        #fileNumber=fileNumber)
                foundDirectories[modality[1]]=[matchingSource,fileNumber]
            else:
                matchCheck.append(modality[1])

        print '\n'
        if matchCheck==[]:
            print '\tFound every modality'
        else:
            print '\tMissing modalities in {subject} are :'.format(subject=subjectName)
            for item in matchCheck:
                print item

                #User confirm for the missing modality
                if re.search('[yY]|[yY][Ee][Ss]',raw_input('\tCheck ? [ Y / N ] : ')):
                    print '\tOkay !'
                else:
                    print '\tExit due to missing modality'
                    sys.exit(0)

        foundDict[subjectName]=foundDirectories
        #foundDict = {subjectName:{modalityName:modalitySource,fileNumber}}

    return foundDict


# In[358]:

def getName(subjFolder):
    '''
    will try getting the name and subj number from the source folder first
    if it fails,
    will require user to type in the subjs' name
    '''
    if re.findall('\d{8}',os.path.basename(subjFolder)):
        patientNumber = re.search('(\d{8})',os.path.basename(subjFolder)).group(0)
        subjName = re.findall('[^\W\d_]+',os.path.basename(subjFolder))

        #Appending first letters
        subjInitial=''
        for i in subjName:
            subjInitial = subjInitial + i[0]

        fullname=''
        for i in subjName:
            fullname = fullname + i[0] + i[1:].lower()

        return subjInitial, fullname, patientNumber

    #if the folder shows no pattern
    else:
        subjName = raw_input('\tEnter the name of the subject in English eg.Cho Kang Ik:')
        patientNumber = raw_input("\tEnter subject's 8digit number eg.45291835:")

        subjwords=subjName.split(' ')
        fullname=''
        subjInitial=''
        for i in subjwords:
            fullname=fullname + i[0].upper()
            fullname=fullname + i[1:]
            subjInitial=subjInitial+i[0][0][0]
        return subjInitial.upper(),fullname,patientNumber

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




def getTargetLocation(subject,group,timeline,backUpTo,df):
    maxNum=maxGroupNum(os.path.join(backUpTo,group))
    subjInitial,fullname,patientNumber=getName(subject)
    target=os.path.join(backUpTo,group)
    if timeline=='baseline':
        targetDirectory='{0}{1}_{2}'.format(group,maxNum,subjInitial)
    else:
        previousInfo = df[df.patientNumber==int(patientNumber)]
        print previousInfo[['DOB','koreanName','subjectName','folderName']]
        if raw_input('\tDoes above contain the same subject information as the current one ? [Y/N] : ').upper() == 'Y':
            previousDir = previousInfo.folderName.values[0]
            print 'previousDir :', previousDir
            print 'previousDir :', previousDir
            print 'previousDir :', previousDir
            print 'previousDir :', previousDir

            targetDirectory=os.path.join(backUpTo,group,previousDir,timeline)

    return target,subjInitial,fullname,patientNumber,targetDirectory,maxNum


def getDOB_NOTE():
        birthday=raw_input('\tDate of birth? [yyyy-mm-dd] : ')
        note=raw_input('\tAny note ? :')

        return birthday,note

def getSex():
        sex=raw_input('\tSex ? [ M / F ] : ')
        return sex.upper()

def getKoreanName():
    koreanName = raw_input('\tKorean name ? [ eg) 조강익 or 윤영우1 ] ')
    return unicode(koreanName, "utf-8")

def studyName():
    studyName=raw_input('\tStudy name ? [ default : enroll, eg) "PET", "meditation", "IDP" ] ')
    if studyName=='':
        studyName='enroll'
    return studyName

def getGroup():
    possibleGroups = str('BADUK,PET,CHR,DNO,EMO,FEP,GHR,NOR,OCM,ONS,OXY,PAIN,SPR,UMO,IGD,IGH,AUD,ETC').split(',')
    subjectNameWithGroup={}

    groupName=raw_input('\twhich group ? [BADUK/PET/CHR/DNO/EMO/FEP/GHR/NOR/OCM/ONS/OXY/PAIN/SPR/UMO/IGH/IGD/AUD/ETC] :')
    timeline=raw_input('\tfollow up (if follow up, type the period) ? [baseline/period] :')
    groupName = groupName.upper()

    if groupName not in possibleGroups:
        print 'not in groups, let Dahye know.'
        groupName=''

    if groupName == 'BADUK':
        followUp=raw_input('\tCNT / PRO ? :')

    return groupName,timeline


def calculate_age2(born,scanDate):
    j = str(int(scanDate))
    i = str(int(born))

    today = datetime.datetime(year=int(j[:4]), month=int(j[4:6]), day=int(j[6:8]))
    born = datetime.datetime(year=int(i[:4]), month=int(i[4:6]), day=int(i[6:8]))

    try:
        birthday = born.replace(year=today.year)
    except ValueError: # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1, born, today
    else:
        return today.year - born.year, born, today

def calculate_age(born,today):
    try:
        birthday = born.replace(year=today.year)
    except ValueError: # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def checkFileNumbers(modalityAndLocationFromOneSubject):
    #Make a checking list
    checkList={'T1':208,
            'DTI':65,
            'DKI':151,
            'REST':4060,
            'REST2':152,
            'REST2Baduk':3132,
            'T2TSE':25,
            'T2FLAIR':25,
            'DTI_EXP':40,
            'DTI_FA':40,
            'DTI_COLFA':40,
            'DKI_EXP':200,
            'DKI_FA':40,
            'DKI_COLFA':40}

    #Check whether they have right numbers
    for modality,(modalityLocation,fileCount) in modalityAndLocationFromOneSubject.iteritems():
        if checkList[modality]!=fileCount:
            print '{modality} numbers does not seem right !  : {fileCount}'.format(
                    modality=modality,
                    fileCount=fileCount)
            if re.search('[yY]|[yY][Ee][Ss]',raw_input('\tCheck ? [ Y / N ] : ')):
                print '\tOkay !'
            else:
                print '\tExit due to unmatching file number'
                sys.exit(0)


def dicomNumberCheckInDictionary(allModalityWithLocation):
    checkList={'T1':208,'DTI':65,'DKI':151,'REST':4060,'REST2':152,'REST2BADUK':3132,'T2TSE':25,'T2FLAIR':25,'DTI_EXP':40,'DTI_FA':40,'DTI_COLFA':40,'DKI_EXP':200,'DKI_FA':40,'DKI_COLFA':40}

    for aModalityWithLocation in allModalityWithLocation:
        #If it is normal modality
        if aModalityWithLocation[0] in checkList.keys():
            if len(os.listdir(aModalityWithLocation[1]))==checkList[aModalityWithLocation[0]]:
                print '{0} number : checked'.format(aModalityWithLocation[0])
            else:
                print '{0} number is not matched. It has {1} files'.format(
                        aModalityWithLocation[0],len(os.listdir(aModalityWithLocation[1])))
        #If it's new modality
        else:
            print '{0} is new, it has {1} files in the directory'.format(
                    aModalityWithLocation[0],len(os.listdir(aModalityWithLocation[1])))


def executeCopy(allInfo,df,newDf):
    #newDf --> {subject:allInfoDf}
    maxNum=0
    #allInfo[subject]=[target,group,followUp,targetDirectory,allModalityWithLocation]
    #allModalityWithLocation
    #{'T1':['source','file number'],'DTI':['source','file number']}

    backedUpGroups=[]
    for subject,infoList in allInfo.iteritems():
        print '-----------------'
        print 'Copying',subject
        print '-----------------'

        #If it's follow up (the name exists)
        #infoList[-1] : koreanName
        if infoList[1] != 'baseline':
            for modality,modalityInfo in infoList[10].iteritems():
                #group + previousdir + follow up period(saved in the variable baseline)
                modalityTarget=os.path.join(infoList[4],infoList[8])
                print 'Copying {}'.format(modality)
                os.system('mkdir -p {0}'.format(modalityTarget))
                shutil.copytree(modalityInfo[0],os.path.join(modalityTarget,modality))



        else:
            for modality,modalityInfo in infoList[10].iteritems():
                # modalityInfo[0] : source
                # modalityInfo[1] : fileNumber
                # allInfo[subject]=[target,group,followUp,targetDirectory,allModalityWithLocation]
                # allModalityWithLocation
                # {'T1':['source','file number'],'DTI':['source','file number']}

                # If the backing up subjects belong to the same group
                # group : allInfo[subject][0]
                # targetDirName : allInfo[subject][8]
                if allInfo[subject][0] in backedUpGroups:
                    uniq=len(backedUpGroups.count(allInfo[subject][0]))
                    currentNum=re.search('[A-Z]{3}(\d{2})',allInfo[subject][8])
                    newNum=int(currentNum)+uniq
                    modalityTarget=os.path.join(
                            allInfo[subject][4],
                            allInfo[subject][8].replace(currentNum,newNum),'baseline')
                    print 'Copying {}'.format(modality)
                    os.system('mkdir -p {0}'.format(modalityTarget))
                    shutil.copytree(modalityInfo[0],os.path.join(modalityTarget,modality))
                else:

                    modalityTarget=os.path.join(allInfo[subject][4],allInfo[subject][8],'baseline')
                    print modalityTarget
                    print 'Copying {}'.format(modality)
                    os.system('mkdir -p {0}'.format(modalityTarget))
                    shutil.copytree(modalityInfo[0],os.path.join(modalityTarget,modality))

        subjectDf = newDf[subject]
        subjectDf.to_csv(os.path.join(modalityTarget,'log.txt'),sep='\t',encoding='utf-8')



# In[308]:

def verifyNumbersAndLog(foundDict,backUpTo,backUpFrom, DataBaseAddress):

    #{subject:{'T1':['source','file number'],'DTI':['source','file number'],...},subject2:{...}}
    allInfo={}



    if os.path.isfile(DataBaseAddress):
        excelFile = pd.ExcelFile(DataBaseAddress)
        df = excelFile.parse(excelFile.sheet_names[0])
    else:
        df = pd.DataFrame.from_dict({None:{'subjectName':None,
                                           'subjectInitial':None,
                                           'group':None,
                                           'sex':None,
                                           'DOB':None,
                                           'scanDate':None,
                                           'age':None,
                                           'timeline':None,
                                           'studyname':None,
                                           'folderName':None,
                                           'T1Number':None,
                                           'DTINumber':None,
                                           'DKINumber':None,
                                           'RESTNumber':None,
                                           'note':None,
                                           'patientNumber':None,
                                           'folderName':None,
                                           'backUpBy':None
                                           }
                                     },orient='index'
                                    )


    newDfList = {}
    #for each subjects
    for subject,allModalityWithLocation in foundDict.iteritems():
        #allModalityWithLocation
        #{'T1':['source','file number'],'DTI':['source','file number']}
        print '----------------------------------------'
        print subject
        print '----------------------------------------'

        modalityToRecheck=[]
        modalityConfirmed=[]

        checkFileNumbers(allModalityWithLocation)

        #Group, followUp(baseline,followup,CNT,PRO)
        koreanName = getKoreanName()
        group,timeline=getGroup()
        birthday,note=getDOB_NOTE()
        sex=getSex()
        studyname = studyName()

        target,subjInitial,fullname,subjNum,targetDirectory,maxNum=getTargetLocation(subject,group,timeline,backUpTo,df)
        os.mkdir(os.path.join(target,targetDirectory))

#        print '\n\n\n-----------------'
#        print group,timeline,birthday,note,target,subjInitial,fullname,subjNum,targetDirectory,sex,allModalityWithLocation,maxNum,backUpTo,backUpFrom
#        print '-----------------\n\n\n'

        allInfoDf = log(subject,koreanName,group,timeline,birthday,note,target,subjInitial,fullname,subjNum,studyname,targetDirectory,sex,allModalityWithLocation,maxNum,backUpTo,backUpFrom)

        newDfList[subject]=allInfoDf


        df = pd.concat([df,allInfoDf])
        df = df[['koreanName','subjectName','subjectInitial','group','sex','age','DOB','scanDate','timeline','studyname','patientNumber',
                 'T1Number','DTINumber','DKINumber','RESTNumber','REST2Number','folderName','backUpBy','note']]
        df = df.reset_index().drop('index',axis=1)


        allInfo[subject]=[group,timeline,birthday,note,target,subjInitial,fullname,subjNum,targetDirectory,sex,allModalityWithLocation,maxNum,backUpTo,backUpFrom,koreanName]

    return allInfo,df,newDfList


# In[309]:

def log(subject,koreanName,group,timeline,birthday,note,target,subjInitial,fullname,subjNum,studyname,targetDirectory,sex,allModalityWithLocation,maxNum,backUpTo,backUpFrom):

    #birthday
    dateOfBirth=date(int(birthday.split('-')[0]),int(birthday.split('-')[1]),int(birthday.split('-')[2]))

    #directory made at
    #{'T1':['source','file number'],'DTI':['source','file number']}
    sourceTime=os.stat(allModalityWithLocation.values()[0][0]).st_ctime
    sourceDate=time.gmtime(sourceTime)
    formalSourceDate=date(sourceDate[0],sourceDate[1],sourceDate[2])

    #Age calculation
    age = calculate_age(dateOfBirth,formalSourceDate)

    #Image numbers
    imageNumbers={}
    for image in 'T1','DTI','DKI','REST','T2FLAIR','T2TSE','REST2':
        try:
            imageNumbers[image]=allModalityWithLocation[image][1]
        except:
            imageNumbers[image]=''


    user=getpass.getuser()
    currentTime=time.ctime()
    destination=os.path.join(target,targetDirectory)



    #new dictionary
    allInfoRearranged = {}

    allInfoRearranged['koreanName']=koreanName
    allInfoRearranged['subjectName']=fullname
    allInfoRearranged['subjectInitial']=subjInitial
    allInfoRearranged['group']=group
    allInfoRearranged['sex']=sex
    allInfoRearranged['timeline']=timeline
    allInfoRearranged['studyname']=studyname

    allInfoRearranged['DOB']=dateOfBirth.isoformat()

    #**스캔데이트를 dicom에서 얻어오는 방법 ?
    allInfoRearranged['scanDate']=formalSourceDate.isoformat()
    allInfoRearranged['age']=age
    allInfoRearranged['T1Number']= imageNumbers['T1']
    allInfoRearranged['DTINumber']=imageNumbers['DTI']
    allInfoRearranged['DKINumber']=imageNumbers['DKI']
    allInfoRearranged['RESTNumber']=imageNumbers['REST']
    allInfoRearranged['REST2Number']=imageNumbers['REST2']
    allInfoRearranged['note']=note
    allInfoRearranged['patientNumber']=subjNum
    allInfoRearranged['folderName']=targetDirectory
    allInfoRearranged['backUpBy']=user

    allInfoDf = pd.DataFrame.from_dict(allInfoRearranged,orient='index').T
    return allInfoDf




#def networkCopy(allInfoDf):

def server_connect(server, data_from):
    ssh = SSHClient()
    ssh.load_system_host_keys()
    username='admin'
    data_to='/volume1/dual_back_up'
    password = getpass.getpass('Password admin@nas : ')
    ssh.connect(server, username=username, password=password)

    with SCPClient(ssh.get_transport()) as scp:
        print 'Connected to {server} and copying data'.format(server=server)
        print '\t',data_from,'to',server+'@'+data_to
        scp.put(data_from, data_to)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
            {codeName} : Copy MRI data from external hard drive to system.
                         It automatically adds logs to ccnc database.
            ========================================
            eg) {codeName}
            '''.format(codeName=os.path.basename(__file__))))

    parser.add_argument(
        '-i', '--inputDirs',
        help='Location of data to back up. Eg) /Volumes/20160420/CHO_KANG_IK_12344321',
        nargs='*',
        default=False,
        )

    parser.add_argument(
        '-hd', '--hddLocation',
        help='Location of external drive that contains new data. Eg) /Volumes/160412',
        default='/Volumes/160412',
        )

    parser.add_argument(
        '-l', '--USBlogFile',
        help='Location of excel file that contains back up log. Eg) /Volumes/160412/log.xlsx',
        default=False,
        )

    parser.add_argument(
        '-b', '--backupDir',
        help='Location of data storage root. Default : "/Volumes/promise/CCNC_MRI_3T"',
        default="/Volumes/CCNC_M2_3/nas_BackUp/CCNC_MRI_3T",
        )
    parser.add_argument(
        '-d', '--database',
        help='Location of database file. Default : "/Volumes/promise/CCNC_MRI_3T/database/database.xls"',
        default="/Volumes/CCNC_M2_3/nas_BackUp/CCNC_MRI_3T",
        )
    parser.add_argument(
        '-s', '--spreadsheet',
        help='Location of output excel file. Default : "/ccnc/MRIspreadsheet/MRI.xls"',
        default="/ccnc/MRI.xls",
        )

    parser.add_argument(
        '-f', '--freesurfer',
        help='Run freesurfer',
        action='store_true',
        default=False,
        )

    parser.add_argument(
        '-m', '--motion',
        help='Run motion extraction',
        action='store_true',
        default=False,
        )

    parser.add_argument(
        '-x', '--executeCopy',
        help='Execute copy and update database',
        action='store_true',
        default=False,
        )

    parser.add_argument(
        '-n', '--nasBackup',
        help='Makes dual back up to NAS',
        action='store_true',
        default=False,
        )
    args = parser.parse_args()
    main(args)


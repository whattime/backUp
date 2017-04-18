#!/ccnc_bin/venv/bin/python -> D1: ananconda
# -*- coding: utf-8 -*-
'''
# Back up data and forms a database from the MRI data
# Created by Kang Ik Kevin Cho
# Contributors: Dahye Stella Bae, Eunseo Cho
# python backUp.py -x -m      (If: changed paths correctly)
'''
from __future__ import division
import re
import time
from datetime import date
import sys
import os
import shutil
from progressbar import AnimatedMarker, ProgressBar, Percentage, Bar
import argparse
import textwrap
import pandas as pd
import updateSpreadSheet
import motionExtraction
#import easyFreesurfer #bienseo: not work -> using freesurfer.py
#import freesurfer_Summary # bienseo: not work
import subject as subj
import dtifit as bien #bienseo dti fa map

# scp modules for network dual back up
import getpass
from paramiko import SSHClient
from scp import SCPClient


def backUp(inputDirs, backUpFrom, USBlogFile, backUpTo,
           DataBaseAddress, spreadsheet,
           freesurfer, motion, copyExecute, nasBackup):

    # External HDD log
    if USBlogFile:
        logFileInUSB = USBlogFile
    elif inputDirs:
        logFileInUSB = os.path.join(os.getcwd(),"log.xlsx")
    else:
        logFileInUSB = os.path.join(backUpFrom,"log.xlsx")

    logDf = copiedDirectoryCheck(backUpFrom, logFileInUSB)
    newDirectoryList,logDf = newDirectoryGrep(inputDirs, backUpFrom, logDf)
    logDf.to_excel(logFileInUSB,'Sheet1')

    if newDirectoryList == []:
        sys.exit('Everything have been backed up !')

    subjectClassList = []
    for newDirectory in newDirectoryList:
        subjClass = subj.subject(newDirectory, backUpTo)
        checkFileNumbers(subjClass)
        subjectClassList.append(subjClass)

        if copyExecute:
            executeCopy(subjClass)

            subjDf = saveLog(subjClass)

            dbDf = processDB(DataBaseAddress)

            newDf = pd.concat([dbDf, subjDf]).reset_index()
            newDf = newDf[[ u'koreanName',  u'subjectName',   u'subjectInitial',
                            u'group',       u'sex',           u'age',
                            u'DOB',         u'scanDate',      u'timeline',
                            u'studyname',   u'patientNumber', u'T1Number',
                            u'DTINumber',   u'DKINumber',     u'RESTNumber',
                            u'REST2Number', u'folderName',    u'backUpBy',
                            u'note']]

            newDf['koreanName'] = newDf['koreanName'].str.decode('utf-8')
            newDf['note'] = newDf['note'].str.decode('utf-8')
            newDf.to_excel(DataBaseAddress, 'Sheet1')
            # os.chmod(DataBaseAddress, 0o2770)

            updateSpreadSheet.main(False, DataBaseAddress, spreadsheet)#False

    if motion:
        print 'Now, running motion_extraction'
        for subjectClass in subjectClassList:
            motionExtraction.main(subjectClass.targetDir, True, True, False)
            bien.dtiFit(os.path.join(subjectClass.targetDir,'DTI'))
    if nasBackup:
        server = '147.47.228.192'
        for subjectClass in subjectClassList:
            copiedDir = os.path.dirname(subjectClass.targetDir)
            server_connect(server, copiedDir)
   # freesurfer.py import error #bienseo
   # if freesurfer:
   #     for subjectClass in subjectClassList:
   #         easyFreesurfer.main(subjectClass.targetDir, 
   #                             os.path.join(subjectClass.targetDir,'FREESURFER'))
   #         freesurfer_Summary.main(copiedDir, None,                #bienseo: only use freesurfer.
   #                                 "ctx_lh_G_cuneus", True, True, True, True)
    print 'Completed\n'
 

def noCall(logDf, backUpFrom, folderName):
    logDf = pd.concat([logDf,pd.DataFrame.from_dict({'directoryName': folderName,
                                                     'backedUpBy': getpass.getuser(),
                                                     'backedUpAt': time.ctime()},orient='index').T])
    return logDf


def copiedDirectoryCheck(backUpFrom, logFileInUSB):
    if os.path.isfile(logFileInUSB):
        df = pd.read_excel(logFileInUSB,'Sheet1')
        print 'Log loaded successfully'
    else:
        df = pd.DataFrame.from_dict({
                                     'directoryName': None,
                                     'backedUpBy': None,
                                     'backedUpAt': None
                                    },orient='index').T
    return df


def newDirectoryGrep(inputDirs, backUpFrom, logDf):
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
        # grebbing directories in the target
        allFiles = os.listdir(backUpFrom)
        directories = [item for item in allFiles if os.path.isdir(os.path.join(backUpFrom, item))
                       and not item.startswith('$')
                       and not item.startswith('.')]

        newDirectories = [item for item in directories if not item in [str(x).encode("ascii") for x in logDf.directoryName]]

        for folderName in newDirectories:
            subjFolder = os.path.join(backUpFrom, folderName)
            stat = os.stat(subjFolder)
            created = os.stat(subjFolder).st_ctime
            asciiTime = time.asctime(time.gmtime(created))
            print '''
            ------------------------------------
            ------{0}
            created on ( {1} )
            ------------------------------------
            '''.format(folderName,asciiTime)
            response = raw_input('\nIs this the name of the subject you want to back up?'
                                 '[Yes/No/Quit/noCall] : ')

            if re.search('[yY]|[yY][Ee][Ss]',response):
                toBackUp.append(subjFolder)
            elif re.search('[Dd][Oo][Nn][Ee]|stop|[Qq][Uu][Ii][Tt]|exit',response):
                break
            elif re.search('[Nn][Oo][Cc][Aa][Ll][Ll]',response):
                logDf = noCall(logDf, backUpFrom, folderName)
            else:
                continue

    print toBackUp
    return toBackUp, logDf


def calculate_age(born, today):
    try:
        birthday = born.replace(year=today.year)
    except ValueError: # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def checkFileNumbers(subjClass):
    # Make a checking list
    checkList = {
                 'T1': 208,
                 'DTI': 65,
                 'DKI': 151,
                 'REST': 4060,
                 'REST2': 152,
                 'REST2Baduk': 3132,
                 'T2TSE': 25,
                 'T2FLAIR': 25,
                 'DTI_EXP': 40,
                 'DTI_FA': 40,
                 'DTI_COLFA': 40,
                 'DKI_EXP': 200,
                 'DKI_FA': 40,
                 'DKI_COLFA': 40,
                 'SCOUT': 9
                }

    # Check whether they have right numbers
    for modality, (modalityLocation, fileCount) in zip(subjClass.modalityMapping, subjClass.dirDicomNum):
        if checkList[modality] != fileCount:
            print '{modality} numbers does not seem right !  : {fileCount}'.format(
                    modality=modality,
                    fileCount=fileCount)
            if re.search('[yY]|[yY][Ee][Ss]',raw_input('\tCheck ? [ Y / N ] : ')):
                print '\tOkay !'
            else:
                print '\tExit due to unmatching file number'
                sys.exit(0)
        else:
            print 'Correct dicom number - \t {modality} : {fileCount}'.format(
                   modality=modality,
                   fileCount=fileCount)


def executeCopy(subjClass):
    print '-----------------'
    print 'Copying', subjClass.koreanName
    print '-----------------'

    totalNum = subjClass.allDicomNum
    accNum = 0
    pbar = ProgressBar().start()
    for source, modality, num in zip(subjClass.dirs, 
                                     subjClass.modalityMapping, 
                                     subjClass.modalityDicomNum.values()):

        os.system('mkdir -p {0}'.format(subjClass.targetDir))

        modalityTarget = os.path.join(subjClass.targetDir, modality)
        shutil.copytree(source, modalityTarget)
        accNum += num
        pbar.update((accNum/totalNum) * 100)
    pbar.finish()


def processDB(DataBaseAddress):
    if os.path.isfile(DataBaseAddress):
        excelFile = pd.ExcelFile(DataBaseAddress)
        df = excelFile.parse(excelFile.sheet_names[0])
        df['koreanName'] = df.koreanName.str.encode('utf-8')
        df['note'] = df.note.str.encode('utf-8')

        print 'df in processDf first parag'
        print df

    else:
        df = pd.DataFrame.from_dict({ None: {
                                               'subjectName': None,
                                               'subjectInitial': None,
                                               'group': None,
                                               'sex': None,
                                               'DOB': None,
                                               'scanDate': None,
                                               'age': None,
                                               'timeline': None,
                                               'studyname': None,
                                               'folderName': None,
                                               'T1Number': None,
                                               'DTINumber': None,
                                               'DKINumber': None,
                                               'RESTNumber': None,
                                               'note': None,
                                               'patientNumber': None,
                                               'folderName': None,
                                               'backUpBy': None
                                            }
                                     },orient='index'
                                    )
    return df

def saveLog(sub):
    df = makeLog(sub.koreanName, sub.group, sub.timeline, sub.dob, sub.note,
                 sub.initial, sub.fullname, sub.sex, sub.id, sub.study,
                 sub.date, sub.folderName, sub.modalityDicomNum, sub.experimenter)
    df.to_csv(os.path.join(sub.targetDir, 'log.txt'))
    return df

def makeLog(koreanName, group, timeline, dob, note,
            subjInitial, fullname, sex, subjNum, studyname,
            scanDate, folderName, modalityCount, user):

    dateOfBirth = date(int(dob[:4]), int(dob[4:6]), int(dob[6:]))
    formalSourceDate = date(int(scanDate[:4]),int(scanDate[4:6]), int(scanDate[6:]))
    age = calculate_age(dateOfBirth,formalSourceDate)

    # Image numbers
    images = ['T1','DTI','DKI','REST','T2FLAIR','T2TSE','REST2']
    imageNumbers = {}
    for image in images:
        try:
            imageNumbers[image] = modalityCount[image]
        except:
            imageNumbers[image] = ''

    # New dictionary  
    allInfoRearranged = {}
    allInfoRearranged = {
                            'koreanName': koreanName,
                            'subjectName': fullname,
                            'subjectInitial': subjInitial,
                            'group': group,
                            'sex': sex,
                            'timeline': timeline,
                            'studyname': studyname,
                            'DOB': dateOfBirth.isoformat(),
                            'scanDate': formalSourceDate.isoformat(),
                            'age': age,

                            'note': note,
                            'patientNumber': subjNum,
                            'folderName': folderName,
                            'backUpBy': user,
                            
                            'T1Number': imageNumbers['T1'],
                            'DTINumber': imageNumbers['DTI'],
                            'DKINumber': imageNumbers['DKI'],
                            'RESTNumber': imageNumbers['REST'],
                            'REST2Number': imageNumbers['REST2'] 
                        }
    allInfoDf = pd.DataFrame.from_dict(allInfoRearranged,orient='index').T
    allInfoDf = allInfoDf[[ 
                            u'koreanName',  u'subjectName',   u'subjectInitial',
                            u'group',       u'sex',           u'age',
                            u'DOB',         u'scanDate',      u'timeline',
                            u'studyname',   u'patientNumber', u'T1Number',
                            u'DTINumber',   u'DKINumber',     u'RESTNumber',
                            u'REST2Number', u'folderName',    u'backUpBy',
                            u'note'
                         ]]
    return allInfoDf


def server_connect(server, data_from):
    ssh = SSHClient()
    ssh.load_system_host_keys()
    username = 'admin'
    data_to = '/volume1/dual_back_up'
    password = getpass.getpass('Password admin@nas : ')
    ssh.connect(server, username=username, password=password)

    with SCPClient(ssh.get_transport()) as scp:
        print 'Connected to {server} and copying data'.format(server=server)
        print '\t',data_from,'to',server+'@'+data_to
        scp.put(data_from, data_to, recursive=True, preserve_times=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
        default=False, #bienseo: directory changed in D1
        )

    parser.add_argument(
        '-hd', '--hddLocation',
        help='Location of external drive that contains new data. Eg) /Volumes/160412',
        default='/media/MRI_cohort', #bienseo: directory changed in D1 #if: directory name changed -> must check this #dahye_bae changed the path Apr15.2017
        )

    parser.add_argument(
        '-l', '--USBlogFile',
        help='Location of excel file that contains back up log. Eg) /Volumes/160412/log.xlsx',
        default=False,
        )

    parser.add_argument(
        '-b', '--backupDir',
        help='Location of data storage root. Default : "/volumes/CCNC_MRI/CCNC_MRI_3T"',
        default="/volume/CCNC_MRI/CCNC_MRI_3T", #bienseo: directory changed in D1 #dahye_bae confirm
        )
    parser.add_argument(
        '-d', '--database',
        help='Location of database file. Default : "/volumes/CCNC_MRI/CCNC_MRI_3T/database/database.xls"',
        default="/volume/CCNC_MRI/CCNC_MRI_3T/database/database.xls", #bienseo: directory changed in D1 #dahye_bae confirm
        )
    parser.add_argument(
        '-s', '--spreadsheet',
        help='Location of output excel file. Default : "/ccnc/MRIspreadsheet/MRI.xls"',
        default="/volume/CCNC_MRI/CCNC_MRI_3T/MRIspreadsheet/MRI.xls", #bienseo: directory changed in D1 #dahye_bae confirm
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

    backUp(args.inputDirs, args.hddLocation, args.USBlogFile, args.backupDir,
           args.database, args.spreadsheet, args.freesurfer, args.motion,
           args.executeCopy, args.nasBackup)

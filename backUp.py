#!/ccnc_bin/venv/bin/python
# -*- coding: utf-8 -*-
import re
import time
from datetime import date
import sys
import os
import shutil
from progressbar import AnimatedMarker,ProgressBar,Percentage,Bar
import argparse
import textwrap
import pandas as pd
import updateSpreadSheet
import motion_extraction
import freesurfer
import freesurfer_summary
import subject as subj

# scp modules for network dual back up
import getpass
from paramiko import SSHClient
from scp import SCPClient



def backUp(inputDirs, backUpFrom, USBlogFile, backUpTo, DataBaseAddress, spreadsheet, freesurfer, motion, executeCopy, nasBackup):
    # External HDD log
    if USBlogFile:
        logFileInUSB = USBlogFile
    elif args.inputDirs:
        logFileInUSB = os.path.join(os.getcwd(),"log.xlsx")
    else:
        logFileInUSB = os.path.join(backUpFrom,"log.xlsx")

    logDf = copiedDirectoryCheck(backUpFrom,logFileInUSB)
    newDirectoryList,logDf = newDirectoryGrep(args.inputDirs, backUpFrom,logDf)
    logDf.to_excel(logFileInUSB,'Sheet1')

    if newDirectoryList==[]:
        sys.exit('Everything have been backed up !')

    subjectClassList = []
    for newDirectory in newDirectoryList:
        subjClass = subj.subject(newDirectory, backUpTo)
        checkFileNumbers(subjClass)
        subjectClassList.append(subjClass, backUpTo)

        if args.executeCopy:
            executeCopy(subjClass)

            subjDf = saveLog(subjClass)

            dbDf = processDB(DataBaseAddress)
            newDf = pd.concat([dbDf, subjDf])
            newDf.to_excel(DataBaseAddress, 'Sheet1')
            os.chmod(DataBaseAddress, 0o2770)

            class spreadsheetInput():
                def __init__(self):
                    self.database = database
                    self.outExcel = spreadsheet
            us_input = spreadsheetInput()
            updateSpreadSheet.main(us_input)


    if args.motion:
        print 'Now, running motion_extraction'
        for subjectClass in subjectClassList:
            #copiedDir=os.path.join(infoList[4],infoList[8],infoList[1])
            copiedDir=subjectClass.targetDir
            motion_extraction.to_nifti(copiedDir,False)
            motion_extraction.to_afni_format(copiedDir)
            motion_extraction.slice_time_correction(copiedDir)
            motion_extraction.motion_correction(copiedDir)
            motion_extraction.make_graph(copiedDir)

    if args.nasBackup:
        server = '147.47.228.192'
        for subjectClass in subjectClassList:
            copiedDir=subjectClass.targetDir
            server_connect(server, copiedDir)

    print 'Completed\n'

    if args.freesurfer:
        for subjectClass in subjectClassList:
            #copiedDir=os.path.join(infoList[4],infoList[8],infoList[1])
            copiedDir=subjectClass.targetDir
            print copiedDir
            fs.directory = copiedDir
            fs.nifti = True
            fs.file_input = False
            fs.cwd = False
            fs.output = os.path.join(copiedDir,'FREESURFER')

            freesurfer(fs_args)
            freesurfer_summary.main(copiedDir, None, "ctx_lh_G_cuneus", True, True, True)

    print 'Completed\n'
    


def noCall(logDf,backUpFrom,folderName):
    logDf = pd.concat([logDf,pd.DataFrame.from_dict({'directoryName':folderName,'backedUpBy':getpass.getuser(),'backedUpAt':time.ctime()},orient='index').T])
    return logDf


def copiedDirectoryCheck(backUpFrom,logFileInUSB):
    if os.path.isfile(logFileInUSB):
        df = pd.read_excel(logFileInUSB,'Sheet1')
        print 'Log loaded successfully'
    else:
        df = pd.DataFrame.from_dict({'directoryName':None,'backedUpBy':None,'backedUpAt':None},orient='index').T

    return df


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

def calculate_age(born,today):
    try:
        birthday = born.replace(year=today.year)
    except ValueError: # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year

def checkFileNumbers(subjClass):
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
    for modality, (modalityLocation, fileCount) in zip(subjClass.modalityMapping, subjClass.dirDicomNum):
        if checkList[modality]!=fileCount:
            print '{modality} numbers does not seem right !  : {fileCount}'.format(
                    modality=modality,
                    fileCount=fileCount)
            if re.search('[yY]|[yY][Ee][Ss]',raw_input('\tCheck ? [ Y / N ] : ')):
                print '\tOkay !'
            else:
                print '\tExit due to unmatching file number'
                sys.exit(0)



def executeCopy(subjClass):
    print '-----------------'
    print 'Copying',subject
    print '-----------------'

    pbar=ProgressBar().start()
    totalNum = subjClass.allDicomNum
    accNum = 0
    for source, modality, num in zip(subjClass.dirs, 
                                     subjClass.modalityMapping, 
                                     subjClass.modalityDicomNum.values()):

        print 'Copying {}'.format(modality)
        modalityTarget = os.path.join(subjClass.targetDir, modality)
        os.system('mkdir -p {0}'.format(modalityTarget))
        shutil.copytree(subjClass.dirs, modalityTarget)
        accNum += num
        pbar.update(accNum/totalNum * 100)
    pbar.finish()


def processDB(DataBaseAddress):
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
    return df

def saveLog(sub):
    df = makeLog(sub.koreanName, sub.group, sub.timeline, sub.dob, sub.note,
                 sub.initial, sub.fullname, sub.sex, sub.id, sub.study,
                 sub.date, sub.modalityDicomNum, sub.experimenter)
    df.to_csv(sub.targetDir, 'log.txt')
    return df

def makeLog(koreanName,group,timeline,dob,note,subjInitial,fullname,sex,subjNum,studyname,scanDate, modalityCount, user):
    dateOfBirth=date(int(dob[:4]),int(dob[4:6]), int(dob[6:]))
    formalSourceDate=date(int(scanDate[:4]),int(scanDate[4:6]), int(scanDate[6:]))
    age = calculate_age(dateOfBirth,formalSourceDate)

    #Image numbers
    imageNumbers={}
    for image in 'T1','DTI','DKI','REST','T2FLAIR','T2TSE','REST2':
        try:
            imageNumbers[image]=modalityCount[image]
        except:
            imageNumbers[image]=''

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



def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]

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

    backUp(args.inputDirs, args.hddLocation, args.USBlogFile, args.backupDir,
            args.database, args.spreadsheet, args.freesurfer, args.motion,
            args.executeCopy, args.nasBackup)

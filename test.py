import backUp
import os
import argparse
import textwrap


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
        default="/Volumes/promise/CCNC_MRI_3T",
        )
    parser.add_argument(
        '-d', '--database',
        help='Location of database file. Default : "/Volumes/promise/CCNC_MRI_3T/database/database.xls"',
        default="/Volumes/promise/CCNC_MRI_3T/database/database.xls",
        )
    parser.add_argument(
        '-s', '--spreadsheet',
        help='Location of output excel file. Default : "/ccnc/MRIspreadsheet/MRI.xls"',
        default="/ccnc/MRIspreadsheet/MRI.xls",
        )

    parser.add_argument(
        '-f', '--freesurfer',
        help='Run freesurfer',
        action='store_true',
        default=True,
        )

    parser.add_argument(
        '-m', '--motion',
        help='Run motion extraction',
        action='store_true',
        default=True,
        )

    parser.add_argument(
        '-x', '--executeCopy',
        help='Execute copy and update database',
        action='store_true',
        default=True,
        )

    args = parser.parse_args()

    #print args



class argparse():
    def __init__(self):
        #self.inputDirs = ['/Users/kcho/backUp/KIM_SE_UK_46676612']
        self.backupDir = '/Volumes/CCNC_M2_3/nas_BackUp/CCNC_MRI_3T'
        self.database = '/Volumes/CCNC_M2_3/nas_BackUp/CCNC_MRI_3T/database/database.xls'
        self.spreadsheet = '/ccnc/MRI.xls'
        self.hddLocation= '/Volumes/160412'
        self.freesurfer = False
        self.executeCopy = False
        self.motion = False
        self.USBlogFile = False
        self.inputDirs= False

args = argparse()
print args.inputDirs
print args.backupDir
print args.database
print args.spreadsheet
print args.hddLocation
print args.USBlogFile
print args.freesurfer
print args.executeCopy

backUp.main(args)

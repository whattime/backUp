import backUp


class argparse():
    def __init__(self):
        self.inputDir = '/Users/kcho/backUp/KIM_SE_UK_46676612'
        self.backupDir = '/Users/kcho/backUp/tmp'
        self.database = '/Users/kcho/backUp/database.xls'
        self.spreadsheet = '/Users/kcho/backUp/MRI.xls'
        self.hddLocation= '/Users/kcho/backUp/'
        self.USBlogFile= '/Users/kcho/backUp/log.xlsx'

args = argparse()
print args.inputDir
print args.backupDir
print args.database
print args.spreadsheet
print args.hddLocation
print args.USBlogFile

backUp.main(args)

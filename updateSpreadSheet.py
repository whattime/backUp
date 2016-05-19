#!/usr/bin/python

import pandas as pd
import os
import re
import argparse
import textwrap
import xlwt
from xlrd import open_workbook
from xlutils.copy import copy
import pwd
import grp
import getpass


def main(args):
    sourceFile = pd.ExcelFile(args.database)
    
    sourceDf = sourceFile.parse(sourceFile.sheet_names[0])
    target = args.outExcel
    os.remove(target)

    try:
        if args.study:
            updateSpreadSheet(sourceDf,target,'studyName')
        else:
            updateSpreadSheet(sourceDf,target,'group')
    except:
        updateSpreadSheet(sourceDf,target,'group')

    #styling
    styleUpdate(target)
    uid = pwd.getpwnam(getpass.getuser()).pw_uid
    gid = grp.getgrnam("ccnc_mri").gr_gid
    os.chmod(target, 0o2775)
    os.chown(target, uid, gid)
    print 'finished'

def styleUpdate(target):
    print target
    rb = open_workbook(target)
    wb = copy(rb)

    #style
    headline = xlwt.easyxf('pattern: pattern solid, fore_color yellow, back_color orange; font: height 260, bold true, color black; align: horizontal center, vertical center, wrap true; border: top thick, bottom double')
    plain = xlwt.easyxf('font: height 200, color black; align: horizontal center, vertical center; border: top thin, bottom thin, right thin, left thin')
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'yyyy-mm-dd'


    #first count sheet format
    sheet = wb.get_sheet(0)
    sheet.col(0).width = 256*13

    sheet.col(0).width = 256*10
    for colNum in range(9):
        sheet.write(0,colNum,rb.sheet_by_index(0).cell(0,colNum).value,style=headline)
        sheet.col(colNum).width = 256*15
        for rowNum in range(1,len(sheet.rows)):
            sheet.write(rowNum,colNum,rb.sheet_by_index(0).cell(rowNum,colNum).value,style=plain)
    sheet.row(0).height_mismatch = True
    sheet.row(0).height = 256*3



    sheetNumber = len(rb.sheet_names())
    #loop through the sheet
    for num in range(1,sheetNumber):
        sheet = wb.get_sheet(num)

        #looping through columns
        for colNum in range(1,20):
            sheet.col(0).width = 256*4
            sheet.write(0,colNum,rb.sheet_by_index(num).cell(0,colNum).value,style=headline)
            sheet.col(colNum).width = 256*15
            for rowNum in range(1,len(sheet.rows)):
                sheet.write(rowNum,colNum,rb.sheet_by_index(num).cell(rowNum,colNum).value,style=plain)

        #write the content with style

        sheet.row(0).height_mismatch = True
        sheet.row(0).height = 256*3

    wb.save(target)


def updateSpreadSheet(df,target,divideBy):
    groupbyGroup = df.groupby(divideBy)

    writer = pd.ExcelWriter(target)

    #group count
    count={}
    for group,dataFrame in groupbyGroup:
        #followUpT1count = len(dataFrame[dataFrame.T1Number >= 208][dataFrame.timeline!='baseline'])
        followUpT1count = len([x for x in dataFrame[dataFrame.timeline!='baseline']['T1Number'] if type(x)==int and x >= 208])
        followUpDTIcount  = len([x for x in dataFrame[dataFrame.timeline!='baseline']['DTINumber'] if type(x)==int and x >= 65])
        followUpDKIcount  = len([x for x in dataFrame[dataFrame.timeline!='baseline']['DKINumber'] if type(x)==int and x >= 151])
        followUpRESTcount  = len([x for x in dataFrame[dataFrame.timeline!='baseline']['RESTNumber'] if type(x)==int and x >= 4060])

        baselineT1count = len([x for x in dataFrame[dataFrame.timeline=='baseline']['T1Number'] if type(x)==int and x >= 208])
        baselineDTIcount  = len([x for x in dataFrame[dataFrame.timeline=='baseline']['DTINumber'] if type(x)==int and x >= 65])
        baselineDKIcount  = len([x for x in dataFrame[dataFrame.timeline=='baseline']['DKINumber'] if type(x)==int and x >= 151])
        baselineRESTcount  = len([x for x in dataFrame[dataFrame.timeline=='baseline']['RESTNumber'] if type(x)==int and x >= 4060])

        count[group]=[baselineT1count, baselineDTIcount, baselineDKIcount, baselineRESTcount,
                followUpT1count, followUpDTIcount, followUpDKIcount, followUpRESTcount]

    countDf = pd.DataFrame.from_dict(count,orient='index')
    countDf.columns = ['baseline T1','baseline DTI','baseline DKI','baseline REST',
            'followUp T1','followUp DTI','followUp DKI','followUp REST']

    countDf.to_excel(writer,'Count')
    df.sort('scanDate',ascending=False)[:20].to_excel(writer,'Recent')

    for group,dataFrame in groupbyGroup:

        print group
        dataFrame = dataFrame.sort('folderName')
        dataFrame.to_excel(writer,group)

    writer.save()



if __name__=='__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
            description = textwrap.dedent('''\
                    {codeName} : Returns information extracted from dicom within the directory
                    ====================
                        eg) {codeName}
                        eg) {codeName} --dir /Users/kevin/NOR04_CKI
                    '''.format(codeName=os.path.basename(__file__))))

            #epilog="By Kevin, 26th May 2014")
    parser.add_argument('-s','--study',action='store_true',help='Divide the database by studies')
    parser.add_argument('-d','--database', help='Database location', 
            default = '/Volumes/promise/nas_BackUp/CCNC_MRI_3T/database/database.xls')
    parser.add_argument('-o','--outExcel', help='Excel spreadsheet output location',
            default = '/ccnc/MRIspreadsheet/MRI.xls')

    args = parser.parse_args()
    print args.study
    main(args)


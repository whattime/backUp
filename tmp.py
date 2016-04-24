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

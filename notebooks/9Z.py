#!/usr/bin/env python
# coding: utf-8

# In[1]:


import datetime
import os

import pandas as pd
import seaborn as sns


# In[2]:


#set variables
csv_location = './'
plate = 'CP228'
foci_filename = 'BarcodePreprocessing_Foci.csv'
#Merge Foci csvs
#Run if csvs are in separate folders
folderlist = os.listdir(csv_location)
df_dict={}
count = 0
print(count, datetime.datetime.ctime(datetime.datetime.now()))
for eachfolder in folderlist:
    if os.path.isfile(os.path.join(eachfolder, foci_filename)):
        try:
            df_dict[eachfolder]=pd.read_csv(os.path.join(csv_location, eachfolder, foci_filename),index_col=False,usecols=["Barcode_MatchedTo_Score", "Barcode_BarcodeCalled","Barcode_MatchedTo_ID"])
        except:
            pass
        count+=1
        if count % 100 == 0:
            print(count, datetime.datetime.ctime(datetime.datetime.now()))
print(count, datetime.datetime.ctime(datetime.datetime.now()))
df_foci = pd.concat(df_dict, ignore_index=True)
print('done concatenating at', datetime.datetime.ctime(datetime.datetime.now()))


# In[3]:


print ("For plate ", plate)
print ("%Barcodes with match > .9:")
print (sum(df_foci['Barcode_MatchedTo_Score']>0.9)*100.0/sum(df_foci['Barcode_MatchedTo_Score']>0))
print ("%Barcodes with perfect match:")
print (sum(df_foci['Barcode_MatchedTo_Score']==1)*100.0/sum(df_foci['Barcode_MatchedTo_Score']>0))
print ("Number of perfect barcodes:")
print (sum(df_foci['Barcode_MatchedTo_Score']==1))
df_foci['PerfectReads']=df_foci['Barcode_MatchedTo_ID'].where(df_foci['Barcode_MatchedTo_Score']==1,0,axis='index')


# In[4]:


sns.distplot(df_foci['Barcode_MatchedTo_Score'], kde=False).set_title(plate)


# In[5]:


df_foci['Barcode_BarcodeCalled'].value_counts().head(20)


# In[6]:


BarcodeCat = df_foci['Barcode_BarcodeCalled'].str.cat()
countG = BarcodeCat.count('G')
countT = BarcodeCat.count('T')
countA = BarcodeCat.count('A')
countC = BarcodeCat.count('C')
print ("Frequency of A is " + str(float(countA)/float((len(BarcodeCat)))))
print ("Frequency of C is " + str(float(countC)/float((len(BarcodeCat)))))
print ("Frequency of G is " + str(float(countG)/float((len(BarcodeCat)))))
print ("Frequency of T is " + str(float(countT)/float((len(BarcodeCat)))))


# In[ ]:





# In[ ]:





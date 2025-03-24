#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import pandas
import seaborn as sns
import datetime
import matplotlib.pyplot as plt


# In[3]:


#set variables
drive = 'awstest/images_corrected_troubleshooting_'
#batch = '20200211_6W_CP151A2'


# # Merge CSVs

# In[3]:


#Merge Foci csvs
#Run if csvs are in separate folders
#topfolder = os.path.join(drive, batch, 'images_corrected\\barcoding\\')
topfolder = drive
filename = 'BarcodePreprocessing_BarcodeFoci.csv'

df_dict={}
count = 0
folderlist = os.listdir(topfolder)
print(count, datetime.datetime.ctime(datetime.datetime.now()))
for eachfolder in folderlist:
        if os.path.isfile(os.path.join(topfolder, eachfolder, filename)):
            df_dict[eachfolder]=pandas.read_csv(os.path.join(topfolder, eachfolder, filename),index_col=False)
            count+=1
            if count % 50 == 0:
                print(count, datetime.datetime.ctime(datetime.datetime.now()))
print(count, datetime.datetime.ctime(datetime.datetime.now()))
df_foci = pandas.concat(df_dict, ignore_index=True)
print('done concatenating at', datetime.datetime.ctime(datetime.datetime.now()))


# In[4]:


#Save the merged Foci CSV
focipath = os.path.join(topfolder, 'Foci_Merged.csv')
df_foci.to_csv(focipath)


# # Load csvs

# In[4]:


#Skip to this point if .csvs don't need to be merged
#load .csvs
df_foci=pandas.read_csv(os.path.join(drive, 'Foci_Merged.csv'))


# # Barcoding Quality

# In[5]:


batch_list = ['99', '995','999','HistogramPreMask_A', 'HistogramPreMask_T',
                       'LoG','LoGNoBackSub','MaskHistARescale','MaskHistogram_A','MaskHistogram_T',
                      'RescaleAfterMask','RescalePostCompensate','RescalePreMask', 'Standard','WholeImage',
                      'WholeImageNoBackSub']


# In[6]:


metrics = []
for batch in batch_list:
    metrics.append('Intensity_MedianIntensity_BarcodeScores_IntValues_' +batch)
melted = df_foci.melt(id_vars=['Metadata_Well','Metadata_Plate'], value_vars=metrics,
        var_name='CorrectionProtocol', value_name='Score')


# In[7]:


if max(melted['Score'])>1:
    melted['Score']=melted['Score']/65535.0


# In[8]:


melted['Usable']=melted.eval('Score > 0.9')
melted['Perfect']=melted.eval('Score >= 1')
melted.head()


# In[9]:


counts = melted.groupby(['CorrectionProtocol','Metadata_Plate','Metadata_Well']).count()


# In[10]:


perperdf = melted.groupby(['CorrectionProtocol','Metadata_Plate','Metadata_Well']).mean()


# In[11]:


perperdf['NSpots'] = counts['Score'] #this could be any column


# In[12]:


perperdf['PerfectCount']=perperdf['Perfect']*perperdf['NSpots']
perperdf['UsableCount']=perperdf['Usable']*perperdf['NSpots']


# In[15]:


perperdf.head()


# In[16]:


perperdf = perperdf.reset_index()


# In[17]:


perperdf.to_csv('summary.csv',index=False)


# In[18]:


perplate= melted.groupby(['CorrectionProtocol','Metadata_Plate']).mean()
perplate.head()


# In[21]:


perplate=perplate.reset_index()


# In[22]:


perplate.to_csv('summary_perplate.csv',index=False)


# In[19]:


g = sns.catplot(data=perperdf, kind='bar',x='Metadata_Plate',y='Perfect',hue='Metadata_Well',col='CorrectionProtocol',col_wrap=4)
g.set_xticklabels(rotation=30)
g.set_titles(col_template = '{col_name}')


# In[20]:


g = sns.catplot(data=perperdf, kind='bar',x='Metadata_Plate',y='Usable',hue='Metadata_Well',col='CorrectionProtocol',col_wrap=4)
g.set_xticklabels(rotation=30)
g.set_titles(col_template = '{col_name}')


# In[21]:


g = sns.catplot(data=perperdf, kind='bar',x='Metadata_Plate',y='PerfectCount',hue='Metadata_Well',col='CorrectionProtocol',col_wrap=4)
g.set_xticklabels(rotation=30)
g.set_titles(col_template = '{col_name}')


# In[12]:


barcode_metric_list = batch_list

for barcode_metric_diff in barcode_metric_list:
    barcode_metric = 'Intensity_MedianIntensity_BarcodeScores_IntValues_' + barcode_metric_diff
    #barcode_metric = 'Barcode_MatchedTo_Score'
    if max(df_foci[barcode_metric]) > 1:
        df_foci[barcode_metric] = df_foci[barcode_metric]/65535.0
    print(barcode_metric)
    print("%Barcodes with match > .9:")
    print( sum(df_foci[barcode_metric]>0.9)*100.0/sum(df_foci[barcode_metric]>0))
    print("%Barcodes with perfect match:")
    percent_perfect = sum(df_foci[barcode_metric]==1)*100.0/sum(df_foci[barcode_metric]>0)
    print(percent_perfect)
    print("Number of perfect barcodes:")
    print(sum(df_foci[barcode_metric]==1))


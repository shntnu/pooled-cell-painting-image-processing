#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt


# # Single Cycle

# In[4]:


# Edit path to folder where you saved your Cells.csv
output_path = '/Users/eweisbar/Desktop/SingleQC'


# In[24]:


df = pd.read_csv(os.path.join(output_path,'Cells.csv'))

num_cells = len(df['Children_Foci_Count'])
num_cells_with_foci = len([x for x in df['Children_Foci_Count'] if x!=0])
num_foci = sum(df['Children_Foci_Count'])
print (f"Percent cells with foci is {num_cells_with_foci/num_cells}")
print (f"Foci/cell (all cells) is {num_foci/num_cells}")
print (f'Foci/cell (cells with foci) is {num_foci/num_cells_with_foci}')


# # Eight Cycles

# In[1]:


# Edit path to folder where you saved your Cells.csv
output_path = '/Users/eweisbar/Desktop/test8'

# Edit path to folder where you saved your Barcodes.csv and column names
barcodes_path = '/Users/eweisbar/Downloads'
gene_col = 'gene_symbol'
barcode_col = 'sgRNA'


# ## Foci Calling Metrics

# In[7]:


df_cells = pd.read_csv(os.path.join(output_path,'Cells.csv'))

num_cells = len(df_cells['Children_BarcodeFoci_Count'])
num_cells_with_foci = len([x for x in df_cells['Children_BarcodeFoci_Count'] if x!=0])
num_foci = sum(df_cells['Children_BarcodeFoci_Count'])

print (f"Percent cells with foci is {num_cells_with_foci/num_cells}")
print (f"Foci/cell (all cells) is {num_foci/num_cells}")
print (f'Foci/cell (cells with foci) is {num_foci/num_cells_with_foci}')


# In[10]:


df_foci = pd.read_csv(os.path.join(output_path,'Foci.csv'))

print (f"Percent perfect is {sum(df_foci['Barcode_MatchedTo_Score'])/len(df_foci['Barcode_MatchedTo_Score'])}")

sns.displot(df_foci['Barcode_MatchedTo_Score'], kde=False)


# In[13]:


# What is the % of each base in the calls?
# Expect to be roughly equal

BarcodeCat = df_foci['Barcode_BarcodeCalled'].str.cat()

countG = BarcodeCat.count('G')
countT = BarcodeCat.count('T')
countA = BarcodeCat.count('A')
countC = BarcodeCat.count('C')

print ("Frequency of A is " + str(float(countA)/float((len(BarcodeCat)))*100))
print ("Frequency of C is " + str(float(countC)/float((len(BarcodeCat)))*100))
print ("Frequency of G is " + str(float(countG)/float((len(BarcodeCat)))*100))
print ("Frequency of T is " + str(float(countT)/float((len(BarcodeCat)))*100))


# In[17]:


# What is the frequency of each base called per cycle?
# Expect to be roughly equal across all cycles

dflist = []
for cycle in range(1,9):
    df_foci['PerCycle'] = df_foci['Barcode_BarcodeCalled'].str.slice(cycle -1, cycle)
    BarcodeCat = df_foci['PerCycle'].str.cat()
    dflist.append({'Cycle' : int(cycle), 'Nucleotide' : 'A', 'Frequency' : float(BarcodeCat.count('A'))/float(len(BarcodeCat))})
    dflist.append({'Cycle' : int(cycle), 'Nucleotide' : 'C', 'Frequency' : float(BarcodeCat.count('C'))/float(len(BarcodeCat))})
    dflist.append({'Cycle' : int(cycle), 'Nucleotide' : 'G', 'Frequency' : float(BarcodeCat.count('G'))/float(len(BarcodeCat))})
    dflist.append({'Cycle' : int(cycle), 'Nucleotide' : 'T', 'Frequency' : float(BarcodeCat.count('T'))/float(len(BarcodeCat))})
df_parsed = pd.DataFrame(dflist)
g = sns.lineplot(x="Cycle", y="Frequency", hue="Nucleotide", data=df_parsed)
g.set_ylim([.1,.5])
handles, labels = g.get_legend_handles_labels()
g.legend(handles=handles[0:], labels=labels[0:])
g.set_xticks(list(range(1,9)))


# ## Alignment

# In[18]:


df_image = pd.read_csv(os.path.join(output_path,'Image.csv'))


# In[59]:


shift_list = []
corr_list = []
overlap_list = []
for col in df_image.columns:
    if 'shift' in col:
        if 'DAPI' in col:
            shift_list.append(col)
    if 'Correlation_Correlation' in col:
        corr_list.append(col)
    if 'Correlation_Overlap' in col:
        overlap_list.append(col)
df_shift = df_image[shift_list]
df_corr = df_image[corr_list]
df_overlap = df_image[overlap_list]


# In[47]:


# Pixels shifted to align each cycle to Cycle01

sns.stripplot(data=df_shift, orient="h")


# In[58]:


# DAPI correlations after alignment (using "Correlation")
# Need all points to be better than red line
g = sns.stripplot(data=df_corr, orient="h")
g.set_xlim([0,1])
plt.vlines(x = .9,ymin = 0, ymax =len(df_corr.columns), colors = 'red',)


# In[60]:


# DAPI correlations after alignment (using "Overlap")
# Need all points to be better than red line
g = sns.stripplot(data=df_overlap, orient="h")
g.set_xlim([0,1])
plt.vlines(x = .9,ymin = 0, ymax =len(df_corr.columns), colors = 'red',)


# ## Representation

# In[82]:


barcodes = pd.read_csv(os.path.join(barcodes_path,'Barcodes.csv'))
perfect_df = df_foci[df_foci["Barcode_MatchedTo_Score"]==1]

print(f"The number of unique genes in the library is {len(barcodes[gene_col].unique())}")
print(f"Perfect barcodes are detected for {len(perfect_matches_only_df['Barcode_MatchedTo_GeneCode'].unique())} genes\n")
print ("The 10 most detected genes are:")
print(perfect_matches_only_df.Barcode_MatchedTo_GeneCode.value_counts().head(n=10))
print(f"\nThe number of unique barcodes in the library is {len(barcodes[barcode_col].unique())}")
print(f"Perfect barcodes are detected for {len(perfect_matches_only_df['Barcode_MatchedTo_Barcode'].unique())} of them\n")
print ("The 10 most detected barcodes are:")
print(perfect_matches_only_df.Barcode_MatchedTo_Barcode.value_counts().head(n=10))


# # Cell Calling Metrics
# ## ROUGH APPROXIMATION
# Take these cell quality calls with a grain of salt because of the very rough cell segmentation.
# Please just use the percent perfect foci calls instead.

# In[8]:


num_perf_cells = len(pd.read_csv(os.path.join(output_path,'Cells_Perfect.csv'),usecols=['ObjectNumber']))
num_great_cells = len(pd.read_csv(os.path.join(output_path,'Cells_Great.csv'),usecols=['ObjectNumber']))
print (f"Percent perfect cells {num_perf_cells/num_cells}")
print (f"Percent useable cells (perfect + great) is {(num_great_cells+num_perf_cells)/num_cells}")


# In[ ]:





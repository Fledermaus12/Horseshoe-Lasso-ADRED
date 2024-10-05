version_id = "r03"
file_translation = '../CID_DB_directory.xlsx'


# Imports
from extern_vars import translation_ext
import pandas as pd
import numpy as np
import pipeline_tools
import importlib
#importlib.reload(pipeline_tools)
filename = f'programfiles/data_{version_id}.csv'
data_og = pd.read_csv(filename, index_col=0)

data = data_og.copy()
# ### Matrix
# 1. Split dataset into the matrix:
# 2. One-Hot encoding
# 3. Only commonly used medications -> choose cutoff value

split_col_number = 13
## Split Matrix in medication and patient data to apply filters
medimatrix = data.iloc[:,split_col_number:].copy()
# scalar into binary
medimatrix[medimatrix != 0] = 1

# The next step is a filter. The cut-off value is arbitary, here we try to go with the 80-20 rule and try to cover 80% of all substances taken in our dataset. We can reach it by setting the cut-off value to **>= 32**. <br>
# How we get to the 32 can be seen in stats file -> it shows the best ratio between covered substance and dimensionality reduction.
# 
# 82 -> If we want to reach a dimension of 120
medimatrix = medimatrix.loc[:, medimatrix.sum() >= 32]


# ---
# ### Translation #############################
# 

tl = pd.read_excel(file_translation).set_index('compound_ger')
tl = tl['compound_eng']

translation = pipeline_tools.translate_medications(medimatrix.columns, tl, translation_ext)
medimatrix = medimatrix.rename(columns=translation)
medimatrix = pipeline_tools.sum_and_remove_duplicates(medimatrix)


colnames_worklist = list(medimatrix.columns)
slash = [item for item in colnames_worklist if "/" in item]
slash_df = pd.DataFrame(slash, columns=['name'])
slash_df.to_excel('modifier_raw.xlsx', index=False)

#
# MODIFIER
#
md = pd.read_excel('modifier.xlsx')
to_split = md[md.Command == 'split']
to_split = to_split.name.to_list()
to_drop = md[md.Command == 'drop']
to_drop = to_drop.name.to_list()
to_drop.append('\\')
to_rename = md[md.Command == 'rename']
to_rename = dict(zip(to_rename['name'], to_rename['Rename']))

mmatrix = pipeline_tools.split_and_distribute(medimatrix, to_split)
mmatrix.drop(to_drop, axis=1, inplace=True)
mmatrix.rename(columns=to_rename, inplace=True)
mmatrix = pipeline_tools.sum_and_remove_duplicates(mmatrix)
mmatrix[mmatrix != 0] = 1


# Second cut-off, only keep the 100 of the most frequent medication

# Calculate column sums
column_sums = mmatrix.sum()
column_sums_df = pd.DataFrame(column_sums, columns=['value_counts']).reset_index()
column_sums_df.to_excel('columns_after_filter_raw.xlsx')
# Sort column sums in descending order and select top 5 columns
top_columns = column_sums.nlargest(100).index
#top_columns_df = pd.DataFrame(list(top_columns), columns=['name'])
mmatrix100 = mmatrix[top_columns]
# sort col alphabetically
mmatrix100 = mmatrix100.sort_index(axis=1, key=lambda x: x.str.lower())


# ### Combine Matrix and Patient data


data_cut = data.iloc[:,:split_col_number]
data_updated = data_cut.join(mmatrix100, how='inner')

# Here we insert a new column that tells us the amount of medication that were excluded during the application the filter.

x = data_updated.iloc[:, split_col_number:].sum(axis=1)
y = -1 * (x - data_updated['Med_Amount'])
data_updated.insert(4, 'Med_Amount_Excluded', y)
del x, y
data_updated

# translate first columns to english
translation_ext = {
    "Alter":"age",
    "Geschlecht":"sex",
    "Patient":"patient"
}
data_updated = data_updated.rename(columns=translation_ext)
## Export
filename = f'programfiles/data-100_R_en_{version_id}.csv'
data_updated.to_csv(filename)



version_id = "r03"
file_smq = '../smq_sturz.xlsx'
file_medikation = '../tbl_Medikation.xlsx'
file_fall = '../tbl_Fall.xlsx'
file_symptome = '../tbl_Symptome_LLT_PT_SOC.xlsx'
file_cyp = '../CYP_analyzed.xlsx'






print('loading symptom file ', file_smq)
symptom_zur_untersuchung = 'Symptom'
import pandas as pd
import numpy as np

## Import medication list from Excel sheet
medikation_og = pd.read_excel(file_medikation)
#medikation_og.columns
medikation_og = pd.DataFrame(medikation_og, columns = ['case_id', 'I_0755_WIRKSTOFF_W'])
medikation = medikation_og.set_index('case_id')
medikation = medikation.rename(columns={'I_0755_WIRKSTOFF_W': 'wirkstoff'})
medikation.fillna('unclear', inplace=True)

# unique medication
case = list(medikation.wirkstoff.unique())
print(len(case))

# group all the medication to an ID
medikation = medikation.groupby('case_id')['wirkstoff'].apply(list).reset_index()

# calculate amount of medication
def listlength(x): return len(x)
medikation['Med_Amount'] = medikation['wirkstoff'].apply(listlength)
medikation.set_index('case_id', inplace=True)

# Patientenstammdaten importieren
patdata = pd.read_excel(file_fall)
patdata = pd.DataFrame(patdata, columns = ['case_id','I_0100_ALTER', 'I_0105_GESCHLECHT'])
patdata.set_index('case_id', inplace=True)
patdata = patdata.rename(columns={
    'I_0100_ALTER': 'Alter',
    'I_0105_GESCHLECHT': 'Geschlecht'})

data = medikation.join(patdata, how='inner')

## import patient systoms from Excel sheet
symptome = pd.read_excel(file_symptome)
symptome = pd.DataFrame(symptome, columns = ['case_id', 'PT_name', "PT_code"])
symptome = symptome.dropna(subset=["PT_code"])
smq = pd.read_excel(file_smq)
smq = smq.PT.to_list()
symptome['PT_code'] = symptome['PT_code'].astype(int)
symptome = symptome.set_index('case_id')

symplist = symptome.loc[symptome.loc[:, 'PT_code'].isin(smq)]
symplist = list(symplist.index)







###############################
# Mit der Extension fill enzyme Prozedur wird eine CYP_analyzed.xlsx Datei generiert 
# Hier wird die Datei als Lexikon benutzt pro Patient 

cypdata = pd.read_excel(file_cyp, index_col=1)
cypdata = cypdata.iloc[:,2:]

li = ["Enoxaparin", "Bicalutamid", "Metoprolol"]

def analyze_cyp(drug_list, cyp_data):
    """
    Analyze the impact of a list of drugs on CYP enzyme data.

    Args:
        drug_list (list): A list of drug names to be analyzed.
        cyp_data (DataFrame): A DataFrame containing CYP enzyme data, where
                              each row corresponds to a drug and each column to a CYP enzyme.
    
    Returns:
        numpy.ndarray: A summary array where each value corresponds to the 
                       cumulative effect of the drug list on the respective CYP enzymes.
    """
    # Initialize a zeroed array with the same length as the number of CYP columns
    cyp_summary = np.zeros(len(cyp_data.columns), dtype=int)

    # Iterate over each drug in the list and sum its CYP effects
    for drug in drug_list:
        try:
            # Accumulate the values from the corresponding row in cyp_data
            cyp_summary += cyp_data.loc[drug].to_numpy()
        except KeyError:
            # Handle the case where a drug is not found in the DataFrame
            print(f"Warning: {drug} not found in CYP data.")
    
    # Return the resulting cumulative array
    return cyp_summary


line = []
data['wirkstoff'].apply(lambda x: line.append(analyze_cyp(x, cypdata)))
result = pd.DataFrame(line, columns=[cypdata.columns])
data = data.reset_index()
data_combined = pd.concat([data, result], axis=1)
data_combined.columns = [col[0] if isinstance(col, tuple) else col for col in data_combined.columns]
data_combined = data_combined.set_index('case_id')


# Make Crosstab
medikation_og['Value'] = 1
matrix = pd.crosstab(medikation_og.case_id, medikation_og['I_0755_WIRKSTOFF_W'])
matrix

# join crosstab matrix with patient data
matrix = data_combined.join(matrix, how='inner')

## check if the patient fell
def check_for_fall(elem):
    if elem in symplist: return 1
    else: return 0
matrix.insert(0,symptom_zur_untersuchung,matrix.index.map(check_for_fall))


## create own column for "Number of appearance" from the case_id

matrix = matrix.reset_index()
matrix.insert(1, 'NumOfApp', value=matrix['case_id'].str.split('_').str[1])
matrix.insert(1, 'Patient', value=matrix['case_id'].str.split('_').str[0])
matrix.drop(columns='wirkstoff', inplace=True)
matrix.set_index('case_id', inplace=True)
matrix

data = matrix.loc[matrix.loc[:,'NumOfApp']=='1',:].copy()
data.drop(columns='NumOfApp', inplace=True)

## save the matrix in a csv file
filename = f'programfiles/data_{version_id}.csv'
print('saving data to ', filename)
data.to_csv(filename)

#######################################################################



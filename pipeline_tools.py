import pandas as pd
def translate_medications(col, tl, translation_ext):
    """
    Translates medication names based on a provided translation DataFrame and a fallback translation dictionary.
    
    Parameters:
    - col (pd.Index or list): Column names or medication names to be translated.
    - tl (pd.DataFrame): A DataFrame where the index contains medication names and a column 'compound_eng' with translations.
    - translation_ext (dict): A dictionary containing additional translations for medications not found in tl.

    Returns:
    - dict: A dictionary containing the translated medication names.
    """
    translation = {i: tl.get(i, None) for i in col if i in tl.index}

    # Log medications that were not found in tl
    not_found = [i for i in col if i not in tl.index]
    if not_found:
        print(f"Medications not found: {not_found}")

    # Merge with additional manual translations
    translation = {**translation, **translation_ext}
    
    return translation


def sum_and_remove_duplicates(df):
    # Step 1: Create a dictionary to store the sum of duplicate columns
    column_data = {}
    
    # Step 2: Iterate over unique column names
    for col in df.columns.unique():
        # Step 3: Sum the duplicate columns for each unique column name
        column_data[col] = df.filter(like=col).sum(axis=1)
    
    # Step 4: Use pd.concat to concatenate the summed columns into a new DataFrame at once
    result_df = pd.concat(column_data, axis=1)
    
    return result_df

def split_and_distribute(table, combinations):
    """
    This function splits combination substances (with slashes in their names) into individual components,
    and sums their values into respective columns. If a component column does not exist, it is created.

    Parameters:
    - tbl: the DataFrame containing combination columns.
    - combinations: a list of strings with combination substances separated by '/'.

    Returns:
    - Updated DataFrame with individual substance columns.
    """
    tbl = table.copy()
    # Iterate over each combination string in the list
    for elem in combinations:
        original_column = tbl[elem]  # Get the values of the combination column
        
        # Split the combination into individual substances, strip any extra spaces, and convert to lowercase
        components = [comp.strip().lower() for comp in elem.split('/')]

        # Loop through each substance in the combination
        for med in components:
            if med in tbl.columns:
                # If the column exists, add the values from the combination column
                tbl[med] = tbl[med] + original_column
            else:
                # If the column does not exist, create it with the values from the combination column
                tbl[med] = original_column

        # Drop the original combination column after processing
        tbl.drop(elem, axis=1, inplace=True)

    return tbl
import pandas as pd
from utils import clean_col

def load_excel(excel_path: str) -> pd.DataFrame:
    df = pd.read_excel(excel_path)
    df.columns = [clean_col(c) for c in df.columns]
    return df
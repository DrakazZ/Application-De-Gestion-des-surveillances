import pandas as pd

class DBHandler:

    REQUIRED_COLUMNS = ['Date', 'Time', 'Teacher']  

    def __init__(self):
        self.data = pd.DataFrame()  # Placeholder for actual data

    def swap_sessions(self, id1, id2):
        # Example logic
        idx1 = self.data.index[self.data['prof_id'] == id1][0]
        idx2 = self.data.index[self.data['prof_id'] == id2][0]
        self.data.iloc[[idx1, idx2]] = self.data.iloc[[idx2, idx1]]
        print(f"Swapped {id1} and {id2}")

    def mark_session_reported(self, prof, date, time):
        # Flag session as reported
        print(f"Marked session for {prof} ({date} {time}) as reported")

    def export_to_excel(self, path):
        self.data.to_excel(path, index=False)
        print(f"Exported data to {path}")

    def import_from_excel(self, path):
        try:
            df = pd.read_excel(path)
        except Exception as e:
            raise ValueError(f"Could not read Excel file: {e}")
        
        # Strip spaces from column names
        df.columns = df.columns.str.strip()

        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        self.data = df
        print(f"Imported data from {path}")
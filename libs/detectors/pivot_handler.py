import pandas as pd

class PivotDetector:
    def __init__(self, df, period=3):
        """
        Initialize the PivotDetector class with a DataFrame and period.
        """
        self.df = df
        self.period = period
        self.pivots = self.find_pivots()

    def find_pivots(self):
        """
        Detect pivot points within the DataFrame.
        """
        pivots = []
        for i in range(self.period, len(self.df) - self.period):
            if i in self.df.index:
                max_range = self.df['High'][max(0, i - self.period):min(i + self.period + 1, len(self.df))]
                min_range = self.df['Low'][max(0, i - self.period):min(i + self.period + 1, len(self.df))]

                if self.df.at[i, 'High'] == max(max_range):
                    pivots.append((i, self.df.at[i, 'High'], 'max'))
                elif self.df.at[i, 'Low'] == min(min_range):
                    pivots.append((i, self.df.at[i, 'Low'], 'min'))
        return pivots

    def add_pivot_column(self):
        """
        Add a column to the DataFrame to indicate pivot points.
        """
        self.df['isPivot'] = 0
        for pivot in self.pivots:
            pivot_type = 1 if pivot[2] == 'max' else 2
            self.df.at[pivot[0], 'isPivot'] = pivot_type
        return self.df

    def list_pivots(self, pivot_type='both'):
        """
        Return a list of pivot points based on the specified type.
        """
        if pivot_type not in ['max', 'min', 'both']:
            raise ValueError("pivot_type must be 'max', 'min', or 'both'")

        if 'isPivot' not in self.df.columns:
            self.add_pivot_column()

        if pivot_type == 'max':
            return self.df[self.df['isPivot'] == 1].index.tolist()
        elif pivot_type == 'min':
            return self.df[self.df['isPivot'] == 2].index.tolist()
        else:  # 'both'
            return self.df[self.df['isPivot'] > 0].index.tolist()
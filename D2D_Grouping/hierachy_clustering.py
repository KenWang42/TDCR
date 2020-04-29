import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster

nMTCD = 30000
MTCD_df = pd.read_csv(f'MTCD_Position/MTCD_position_{nMTCD}.csv')

X = np.vstack((MTCD_df.x, MTCD_df.y)).T

Z = linkage(X, 'complete')

clusters = fcluster(Z, 100, criterion='distance')

df = MTCD_df.assign(clusters=list(clusters))

df.to_csv(f'D2D_Grouping/MTCD_grouping_{nMTCD}.csv', index=False)
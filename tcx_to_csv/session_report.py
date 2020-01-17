import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

df = pd.read_csv('./20180111T151701Z_Biking.csv', sep=',', comment="#")
FTP_df = df.loc[:1120, ['Time(s)', 'HeartRateBpm', 'Cadence(1/min)', 'Power(Watts)']].copy()
FTP_df.rename(columns={'Time(s)': 'Time(min)'}, inplace=True)
FTP_df['Time(min)'] = FTP_df['Time(min)']/60

rcpo = mpl.rcParamsOrig
rcpd = mpl.rcParamsDefault
origDF = pd.DataFrame([str(val) for val in rcpo.values()], index=rcpo.keys())
defDF = pd.DataFrame([str(val) for val in rcpd.values()], index=rcpd.keys())
rcDF = pd.concat([origDF, defDF], axis=1)
rcDF.columns = ['o', 'd']
rcDF[(rcDF['o'] != rcDF['d'])]

mpl.rcParams.update(mpl.rcParamsOrig)
FTP_df.plot(x=0)
plt.show()
mpl.rcParams['figure.dpi'] = 720.0

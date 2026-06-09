import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 設定字型為微軟正黑體
plt.rcParams['axes.unicode_minus'] = False

conn = sqlite3.connect('MLB.db')
cursor = conn.cursor()

query = """SELECT  
    th.TeamSeasonID,
    th.AVG AS BattingAVG,
    th.HR,
    tp.W,
    tp.L,
    CAST(W AS FLOAT) / (W + L) AS WinRate
FROM TeamHittingStats th
JOIN TeamPitchingStats tp
    ON th.TeamSeasonID = tp.TeamSeasonID 
JOIN Season s  
    ON th.SeasonID = s.SeasonID 
WHERE s.SeasonYear BETWEEN 2003 AND 2023
ORDER BY WinRate ASC;"""

# 讀取成 DataFrame
df = pd.read_sql_query(query, conn)


# 預覽結果
# print(df.head())

# Q1
df['WinRate'] = pd.to_numeric(df['WinRate'])
df['BattingAVG'] = pd.to_numeric(df['BattingAVG'])

df.plot(x='WinRate', y='BattingAVG')
plt.title('Batting AVG vs Win Rate')
plt.savefig('Q1_scatter_plot.png')
plt.clf()

bins = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
labels = ['0.2-0.3', '0.3-0.4', '0.4-0.5', '0.5-0.6', '0.6-0.7', '0.7-0.8']
df['WinRate_Group'] = pd.cut(df['WinRate'], bins=bins, labels=labels)
sns.violinplot(x='WinRate_Group', y='BattingAVG', data=df)
plt.title('Batting AVG Distribution by Win Rate Group')
plt.savefig('Q1_violin_plot.png')
plt.clf()

# Q2
hr_total_by_group = df.groupby('WinRate_Group')['HR'].sum().reset_index()
sns.barplot(x='WinRate_Group', y='HR', data=hr_total_by_group)
plt.title('Total Home Runs by Win Rate Group')
plt.savefig('Q2_barchart.png')
plt.clf()

# ---------------------------------------------------------------------------------
query2 = """SELECT  
    s.SeasonID,
    tp.TeamSeasonID,
    pp.ERA,
    tp.W,
    tp.L,
    CAST(tp.W AS FLOAT) / (tp.W + tp.L) AS WinRate
FROM PlayerPitchingStats pp
JOIN TeamPitchingStats tp
    ON pp.TeamSeasonID = tp.TeamSeasonID 
JOIN Season s  
    ON pp.SeasonID = s.SeasonID 
WHERE s.SeasonYear BETWEEN 2003 AND 2023;"""

df_pitchers = pd.read_sql_query(query2, conn)

# Q3
# 確保 ERA 是數字格式，並排除掉沒有 ERA (NaN) 的無效資料
df_pitchers['ERA'] = pd.to_numeric(df_pitchers['ERA'], errors='coerce')
df_pitchers = df_pitchers.dropna(subset=['ERA'])

# 先整理出一份乾淨的「球隊勝率清單」
team_win_rates = df_pitchers[['SeasonID', 'TeamSeasonID', 'WinRate']].drop_duplicates()

# 利用 idxmax() 和 idxmin() 找出每年 (SeasonID) 勝率最大和最小的 row
best_teams_idx = team_win_rates.groupby('SeasonID')['WinRate'].idxmax()
worst_teams_idx = team_win_rates.groupby('SeasonID')['WinRate'].idxmin()

best_teams = team_win_rates.loc[best_teams_idx, 'TeamSeasonID']
worst_teams = team_win_rates.loc[worst_teams_idx, 'TeamSeasonID']

# 將屬於這些極端球隊的投手 ERA 篩選出來
best_pitchers_era = df_pitchers[df_pitchers['TeamSeasonID'].isin(best_teams)]['ERA']
worst_pitchers_era = df_pitchers[df_pitchers['TeamSeasonID'].isin(worst_teams)]['ERA']

# 設定邊界與對應的標籤名稱
custom_bins = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 200.0]
bin_labels = ['0-1', '1-2', '2-3', '3-4', '4-5', '5-6', '6-7', '7-8', '8-9', '9-10', '10-200']

# 用 pd.cut 把原本的 ERA 數字轉換成這 11 個標籤
best_era_groups = pd.cut(best_pitchers_era, bins=custom_bins, labels=bin_labels)
worst_era_groups = pd.cut(worst_pitchers_era, bins=custom_bins, labels=bin_labels)

sns.countplot(x=best_era_groups)
plt.title('Highest Winning Rate Teams')
plt.xlabel('ERA')
plt.ylabel('投手人數')
plt.ylim(0, 130)
plt.tight_layout() # 自動調整排版避免邊緣被裁切
plt.savefig('Q3_highest_teams_era.png')
plt.clf()

sns.countplot(x=worst_era_groups)
plt.title('Lowest Winning Rate Teams')
plt.xlabel('ERA')
plt.ylabel('投手人數')
plt.ylim(0, 130)
plt.tight_layout()
plt.savefig('Q3_lowest_teams_era.png')
plt.clf()


# Q4
best_counts = best_era_groups.value_counts(sort=False)
patches, texts = plt.pie(best_counts, startangle=140)
total_best = best_counts.sum()
best_legend_labels = [f'{idx}: {count}人 ({count/total_best*100:.1f}%)' 
                      for idx, count in zip(best_counts.index, best_counts)]
plt.legend(patches, best_legend_labels, title="ERA Range", loc="center left", bbox_to_anchor=(1, 0.5))
plt.title('ERA Distribution: Highest Winning Rate Teams')
plt.savefig('Q4_highest_teams_pie.png', bbox_inches='tight')
plt.clf()

worst_counts = worst_era_groups.value_counts(sort=False)
patches, texts = plt.pie(worst_counts, startangle=140)
total_best = worst_counts.sum()
best_legend_labels = [f'{idx}: {count}人 ({count/total_best*100:.1f}%)' 
                      for idx, count in zip(worst_counts.index, worst_counts)]
plt.legend(patches, best_legend_labels, title="ERA Range", loc="center left", bbox_to_anchor=(1, 0.5))
plt.title('ERA Distribution: Lowest Winning Rate Teams')
plt.savefig('Q4_lowest_teams_pie.png', bbox_inches='tight')
plt.close()

conn.close()
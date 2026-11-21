# RESULTS SUMMARY (generated 2026-11-21 13:58), python 3.12.10, pandas 2.3.3, numpy 2.2.6

## DESCRIPTIVE ANALYTICS
Modeling rows: 4850; distinct contests: 1395

### numeric_summary.csv
```
      attribute       mean     median         sd     variance       min        q1         q3        max        iqr  skew
    party_votes  578738.61  188104.50  935346.02 8.748722e+11      1.00  21523.50  780143.75 12244170.0  758620.25  3.51
    total_votes 2085983.72 1388708.00 2175631.71 4.733373e+12 101973.00 579784.00 2707327.00 17500881.0 2127543.00  2.27
party_share_pct      28.76      34.66      24.69 6.094600e+02      0.00      1.54      49.70      100.0      48.15  0.13
     margin_pct      18.38      15.13      15.62 2.441300e+02      0.01      6.48      25.95      100.0      19.47  1.62
```

### freq_party_simplified.csv
```
party_simplified  count  percent
      REPUBLICAN   1382    28.49
        DEMOCRAT   1378    28.41
           OTHER   1197    24.68
     LIBERTARIAN    893    18.41
```

### freq_office.csv
```
      office  count  percent
   US SENATE   2496    51.46
US PRESIDENT   2354    48.54
```

### freq_us_region.csv
```
us_region  count  percent
    South   1535    31.65
     West   1260    25.98
  Midwest   1176    24.25
Northeast    879    18.12
```

### freq_election_era.csv
```
  election_era  count  percent
Era3_2005_2021   1702    35.09
Era2_1990_2004   1683    34.70
Era1_1976_1988   1465    30.21
```

### freq_is_contest_winner.csv
```
 is_contest_winner  count  percent
                 0   3455    71.24
                 1   1395    28.76
```
Class imbalance (non-winner : winner) = 2.48 : 1

### correlation_matrix.csv
```
                 party_share_pct  margin_pct  log_total_votes  log_party_votes
party_share_pct            1.000       0.068           -0.048            0.783
margin_pct                 0.068       1.000           -0.318           -0.102
log_total_votes           -0.048      -0.318            1.000            0.377
log_party_votes            0.783      -0.102            0.377            1.000
```

### margin_by_office.csv
```
              count   mean  median    std
office                                   
US PRESIDENT    612  15.80   13.01  13.77
US SENATE       783  22.02   17.50  18.65
```

### margin_by_us_region.csv
```
           count   mean  median    std
us_region                             
Midwest      331  16.41   13.21  14.12
Northeast    248  18.34   15.78  13.56
South        457  20.52   16.30  19.41
West         359  21.05   16.57  17.80
```

### margin_by_election_era.csv
```
                count   mean  median    std
election_era                               
Era1_1976_1988    436  18.74   14.31  17.05
Era2_1990_2004    477  18.64   13.39  17.36
Era3_2005_2021    482  20.44   17.35  16.45
```

### pres_votes_by_year.csv
```
      pres_total_votes
year                  
1976          81601344
1980          86496851
1984          92654861
1988          91586825
1992         104599780
1996          96389818
2000         105593982
2004         122349450
2008         131419253
2012         129139997
2016         136787187
2020         158528503
```
Tightest 5 states (mean margin): NC=6.27, PA=8.51, MO=9.4, WI=9.84, CO=9.96
Widest 5 states (mean margin): ID=31.3, UT=32.86, HI=33.15, WY=35.24, DC=76.4

### pie_angles.csv
```
                       votes  percent  angle_deg  contest_wins
party_simplified                                              
DEMOCRAT          1380041843    49.17     177.01           643
LIBERTARIAN         25220277     0.90       3.24             0
OTHER              100448346     3.58      12.89             9
REPUBLICAN        1301171797    46.36     166.90           743
```

### scaling_before_after.csv
```
          raw  minmax  zscore  decimal(j=2)
min   11.5325  0.0000 -2.4923        0.1153
max   16.6778  1.0000  2.5604        0.1668
mean  14.0705  0.4933  0.0000        0.1407
std    1.0183  0.1979  1.0000        0.0102
```
Tertile cut points of total_votes: [802583.0, 2168477.0]

### region_hierarchy.csv
```
                                                                       states
us_region                                                                    
Midwest                        IA, IL, IN, KS, MI, MN, MO, ND, NE, OH, SD, WI
Northeast                                  CT, MA, ME, NH, NJ, NY, PA, RI, VT
South      AL, AR, DC, DE, FL, GA, KY, LA, MD, MS, NC, OK, SC, TN, TX, VA, WV
West                       AK, AZ, CA, CO, HI, ID, MT, NM, NV, OR, UT, WA, WY
```
party_votes (modeling table): rows above upper fence 1,918,074.1: 377
total_votes (modeling table): rows above upper fence 5,898,641.5: 291
Rows with total_votes < 1000 (investigate): 0

## PLOTS (saved in outputs/plots)
```
Stem-and-leaf: 2020 presidential total votes, 51 jurisdictions
Key: 3 | 4 = 3.4 million

  0 | 2 3 3 3 3 4 5 5 5 6 7 8 8 8 9 9
  1 | 2 3 3 4 4 5 7 8
  2 | 1 1 3 3 5
  3 | 0 0 0 0 2 2 2 3 6
  4 | 0 4 5 9
  5 | 5 5 9
  6 | 0 9
  7 | 
  8 | 6
  9 | 
 10 | 
 11 | 0 3
 12 | 
 13 | 
 14 | 
 15 | 
 16 | 
 17 | 5
```
14 plots written. Now OPEN each one and write Observation / Inferences from what you SEE and from tables/*.csv.

## DIC
N=4850, min_support=0.15, min_count=728, min_conf=0.7, M=485, max_k=8
DIC finished in 37 intervals (= 3.70 equivalent database passes), 0.128s; frequent itemsets = 162

### dic_trace.csv
```
 interval  transactions_in_interval  DC  DS  SC  SS  new_candidates
        1                       485  27   0   0   0               0
        2                       485  27   3   0   0               3
        3                       485  29   4   0   0               3
        4                       485  40   8   0   0              15
        5                       485  91  14   0   0              57
        6                       485 160  20   0   0              75
        7                       485 233  25   0   0              78
        8                       485 275  29   0   0              46
        9                       485 296  33   0   0              25
       10                       485 291  15   2  25               4
       11                       485 288  21   2  25               3
       12                       485 285  29   2  28               8
       13                       485 286  30   2  31               5
       14                       485 285  32   6  42              16
       15                       485 267  20  40  65              27
       16                       485 199  17 106  74               4
       17                       485 156   7 164  94              25
       18                       485 110   7 205  99               0
       19                       485  84   9 228 101               1
       20                       485  79  10 228 105               0
       21                       485  75  12 228 108               1
       22                       485  70   9 230 114               0
       23                       485  70   5 230 119               1
       24                       485  58   3 237 128               2
       25                       485  31   4 252 140               1
       26                       485  29   2 253 143               0
       27                       485   7   0 266 155               1
       28                       485   6   1 266 155               0
       29                       485   6   0 266 156               0
       30                       485   5   1 266 156               0
       31                       485   5   0 266 157               0
       32                       485   4   1 266 157               0
       33                       485   3   1 266 158               0
       34                       485   1   1 266 160               0
       35                       485   1   0 266 161               0
       36                       485   1   0 266 161               0
       37                       485   0   0 266 162               0
```
Frequent itemsets by size: {1: 25, 2: 74, 3: 56, 4: 7}
Top 25 frequent itemsets (full list in tables/dic_frequent_itemsets.csv):
```
                                                 itemset  size  count  support_pct
                                         Contest=Regular     1   4773        98.41
                                               Winner=No     1   3455        71.24
                             Contest=Regular & Winner=No     2   3402        70.14
                                        Office=US_SENATE     1   2496        51.46
                                 Margin=Margin_Safe_gt15     1   2444        50.39
                      Contest=Regular & Office=US_SENATE     2   2419        49.88
               Contest=Regular & Margin=Margin_Safe_gt15     2   2407        49.63
                                     Office=US_PRESIDENT     1   2354        48.54
                   Contest=Regular & Office=US_PRESIDENT     2   2354        48.54
                              Share=Share_Negligible_0_5     1   1796        37.03
                  Share=Share_Negligible_0_5 & Winner=No     2   1796        37.03
Contest=Regular & Share=Share_Negligible_0_5 & Winner=No     3   1769        36.47
            Contest=Regular & Share=Share_Negligible_0_5     2   1769        36.47
                         Office=US_PRESIDENT & Winner=No     2   1742        35.92
       Contest=Regular & Office=US_PRESIDENT & Winner=No     3   1742        35.92
                     Margin=Margin_Safe_gt15 & Winner=No     2   1724        35.55
                            Office=US_SENATE & Winner=No     2   1713        35.32
                                      Era=Era3_2005_2021     1   1702        35.09
   Contest=Regular & Margin=Margin_Safe_gt15 & Winner=No     3   1698        35.01
                                      Era=Era2_1990_2004     1   1683        34.70
          Contest=Regular & Office=US_SENATE & Winner=No     3   1660        34.23
                    Contest=Regular & Era=Era2_1990_2004     2   1659        34.21
                    Contest=Regular & Era=Era3_2005_2021     2   1659        34.21
                             Turnout=Turnout_Low_Tertile     1   1619        33.38
                            Turnout=Turnout_High_Tertile     1   1617        33.34
```
Rules with conf >= 0.7: 163

Top definitional rules (4 total):
```
                   antecedent                  consequent  support  confidence   lift  count
  Share=Share_Majority_50_100                  Winner=Yes   0.2421      1.0000 3.4767   1174
                   Winner=Yes Share=Share_Majority_50_100   0.2421      0.8416 3.4767   1174
   Share=Share_Negligible_0_5                   Winner=No   0.3703      1.0000 1.4038   1796
Share=Share_Competitive_35_50                   Winner=No   0.2080      0.8203 1.1515   1009
```

Top informative rules (159 total):
```
                                     antecedent                                               consequent  support  confidence   lift  count
  Contest=Regular & Share=Share_Majority_50_100                                               Winner=Yes   0.2377      1.0000 3.4767   1153
                                     Winner=Yes            Contest=Regular & Share=Share_Majority_50_100   0.2377      0.8265 3.4767   1153
                    Share=Share_Majority_50_100                             Contest=Regular & Winner=Yes   0.2377      0.9821 3.4743   1153
                   Contest=Regular & Winner=Yes                              Share=Share_Majority_50_100   0.2377      0.8410 3.4743   1153
                              Party=LIBERTARIAN             Contest=Regular & Share=Share_Negligible_0_5   0.1765      0.9586 2.6281    856
                              Party=LIBERTARIAN Contest=Regular & Share=Share_Negligible_0_5 & Winner=No   0.1765      0.9586 2.6281    856
                  Party=LIBERTARIAN & Winner=No             Contest=Regular & Share=Share_Negligible_0_5   0.1765      0.9586 2.6281    856
                              Party=LIBERTARIAN                               Share=Share_Negligible_0_5   0.1788      0.9709 2.6218    867
                              Party=LIBERTARIAN                   Share=Share_Negligible_0_5 & Winner=No   0.1788      0.9709 2.6218    867
                  Party=LIBERTARIAN & Winner=No                               Share=Share_Negligible_0_5   0.1788      0.9709 2.6218    867
            Contest=Regular & Party=LIBERTARIAN                               Share=Share_Negligible_0_5   0.1765      0.9705 2.6208    856
            Contest=Regular & Party=LIBERTARIAN                   Share=Share_Negligible_0_5 & Winner=No   0.1765      0.9705 2.6208    856
Contest=Regular & Party=LIBERTARIAN & Winner=No                               Share=Share_Negligible_0_5   0.1765      0.9705 2.6208    856
                        Party=OTHER & Winner=No                               Share=Share_Negligible_0_5   0.1911      0.7803 2.1072    927
      Contest=Regular & Party=OTHER & Winner=No                               Share=Share_Negligible_0_5   0.1878      0.7800 2.1063    911
```

### dic_sensitivity.csv
```
 min_support  min_confidence  frequent_itemsets  rules
        0.10             0.6                372    480
        0.10             0.7                372    404
        0.10             0.8                372    318
        0.15             0.6                162    180
        0.15             0.7                162    163
        0.15             0.8                162    122
        0.20             0.6                 80     91
        0.20             0.7                 80     77
        0.20             0.8                 80     54
```

## CLOSET
f-list (descending support): ['Contest=Regular', 'Winner=No', 'Office=US_SENATE', 'Margin=Margin_Safe_gt15', 'Office=US_PRESIDENT', 'Share=Share_Negligible_0_5', 'Era=Era3_2005_2021', 'Era=Era2_1990_2004', 'Turnout=Turnout_Low_Tertile', 'Turnout=Turnout_High_Tertile', 'Turnout=Turnout_Mid_Tertile', 'Region=South', 'Margin=Margin_Moderate_5_15', 'Era=Era1_1976_1988', 'Winner=Yes', 'Party=REPUBLICAN', 'Party=DEMOCRAT', 'Region=West', 'Share=Share_Competitive_35_50', 'Party=OTHER', 'Region=Midwest', 'Share=Share_Majority_50_100', 'Margin=Margin_Close_lt5', 'Party=LIBERTARIAN', 'Region=Northeast']
CLOSET: 133 closed frequent itemsets in 0.281s
Closedness verification (brute force over DIC frequent itemsets): sets equal = True; violations (CFI with equal-support superset) = 0
Lossless check (support of every frequent itemset recovered from closed supersets): True
DIC frequent itemsets F=162, closed C=133, reduction=17.90%
```
                                                                           itemset  size  count  support_pct
                                                                   Contest=Regular     1   4773        98.41
                                                                         Winner=No     1   3455        71.24
                                                       Contest=Regular & Winner=No     2   3402        70.14
                                                                  Office=US_SENATE     1   2496        51.46
                                                           Margin=Margin_Safe_gt15     1   2444        50.39
                                                Contest=Regular & Office=US_SENATE     2   2419        49.88
                                         Contest=Regular & Margin=Margin_Safe_gt15     2   2407        49.63
                                             Contest=Regular & Office=US_PRESIDENT     2   2354        48.54
                                            Share=Share_Negligible_0_5 & Winner=No     2   1796        37.03
                          Contest=Regular & Share=Share_Negligible_0_5 & Winner=No     3   1769        36.47
                                 Contest=Regular & Office=US_PRESIDENT & Winner=No     3   1742        35.92
                                               Margin=Margin_Safe_gt15 & Winner=No     2   1724        35.55
                                                      Office=US_SENATE & Winner=No     2   1713        35.32
                                                                Era=Era3_2005_2021     1   1702        35.09
                             Contest=Regular & Margin=Margin_Safe_gt15 & Winner=No     3   1698        35.01
                                                                Era=Era2_1990_2004     1   1683        34.70
                                    Contest=Regular & Office=US_SENATE & Winner=No     3   1660        34.23
                                              Contest=Regular & Era=Era2_1990_2004     2   1659        34.21
                                              Contest=Regular & Era=Era3_2005_2021     2   1659        34.21
                                                       Turnout=Turnout_Low_Tertile     1   1619        33.38
                                                      Turnout=Turnout_High_Tertile     1   1617        33.34
                                                       Turnout=Turnout_Mid_Tertile     1   1614        33.28
                                     Contest=Regular & Turnout=Turnout_Low_Tertile     2   1598        32.95
                                    Contest=Regular & Turnout=Turnout_High_Tertile     2   1592        32.82
                                     Contest=Regular & Turnout=Turnout_Mid_Tertile     2   1583        32.64
                                                                      Region=South     1   1535        31.65
                                                    Contest=Regular & Region=South     2   1500        30.93
                                                       Margin=Margin_Moderate_5_15     1   1470        30.31
                                                                Era=Era1_1976_1988     1   1465        30.21
                                              Contest=Regular & Era=Era1_1976_1988     2   1455        30.00
                                     Contest=Regular & Margin=Margin_Moderate_5_15     2   1448        29.86
                                        Margin=Margin_Safe_gt15 & Office=US_SENATE     2   1404        28.95
                                                                        Winner=Yes     1   1395        28.76
                                                                  Party=REPUBLICAN     1   1382        28.49
                                                                    Party=DEMOCRAT     1   1378        28.41
                                                      Contest=Regular & Winner=Yes     2   1371        28.27
                      Contest=Regular & Margin=Margin_Safe_gt15 & Office=US_SENATE     3   1367        28.19
                                                Contest=Regular & Party=REPUBLICAN     2   1359        28.02
                                                  Contest=Regular & Party=DEMOCRAT     2   1355        27.94
                                                                       Region=West     1   1260        25.98
                                                     Contest=Regular & Region=West     2   1242        25.61
                                                     Share=Share_Competitive_35_50     1   1230        25.36
                                                    Era=Era3_2005_2021 & Winner=No     2   1220        25.15
                                   Contest=Regular & Share=Share_Competitive_35_50     2   1208        24.91
                                                    Era=Era2_1990_2004 & Winner=No     2   1206        24.87
                                                                       Party=OTHER     1   1197        24.68
                                  Contest=Regular & Era=Era2_1990_2004 & Winner=No     3   1190        24.54
                                  Contest=Regular & Era=Era3_2005_2021 & Winner=No     3   1190        24.54
                                                           Party=OTHER & Winner=No     2   1188        24.49
                                                     Contest=Regular & Party=OTHER     2   1177        24.27
                                                                    Region=Midwest     1   1176        24.25
                                          Turnout=Turnout_High_Tertile & Winner=No     2   1175        24.23
                                          Share=Share_Majority_50_100 & Winner=Yes     2   1174        24.21
                                         Contest=Regular & Party=OTHER & Winner=No     3   1168        24.08
                        Contest=Regular & Turnout=Turnout_High_Tertile & Winner=No     3   1157        23.86
                                                  Contest=Regular & Region=Midwest     2   1156        23.84
                        Contest=Regular & Share=Share_Majority_50_100 & Winner=Yes     3   1153        23.77
                                           Turnout=Turnout_Mid_Tertile & Winner=No     2   1148        23.67
                                           Turnout=Turnout_Low_Tertile & Winner=No     2   1132        23.34
                         Contest=Regular & Turnout=Turnout_Mid_Tertile & Winner=No     3   1128        23.26
                         Contest=Regular & Turnout=Turnout_Low_Tertile & Winner=No     3   1117        23.03
                                                          Region=South & Winner=No     2   1078        22.23
                                           Margin=Margin_Moderate_5_15 & Winner=No     2   1060        21.86
                                        Contest=Regular & Region=South & Winner=No     3   1055        21.75
                         Contest=Regular & Margin=Margin_Moderate_5_15 & Winner=No     3   1046        21.57
                             Margin=Margin_Safe_gt15 & Turnout=Turnout_Low_Tertile     2   1041        21.46
                   Contest=Regular & Margin=Margin_Safe_gt15 & Office=US_PRESIDENT     3   1040        21.44
           Contest=Regular & Margin=Margin_Safe_gt15 & Turnout=Turnout_Low_Tertile     3   1030        21.24
                                                    Era=Era1_1976_1988 & Winner=No     2   1029        21.22
                                  Contest=Regular & Era=Era1_1976_1988 & Winner=No     3   1022        21.07
                                         Share=Share_Competitive_35_50 & Winner=No     2   1009        20.80
                       Contest=Regular & Share=Share_Competitive_35_50 & Winner=No     3    990        20.41
                                      Era=Era3_2005_2021 & Margin=Margin_Safe_gt15     2    981        20.23
                    Contest=Regular & Era=Era3_2005_2021 & Margin=Margin_Safe_gt15     3    960        19.79
                            Margin=Margin_Safe_gt15 & Office=US_SENATE & Winner=No     3    956        19.71
    Contest=Regular & Office=US_PRESIDENT & Share=Share_Negligible_0_5 & Winner=No     4    949        19.57
                                                           Margin=Margin_Close_lt5     1    936        19.30
          Contest=Regular & Margin=Margin_Safe_gt15 & Office=US_SENATE & Winner=No     4    930        19.18
                              Party=OTHER & Share=Share_Negligible_0_5 & Winner=No     3    927        19.11
                                         Contest=Regular & Margin=Margin_Close_lt5     2    918        18.93
            Contest=Regular & Party=OTHER & Share=Share_Negligible_0_5 & Winner=No     4    911        18.78
                                             Era=Era3_2005_2021 & Office=US_SENATE     2    910        18.76
                                                           Region=West & Winner=No     2    901        18.58
                  Margin=Margin_Safe_gt15 & Share=Share_Negligible_0_5 & Winner=No     3    894        18.43
                                                     Party=LIBERTARIAN & Winner=No     2    893        18.41
                                         Contest=Regular & Region=West & Winner=No     3    888        18.31
                                             Era=Era2_1990_2004 & Office=US_SENATE     2    883        18.21
                                   Contest=Regular & Party=LIBERTARIAN & Winner=No     3    882        18.19
Contest=Regular & Margin=Margin_Safe_gt15 & Share=Share_Negligible_0_5 & Winner=No     4    881        18.16
                                                                  Region=Northeast     1    879        18.12
                                                Contest=Regular & Region=Northeast     2    875        18.04
                           Contest=Regular & Era=Era3_2005_2021 & Office=US_SENATE     3    867        17.88
                        Party=LIBERTARIAN & Share=Share_Negligible_0_5 & Winner=No     3    867        17.88
                                    Office=US_SENATE & Turnout=Turnout_Mid_Tertile     2    865        17.84
                           Contest=Regular & Era=Era2_1990_2004 & Office=US_SENATE     3    859        17.71
      Contest=Regular & Party=LIBERTARIAN & Share=Share_Negligible_0_5 & Winner=No     4    856        17.65
                         Office=US_SENATE & Share=Share_Negligible_0_5 & Winner=No     3    847        17.46
                                                        Region=Midwest & Winner=No     2    845        17.42
                                    Office=US_SENATE & Turnout=Turnout_Low_Tertile     2    834        17.20
                  Contest=Regular & Office=US_SENATE & Turnout=Turnout_Mid_Tertile     3    834        17.20
                                      Contest=Regular & Region=Midwest & Winner=No     3    831        17.13
       Contest=Regular & Office=US_SENATE & Share=Share_Negligible_0_5 & Winner=No     4    820        16.91
              Contest=Regular & Office=US_PRESIDENT & Turnout=Turnout_High_Tertile     3    820        16.91
               Contest=Regular & Margin=Margin_Moderate_5_15 & Office=US_PRESIDENT     3    815        16.80
                  Contest=Regular & Office=US_SENATE & Turnout=Turnout_Low_Tertile     3    813        16.76
                        Contest=Regular & Era=Era2_1990_2004 & Office=US_PRESIDENT     3    800        16.49
                                   Office=US_SENATE & Turnout=Turnout_High_Tertile     2    797        16.43
                                            Margin=Margin_Safe_gt15 & Region=South     2    793        16.35
                             Margin=Margin_Safe_gt15 & Turnout=Turnout_Mid_Tertile     2    792        16.33
                        Contest=Regular & Era=Era3_2005_2021 & Office=US_PRESIDENT     3    792        16.33
               Contest=Regular & Office=US_PRESIDENT & Turnout=Turnout_Low_Tertile     3    785        16.19
                                                     Office=US_SENATE & Winner=Yes     2    783        16.14
           Contest=Regular & Margin=Margin_Safe_gt15 & Turnout=Turnout_Mid_Tertile     3    776        16.00
                          Contest=Regular & Margin=Margin_Safe_gt15 & Region=South     3    775        15.98
                 Contest=Regular & Office=US_SENATE & Turnout=Turnout_High_Tertile     3    772        15.92
                                               Office=US_SENATE & Party=REPUBLICAN     2    770        15.88
                              Contest=Regular & Office=US_PRESIDENT & Region=South     3    769        15.86
       Contest=Regular & Margin=Margin_Safe_gt15 & Office=US_PRESIDENT & Winner=No     4    768        15.84
                                                   Office=US_SENATE & Region=South     2    766        15.79
                                                 Office=US_SENATE & Party=DEMOCRAT     2    766        15.79
                        Contest=Regular & Era=Era1_1976_1988 & Office=US_PRESIDENT     3    762        15.71
                                      Era=Era2_1990_2004 & Margin=Margin_Safe_gt15     2    760        15.67
                                   Contest=Regular & Office=US_SENATE & Winner=Yes     3    759        15.65
                                        Region=South & Turnout=Turnout_Mid_Tertile     2    756        15.59
               Contest=Regular & Office=US_PRESIDENT & Turnout=Turnout_Mid_Tertile     3    749        15.44
                    Contest=Regular & Era=Era2_1990_2004 & Margin=Margin_Safe_gt15     3    748        15.42
                             Contest=Regular & Office=US_SENATE & Party=REPUBLICAN     3    747        15.40
                                                     Party=REPUBLICAN & Winner=Yes     2    743        15.32
                               Contest=Regular & Office=US_SENATE & Party=DEMOCRAT     3    743        15.32
                      Contest=Regular & Region=South & Turnout=Turnout_Mid_Tertile     3    738        15.22
                                                        Party=DEMOCRAT & Winner=No     2    735        15.15
                                 Contest=Regular & Office=US_SENATE & Region=South     3    731        15.07
                                   Contest=Regular & Party=REPUBLICAN & Winner=Yes     3    730        15.05
```
Association rules derived from CFIs (conf >= 0.7): 146
```
                                     antecedent                                               consequent  support  confidence   lift
                    Share=Share_Majority_50_100                                               Winner=Yes   0.2421      1.0000 3.4767
                                     Winner=Yes            Contest=Regular & Share=Share_Majority_50_100   0.2377      0.8265 3.4767
  Contest=Regular & Share=Share_Majority_50_100                                               Winner=Yes   0.2377      1.0000 3.4767
                                     Winner=Yes                              Share=Share_Majority_50_100   0.2421      0.8416 3.4767
                    Share=Share_Majority_50_100                             Contest=Regular & Winner=Yes   0.2377      0.9821 3.4743
                   Contest=Regular & Winner=Yes                              Share=Share_Majority_50_100   0.2377      0.8410 3.4743
                              Party=LIBERTARIAN Contest=Regular & Share=Share_Negligible_0_5 & Winner=No   0.1765      0.9586 2.6281
                  Party=LIBERTARIAN & Winner=No             Contest=Regular & Share=Share_Negligible_0_5   0.1765      0.9586 2.6281
                  Party=LIBERTARIAN & Winner=No                               Share=Share_Negligible_0_5   0.1788      0.9709 2.6218
                              Party=LIBERTARIAN                   Share=Share_Negligible_0_5 & Winner=No   0.1788      0.9709 2.6218
            Contest=Regular & Party=LIBERTARIAN                   Share=Share_Negligible_0_5 & Winner=No   0.1765      0.9705 2.6208
Contest=Regular & Party=LIBERTARIAN & Winner=No                               Share=Share_Negligible_0_5   0.1765      0.9705 2.6208
                        Party=OTHER & Winner=No                               Share=Share_Negligible_0_5   0.1911      0.7803 2.1072
      Contest=Regular & Party=OTHER & Winner=No                               Share=Share_Negligible_0_5   0.1878      0.7800 2.1063
                        Party=OTHER & Winner=No             Contest=Regular & Share=Share_Negligible_0_5   0.1878      0.7668 2.1024
```

## KNN (grouped split by contest; seed 42)
Class distribution: {0: 3455, 1: 1395}

### Variant: full
Features: ['year', 'log_total_votes', 'log_party_votes', 'num_candidates', 'writein_share_pct'] + one-hot office, party_simplified, us_region
train=3878, test=972, shared contests between train/test = 0

### knn_cv_full.csv
```
 K  cv_f1_mean  cv_f1_sd
 3      0.7403    0.0294
 5      0.7333    0.0291
 7      0.7454    0.0350
 9      0.7330    0.0360
11      0.7340    0.0359
13      0.7184    0.0408
15      0.7190    0.0392
17      0.7161    0.0271
19      0.7117    0.0230
21      0.7030    0.0344
23      0.7009    0.0400
25      0.6991    0.0329
```

### knn_examples.csv
```
                contest_id party_simplified  party_share_pct  actual  predicted
US PRESIDENT|1976|MN|False         DEMOCRAT            54.90       1          0
US PRESIDENT|1976|MN|False       REPUBLICAN            42.02       0          1
US PRESIDENT|1976|MN|False            OTHER             2.90       0          0
US PRESIDENT|1976|MN|False      LIBERTARIAN             0.18       0          0
US PRESIDENT|1976|NE|False       REPUBLICAN            59.20       1          1
US PRESIDENT|1976|NE|False         DEMOCRAT            38.45       0          0
US PRESIDENT|1976|NE|False            OTHER             2.10       0          0
US PRESIDENT|1976|NE|False      LIBERTARIAN             0.24       0          0
US PRESIDENT|1976|NH|False       REPUBLICAN            54.75       1          1
US PRESIDENT|1976|NH|False         DEMOCRAT            43.47       0          0
```

Neighbour explanation for test row 0 (US PRESIDENT|1976|MN|False, DEMOCRAT):
```
 distance                  neighbour    party  label
    0.030 US PRESIDENT|1976|MO|False DEMOCRAT      1
    0.130 US PRESIDENT|1976|IN|False DEMOCRAT      0
    0.305 US PRESIDENT|1980|MN|False DEMOCRAT      1
    0.311 US PRESIDENT|1980|MO|False DEMOCRAT      0
    0.335 US PRESIDENT|1980|WI|False DEMOCRAT      0
    0.342 US PRESIDENT|1980|IN|False DEMOCRAT      0
    0.475 US PRESIDENT|1976|IA|False DEMOCRAT      0
-> majority vote = 0, actual = 1
```

Neighbour explanation for test row 1 (US PRESIDENT|1976|MN|False, REPUBLICAN):
```
 distance                  neighbour      party  label
    0.053 US PRESIDENT|1976|MO|False REPUBLICAN      0
    0.202 US PRESIDENT|1976|IN|False REPUBLICAN      1
    0.302 US PRESIDENT|1980|MN|False REPUBLICAN      0
    0.326 US PRESIDENT|1980|MO|False REPUBLICAN      1
    0.354 US PRESIDENT|1980|WI|False REPUBLICAN      1
    0.374 US PRESIDENT|1980|IN|False REPUBLICAN      1
    0.429 US PRESIDENT|1976|IA|False REPUBLICAN      1
-> majority vote = 1, actual = 0
```

Neighbour explanation for test row 2 (US PRESIDENT|1976|MN|False, OTHER):
```
 distance                  neighbour party  label
    0.786 US PRESIDENT|1976|IA|False OTHER      0
    0.815 US PRESIDENT|1980|WI|False OTHER      0
    0.829 US PRESIDENT|1980|MN|False OTHER      0
    1.001 US PRESIDENT|1988|MN|False OTHER      0
    1.045 US PRESIDENT|1984|MN|False OTHER      0
    1.051 US PRESIDENT|1984|WI|False OTHER      0
    1.275 US PRESIDENT|1984|MI|False OTHER      0
-> majority vote = 0, actual = 0
```

### Variant: no_party_votes (leakage ablation)
Features: ['year', 'log_total_votes', 'num_candidates', 'writein_share_pct'] + one-hot office, party_simplified, us_region
train=3878, test=972, shared contests between train/test = 0

### knn_cv_no_party_votes.csv
```
 K  cv_f1_mean  cv_f1_sd
 3      0.7015    0.0208
 5      0.6942    0.0296
 7      0.7190    0.0348
 9      0.7074    0.0444
11      0.7152    0.0443
13      0.6994    0.0431
15      0.7002    0.0367
17      0.6920    0.0255
19      0.6950    0.0256
21      0.6861    0.0361
23      0.6786    0.0294
25      0.6787    0.0331
```

### knn_summary.csv
```
                          variant  K  accuracy  precision  recall  specificity     f1  roc_auc  TN  FP  FN  TP  baseline_accuracy
                             full  7    0.8642     0.7634  0.7634       0.9048 0.7634   0.9222 627  66  66 213              0.713
no_party_votes (leakage ablation)  7    0.8323     0.7071  0.7097       0.8817 0.7084   0.9002 611  82  81 198              0.713
```

## AGNES on states (presidential contests, z-scored, Euclidean)
n = 51 states; features = ['mean_dem_share', 'volatility_dem_share_sd', 'mean_margin', 'close_race_fraction']

### agnes_cophenetic.csv
```
 linkage  cophenetic_corr
  single           0.7836
complete           0.7517
 average           0.8651
```
Linkage with highest cophenetic correlation: average. Reporting that one.

### agnes_lifetimes.csv
```
 K  merge_height_before  merge_height_after  lifetime
 2               2.9071              7.7031    4.7960
 3               2.6563              2.9071    0.2508
 4               2.6193              2.6563    0.0370
 5               2.1378              2.6193    0.4816
 6               1.8080              2.1378    0.3298
 7               1.6592              1.8080    0.1488
 8               1.4175              1.6592    0.2417
```
Chosen K (largest lifetime among K>=3; K=2 shown in table for reference): 5

### agnes_cluster_profiles.csv
```
         size  mean_dem_share  mean_margin  volatility  close_frac                                                                                                                                      states
cluster                                                                                                                                                                                                       
1           7           33.12        26.70        5.22        0.01                                                                                                                  AK, ID, ND, NE, OK, UT, WY
2          35           46.98        13.83        6.36        0.19  AL, AR, AZ, CA, CO, CT, DE, GA, HI, IA, IL, IN, KS, KY, LA, MA, MD, ME, MI, MS, MT, NH, NJ, NM, NY, OR, RI, SC, SD, TN, TX, VA, VT, WA, WV
3           7           47.06         6.83        4.16        0.50                                                                                                                  FL, MN, MO, NC, OH, PA, WI
4           1           43.74        10.84        8.26        0.58                                                                                                                                          NV
5           1           86.23        76.40        5.14        0.00                                                                                                                                          DC
```
import pandas as pd
import sys

input_file = sys.argv[1]
output_file = sys.argv[2]
year = sys.argv[3]


def quantile(df, col, n):
    df[col] = pd.qcut(df[col], n, labels=list(map(str, range(1,n+1))))


df = pd.read_csv(input_file)

quantile(df, "Avg24hPM2.5Exposure", 5)
quantile(df, "Max24hPM2.5Exposure", 5)
quantile(df, "Avg24hOzoneExposure", 5)
quantile(df, "Max24hOzoneExposure", 5)
quantile(df, "EstResidentialDensity", 5)
quantile(df, "EstResidentialDensity25Plus", 5)
quantile(df, "EstProbabilityNonHispWhite", 4)
quantile(df, "EstProbabilityHouseholdNonHispWhite", 4)
quantile(df, "EstProbabilityHighSchoolMaxEducation", 4)
quantile(df, "EstProbabilityNoAuto", 4)
quantile(df, "EstProbabilityNoHealthIns", 4)
quantile(df, "EstProbabilityESL", 4)
quantile(df, "EstHouseholdIncome", 5)
df["MajorRoadwayHighwayExposure"] = pd.cut(df["MajorRoadwayHighwayExposure"], [-1, 0, 50, 100, 200, 300, 500], labels=list(map(str, [6, 1, 2, 3, 4, 5])))
df["MepolizumabVisit"] = 0

df["year"] = year

df.to_csv(output_file, index=False)

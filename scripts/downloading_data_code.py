import requests as re
import os

parameters = [
    "T2M", "ALLSKY_SFC_SW_DWN", "WS2M", "RH2M", "T2M_MAX", "T2M_MIN", "WS50M", "WD50M", "WD2M",
    "CLOUD_AMT", "PRECTOTCORR", "GWETPROF", "TS", "QV2M", "GWETROOT", "GWETTOP", "WS50M_MAX",
    "WS50M_MIN", "ALLSKY_SFC_UVA", "ALLSKY_SFC_UVB", "ALLSKY_SFC_UV_INDEX", "MIDDAY_INSOL",
    "TS_MAX", "TS_MIN", "WS2M_MAX", "WS2M_MIN", "PW", "AIRMASS", "CLOUD_AMT_DAY",
    "CLOUD_AMT_NIGHT", "CLRSKY_DAYS", "EVLAND", "PSH", "PRECSNO",
    "RHOA", "TO3", "T10M", "T10M_MAX", "T10M_MIN", "TSOIL1", "TSOIL2", "TSOIL3", "TSOIL4",
    "TSOIL5", "TSOIL6", "Z0M"
]

region = {
    "large_region": [22, 32, 24.5, 34.5],
    "small_region": [22, 26, 34.5, 37]
}

for y in range(2019, 2024):
    for r_name, r in region.items():
        for param in parameters:
            url = f'https://power.larc.nasa.gov/api/temporal/daily/regional?start={y}0101&end={y}1231&latitude-min={r[0]}&latitude-max={r[1]}&longitude-min={r[2]}&longitude-max={r[3]}&community=ag&parameters={param}&format=csv&header=true&time-standard=utc'
            response = re.get(url)
            if response.status_code == 200:
                with open(f"D:/data/{r_name}/{y}/{param}.csv", "w") as file:
                    file.write(response.text)
                print('.', sep="")
            else:
                print(f"Error with D:/data/{r_name}/{y}/{param}.csv")
                print(response.status_code)

for r_name, r in region.items():
    for param in parameters:
        url = f'https://power.larc.nasa.gov/api/temporal/monthly/regional?start=1990&end=2023&latitude-min={r[0]}&latitude-max={r[1]}&longitude-min={r[2]}&longitude-max={r[3]}&community=ag&parameters={param}&format=csv&header=true&time-standard=utc'
        response = re.get(url)
        if response.status_code == 200:
            with open(f"D:/data/{r_name}/{param}.csv", "w") as file:
                file.write(response.text)
            print('.', sep="")
        else:
            print(f"Error with D:/data/{r_name}/{param}.csv")
            print(response.status_code)


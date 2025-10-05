import requests, pandas as pd, numpy as np

def om_hist_precip(lat, lon, y0=2000, y1=2024, tz="America/Mexico_City"):
    url = "https://archive-api.open-meteo.com/v1/archive"
    p = {"latitude":lat,"longitude":lon,"daily":"precipitation_sum",
         "start_date":f"{y0}-01-01","end_date":f"{y1}-12-31","timezone":tz}
    r = requests.get(url, params=p, timeout=60); r.raise_for_status()
    j = r.json().get("daily", {})
    df = pd.DataFrame(j); df["time"]=pd.to_datetime(df["time"])
    df["mm"]=df["precipitation_sum"].astype(float)
    return df[["time","mm"]]

def prob_lluvia(lat, lon, fecha, y0=2000, y1=2024, k=5, umbral=1.0, tz="America/Mexico_City"):
    df = om_hist_precip(lat, lon, y0, y1, tz)
    t = pd.Timestamp(fecha); m, d = t.month, t.day
    s = df.loc[(df.time.dt.month==m)&(abs(df.time.dt.day-d)<=k),"mm"].dropna()
    if s.empty: return {"n":0,"p_lluvia":None,"msg":"sin datos"}
    return {
        "n": int(s.size),
        "ventana_dias": 2*k+1,
        "p_lluvia": float((s>=umbral).mean()),
        "p50_mm": float(np.percentile(s,50)),
        "p90_mm": float(np.percentile(s,90)),
        "mediana_si_llueve_mm": float(s[s>=umbral].median()) if (s>=umbral).any() else 0.0
    }

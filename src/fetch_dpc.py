import xarray as xr
import requests

def fetch_dpc(lat, lon):
    url = "https://dati.protezionecivile.gov.it/radar/SRI/latest.nc"
    r = requests.get(url)
    with open("latest.nc", "wb") as f:
        f.write(r.content)
    ds = xr.open_dataset("latest.nc")
    sri = ds.sel(latitude=lat, longitude=lon, method="nearest")["SRI"].values.item()
    return sri

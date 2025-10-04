from fastapi import APIRouter

router = APIRouter(tags=["metadata"])

@router.get("/factors")
def list_factors():
    return [
        {"factor":"temperature","units":"°C","dataset":"ERA5-Land"},
        {"factor":"precipitation","units":"mm/day","dataset":"IMERG"},
        {"factor":"windspeed","units":"m/s","dataset":"ERA5"},
        {"factor":"dust","units":"µg/m³","dataset":"MERRA-2"}
    ]

@router.get("/metadata/datasets")
def datasets():
    return {
        "ERA5-Land":{"period":"1981-2024","spatial_res":"~0.1°"},
        "IMERG":{"period":"2000-2024","spatial_res":"0.1°"},
        "MERRA-2":{"period":"1980-2024","spatial_res":"~0.5°"}
    }

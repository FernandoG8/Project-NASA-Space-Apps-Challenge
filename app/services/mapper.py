FACTOR_TO_POWER_VARS = {
    "temperature":   ["T2M"],
    "precipitation": ["PRECTOTCORR"],
    "windspeed":     ["WS10M"],
    "humidity":      ["RH2M"],
    # "comfort": depende de T2M y RH2M (lo añade el servicio)
}

FACTOR_UNITS = {
    "temperature": "°C",
    "precipitation": "mm/day",
    "windspeed": "m/s",
    "humidity": "%",
    "comfort": "°C (HI)",
}

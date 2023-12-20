from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/historic_timeseries/{region}")
def get_historic_timeseries(region: str):
    return {"region": region}

@app.get("/forecast_timeseries/{region}")
def get_forecast_timeseries(region: str):
    return {"region": region}

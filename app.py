from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Use env vars if set (Kubernetes), else fallback to localhost (local dev)
specialty_predictor_url = os.getenv("SPECIALITY_URL", "http://speciality:8080/predict")
doctor_recommendation_url = os.getenv("BANDIT_URL", "http://bandit:8000/recommend/")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process", response_class=HTMLResponse)
async def process(request: Request, symptoms: str = Form(...)):
    try:
        response = requests.post(
            specialty_predictor_url,
            json={"symptoms": symptoms},
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        response.raise_for_status()
        specialty_data = response.json()
        specialties = [spec["speciality"] for spec in specialty_data["top_specialists"]]

        doctor_response = requests.post(
            doctor_recommendation_url,
            json={"specialists": specialties},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        doctor_response.raise_for_status()
        doctor_data = doctor_response.json()["recommendations"]

        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "symptoms": symptoms,
                "specialties": specialties,
                "recommendations": doctor_data,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(e)},
        )

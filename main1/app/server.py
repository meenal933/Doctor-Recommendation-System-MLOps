from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import uvicorn
from fastapi.responses import RedirectResponse
from bandit_experience import MultiArmedBanditExperience
from fastapi.responses import FileResponse
import os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all HTTP headers
)


model_path = './app/bandit.joblib'
bandit_with_experience = joblib.load(model_path)


@app.get("/frontend", include_in_schema=False)
def serve_frontend():
    return FileResponse(os.path.join("app", "static", "index.html"))


# Define input schema for API requests
class DoctorRequest(BaseModel):
    specialists: list[str]

class CompositeScoreRequest(BaseModel):
    ratings_weight: float
    experience_weight: float

@app.get("/")
def root():
    return RedirectResponse(url="/frontend")
    # return {"message": "Welcome to the Doctor Recommendation System API"}

@app.post("/recommend/")
def recommend_doctors(request: DoctorRequest):
    """
    Recommend top doctors for the given specialties.
    """
    specialists = request.specialists
    if not specialists:
        raise HTTPException(status_code=400, detail="Specialists list cannot be empty.")
    
    results = bandit_with_experience.recommend_doctor(specialists)

    # Format the response
    response = {}
    for specialist, doctors in results.items():
        if isinstance(doctors, list):
            response[specialist] = [
                {"name": doctor[0], "rating": doctor[1], "experience": doctor[2]} for doctor in doctors
            ]
        else:
            response[specialist] = doctors  # Message for no doctors

    return {"recommendations": response}

@app.post("/update_weights/")
def update_composite_weights(request: CompositeScoreRequest):
    """
    Update composite score weights for ratings and experience.
    """
    try:
        ratings_weight = request.ratings_weight
        experience_weight = request.experience_weight

        # Validate weights
        if ratings_weight + experience_weight != 1:
            raise ValueError("Ratings weight and experience weight must sum up to 1.")

        # Update weights in the model
        bandit_with_experience.ratings_weight = ratings_weight
        bandit_with_experience.experience_weight = experience_weight

        # Recompute composite scores
        bandit_with_experience.data['Composite Score'] = (
            bandit_with_experience.data['Normalized Ratings'] * ratings_weight +
            bandit_with_experience.data['Normalized Experience'] * experience_weight
        )

        return {"message": "Weights updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app , host="0.0.0.0", port=8000)

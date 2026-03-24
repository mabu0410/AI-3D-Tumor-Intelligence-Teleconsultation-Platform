from fastapi import APIRouter

from app.api.v1.endpoints import (
    cases,
    patients,
    auth,
    segmentation,
    reconstruction,
    features,
    classification,
    prediction,
    telemedicine,
    scheduling,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(cases.router, prefix="/cases", tags=["Cases"])

# Module 1
api_router.include_router(segmentation.router, prefix="/segmentation", tags=["Module 1: Segmentation"])

# Module 2
api_router.include_router(reconstruction.router, prefix="/reconstruction", tags=["Module 2: Reconstruction"])

# Module 3
api_router.include_router(features.router, prefix="/features", tags=["Module 3: Features"])

# Module 4
api_router.include_router(classification.router, prefix="/classification", tags=["Module 4: Classification"])

# Module 5
api_router.include_router(prediction.router, prefix="/prediction", tags=["Module 5: Prediction"])

# Module 6
api_router.include_router(telemedicine.router, prefix="/telemedicine", tags=["Module 6: Telemedicine"])

# Module 7
api_router.include_router(scheduling.router, prefix="/scheduling", tags=["Module 7: Scheduling"])

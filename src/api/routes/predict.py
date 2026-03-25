from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class PropertyFeatures(BaseModel):
    city: str
    property_type: str
    surface_area: float
    rooms: int
    condition: str = "Bon état"

@router.post("/simulate")
def simulate_price(features: PropertyFeatures):
    # Dynamic base price per square meter depending on the city
    base_price_sqm = 3480
    if features.city == "Paris, 75000":
        base_price_sqm = 10500
    elif features.city == "Lyon, 69000":
        base_price_sqm = 5200
    elif features.city == "Bordeaux, 33000":
        base_price_sqm = 4600
    elif features.city == "Nantes, 44000":
        base_price_sqm = 3500
        
    # Condition multiplier
    cond_mult = 1.0
    if features.condition == "Neuf":
        cond_mult = 1.15
    elif features.condition == "À rénover":
        cond_mult = 0.85
        
    # Property type multiplier
    if features.property_type == "Maison":
        cond_mult *= 1.2

    estimated_price = features.surface_area * base_price_sqm * cond_mult

    
    return {
        "current_estimated_price": estimated_price,
        "confidence": 87,
        "price_per_sqm": int(estimated_price / features.surface_area),
        "projection_temporelle": [
            {"period": "6 mois", "price": estimated_price * 1.023, "pct": "+2.3%"},
            {"period": "1 an", "price": estimated_price * 1.048, "pct": "+4.8%"},
            {"period": "3 ans", "price": estimated_price * 1.155, "pct": "+15.5%"},
            {"period": "5 ans", "price": estimated_price * 1.265, "pct": "+26.5%"},
        ],
        "chart_data": [
            { "period": "Auj.", "price": estimated_price },
            { "period": "6m", "price": estimated_price * 1.023 },
            { "period": "1 an", "price": estimated_price * 1.048 },
            { "period": "3 ans", "price": estimated_price * 1.155 },
            { "period": "5 ans", "price": estimated_price * 1.265 },
        ]
    }

import pandas as pd
import numpy as np
from backend.database import SessionLocal
from backend.models.db_models import VideoAnalysisResult

def main():
    db = SessionLocal()
    results = db.query(VideoAnalysisResult).all()
    db.close()
    
    data = []
    for r in results:
        data.append({
            'expression_score': r.expression_score,
            'acoustic_score': r.acoustic_score,
            'collaboration_score': r.collaboration_score,
            'risk_taking_score': r.risk_taking_score,
        })
        
    df = pd.DataFrame(data).dropna()
    print("Korelasi JOYFUL:")
    print(df.corr())

if __name__ == "__main__":
    main()

"""
Model Cache Manager
Keeps models in memory to avoid reloading on every prediction
"""
import torch
from typing import Optional, Dict
from pathlib import Path

class ModelCache:
    """Singleton cache for ML models"""
    _instance = None
    _models: Dict[str, any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_cnn_model(self, model_path: Optional[str] = None):
        """Get cached CNN model or load if not cached"""
        cache_key = f"cnn_{model_path or 'default'}"
        
        if cache_key in self._models:
            print(f"✅ Using cached CNN model: {cache_key}")
            return self._models[cache_key]
        
        print(f"📥 Loading CNN model: {model_path or 'default'}")
        from backend.ai.video.cnn_pipeline import build_model
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = build_model(num_classes=2)
        
        if model_path and Path(model_path).exists():
            state = torch.load(model_path, map_location=device)
            model.load_state_dict(state)
        
        model.to(device)
        model.eval()
        
        self._models[cache_key] = model
        print(f"✅ CNN model cached: {cache_key}")
        return model
    
    def clear_cache(self):
        """Clear all cached models"""
        print(f"🗑️ Clearing model cache ({len(self._models)} models)")
        self._models.clear()
    
    def get_cache_info(self):
        """Get information about cached models"""
        return {
            "cached_models": list(self._models.keys()),
            "count": len(self._models),
            "device": str(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        }


# Global cache instance
model_cache = ModelCache()

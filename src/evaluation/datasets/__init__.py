"""
Test datasets for evaluation framework.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

DATASETS_DIR = Path(__file__).parent


def load_dataset(name: str) -> Dict[str, Any]:
    """
    Load a dataset by name.
    
    Args:
        name: Dataset name (without .json extension)
        
    Returns:
        Parsed JSON data
    """
    file_path = DATASETS_DIR / f"{name}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_datasets() -> List[str]:
    """List all available datasets."""
    return [f.stem for f in DATASETS_DIR.glob("*.json")]


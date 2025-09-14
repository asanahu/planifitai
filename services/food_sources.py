from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import requests
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class FoodHit(BaseModel):
    """Minimal search hit for a food item in a specific source."""

    source: str  # e.g., "fdc"
    source_id: str  # e.g., FDC fdcId
    name: str  # I18N: keep FDC name as-is in MVP


class FoodDetails(BaseModel):
    """Canonicalized food details per 100 g with audit payload."""

    source: str  # e.g., "fdc"
    source_id: str
    name: str
    # canonical per 100 g
    calories_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    # full API payload for audit/debug
    raw_payload: Dict[str, Any]


@runtime_checkable
class FoodSourceAdapter(Protocol):
    """Interface all food source adapters must implement."""

    def search(self, query: str, page: int = 1, page_size: int = 10) -> List[FoodHit]:
        ...

    def get_details(self, source_id: str) -> FoodDetails:
        ...


class UnsupportedFoodSourceError(RuntimeError):
    pass


class FdcAdapter:
    """
    USDA FoodData Central adapter.

    MVP behavior:
    - Search foods by name.
    - Fetch details and map core macros per 100 g.
    - Keep the original payload in raw_payload for audit.
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"

    # FDC nutrient numbers -> canonical
    NUTRIENT_MAP = {
        208: ("calories_kcal", "KCAL"),  # Energy (kcal)
        203: ("protein_g", "G"),  # Protein
        205: ("carbs_g", "G"),  # Carbohydrate, by difference
        204: ("fat_g", "G"),  # Total lipid (fat)
    }

    def __init__(
        self,
        api_key: str,
        session: Optional[requests.Session] = None,
        *,
        timeout: float = 2.5,
        retries: int = 1,
    ):
        if not api_key:
            raise ValueError("FDC_API_KEY is required for FdcAdapter")
        self.api_key = api_key
        self.timeout = timeout
        if session is not None:
            self.session = session
        else:
            s = requests.Session()
            retry = Retry(
                total=retries,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"],
                backoff_factor=0.3,
            )
            adapter = HTTPAdapter(max_retries=retry)
            s.mount("http://", adapter)
            s.mount("https://", adapter)
            self.session = s

    def search(self, query: str, page: int = 1, page_size: int = 10) -> List[FoodHit]:
        """Search foods by name.

        Uses POST /foods/search. Keeps MVP simple with query, page, page_size.
        """
        url = f"{self.BASE_URL}/foods/search?api_key={self.api_key}"
        payload = {
            "query": query,
            "pageNumber": page,
            "pageSize": page_size,
        }
        resp = self.session.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        foods = data.get("foods", [])
        hits: List[FoodHit] = []
        for f in foods:
            hits.append(
                FoodHit(
                    source="fdc",
                    source_id=str(f.get("fdcId")),
                    name=f.get("description") or f.get("description", ""),
                )
            )
        return hits

    def get_details(self, source_id: str) -> FoodDetails:
        """Fetch details and map macros per 100 g, keeping raw payload."""
        url = f"{self.BASE_URL}/food/{source_id}?api_key={self.api_key}"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()

        name = payload.get("description") or ""

        # Try to map macros from detailed nutrients (preferred for foundation/srLegacy)
        macros: Dict[str, float] = {}
        for fn in payload.get("foodNutrients", []) or []:
            nutrient = fn.get("nutrient") or {}
            number = nutrient.get("number")
            try:
                number = int(number) if number is not None else None
            except Exception:
                number = None
            if number in self.NUTRIENT_MAP and fn.get("amount") is not None:
                key, expected_unit = self.NUTRIENT_MAP[number]
                # Assume units are correct for MVP; real-world could validate unitName
                macros[key] = float(fn.get("amount"))

        # If branded with labelNutrients + servingSize in grams, scale to 100 g
        serving_size = payload.get("servingSize")
        serving_unit = (payload.get("servingSizeUnit") or "").lower()
        label = payload.get("labelNutrients") or {}
        if serving_size and serving_unit in {"g", "gram", "grams"} and label:
            scale = 100.0 / float(serving_size)
            # label keys typically: calories, protein, carbohydrate, fat
            if "calories" in label and "calories_kcal" not in macros:
                val = label["calories"].get("value")
                if val is not None:
                    macros["calories_kcal"] = float(val) * scale
            if "protein" in label and "protein_g" not in macros:
                val = label["protein"].get("value")
                if val is not None:
                    macros["protein_g"] = float(val) * scale
            # FDC uses 'carbohydrates' in labelNutrients (plural); accept both just in case
            if "carbohydrates" in label and "carbs_g" not in macros:
                val = label["carbohydrates"].get("value")
                if val is not None:
                    macros["carbs_g"] = float(val) * scale
            elif "carbohydrate" in label and "carbs_g" not in macros:
                val = label["carbohydrate"].get("value")
                if val is not None:
                    macros["carbs_g"] = float(val) * scale
            if "fat" in label and "fat_g" not in macros:
                val = label["fat"].get("value")
                if val is not None:
                    macros["fat_g"] = float(val) * scale

        return FoodDetails(
            source="fdc",
            source_id=str(source_id),
            name=name,
            calories_kcal=macros.get("calories_kcal"),
            protein_g=macros.get("protein_g"),
            carbs_g=macros.get("carbs_g"),
            fat_g=macros.get("fat_g"),
            raw_payload=payload,
        )


class OpenFoodFactsAdapter:
    """
    Open Food Facts adapter.
    
    Provides access to the collaborative food database with global coverage
    and support for multiple languages including Spanish.
    """

    BASE_URL = "https://world.openfoodfacts.org"

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        *,
        timeout: float = 2.0,
        retries: int = 1,
    ):
        self.timeout = timeout
        if session is not None:
            self.session = session
        else:
            s = requests.Session()
            retry = Retry(
                total=retries,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
                backoff_factor=0.5,
            )
            adapter = HTTPAdapter(max_retries=retry)
            s.mount("http://", adapter)
            s.mount("https://", adapter)
            self.session = s

    def search(self, query: str, page: int = 1, page_size: int = 10) -> List[FoodHit]:
        """Search foods by name using Open Food Facts API."""
        url = f"{self.BASE_URL}/cgi/search.pl"
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": min(page_size, 24),  # OFF max is 24
            "page": page,
        }
        
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        
        products = data.get("products", [])
        hits: List[FoodHit] = []
        
        for product in products:
            # Use barcode as source_id, fallback to _id
            source_id = product.get("code") or product.get("_id", "")
            name = product.get("product_name") or product.get("product_name_en", "")
            
            if source_id and name:
                hits.append(
                    FoodHit(
                        source="openfoodfacts",
                        source_id=str(source_id),
                        name=name,
                    )
                )
        
        return hits

    def get_details(self, source_id: str) -> FoodDetails:
        """Fetch product details from Open Food Facts."""
        url = f"{self.BASE_URL}/api/v0/product/{source_id}.json"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        
        product = data.get("product", {})
        if not product:
            raise requests.exceptions.HTTPError(f"Product {source_id} not found")
        
        name = product.get("product_name") or product.get("product_name_en", "")
        
        # Extract nutritional information per 100g
        nutriments = product.get("nutriments", {})
        
        # Map Open Food Facts nutrients to our canonical format
        calories_kcal = None
        protein_g = None
        carbs_g = None
        fat_g = None
        
        # Energy (prefer kcal, fallback to kJ conversion)
        if "energy-kcal_100g" in nutriments:
            calories_kcal = float(nutriments["energy-kcal_100g"])
        elif "energy_100g" in nutriments:
            # Convert kJ to kcal (1 kcal = 4.184 kJ)
            calories_kcal = float(nutriments["energy_100g"]) / 4.184
        
        # Macronutrients
        if "proteins_100g" in nutriments:
            protein_g = float(nutriments["proteins_100g"])
        
        if "carbohydrates_100g" in nutriments:
            carbs_g = float(nutriments["carbohydrates_100g"])
        
        if "fat_100g" in nutriments:
            fat_g = float(nutriments["fat_100g"])
        
        return FoodDetails(
            source="openfoodfacts",
            source_id=str(source_id),
            name=name,
            calories_kcal=calories_kcal,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            raw_payload=product,
        )


class BedcaAdapter:
    """
    BEDCA adapter placeholder.

    Intentionally not implemented in MVP; keeps interface parity with FDC.
    """

    def search(self, query: str, page: int = 1, page_size: int = 10) -> List[FoodHit]:
        raise NotImplementedError("BedcaAdapter is not implemented yet")

    def get_details(self, source_id: str) -> FoodDetails:
        raise NotImplementedError("BedcaAdapter is not implemented yet")


def get_food_source_adapter() -> FoodSourceAdapter:
    """Resolve the active adapter using app settings.

    Supports both FDC and Open Food Facts sources.
    """
    # Lazy import to avoid circulars
    from app.core.config import settings

    source = (settings.FOOD_SOURCE or "openfoodfacts").lower()
    
    if source == "openfoodfacts":
        return OpenFoodFactsAdapter()
    elif source == "fdc":
        if not settings.FDC_API_KEY:
            raise ValueError("FDC_API_KEY is required when FOOD_SOURCE=fdc")
        return FdcAdapter(api_key=settings.FDC_API_KEY)
    else:
        raise UnsupportedFoodSourceError(f"Unsupported FOOD_SOURCE: {settings.FOOD_SOURCE}. Supported: openfoodfacts, fdc")

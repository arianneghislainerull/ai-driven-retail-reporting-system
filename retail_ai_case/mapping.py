import json
from dataclasses import dataclass
from typing import Dict, Optional, List

@dataclass
class Mapping:
    date: Optional[str] = None
    year: Optional[str] = None
    month: Optional[str] = None
    quarter: Optional[str] = None

    units: Optional[str] = None
    price: Optional[str] = None
    cost: Optional[str] = None

    region: Optional[str] = None
    store: Optional[str] = None
    store_size: Optional[str] = None

    product_id: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    division: Optional[str] = None
    brand: Optional[str] = None

    def as_dict(self) -> Dict[str, Optional[str]]:
        return self.__dict__.copy()

def find_col(df_cols: List[str], candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df_cols:
            return c
    return None

def auto_map(df_cols: List[str]) -> Mapping:
    # Adjusted to your dataset columns
    return Mapping(
        date=find_col(df_cols, ["date"]),
        year=find_col(df_cols, ["year"]),
        month=find_col(df_cols, ["month"]),
        quarter=find_col(df_cols, ["quarter", "qtr"]),

        units=find_col(df_cols, ["units_sold", "units", "qty", "quantity"]),
        price=find_col(df_cols, ["selling_price_per_unit", "selling_price", "unit_price", "price"]),
        cost=find_col(df_cols, ["cost_per_unit", "cost", "unit_cost"]),

        region=find_col(df_cols, ["region"]),
        store=find_col(df_cols, ["store_id", "store", "store_name"]),
        store_size=find_col(df_cols, ["store_size"]),

        product_id=find_col(df_cols, ["product_id", "sku", "item_id"]),
        product_name=find_col(df_cols, ["product_name", "product"]),
        category=find_col(df_cols, ["product_category", "category"]),
        division=find_col(df_cols, ["product_division", "division"]),
        brand=find_col(df_cols, ["brand"]),
    )

def validate_mapping(m: Mapping):
    req = ["units", "price", "cost"]
    missing = [k for k in req if getattr(m, k) is None]
    if missing:
        raise ValueError(f"Missing required mapping fields: {missing}")

def pretty_print_mapping(m: Mapping):
    print("Auto-mapped fields:")
    print(json.dumps(m.as_dict(), indent=2))
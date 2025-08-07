from pydantic import BaseModel, Field,validator
from typing import List, Optional, Literal
   
class MagentoAPIBase(BaseModel):
    store_view_code: Optional[str] = "default"
    api_version: Optional[str] = "v1"


class ViewProductInput(MagentoAPIBase):
    sku: str 

class CreateProductInput(BaseModel):
    sku: str
    name: str
    price: float
    status: int  # 1 = Enabled, 2 = Disabled
    type_id: str = "simple"
    attribute_set_id: int = 4  # Default attribute set
    weight: Optional[float] = 1.0
    visibility: int = 4  # 4 = Catalog, Search
    qty: Optional[float] = 0
    is_in_stock: Optional[bool] = True

class UpdateProductInput(BaseModel):
    sku: str
    name: Optional[str] = None
    price: Optional[float] = None
    status: Optional[int] = None  # 1 = Enabled, 2 = Disabled
    visibility: Optional[int] = None  # 1 = Not visible, 2 = Catalog, 3 = Search, 4 = Catalog/Search
    weight: Optional[float] = None
    qty: Optional[float] = None
    is_in_stock: Optional[bool] = None

class SearchProductsInput(BaseModel):
    query: Optional[str] = Field(description="Search query for products")
    category_id: Optional[int] = Field(default=None, description="Filter by category")
    min_price: Optional[float] = Field(default=None, description="Minimum price filter")
    max_price: Optional[float] = Field(default=None, description="Maximum price filter")
    sort_by: Optional[str] = Field(default="relevance", description="Sort by: relevance, price_asc, price_desc, rating, newest")
    limit: Optional[int] = Field(default=10, description="Maximum number of results")

class DeleteProductInput(BaseModel):
    sku: str

class TopSellingProductsInput(BaseModel):
    limit: int = Field(10, description="Number of top-selling products to return")
    last_n_days: Optional[int] = Field(7, description="Number of days to look back for sales data (optional)")
    rank_by: Optional[Literal["quantity", "revenue"]] = Field(
        default="quantity",
        description="Rank products by 'quantity' sold or 'revenue' generated."
    )

class ProductDescription(BaseModel):
    short_description: str
    description: str

class LinkedProductsInput(BaseModel):
    sku: str = Field(..., description="SKU of the product.")
   

class LinkedProductsOutput(BaseModel):
    linked_skus: list[str] = Field(..., description="List of SKUs to link to the given SKU.")
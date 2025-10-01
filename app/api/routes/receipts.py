import mimetypes
import base64
import json
from typing import List
from fastapi import APIRouter, File, UploadFile, status, Depends
from openai import OpenAI

from app.core.settings import settings
from app.schemas.receipt import ReceiptAnalysisResponse, ErrorResponse
from app.core.logging import receipt_logger
from app.core.log_utils import log_openai_request
from app.core.rate_limiter import receipt_rate_limit
from app.core.exceptions import FileProcessingException

router = APIRouter(prefix="/receipts", tags=["Receipts"])

client = OpenAI(
    api_key=settings.OPEN_AI_SECRET_KEY,
)

MAX_FILE_SIZE = 1024 * 1024 * 10  # 10 MB
ALLOWED_FILE_TYPES = ["image/png", "image/jpeg", "image/jpg"]

SYSTEM_PROMPT = """
You are an expert agent specialized in receipt and payment voucher analysis.
Your task is to read receipt text and return structured information in JSON format.

CRITICAL FORMATTING REQUIREMENTS:
- Date MUST be in YYYY-MM-DD format (e.g., "2024-01-15", NOT "01/15/2024" or "Jan 15, 2024")
- Convert any date format to YYYY-MM-DD
- If date is ambiguous, use the most recent logical date

CURRENCY EXTRACTION:
- ALWAYS include a currency field in the response
- Extract the currency code (e.g., "USD", "EUR", "COP", "GBP", "PEN", etc.) from symbols or explicit mentions
- Common currency symbols: $ = USD, € = EUR, £ = GBP, etc.
- If no currency symbol is visible, use "USD" as default
- Currency field should be the 3-letter code (ISO 4217 format)

CATEGORIZATION RULES:
- Grocery stores (Walmart, Target, Kroger, Safeway, Whole Foods, Trader Joe's, Costco, Sam's Club, Aldi, Publix, Wegmans, Éxito, Carulla, Jumbo): "groceries"
- Restaurants/Fast food (McDonald's, Starbucks, Chipotle, Taco Bell, Subway, KFC, etc.): "dining"
- Gas stations (Shell, Exxon, Chevron, BP, Speedway, Terpel, Petrobras, etc.): "gas"
- Pharmacies (CVS, Walgreens, Rite Aid, Cruz Verde, Copidrogas, etc.): "healthcare"
- Department stores (Macy's, Kohl's, JCPenney, Falabella, Liverpool, etc.): "shopping"
- Electronics (Best Buy, Apple Store, Ktronix, etc.): "electronics"
- Home improvement (Home Depot, Lowe's, Homecenter, etc.): "home"
- Clothing (Gap, Old Navy, H&M, Zara, Arturo Calle, etc.): "clothing"
- Online services (Amazon, eBay, MercadoLibre, etc.): "shopping"
- Utilities (electric, gas, water, internet): "utilities"
- Entertainment (movies, concerts, etc.): "entertainment"
- Travel (hotels, airlines, etc.): "travel"
- Education (schools, universities, courses): "education"
- Public transportation (metro, bus, taxi, Uber): "transportation"
- Other: Use your best judgment to categorize appropriately

PAYMENT METHODS:
Common values include "cash", "credit card", "debit card", "bank transfer", "check", "gift card", "digital wallet", "PSE", "Nequi", "Daviplata"

FIELDS TO EXTRACT:

merchant: Name of the store, company, or issuing entity.
date: Issue date (ISO format: YYYY-MM-DD).
total_amount: Total amount paid (as number, without symbols).
currency: Currency in standard ISO format (e.g., "USD", "COP", "EUR", "PEN").
payment_method: Payment method according to the options listed above.
category: Expense category according to categorization rules.
description: Brief summary of the receipt or service/product purchased (respond in the same language detected in the receipt/image).
receipt_number: Receipt or invoice number (if present).
taxes: Total tax or VAT amount (if present, as number).
items: List of purchased products or services with:
  - name: item name or description (in the same language detected in the receipt/image)
  - quantity: quantity (if present, otherwise null)
  - unit_price: unit price (if present, otherwise null)
  - total_price: calculated subtotal per item (if present, otherwise null)

ADDITIONAL INSTRUCTIONS:
- If any field doesn't appear on the receipt, return it with null value
- DO NOT invent values: if information doesn't exist, mark it as null
- Extract all visible receipt information accurately
- If information is not visible, use reasonable defaults or omit if not applicable
- ALWAYS return valid and well-formatted JSON
- Respond ONLY with valid JSON, no additional text
- LANGUAGE DETECTION: Detect the language used in the receipt/image and respond with description and item names in that same language

EXAMPLE:
{
  "merchant": "La Esperanza Supermarket",
  "date": "2025-09-20",
  "total_amount": 152000,
  "currency": "COP",
  "payment_method": "debit card",
  "category": "groceries",
  "description": "Purchase of groceries and household products",
  "receipt_number": "FAC-908123",
  "taxes": 19000,
  "items": [
    {
      "name": "Rice 5kg",
      "quantity": 1,
      "unit_price": 25000,
      "total_price": 25000
    },
    {
      "name": "Oil 1L",
      "quantity": 2,
      "unit_price": 15000,
      "total_price": 30000
    },
    {
      "name": "Detergent 2kg",
      "quantity": 1,
      "unit_price": 20000,
      "total_price": 20000
    }
  ]
}
"""


@log_openai_request(settings.OPEN_AI_MODEL)
async def call_openai_for_receipt_analysis(base64_image: str, filename: str):
    """
    Call OpenAI API to analyze receipt image and extract structured data.

    Args:
        base64_image: Base64 encoded image data
        filename: Original filename for logging purposes

    Returns:
        OpenAI completion response

    Raises:
        Exception: If OpenAI API call fails
    """
    return client.chat.completions.create(
        model=settings.OPEN_AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract receipt data from this image following the formatting and categorization rules.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            },
        ],
        response_format={
            "type": "json_object",
        },
    )


@router.post(
    "/",
    response_model=ReceiptAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze receipt image",
    description="Upload a receipt image and extract structured data using AI analysis.",
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Bad request - invalid file or format",
        },
        413: {"model": ErrorResponse, "description": "File too large"},
        422: {
            "model": ErrorResponse,
            "description": "Unprocessable entity - unsupported file type",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error - AI analysis failed",
        },
    },
)
async def analyze_receipt(
    receipt: UploadFile = File(
        ...,
        description="Receipt image file (PNG, JPEG, or JPG format, max 10MB)",
        media_type="image/*",
    ),
    _: None = Depends(receipt_rate_limit),
) -> ReceiptAnalysisResponse:
    """
    Upload and analyze a receipt image to extract structured financial data.

    This endpoint uses AI to process receipt images and extract key information including:
    - Merchant name and transaction details
    - Date, amount, and currency
    - Payment method and category classification
    - Individual items with prices (when available)
    - Tax information

    **Supported formats:** PNG, JPEG, JPG
    **Maximum file size:** 10MB
    **Languages:** Auto-detected (English, Spanish, French, Portuguese, etc.)

    **Categories include:**
    - groceries, dining, gas, healthcare, shopping
    - electronics, home, clothing, utilities, entertainment
    - travel, education, transportation

    **Returns structured data** that can be used to create transactions automatically.
    """
    if not receipt.filename or receipt.filename == "":
        receipt_logger.error("receipt_analysis_failed", error="No file provided")
        raise FileProcessingException(
            message="No file provided",
            filename=None,
            error_type="MISSING_FILE"
        )

    file_type, _ = mimetypes.guess_type(receipt.filename)
    if not file_type or file_type not in ALLOWED_FILE_TYPES:
        raise FileProcessingException(
            message=f"Invalid file type. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}",
            filename=receipt.filename,
            file_type=file_type,
            error_type="UNSUPPORTED_FORMAT",
            details={"supported_formats": ALLOWED_FILE_TYPES}
        )

    if receipt.size and receipt.size > MAX_FILE_SIZE:
        raise FileProcessingException(
            message=f"File too large. Maximum size allowed: {MAX_FILE_SIZE // (1024 * 1024)}MB",
            filename=receipt.filename,
            file_type=file_type,
            error_type="FILE_TOO_LARGE",
            details={
                "file_size": receipt.size,
                "max_size": MAX_FILE_SIZE,
                "max_size_mb": MAX_FILE_SIZE // (1024 * 1024)
            }
        )

    file_content = await receipt.read()
    base64_image = base64.b64encode(file_content).decode("utf-8")

    try:
        response = await call_openai_for_receipt_analysis(
            base64_image, receipt.filename
        )
    except Exception as e:
        raise FileProcessingException(
            message=f"AI analysis failed: {str(e)}",
            filename=receipt.filename,
            file_type=file_type,
            error_type="AI_PROCESSING_FAILED",
            details={"original_error": str(e)}
        )

    if not response.choices or not response.choices[0].message.content:
        receipt_logger.error(
            "receipt_analysis_failed",
            error="Empty AI response",
            filename=receipt.filename,
        )
        raise FileProcessingException(
            message="Could not extract receipt data from the provided image",
            filename=receipt.filename,
            file_type=file_type,
            error_type="EXTRACTION_FAILED",
            details={"reason": "Empty AI response"}
        )

    try:
        receipt_data = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        receipt_logger.error(
            "receipt_analysis_failed",
            error="Failed to parse AI response",
            filename=receipt.filename,
            parse_error=str(e),
        )
        raise FileProcessingException(
            message=f"Failed to parse AI response: {str(e)}",
            filename=receipt.filename,
            file_type=file_type,
            error_type="RESPONSE_PARSING_FAILED",
            details={"parse_error": str(e), "ai_response": response.choices[0].message.content[:200]}
        )

    return ReceiptAnalysisResponse(receipt=receipt_data)

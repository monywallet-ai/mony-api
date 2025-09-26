from fastapi import APIRouter, File, HTTPException, UploadFile, status
import mimetypes


router = APIRouter(tags=["Receipts"])
MAX_FILE_SIZE = 1024 * 1024 * 10  # 10 MB
ALLOWED_FILE_TYPES = ["image/png", "image/jpeg", "image/jpg"]


@router.post("/receipts")
async def upload_receipt(
    receipt: UploadFile = File(
        title="Receipt file",
        description="Receipt file",
    ),
):
    if not receipt.filename or receipt.filename == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    file_type, _ = mimetypes.guess_type(receipt.filename)
    if not file_type or file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type",
        )

    if receipt.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large",
        )

    return {
        "receipt": receipt,
    }

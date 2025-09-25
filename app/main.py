from typing import IO, Annotated
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

FILE_SIZE_LIMIT = 1024 * 1024 * 10  # 10 MB
ALLOWED_FILE_TYPES = ["image/png", "image/jpeg", "image/jpg"]


def validate_size(receipt: IO):

    pass


@app.post("/receipts")
def upload_receipt(
    receipt: Annotated[UploadFile, File(description="Receipt file")],
):

    return {
        "receipt": receipt,
    }

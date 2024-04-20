from typing import Annotated
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.post("/ingest")
async def create_upload_files(
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    filenames = [file.filename for file in files]
    return {"message": f"Successfully uploaded {', '.join(filenames)}"}

@app.get("/")
async def main():
    content = """
<body>
<form action="/ingest" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)
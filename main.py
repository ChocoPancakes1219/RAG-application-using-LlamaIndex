from typing import Annotated
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from IPython.display import Markdown, display
import os

os.environ["OPENAI_API_KEY"]= "API KEY"

app = FastAPI()

#Ensure the data directory exists
os.makedirs('data', exist_ok=True)


#Load data from data folder to llamaindex
documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)

#initialize query engine
query_engine= index.as_query_engine(streaming=True)

@app.post("/ingest")
async def ingest(
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    new_documents = []
    #Loop through files uploaded
    for file in files:
        out_file_path = os.path.join('data', file.filename)
        #Open a new file in write-binary mode in the 'data' folder
        with open(out_file_path, 'wb') as out_file:
            #Write the content of the uploaded file to the new file
            contents = await file.read()
            out_file.write(contents)
            #Reset file pointer of the UploadFile
            await file.seek(0)
        new_documents.append(out_file_path)

    # Update the index with new documents
    if new_documents:
        documents = SimpleDirectoryReader("data").load_data()
        index = VectorStoreIndex.from_documents(documents)
    
            
    filenames = [file.filename for file in files]
    return {"message": f"Successfully uploaded and saved {', '.join(filenames)}"}

@app.get("/query")
async def search_query(query: str ):
    #Retrieve response from the query engine
    response = query_engine.query(query)
    results = Markdown(f"<b>{response}</b>")
    return {"query": query, "results": results}


@app.get("/")
async def main():
    content = """
<body>
<form action="/ingest" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit" value="Upload Files">
</form>
<form action="/query" method="get">
<input name="query" type="text" placeholder="Enter your search query here...">
<input type="submit" value="Search">
</form>
</body>
    """
    return HTMLResponse(content=content)

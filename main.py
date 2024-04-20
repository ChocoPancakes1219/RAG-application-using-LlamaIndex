from typing import Annotated,List
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import StorageContext, load_index_from_storage
from IPython.display import Markdown, display
import os
from dotenv import load_dotenv

#os.environ["OPENAI_API_KEY"]= "your API Key"

#Get api from external file to avoid accidentally pushing api key
config_path = "C:\\Users\\User\\Documents\\openai_key.env"
load_dotenv(dotenv_path=config_path)
api_key = os.getenv('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"]= api_key

app = FastAPI()

#Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# check if storage already exists
PERSIST_DIR = "./storage"
if not os.path.exists(PERSIST_DIR):
    # load the documents from data folder and create the index
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)

    # store vectors and index in storage for future use
    index.storage_context.persist()
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    index = load_index_from_storage(storage_context)

#initialize query engine
query_engine= index.as_query_engine(streaming=True)

# Function to filter out all non txt files
def filter_file_format(files: List[UploadFile]) -> List[UploadFile]:
    filtered_files = [file for file in files if file.filename.endswith('.txt')]
    removed_files = [file for file in files if not file.filename.endswith('.txt')]
    removed_documents=[]
    for removed_file in removed_files:
        removed_documents.append(removed_file.filename)

    return removed_documents,filtered_files

@app.post("/ingest")
async def ingest(
    files: Annotated[
        List[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    removed_documents,files=filter_file_format(files)
    new_documents = []
    #Loop through files uploaded
    for file in files:
        out_file_path = os.path.join('data', file.filename)
        try:
            with open(out_file_path, 'wb') as out_file:
                while True:
                  #Read in chunks of 1MB
                    chunk = await file.read(1024*1024)
                    if not chunk:
                        break
                    out_file.write(chunk)
            new_documents.append(out_file_path)
            # Insert the document into the index

            new_documents.append(out_file_path)
        except Exception as e:
            if file.filename== '':
              return JSONResponse(status_code=400, content={"message": "No files detected. Please upload at least one file."})
            else:
              return JSONResponse(status_code=500, content={"message": f"Failed to process file {file.filename}: {str(e)}"})



    # Update the index with new documents, reload query engine
    if new_documents:
        documents = SimpleDirectoryReader("data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist()
        query_engine= index.as_query_engine(streaming=True)
    
            
    filenames = [file.filename for file in files]
    return {"message": f"Removed from uploads (Non-txt format):<br>- {'<br>- '.join([os.path.basename(doc) for doc in removed_documents])}<br><br>Successfully uploaded and saved:<br>- {'<br>- '.join([os.path.basename(doc) for doc in new_documents])}<br><br>"}

@app.get("/query")
def search_query(query: str ):
    #Retrieve response from the query engine
    response = query_engine.query(query)
    results = Markdown(f"<b>{response}</b>")
    return {"query": query, "results": results.data}


@app.get("/")
async def main():
    content = """
<body>
<div id="chat-interface">
  <form id="upload-form" enctype="multipart/form-data" method="post">
    <input name="files" type="file" multiple>
    <button type="submit">Upload Files</button>
  </form>
  <div id="upload-response"></div>
  <form id="search-form" method="get">
    <input name="query" type="text" placeholder="Enter your search query here...">
    <button type="submit">Search</button>
  </form>
  <div id="results-container"></div>
</div>
<script>
document.getElementById('upload-form').onsubmit = async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const response = await fetch('/ingest', {
    method: 'POST',
    body: formData,
  });
  const data = await response.json();
  document.getElementById('upload-response').innerHTML = `<div>${data.message}</div>`;
};

document.getElementById('search-form').onsubmit = async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const query = formData.get('query');
  const response = await fetch(`/query?query=${encodeURIComponent(query)}`);
  const data = await response.json();
  document.getElementById('results-container').innerHTML = `<div>${data.results}</div>`;
};
</script>
</body>
    """
    return HTMLResponse(content=content)

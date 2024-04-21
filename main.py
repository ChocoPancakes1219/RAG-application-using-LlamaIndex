from typing import Annotated,List
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader,StorageContext, load_index_from_storage
from IPython.display import Markdown
from dotenv import load_dotenv
import os

#os.environ["OPENAI_API_KEY"]= "your API Key"

#Get api from external file to avoid accidentally pushing api key
#Comment out this part of the code if you wish to input your API key directly in python, else replace the path to your api key env
config_path = "./openai_key.env"
load_dotenv(dotenv_path=config_path)
api_key = os.getenv('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"]= api_key



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
query_engine = index.as_query_engine(response_mode="tree_summarize")

#define function to update query engine from api calls to ensure real-time update
def update_query_engine(index):
    global query_engine
    query_engine = index.as_query_engine()


app = FastAPI()

# Function to filter out all non txt files
def filter_file_format(files: List[UploadFile]) -> List[UploadFile]:
    filtered_files = [file for file in files if file.filename.endswith('.txt')]

    #Record removed files for response
    removed_files = [file for file in files if not file.filename.endswith('.txt')]
    removed_documents=[]
    for removed_file in removed_files:
        removed_documents.append(removed_file.filename)

    return removed_documents,filtered_files

#Ingest API Definition
@app.post("/ingest")
async def ingest(
    files: Annotated[
        List[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    #Check if file uploaded is empty
    if len(files) ==1 and files[0].filename == '':
      return JSONResponse(status_code=400, content={"message": "No files detected. Please upload at least one file."})  

    #filter out non txt files 
    removed_documents,files=filter_file_format(files)

    # Variable to save filenames for output
    new_documents = []

    # Add files into data folder, and update query engine if there's any txt file uploaded
    if files:
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
          except Exception as e:
              return JSONResponse(status_code=500, content={"message": f"Failed to process file {file.filename}: {str(e)}"})

      # Update the index with new documents, reload query engine
      documents = SimpleDirectoryReader("data").load_data()
      index = VectorStoreIndex.from_documents(documents)
      index.storage_context.persist()
      update_query_engine(index)
              
    filenames = [file.filename for file in files]
    return {"message": f"Removed from uploads (Non-txt format):<br>- {'<br>- '.join([os.path.basename(doc) for doc in removed_documents])}<br><br>Successfully uploaded and saved:<br>- {'<br>- '.join([os.path.basename(doc) for doc in new_documents])}<br><br>"}

#Query API Definition
@app.get("/query")
async def search_query(query: str ):
    #Retrieve response from the query engine
    if query =='':
        return JSONResponse(status_code=400, content={"message": "No query text detected. Please ensure query is not empty."}) 
    try: 
      response =  query_engine.query(query)
      results = Markdown(f"{response}")
      return {"query": query, "results": results.data}
    except Exception as e:
      return JSONResponse(status_code=500, content={"message": f"Failed to process query: {str(e)}"})


#Retrieve html code for the main interface
def load_content():
    try:
        with open('chat_interface.html', 'r') as file:
            content = file.read()
        return content
    except IOError as e:
        print(f"Error reading file: {e}")
        return None

#Main interface for web application
@app.get("/")
async def main():
    content = load_content()
    return HTMLResponse(content=content)

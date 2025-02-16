from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from tasksA import *
from tasksB import *
import requests
from dotenv import load_dotenv
import os
import httpx
import json

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# CORS Middleware to allow all origins (useful for development and testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# AI Proxy and API settings
openai_api_chat = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
openai_api_key = os.getenv("AIPROXY_TOKEN")

headers = {
    "Authorization": f"Bearer {openai_api_key}",
    "Content-Type": "application/json",
}

# Function Definitions for LLM
function_definitions_llm = [
    {"name": "A1", "description": "Run datagen.py with email as argument.", "parameters": {"type": "object", "properties": {"email": {"type": "string"}}, "required": ["email"]}},
    {"name": "A2", "description": "Format a markdown file using Prettier.", "parameters": {"type": "object", "properties": {"prettier_version": {"type": "string"}, "filename": {"type": "string"}}, "required": ["prettier_version", "filename"]}},
    {"name": "A3", "description": "Count Wednesdays in a date file.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "targetfile": {"type": "string"}, "weekday": {"type": "integer"}}, "required": ["filename", "targetfile", "weekday"]}},
    {"name": "A4", "description": "Sort contacts by last and first name.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "targetfile": {"type": "string"}}, "required": ["filename", "targetfile"]}},
    {"name": "A5", "description": "Get first line of 10 most recent log files.", "parameters": {"type": "object", "properties": {"log_dir_path": {"type": "string"}, "output_file_path": {"type": "string"}, "num_files": {"type": "integer"}}, "required": ["log_dir_path", "output_file_path", "num_files"]}},
    {"name": "A6", "description": "Index Markdown files by H1 title.", "parameters": {"type": "object", "properties": {"doc_dir_path": {"type": "string"}, "output_file_path": {"type": "string"}}, "required": ["doc_dir_path", "output_file_path"]}},
    {"name": "A7", "description": "Extract sender's email from a text file.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "output_file": {"type": "string"}}, "required": ["filename", "output_file"]}},
    {"name": "A8", "description": "Extract credit card number from image.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "image_path": {"type": "string"}}, "required": ["filename", "image_path"]}},
    {"name": "A9", "description": "Find the most similar pair of comments.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "output_filename": {"type": "string"}}, "required": ["filename", "output_filename"]}},
    {"name": "A10", "description": "Calculate total sales for Gold tickets.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "output_filename": {"type": "string"}, "query": {"type": "string"}}, "required": ["filename", "output_filename", "query"]}},
]

# Function to get completions from AI Proxy
def get_completions(prompt: str):
    with httpx.Client(timeout=20) as client:
        response = client.post(
            openai_api_chat,
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a function classifier that extracts structured parameters from queries."},
                    {"role": "user", "content": prompt}
                ],
                "tools": [
                    {"type": "function", "function": function}
                    for function in function_definitions_llm
                ],
                "tool_choice": "auto"
            }
        )
    return response.json()["choices"][0]["message"]["tool_calls"][0]["function"]

# Endpoint to handle custom prompts
@app.get("/ask")
def ask(prompt: str):
    result = get_completions(prompt)
    return result

# Main Endpoint to Run Tasks
@app.post("/run")
async def run_task(task: str):
    try:
        response = get_completions(task)
        task_code = response['name']
        arguments = json.loads(response['arguments'])

        # Map the task code to the corresponding function
        if task_code in globals():
            globals()[task_code](**arguments)
        else:
            raise HTTPException(status_code=400, detail="Unknown task")

        return {"message": f"{task_code} Task '{task}' executed successfully"}
    except Exception as e:
        print(f"❌ Error in {task}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to Read File Contents
@app.get("/read", response_class=PlainTextResponse)
async def read_file(path: str = Query(..., description="File path to read")):
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run Uvicorn Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

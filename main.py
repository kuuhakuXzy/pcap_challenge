import os
import subprocess
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import logging

# Configuration 
PCAP_DIRECTORY = "pcaps"
INDEX_FILE = "pcap_index.json"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="Pcap Catalog Service",
    description="A service to index and search pcap files by protocol."
)

# Core Logic
def get_protocols_from_pcap(pcap_file: str) -> Optional[List[str]]:
    command = ['tshark', '-r', pcap_file, '-T', 'fields', '-e', 'frame.protocols']
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        unique_protocols = set()
        output = result.stdout.strip()
        if not output: 
            return []
        for line in output.splitlines():
            protocols_in_frame = line.strip().split(':')
            unique_protocols.update(p for p in protocols_in_frame if p)
        return sorted(list(unique_protocols))
    except subprocess.CalledProcessError as e:
        logger.error(f"Error analyzing {pcap_file}: {e.stderr}")
        return None

# Indexing Functionality
def scan_and_index(exclude_files: List[str] = None) -> dict:
    if exclude_files is None:
        exclude_files = []

    logger.info(f"Start scanning folder: {PCAP_DIRECTORY}")
    logger.info(f"Excluded files: {exclude_files}") 
    index_data = []

    if not os.path.isdir(PCAP_DIRECTORY):
        logger.error(f"Directory '{PCAP_DIRECTORY}' does not exist.")
        return {"error": f"Directory '{PCAP_DIRECTORY}' does not exist."}
    for filename in os.listdir(PCAP_DIRECTORY):
        if filename in exclude_files:
            logger.info(f"Skip the excluded files : {filename}")
            continue

        if filename.endswith((".pcap", ".cap")):
            file_path = os.path.join(PCAP_DIRECTORY, filename)
            logger.info(f"Processing file: {file_path}")
            protocols = get_protocols_from_pcap(file_path)
            if protocols is not None:
                file_size = os.path.getsize(file_path)
                index_data.append({
                    "filename": filename,
                    "path": file_path,
                    "size_bytes": file_size,
                    "protocols": protocols
                })
            else:
                logger.warning(f"Skipping file {filename} from index due to processing error.")

    try:
        with open(INDEX_FILE, 'w') as f:
            json.dump(index_data, f, indent=2)
        logger.info(f"Indexing successful. Saved to {INDEX_FILE}")
        return {"status": "success", "indexed_files": len(index_data)}
    except IOError as e:
        logger.error(f"Could not write index file {INDEX_FILE}: {e}")
        return {"error": f"Could not write index file {INDEX_FILE}"}

# API Endpoints
@app.on_event("startup")
async def startup_event():
    if not os.path.exists(INDEX_FILE):
        scan_and_index()

@app.post("/reindex", summary="Rescan the pcap directory and update the index")
async def reindex_pcaps(exclude: Optional[List[str]] = Query(None, description="List of files excluded from scanning.")):
    result = scan_and_index(exclude_files=exclude)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return JSONResponse(content=result)

@app.get("/search", summary="Search for pcaps containing a specific protocol")
async def search_pcaps(protocol: str = Query(..., description="The protocol name to search for, e.g., sip")):
    if not os.path.exists(INDEX_FILE):
        raise HTTPException(
            status_code=404, 
            detail=f"Index file '{INDEX_FILE}' not found. Please run the /reindex endpoint first."
        )
    
    with open(INDEX_FILE, 'r') as f:
        index_data = json.load(f)
        
    search_protocol = protocol.lower()
    results = [
        item for item in index_data 
        if search_protocol in [p.lower() for p in item.get("protocols", [])]
    ]
    
    return results

@app.get("/pcaps/{filename}", summary="Download a specific pcap file")
async def download_pcap(filename: str):
    file_path = os.path.join(PCAP_DIRECTORY, filename)
    
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    return FileResponse(file_path, media_type='application/vnd.tcpdump.pcap', filename=filename)

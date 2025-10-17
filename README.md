# Pcap Catalog Service

A web service that scans a directory of pcap files, catalogs them based on their protocol contents, and provides an API to search and download them.

This project was created as a technical challenge.

## Features

-   Scans a directory for `.pcap` and `.cap` files.
-   Analyzes files using `tshark` to extract all protocols.
-   Creates a JSON index for fast searching.
-   Provides a REST API to search for pcaps by protocol and download them.
-   Packaged with Docker and Docker Compose for easy deployment.

## Requirements

-   Docker
-   Docker Compose

## How to Run

1.  Place your pcap files into the `pcaps` directory. If the directory does not exist, create it: `mkdir pcaps`.
2.  From the project root directory, build and run the service using a single command:
    ```bash
    docker-compose up --build
    ```
3.  The service is now running and available at `http://localhost:8000`.

## How to Use the API

An interactive API documentation (Swagger UI) is automatically generated and available at:
[http://localhost:8000/docs](http://localhost:8000/docs)

You can also use `curl`:

-   **To catalog all pcaps:** (This runs automatically on startup)
    ```bash
    curl -X POST http://localhost:8000/reindex
    ```

-   **To search for a protocol (e.g., 'isup'):**
    ```bash
    curl http://localhost:8000/search?protocol=isup | jq
    ```

-   **To download a file (e.g., 'isup.cap'):**
    ```bash
    curl -o isup.cap_downloaded http://localhost:8000/pcaps/isup.cap
    ```

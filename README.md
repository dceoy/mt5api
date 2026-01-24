# pdmt5-api

MetaTrader 5 REST API

## Overview

This repository provides a REST interface for the `pdmt5` Python dependency. The API wraps
common MetaTrader 5 actions (initialization, account info, symbols, orders, positions) and
exposes them via FastAPI.

## Install

```bash
python -m pip install -e .
```

## Run

```bash
pdmt5-api --host 0.0.0.0 --port 8000
```

Optional configuration can be supplied as JSON:

```bash
pdmt5-api --config config.json
```

## API

- `GET /health`
- `POST /connect`
- `POST /shutdown`
- `GET /account`
- `GET /symbols`
- `GET /symbols/{symbol}`
- `GET /positions`
- `GET /orders`
- `POST /orders`

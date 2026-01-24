# Deployment Guide (Windows Service)

This guide describes how to deploy the pdmt5 REST API as a Windows service
alongside the MetaTrader 5 terminal.

## Prerequisites

- Windows 10/11
- MetaTrader 5 installed and logged in
- Python 3.11+
- `pdmt5[api]` installed

## Service Setup (NSSM)

1. Download NSSM: https://nssm.cc/download
2. Open an elevated PowerShell session.
3. Create a service:

```powershell
nssm install pdmt5-api
```

4. Set the application path and arguments:

- Path: `C:\Path\To\Python\python.exe`
- Arguments: `-m uvicorn pdmt5.api.main:app --host 0.0.0.0 --port 8000`
- Startup directory: your project directory

5. Set environment variables in the NSSM GUI:

```
MT5_API_KEY=your-secret-api-key
API_LOG_LEVEL=INFO
API_RATE_LIMIT=100
API_CORS_ORIGINS=*
```

6. Start the service:

```powershell
nssm start pdmt5-api
```

## Validation

```powershell
curl http://localhost:8000/api/v1/health
```

Expected status: `healthy` (or `unhealthy` if MT5 is not connected).

## Troubleshooting

- Ensure the MT5 terminal is running and logged in.
- Confirm firewall rules allow inbound traffic on the API port.
- Check Windows Event Viewer for NSSM service logs.

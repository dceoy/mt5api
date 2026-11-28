# Deployment Guide (Windows Service)

This guide describes how to deploy the mt5api REST API as a Windows service
alongside the MetaTrader 5 terminal.

This is a Windows-only deployment target. The API server cannot run on Linux or
macOS because the `MetaTrader5` Python package is supported only on Windows.

## Prerequisites

- Windows 10/11
- MetaTrader 5 installed and logged in
- `mt5api` installed
- PowerShell access with permission to install and manage services

## Service Setup (NSSM)

1. Download NSSM: https://nssm.cc/download
2. Open an elevated PowerShell session.
3. Create a service:

```powershell
nssm install mt5api
```

4. Set the application path and arguments:

- Path: `C:\Path\To\Python\python.exe`
- Arguments: `-m uvicorn mt5api.main:app --host 127.0.0.1 --port 8000`
- Startup directory: your project directory

5. Set environment variables in the NSSM GUI:

```
# Required: set a secret API key.
MT5API_SECRET_KEY=your-secret-api-key
MT5API_LOG_LEVEL=INFO
MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS=100
MT5API_ROUTER_PREFIX=/api/v1
```

Optionally set `MT5API_MT5_PATH` to the full path of `terminal64.exe` for
this service. The path is retained on login; unset or empty uses the default
terminal selection. Run separate services on different ports to pin each to a
different terminal.

6. Start the service:

```powershell
nssm start mt5api
```

## Validation

In PowerShell, use `curl.exe` if `curl` resolves to `Invoke-WebRequest`.

```console
curl "http://localhost:8000/api/v1/health"
```

Expected status: `healthy` (or `unhealthy` if MT5 is not connected).

## Troubleshooting

- Ensure the MT5 terminal is running and logged in.
- Confirm firewall rules allow inbound traffic on the API port.
- Check Windows Event Viewer for NSSM service logs.

The server requires a nonempty `MT5API_SECRET_KEY` and binds to `127.0.0.1`
by default. For remote access with the NSSM command above, change its uvicorn `--host`
argument to the desired bind address and set `MT5API_TRUSTED_HOSTS` to a comma-separated list of
allowed Host names or IP addresses, such as `windows-host,localhost,127.0.0.1`.
The default allowlist is `localhost,127.0.0.1,[::1]`.

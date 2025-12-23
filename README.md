# cloud0

A simple multi-cloud status checker that monitors the operational status of major cloud service providers.

## Features

- Check real-time status of multiple cloud providers (AWS, Azure, GCP, DigitalOcean, Cloudflare)
- Simple CLI interface with colored output
- JSON output support for automation
- Lightweight and fast

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Check all cloud providers

```bash
python cloud0.py
```

### Check specific provider

```bash
python cloud0.py --provider aws
python cloud0.py --provider azure
python cloud0.py --provider gcp
```

### Get JSON output

```bash
python cloud0.py --json
```

### Available Providers

- `aws` - Amazon Web Services
- `azure` - Microsoft Azure
- `gcp` - Google Cloud Platform
- `digitalocean` - DigitalOcean
- `cloudflare` - Cloudflare

## Example Output

```
Cloud Provider Status Check
===========================

AWS:              ✓ Operational
Azure:            ✓ Operational
GCP:              ✓ Operational
DigitalOcean:     ✓ Operational
Cloudflare:       ✓ Operational
```

## Requirements

- Python 3.7+
- requests library

## License

MIT

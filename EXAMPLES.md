# cloud0 Usage Examples

## Basic Usage

### Check all cloud providers

```bash
python cloud0.py
```

Output:
```
Cloud Provider Status Check
==================================================

AWS                ✓ Operational
Azure              ✓ Operational
GCP                ✓ Operational
DigitalOcean       ✓ Operational
Cloudflare         ✓ Operational
```

### Check a specific provider

```bash
python cloud0.py --provider aws
```

### Check with custom timeout

```bash
python cloud0.py --timeout 10
```

## JSON Output

Get machine-readable output for automation:

```bash
python cloud0.py --json
```

Output:
```json
{
  "aws": {
    "status": "operational",
    "message": "Service reachable",
    "provider": "AWS",
    "url": "https://status.aws.amazon.com/"
  },
  "azure": {
    "status": "operational",
    "message": "Service reachable",
    "provider": "Azure",
    "url": "https://status.azure.com/en-us/status"
  }
}
```

## Integration Examples

### Shell Script

```bash
#!/bin/bash

# Check cloud status before deployment
if python cloud0.py --provider aws; then
    echo "AWS is operational, proceeding with deployment..."
    # Your deployment commands here
else
    echo "AWS has issues, aborting deployment"
    exit 1
fi
```

### Python Integration

```python
from cloud0 import CloudStatusChecker

checker = CloudStatusChecker()

# Check all providers
results = checker.check_all()

for provider, status_info in results.items():
    if status_info['status'] != 'operational':
        print(f"Warning: {provider} is {status_info['status']}")

# Check specific provider
aws_status = checker.check_provider('aws')
if aws_status['status'] == 'operational':
    # Proceed with AWS operations
    pass
```

### Cron Job Monitoring

Add to crontab to check every 5 minutes:

```bash
*/5 * * * * /usr/bin/python3 /path/to/cloud0.py --json >> /var/log/cloud-status.log
```

### CI/CD Pipeline

Use in GitHub Actions or GitLab CI:

```yaml
- name: Check Cloud Provider Status
  run: |
    python cloud0.py --provider aws
    if [ $? -ne 0 ]; then
      echo "Cloud provider has issues, skipping deployment"
      exit 1
    fi
```

## Exit Codes

- `0`: All checked providers are operational
- `1`: At least one provider is degraded, has errors, or unknown status

This makes it easy to use in scripts and automation workflows.

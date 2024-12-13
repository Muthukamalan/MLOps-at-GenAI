goto: `localhost:9090`

check: Target-Health

query: 🎨🖌️
- DiskAvailable{job='torchserve'}
- rate(MemoryUsed{job='torchserve'}[5m]) / 1024 / 1024  # In MB
- rate(process_virtual_memory_bytes{job='prometheus'}[5m]) / 1024 / 1024  # In MB
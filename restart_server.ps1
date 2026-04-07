# Stop any Python process using port 8000
$port = 8000
$processId = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess

if ($processId) {
    Write-Host "Stopping process $processId using port $port..."
    Stop-Process -Id $processId -Force
    Start-Sleep -Seconds 2
}

# Start the server
Write-Host "Starting server..."
python main.py

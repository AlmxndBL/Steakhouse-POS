$ErrorActionPreference = "Stop"
$workspaceRoot = Split-Path -Parent $PSScriptRoot
Push-Location $workspaceRoot

try {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($docker) {
        $dockerPath = $docker.Source
    }
    else {
        $dockerPath = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\docker.exe"
    }

    if (-not (Test-Path -LiteralPath $dockerPath)) {
        throw "Docker CLI was not found. Start Docker Desktop and ensure docker.exe is installed."
    }

    & $dockerPath compose -f docker-compose.test.yml up -d --wait --force-recreate test-db
    if ($LASTEXITCODE -ne 0) {
        throw "Could not start the isolated POS test PostgreSQL service."
    }

    & $dockerPath compose -f docker-compose.test.yml run --build --rm test-runner python -m unittest tests.test_cashier_workflow tests.test_supporting_services -v
    if ($LASTEXITCODE -ne 0) {
        throw "Service workflow tests failed. The isolated test database remains available for inspection."
    }
}
finally {
    Pop-Location
}

param(
    [string]$OutputPath = ".\docs\openapi-v1.yaml"
)

$ErrorActionPreference = "Stop"

Write-Host "Exporting OpenAPI schema to $OutputPath"
python manage.py spectacular --file $OutputPath --validate

if ($LASTEXITCODE -ne 0) {
    throw "OpenAPI export failed."
}

Write-Host "OpenAPI schema exported and validated successfully."

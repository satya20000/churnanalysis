# Set the source root from the location of this script, with no Python dependency.
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path.Replace('\','/')
$modelPath = Join-Path $PSScriptRoot 'SaaS.SemanticModel/model.bim'
$model = Get-Content -LiteralPath $modelPath -Raw | ConvertFrom-Json
$parameter = $model.model.expressions | Where-Object { $_.name -eq 'ProjectRoot' }
$parameter.expression = '"' + $repoRoot + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
$model | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $modelPath -Encoding UTF8
Write-Host 'Path configured. Open SaaS_Churn_Revenue_Intelligence.pbip and select Refresh.'

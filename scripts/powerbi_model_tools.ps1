param(
    [Parameter(Mandatory)][ValidateSet('Serialize','Query','Inspect','Audit')][string]$Action,
    [Parameter(Mandatory)][string]$LibraryDirectory,
    [string]$Server,
    [string]$InputPath,
    [Parameter(Mandatory)][string]$OutputPath
)
# Outils officiels Microsoft AMO/ADOMD, version 19.118.3, hors du dépôt.
# Aucun secret ; le serveur local doit être résolu et identifié au préalable.
$ErrorActionPreference = 'Stop'
if ($Action -eq 'Serialize') {
    Add-Type -Path (Join-Path $LibraryDirectory 'tom/lib/net8.0/Microsoft.AnalysisServices.Core.dll')
    Add-Type -Path (Join-Path $LibraryDirectory 'tom/lib/net8.0/Microsoft.AnalysisServices.Tabular.dll')
    $j07Database = [Microsoft.AnalysisServices.Tabular.JsonSerializer]::DeserializeDatabase((Get-Content -Raw -LiteralPath $InputPath))
    [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::SerializeDatabaseToFolder($j07Database, $OutputPath)
    return
}
if ($Server -notmatch '^localhost:\d+$') { throw 'Un serveur Desktop local explicite est requis.' }
if ($Action -in @('Inspect','Audit')) {
    Add-Type -Path (Join-Path $LibraryDirectory 'tom/lib/net8.0/Microsoft.AnalysisServices.Core.dll')
    Add-Type -Path (Join-Path $LibraryDirectory 'tom/lib/net8.0/Microsoft.AnalysisServices.Tabular.dll')
    $j07Server = [Microsoft.AnalysisServices.Tabular.Server]::new()
    try {
        $j07Server.Connect($Server)
        if ($j07Server.Databases.Count -ne 1) { throw 'Base Desktop ambiguë.' }
        $j07Database = $j07Server.Databases[0]
        if ($Action -eq 'Inspect') {
            [Microsoft.AnalysisServices.Tabular.JsonSerializer]::SerializeDatabase($j07Database) | Set-Content -LiteralPath $OutputPath -Encoding utf8
        } else {
            [ordered]@{
                compatibilityLevel = $j07Database.CompatibilityLevel
                tables = @($j07Database.Model.Tables | ForEach-Object {
                    [ordered]@{ name=$_.Name; partitions=@($_.Partitions | ForEach-Object {
                        [ordered]@{ name=$_.Name; mode=$_.Mode.ToString(); state=$_.State.ToString(); refreshedTime=$_.RefreshedTime.ToString('o') }
                    }); measures=@($_.Measures | ForEach-Object {
                        [ordered]@{ name=$_.Name; state=$_.State.ToString(); errorMessage=$_.ErrorMessage }
                    }) }
                })
                relationships = @($j07Database.Model.Relationships | ForEach-Object {
                    [ordered]@{ name=$_.Name; fromTable=$_.FromTable.Name; toTable=$_.ToTable.Name;
                        fromCardinality=$_.FromCardinality.ToString(); toCardinality=$_.ToCardinality.ToString();
                        crossFilteringBehavior=$_.CrossFilteringBehavior.ToString(); isActive=$_.IsActive }
                })
            } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8
        }
    } finally { $j07Server.Disconnect() }
    return
}
Add-Type -Path (Join-Path $LibraryDirectory 'adomd/lib/net8.0/Microsoft.AnalysisServices.AdomdClient.dll')
$j07Connection = [Microsoft.AnalysisServices.AdomdClient.AdomdConnection]::new("Data Source=$Server")
$j07Rows = [System.Collections.Generic.List[object]]::new()
try {
    $j07Connection.Open()
    $j07Command = $j07Connection.CreateCommand()
    $j07Command.CommandText = Get-Content -Raw -LiteralPath $InputPath
    $j07Command.CommandTimeout = 120
    $j07Reader = $j07Command.ExecuteReader()
    try {
        while ($j07Reader.Read()) {
            $j07Row = [ordered]@{}
            for ($j07Index=0; $j07Index -lt $j07Reader.FieldCount; $j07Index++) {
                $j07Value = $j07Reader.GetValue($j07Index)
                if ($j07Value -is [DBNull]) { $j07Value = $null }
                elseif ($j07Value -is [datetime]) { $j07Value = $j07Value.ToString('yyyy-MM-ddTHH:mm:ss') }
                $j07Row[$j07Reader.GetName($j07Index)] = $j07Value
            }
            $j07Rows.Add([pscustomobject]$j07Row)
        }
    } finally { $j07Reader.Close() }
} finally { $j07Connection.Close() }
ConvertTo-Json -InputObject @($j07Rows.ToArray()) -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8

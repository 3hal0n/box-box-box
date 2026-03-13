$passed = 0
$failed = 0
$files = Get-ChildItem "data/test_cases/inputs/test_*.json"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Box Box Box - PowerShell Test Runner " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Running $($files.Count) tests..."
Write-Host ""

foreach ($file in $files) {
    $name = $file.BaseName

    # Run the python script, capturing stdout
    $outputJson = Get-Content $file.FullName | python solution/race_simulator.py | Out-String

    if ([string]::IsNullOrWhiteSpace($outputJson)) {
        Write-Host "FAIL $name - Script crashed or returned empty" -ForegroundColor Red
        $failed++
        continue
    }

    $actual = (ConvertFrom-Json $outputJson).finishing_positions -join ","

    # Get expected answer if it exists
    $expectedPath = "data/test_cases/expected_outputs/$name.json"
    if (Test-Path $expectedPath) {
        $expected = (Get-Content $expectedPath | ConvertFrom-Json).finishing_positions -join ","
        if ($actual -eq $expected) {
            Write-Host "PASS $name" -ForegroundColor Green
            $passed++
        } else {
            Write-Host "FAIL $name - Incorrect prediction" -ForegroundColor Red
            $failed++
        }
    } else {
        Write-Host "WARN $name - Output generated (no answer key)" -ForegroundColor Yellow
        $passed++
    }
}

$score = if ($files.Count -gt 0) { [math]::Round(($passed / $files.Count) * 100, 1) } else { 0 }
Write-Host ""
Write-Host "Total Tests: $($files.Count)"
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Score: $score%" -ForegroundColor Cyan
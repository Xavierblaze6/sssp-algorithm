Write-Host '==================== DEMO: SSSP ====================' -ForegroundColor Cyan
Write-Host 'Python:' (python -V)

Write-Host "\n[1/3] Quick demo (quick_test.py)" -ForegroundColor Yellow
python quick_test.py

Write-Host "\n[2/3] Run experiments (this may take ~1-2 minutes)" -ForegroundColor Yellow
python run_experiments.py

Write-Host "\n[3/3] Analyze results" -ForegroundColor Yellow
python analyze_results.py

Write-Host "\nDemo complete. Artifacts: experiment_results.csv (and plots/ if matplotlib installed)." -ForegroundColor Green

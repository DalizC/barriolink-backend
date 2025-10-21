# Script PowerShell para ejecutar herramientas de calidad de código
# Ejecutar con: ./lint.ps1

Write-Host "🔍 Ejecutando Flake8..." -ForegroundColor Cyan
flake8 app core --count --statistics

Write-Host ""
Write-Host "📊 Resumen:" -ForegroundColor Green
Write-Host "✅ Solo se muestran errores en tu código (no en dependencias)" -ForegroundColor Green
Write-Host "❌ Errores encontrados arriba" -ForegroundColor Red

Write-Host ""
Write-Host "💡 Para corregir automáticamente algunos errores:" -ForegroundColor Yellow
Write-Host "   autopep8 --in-place --aggressive app/ core/" -ForegroundColor White

Write-Host ""
Write-Host "🎯 Errores comunes y cómo solucionarlos:" -ForegroundColor Blue
Write-Host "   E302: Agregar 2 líneas en blanco entre funciones de nivel superior" -ForegroundColor White
Write-Host "   E501: Dividir líneas largas (máximo 88 caracteres)" -ForegroundColor White  
Write-Host "   F401: Eliminar imports no utilizados" -ForegroundColor White
Write-Host "   W292: Agregar nueva línea al final del archivo" -ForegroundColor White
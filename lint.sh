#!/bin/bash
# Script para ejecutar herramientas de calidad de código

echo "🔍 Ejecutando Flake8..."
flake8 app core --count --statistics

echo ""
echo "📊 Resumen:"
echo "✅ Solo se muestran errores en tu código (no en dependencias)"
echo "❌ Errores encontrados arriba"

echo ""
echo "💡 Para corregir automáticamente algunos errores, puedes usar:"
echo "   autopep8 --in-place --aggressive app/ core/"

echo ""
echo "🎯 Errores comunes y cómo solucionarlos:"
echo "   E302: Agregar 2 líneas en blanco entre funciones de nivel superior"
echo "   E501: Dividir líneas largas (máximo 88 caracteres)"
echo "   F401: Eliminar imports no utilizados"
echo "   W292: Agregar nueva línea al final del archivo"
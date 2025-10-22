# 🚀 GUÍA DE DESPLIEGUE EN AZURE APP SERVICE

## 📋 Pre-requisitos

1. ✅ Cuenta de Azure activa
2. ✅ PostgreSQL Flexible Server configurado
3. ✅ Repositorio en GitHub con el código
4. ✅ Base de datos `barriolink-prod` creada

## 🔧 Paso 1: Crear App Service

### Opción A: Azure Portal (Recomendado)
1. **Ir a Azure Portal** → "Create a resource" → "Web App"
2. **Configuración básica:**
   - **Name**: `barriolink-api` (o el nombre que prefieras)
   - **Runtime**: `Python 3.12`
   - **Region**: La misma de tu PostgreSQL
   - **Plan**: `B1` (Basic) para desarrollo, `S1` (Standard) para producción

### Opción B: Azure CLI
```bash
# Crear resource group (si no existe)
az group create --name barriolink-rg --location westus2

# Crear App Service Plan
az appservice plan create --name barriolink-plan --resource-group barriolink-rg --sku B1 --is-linux

# Crear Web App
az webapp create --name barriolink-api --resource-group barriolink-rg --plan barriolink-plan --runtime "PYTHON|3.12"
```

## ⚙️ Paso 2: Configurar Variables de Entorno

En **Azure Portal** → **App Service** → **Configuration** → **Application Settings**:

```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=TU_SECRET_KEY_SUPER_SEGURA_AQUI
ALLOWED_HOSTS=barriolink-api.azurewebsites.net
CSRF_TRUSTED_ORIGINS=https://barriolink-api.azurewebsites.net

DB_HOST=pg-barriolink01-dev.postgres.database.azure.com
DB_NAME=barriolink-prod
DB_USER=barriolink_app_user
DB_PASSWORD=TU_PASSWORD_DE_DB
DB_PORT=5432
DB_SSLMODE=require

CORS_ALLOWED_ORIGINS=https://tu-frontend-angular.com,https://localhost:4200

STATIC_URL=/static/
STATIC_ROOT=/home/site/wwwroot/staticfiles
MEDIA_URL=/media/
MEDIA_ROOT=/home/site/wwwroot/media

LOG_LEVEL=INFO
```

## 📦 Paso 3: Desplegar desde GitHub

### Configurar Continuous Deployment:
1. **Azure Portal** → **App Service** → **Deployment Center**
2. **Source**: GitHub
3. **Autorizar** tu cuenta de GitHub
4. **Seleccionar**: Organización, Repositorio, Branch (main)
5. **Build Provider**: App Service Build Service
6. **Guardar**

Azure creará automáticamente el workflow de GitHub Actions.

## 🛡️ Paso 4: Configuración de Red y Seguridad

### Permitir conexión a PostgreSQL:
1. **PostgreSQL** → **Networking** → **Firewall rules**
2. **Agregar**: "Allow access from Azure services" = ON
3. **O agregar IP específica** del App Service

### SSL y Dominio personalizado (Opcional):
1. **App Service** → **Custom domains**
2. **TLS/SSL settings** → **Bindings**

## 🔍 Paso 5: Verificación y Monitoreo

### URLs importantes:
- **API Base**: `https://barriolink-api.azurewebsites.net/`
- **Admin**: `https://barriolink-api.azurewebsites.net/admin/`
- **API Docs**: `https://barriolink-api.azurewebsites.net/api/`

### Logs y troubleshooting:
```bash
# Ver logs en tiempo real
az webapp log tail --name barriolink-api --resource-group barriolink-rg

# Descargar logs
az webapp log download --name barriolink-api --resource-group barriolink-rg
```

## 📊 Paso 6: Configurar el Frontend Angular

En tu aplicación Angular, actualizar las URLs de la API:

```typescript
// environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://barriolink-api.azurewebsites.net/api/',
  baseUrl: 'https://barriolink-api.azurewebsites.net'
};
```

## 💰 Costos Estimados (USD/mes)

- **App Service B1**: ~$13/mes
- **App Service S1**: ~$73/mes  
- **PostgreSQL Flexible**: ~$30-100/mes (según configuración)
- **Ancho de banda**: Variable según uso

## 🚨 Checklist de Producción

- [ ] Variables de entorno configuradas
- [ ] DEBUG=False
- [ ] SECRET_KEY única y segura
- [ ] ALLOWED_HOSTS configurado
- [ ] CORS configurado para tu frontend
- [ ] SSL habilitado
- [ ] Base de datos de producción
- [ ] Logs funcionando
- [ ] Backups de DB configurados
- [ ] Monitoring configurado

## 🔄 Actualizaciones

Simplemente haz push a tu rama main en GitHub. Azure automaticamente:
1. Descargará el código
2. Instalará dependencias
3. Ejecutará migraciones
4. Reiniciará la aplicación

## 📞 Soporte y Troubleshooting

### Errores comunes:
- **500 Error**: Revisar logs, variables de entorno
- **Database connection**: Verificar firewall PostgreSQL
- **Static files**: Verificar STATIC_ROOT y collectstatic
- **CORS**: Verificar dominios en CORS_ALLOWED_ORIGINS
# TODO - BarrioLink Backend

## Pendientes de Implementación

### 🔴 Alta Prioridad

#### Validación de Conflictos de Eventos en el Backend
**Descripción**: Implementar validación en el backend para prevenir solapamiento de eventos en la misma facility.

**Motivo**: Actualmente la validación solo existe en el frontend. Para mayor seguridad y consistencia de datos, el backend debe validar antes de guardar.

**Implementación Sugerida**:

1. **Crear endpoint de validación** (opcional):
   ```python
   POST /api/event/check-availability/
   {
       "facility_id": 123,
       "start_datetime": "2025-11-26T10:00:00",
       "end_datetime": "2025-11-26T12:00:00",
       "recurrence_type": "weekly",  # opcional
       "recurrence_days_of_week": "3,4",  # opcional
       "recurrence_end_date": "2026-02-10",  # opcional
       "exclude_event_id": 456  # opcional, para editar eventos
   }
   ```

   Respuesta:
   ```json
   {
       "has_conflict": true,
       "conflicting_events": [
           {
               "id": 789,
               "title": "Reunión Vecinal",
               "start_datetime": "2025-11-26T11:00:00",
               "end_datetime": "2025-11-26T13:00:00"
           }
       ]
   }
   ```

2. **Validación en create/update**:
   ```python
   # En models.py o serializers.py
   def validate_no_conflicts(self):
       """
       Valida que no existan conflictos de horario en la misma facility
       """
       if not self.facility_id:
           return  # Sin facility, no hay conflicto posible

       # Obtener eventos existentes en la facility
       existing_events = Event.objects.filter(
           facility_id=self.facility_id,
           is_active=True
       ).exclude(id=self.id)  # Excluir el evento actual si es edición

       # Para cada evento existente, expandir ocurrencias y verificar solapamiento
       for event in existing_events:
           if self._check_time_overlap(event):
               raise ValidationError(
                   f"Conflicto de horario con el evento '{event.title}'"
               )
   ```

3. **Lógica de detección de solapamiento**:
   - Para eventos únicos (recurrence_type='none'): comparar directamente start_datetime y end_datetime
   - Para eventos periódicos semanales: expandir ocurrencias basadas en recurrence_days_of_week
   - Para eventos periódicos mensuales/anuales: expandir ocurrencias según intervalo

4. **Respuesta de error**:
   ```python
   # En views.py o serializers.py
   try:
       event.validate_no_conflicts()
       event.save()
   except ValidationError as e:
       return Response(
           {"detail": str(e), "error_code": "CONFLICT_DETECTED"},
           status=status.HTTP_409_CONFLICT
       )
   ```

**Archivos a Modificar**:
- `events/models.py`: Agregar método `validate_no_conflicts()`
- `events/serializers.py`: Llamar validación en `validate()` o `create()`/`update()`
- `events/views.py`: (opcional) Agregar endpoint `/check-availability/`
- `events/tests.py`: Agregar tests para validación de conflictos

**Beneficios**:
- ✅ Seguridad: Previene race conditions (dos usuarios creando eventos simultáneamente)
- ✅ Integridad de datos: Garantiza que no haya conflictos en la BD
- ✅ Confiabilidad: No depende solo del frontend

**Prioridad**: Alta (necesario para producción)
**Estimación**: 4-6 horas de desarrollo + tests

---

## Notas Adicionales

### Frontend Implementado ✅
- Validación en tiempo real al cambiar facility/fecha/hora
- Indicadores visuales de conflictos en el wizard
- Prevención de submit si hay conflictos detectados
- Expansión de eventos recurrentes para detección de solapamientos

### Próximos Pasos
1. Implementar validación en backend (este TODO)
2. Agregar tests de integración frontend-backend
3. Documentar API de validación en Swagger/OpenAPI

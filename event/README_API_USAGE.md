# Event API - Guía de Uso

## Cambios Importantes: DateTimeField con Campos Auxiliares

El modelo Event ahora usa `start_datetime` y `end_datetime` (DateTimeField) para mejor manejo de fechas/horas, zonas horarias y queries. Sin embargo, el serializer soporta **dos formas** de enviar datos desde el frontend.

---

## 📤 Opción 1: Enviar DateTimeField directamente (Recomendado)

### Formato ISO 8601
```json
POST /api/events/
{
  "title": "Clases de matemáticas",
  "description": "Para niños",
  "start_datetime": "2025-06-10T17:00:00",
  "end_datetime": "2025-06-10T19:00:00",
  "recurrence_type": "weekly",
  "recurrence_days_of_week": "2,4",
  "recurrence_end_date": "2025-07-30",
  "capacity": 20,
  "facility": 1
}
```

### En Angular/TypeScript:
```typescript
interface Event {
  title: string;
  start_datetime: string; // ISO 8601: "YYYY-MM-DDTHH:mm:ss"
  end_datetime?: string | null;
  // ... otros campos
}

// Combinar fecha y hora desde el formulario
const startDatetime = `${startDate}T${startTime}:00`;
const endDatetime = endTime ? `${endDate || startDate}T${endTime}:00` : null;

const event: Event = {
  title: 'Mi evento',
  start_datetime: startDatetime,
  end_datetime: endDatetime,
  // ...
};
```

---

## 📤 Opción 2: Enviar campos separados (Compatibilidad UI)

El serializer acepta campos auxiliares `start_date`, `start_time`, `end_date`, `end_time` y los convierte automáticamente a datetime.

```json
POST /api/events/
{
  "title": "Clases de matemáticas",
  "description": "Para niños",
  "start_date": "2025-06-10",
  "start_time": "17:00:00",
  "end_date": null,
  "end_time": "19:00:00",
  "recurrence_type": "weekly",
  "recurrence_days_of_week": "2,4",
  "recurrence_end_date": "2025-07-30",
  "capacity": 20,
  "facility": 1
}
```

### En Angular/TypeScript:
```typescript
interface EventFormData {
  title: string;
  start_date: string;    // "YYYY-MM-DD"
  start_time: string;    // "HH:mm:ss"
  end_date?: string | null;
  end_time?: string | null;
  // ... otros campos
}

// Enviar directamente desde el formulario
const eventData: EventFormData = {
  title: formValue.title,
  start_date: formValue.date,
  start_time: formValue.startTime,
  end_time: formValue.endTime,
  // Si no hay end_date, el backend asume mismo día
};
```

---

## 📥 Respuesta de la API (GET)

La API siempre retorna `start_datetime` y `end_datetime`:

```json
{
  "id": 1,
  "title": "Clases de matemáticas",
  "start_datetime": "2025-06-10T17:00:00-04:00",
  "end_datetime": "2025-06-10T19:00:00-04:00",
  "duration": 7200,
  "is_multi_day": false,
  "is_recurring": true,
  // ... otros campos
}
```

### Parsear en Angular:
```typescript
// Separar datetime en fecha y hora para formularios
parseDateTime(datetime: string) {
  const dt = new Date(datetime);
  return {
    date: dt.toISOString().split('T')[0],        // "2025-06-10"
    time: dt.toTimeString().slice(0, 5)          // "17:00"
  };
}

// Uso
const { date, time } = this.parseDateTime(event.start_datetime);
this.form.patchValue({
  startDate: date,
  startTime: time
});
```

---

## 🎯 Casos de Uso

### 1. Evento de un día sin hora de fin
```json
{
  "title": "Completada a beneficio",
  "start_datetime": "2025-11-30T14:00:00",
  "end_datetime": null,
  "capacity": null
}
```
O con campos separados:
```json
{
  "start_date": "2025-11-30",
  "start_time": "14:00:00",
  "end_time": null
}
```

### 2. Evento multi-día
```json
{
  "title": "Acampada de verano",
  "start_datetime": "2025-12-01T12:00:00",
  "end_datetime": "2025-12-03T18:00:00",
  "capacity": 15
}
```
O con campos separados:
```json
{
  "start_date": "2025-12-01",
  "start_time": "12:00:00",
  "end_date": "2025-12-03",
  "end_time": "18:00:00"
}
```

### 3. Evento recurrente
```json
{
  "title": "Clases semanales",
  "start_datetime": "2025-06-10T17:00:00",
  "end_datetime": "2025-06-10T19:00:00",
  "recurrence_type": "weekly",
  "recurrence_days_of_week": "2,4",
  "recurrence_end_date": "2025-07-30"
}
```

---

## 🔍 Filtros en GET /api/events/

```
GET /api/events/?start_from=2025-06-01&start_to=2025-06-30
GET /api/events/?start_from=2025-06-10T17:00:00
GET /api/events/?recurrence_type=weekly
GET /api/events/?is_active=true&is_public=true
```

**Nota:** Los filtros aceptan fecha (`YYYY-MM-DD`) o datetime completo (`YYYY-MM-DDTHH:MM:SS`).

---

## ✅ Ventajas del Diseño Actual

1. **Modelo simple**: 2 campos DateTimeField
2. **Timezone-aware**: Maneja horario de verano de Chile
3. **Queries eficientes**: Un solo campo para filtrar/ordenar
4. **UI flexible**: Soporta ambos formatos (datetime o date+time separados)
5. **Compatible con estándares**: iCalendar, Google Calendar, etc.
6. **Menos bugs**: Validación en un solo lugar (constraint DB)

---

## 🛠️ Recomendación para el Frontend

**Opción A (Simple):** Usar campos separados en el form y enviar `start_date`/`start_time`/`end_date`/`end_time`. El serializer los combina.

**Opción B (Óptimo):** Combinar en el componente y enviar `start_datetime`/`end_datetime` directamente. Más control y claridad.

### Ejemplo completo en Angular:

```typescript
// event-form.component.ts
export class EventFormComponent {
  eventForm = this.fb.group({
    title: ['', Validators.required],
    startDate: ['', Validators.required],
    startTime: ['', Validators.required],
    endDate: [''],
    endTime: ['']
  });

  onSubmit() {
    const formValue = this.eventForm.value;

    // Opción A: Enviar campos separados
    const eventData = {
      ...formValue,
      start_date: formValue.startDate,
      start_time: formValue.startTime,
      end_date: formValue.endDate || null,
      end_time: formValue.endTime || null
    };

    // Opción B: Combinar antes de enviar (recomendado)
    const eventData = {
      title: formValue.title,
      start_datetime: `${formValue.startDate}T${formValue.startTime}:00`,
      end_datetime: formValue.endTime
        ? `${formValue.endDate || formValue.startDate}T${formValue.endTime}:00`
        : null
    };

    this.eventService.createEvent(eventData).subscribe();
  }
}
```

---

## 📝 Notas Técnicas

- **Zona horaria**: Django usa `USE_TZ=True`, los datetime se guardan en UTC y se convierten según `TIME_ZONE='America/Santiago'`
- **Validación**: `end_datetime` debe ser mayor que `start_datetime` (constraint de BD)
- **Campos write-only**: `start_date`, `start_time`, `end_date`, `end_time` solo se usan en POST/PUT/PATCH, no aparecen en GET
- **Duration**: Se calcula automáticamente en segundos, read-only
- **is_multi_day**: True si el evento cruza más de un día calendario

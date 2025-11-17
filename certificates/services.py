"""Servicios para generación y envío de certificados en PDF.

Implementación on-demand: no se almacena el PDF en disco ni en FileField.

Nota: Evitamos importar WeasyPrint a nivel de módulo para que `manage.py check`
pueda ejecutarse incluso si faltan dependencias nativas en el entorno.
"""
from django.template.loader import render_to_string
from django.core.mail import EmailMessage


def generate_certificate_pdf_bytes(certificate) -> tuple[bytes, str]:
    """Generar un PDF en memoria para un Certificate.

    Retorna una tupla (pdf_bytes, file_name). No escribe en disco.
    """
    context = {'cert': certificate}
    # Intento 1: WeasyPrint (HTML → PDF). Importación perezosa.
    try:
        from weasyprint import HTML  # type: ignore
        html_content = (
            render_to_string('certificates/certificate_pdf.html', context)
            if template_exists('certificates/certificate_pdf.html')
            else _fallback_html(context)
        )
        pdf_bytes: bytes = HTML(string=html_content).write_pdf()
        file_name = f'certificate_{certificate.id or "temp"}.pdf'
        return pdf_bytes, file_name
    except Exception:
        # Intento 2: Fallback con ReportLab (no requiere deps nativas de GTK/Pango)
        return _generate_pdf_reportlab(certificate)


def template_exists(template_name: str) -> bool:
    from django.template import engines
    django_engine = engines['django']
    try:
        django_engine.get_template(template_name)
        return True
    except Exception:
        return False


def _fallback_html(ctx: dict) -> str:
    cert = ctx['cert']
    return f"""
    <html><head><meta charset='utf-8'><style>
    body {{ font-family: Arial, sans-serif; margin:40px; }}
    .box {{ border:2px solid #444; padding:30px; border-radius:12px; }}
    h1 {{ text-align:center; margin-bottom:10px; }}
    .meta {{ font-size:12px; color:#666; margin-top:30px; }}
    </style></head><body>
      <div class='box'>
        <h1>Certificado de Residencia</h1>
        <p>Se certifica que <strong>{cert.user.name}</strong> mantiene registro de residencia en el sistema BarrioLink.</p>
        <p>Título: <em>{cert.title}</em></p>
        <p>Emitido el: {cert.issued_at}</p>
        {f"<p>Válido hasta: {cert.expires_at}</p>" if cert.expires_at else ''}
        <p>Estado: {cert.status}</p>
        <div class='meta'>Generado automáticamente por BarrioLink.</div>
      </div>
    </body></html>
    """


def send_certificate_email(certificate, to_email: str):
    """Enviar el certificado por correo generándolo en memoria (sin guardar)."""
    from django.utils import timezone

    pdf_bytes, file_name = generate_certificate_pdf_bytes(certificate)

    context = {
        'cert': certificate,
        'now': timezone.now()
    }

    subject = f"Certificado: {certificate.title}"

    # Intenta usar el template HTML para el email
    if template_exists('certificates/email_certificate.html'):
        html_body = render_to_string('certificates/email_certificate.html', context)
        email = EmailMessage(subject, html_body, to=[to_email])
        email.content_subtype = 'html'  # Importante: indica que el cuerpo es HTML
    else:
        # Fallback a texto plano
        body = "Adjunto encontrarás tu certificado de residencia."
        email = EmailMessage(subject, body, to=[to_email])

    email.attach(file_name, pdf_bytes, 'application/pdf')
    email.send(fail_silently=False)


def _generate_pdf_reportlab(certificate) -> tuple[bytes, str]:
    """Genera un PDF básico usando ReportLab como fallback.

    Útil en Windows cuando faltan dependencias nativas de WeasyPrint.
    """
    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        import textwrap
    except Exception as exc:
        raise RuntimeError(
            'No se pudo usar WeasyPrint ni ReportLab. Instala dependencias de WeasyPrint '
            'o ejecuta: pip install reportlab'
        ) from exc

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    title = 'Certificado de Residencia'
    c.setTitle(title)

    # Encabezado
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(width/2, height - 30*mm, title)

    # Contenido
    c.setFont('Helvetica', 12)
    y = height - 50*mm
    lines = [
        f"Nombre: {getattr(certificate.user, 'name', certificate.user.email)}",
        f"Título: {certificate.title}",
        f"Emitido el: {certificate.issued_at}",
    ]
    if certificate.expires_at:
        lines.append(f"Válido hasta: {certificate.expires_at}")
    lines.append(f"Estado: {certificate.status}")
    if certificate.description:
        lines.append("")
        lines.append("Descripción:")
        desc_lines = textwrap.wrap(certificate.description, width=90)
        lines.extend(desc_lines)

    for line in lines:
        c.drawString(25*mm, y, line)
        y -= 8*mm

    # Pie de página
    c.setFont('Helvetica-Oblique', 10)
    c.drawCentredString(width/2, 20*mm, 'Generado automáticamente por BarrioLink')

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes, f'certificate_{certificate.id or "temp"}.pdf'

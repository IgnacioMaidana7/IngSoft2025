from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
from django.conf import settings
from .serializers import obtener_supermercado_usuario

class TicketPDFGenerator:
    """Generador de tickets de venta en formato PDF"""
    
    def __init__(self, venta):
        self.venta = venta
        self.buffer = BytesIO()
    
    def get_supermercado_info(self):
        """Obtiene la información del supermercado"""
        supermercado = obtener_supermercado_usuario(self.venta.cajero)
        return {
            'nombre': supermercado.nombre_supermercado if hasattr(supermercado, 'nombre_supermercado') else 'SUPERMERCADO',
            'user': supermercado
        }
        
    def generate_ticket(self):
        """Genera el ticket en formato PDF"""
        # Crear documento PDF tamaño ticket (80mm de ancho)
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=(80*mm, 200*mm),  # Ancho fijo de 80mm, largo variable
            rightMargin=2*mm,
            leftMargin=2*mm,
            topMargin=5*mm,
            bottomMargin=5*mm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo para el encabezado
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.black
        )
        
        # Estilo para texto normal
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=3,
            alignment=TA_LEFT
        )
        
        # Estilo para texto centrado
        center_style = ParagraphStyle(
            'CustomCenter',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=3,
            alignment=TA_CENTER
        )
        
        # Estilo para totales
        total_style = ParagraphStyle(
            'CustomTotal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            alignment=TA_RIGHT,
            textColor=colors.black
        )
        
        # Obtener información del supermercado
        supermercado_info = self.get_supermercado_info()
        
        # Contenido del ticket
        story = []
        
        # Encabezado
        story.append(Paragraph(supermercado_info['nombre'].upper(), title_style))
        story.append(Paragraph("TICKET DE VENTA", center_style))
        story.append(Spacer(1, 3*mm))
        
        # Información de la venta
        story.append(Paragraph(f"<b>N° Venta:</b> {self.venta.numero_venta}", normal_style))
        story.append(Paragraph(f"<b>Fecha:</b> {self.venta.fecha_creacion.strftime('%d/%m/%Y %H:%M')}", normal_style))
        
        # Mostrar información del cajero según el tipo
        if self.venta.empleado_cajero:
            # Es una venta realizada por un empleado cajero
            cajero_nombre = f"{self.venta.empleado_cajero.nombre} {self.venta.empleado_cajero.apellido}"
        else:
            # Es una venta realizada por el admin del supermercado
            cajero_nombre = self.venta.cajero.get_full_name() or "Administrador"
        
        story.append(Paragraph(f"<b>Cajero:</b> {cajero_nombre}", normal_style))
        
        if self.venta.cliente_telefono:
            story.append(Paragraph(f"<b>Cliente:</b> {self.venta.cliente_telefono}", normal_style))
        
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("=" * 40, center_style))
        story.append(Spacer(1, 2*mm))
        
        # Items de la venta
        # Crear tabla para los items
        data = [['Producto', 'Cant.', 'P.Unit', 'Subtotal']]
        
        for item in self.venta.items.all():
            data.append([
                item.producto.nombre[:20],  # Truncar nombre si es muy largo
                str(item.cantidad),
                f"${item.precio_unitario}",
                f"${item.subtotal}"
            ])
        
        # Crear tabla
        table = Table(data, colWidths=[35*mm, 10*mm, 15*mm, 15*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 3*mm))
        
        # Totales
        story.append(Paragraph("=" * 40, center_style))
        story.append(Spacer(1, 2*mm))
        
        if self.venta.descuento and float(self.venta.descuento) > 0:
            story.append(Paragraph(f"<b>Subtotal: ${self.venta.subtotal}</b>", total_style))
            story.append(Paragraph(f"<b>Descuento: -${self.venta.descuento}</b>", total_style))
        
        story.append(Paragraph(f"<b>TOTAL: ${self.venta.total}</b>", title_style))
        story.append(Spacer(1, 5*mm))
        
        # Pie del ticket
        story.append(Paragraph("¡Gracias por su compra!", center_style))
        
        if self.venta.observaciones:
            story.append(Spacer(1, 3*mm))
            story.append(Paragraph(f"Observaciones: {self.venta.observaciones}", normal_style))
        
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("=" * 40, center_style))
        
        # Generar PDF
        doc.build(story)
        
        # Volver al inicio del buffer
        self.buffer.seek(0)
        
        return self.buffer
    
    def get_pdf_response(self, filename=None):
        """Retorna una respuesta HTTP con el PDF"""
        if not filename:
            filename = f"ticket_{self.venta.numero_venta}.pdf"
        
        pdf_buffer = self.generate_ticket()
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def save_pdf_file(self, filepath=None):
        """Guarda el PDF en el sistema de archivos"""
        if not filepath:
            # Crear directorio para tickets si no existe
            tickets_dir = os.path.join(settings.MEDIA_ROOT, 'tickets')
            os.makedirs(tickets_dir, exist_ok=True)
            
            filename = f"ticket_{self.venta.numero_venta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(tickets_dir, filename)
        
        pdf_buffer = self.generate_ticket()
        
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        return filepath


def generar_ticket_pdf(venta):
    """Función helper para generar ticket PDF"""
    generator = TicketPDFGenerator(venta)
    return generator.generate_ticket()


def generar_ticket_pdf_response(venta, filename=None):
    """Función helper para generar respuesta HTTP con PDF"""
    generator = TicketPDFGenerator(venta)
    return generator.get_pdf_response(filename)


def guardar_ticket_pdf(venta, filepath=None):
    """Función helper para guardar PDF en archivo"""
    generator = TicketPDFGenerator(venta)
    return generator.save_pdf_file(filepath)
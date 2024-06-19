from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
from flask import render_template, Response, send_file, current_app
from .models import Order, OrderItem, Product, User
from . import db, mail

def create_invoice(order):
    # Fetch necessary data
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    user = User.query.get(order.user_id)
    
    # Create a buffer to hold the PDF data
    pdf_buffer = BytesIO()
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    
    # Sample styles for paragraphs and table
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    subtitle_style = ParagraphStyle('Subtitle', fontSize=14, spaceAfter=12, alignment=1)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4BACC6")),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#D9EAD3")),  # Body background
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#D9EAD3"), colors.white]),  # Alternating rows
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ])
    
    # Adding a logo to the document
    elements = []
    logo_path = '/path/to/your/logo.png'  # Adjust the path to your logo file
    
    if os.path.exists(logo_path):  # Ensure the logo file exists
        logo = Image(logo_path, width=2.5 * inch, height=1 * inch)  # Adjust size as needed
        logo.hAlign = 'CENTER'  # Align the logo at the center
        elements.append(logo)
        elements.append(Spacer(1, 0.2 * inch))  # Add some space below the logo
    
    # Adding a title and other elements
    elements.append(Paragraph("Invoice", title_style))
    elements.append(Spacer(1, 0.2 * inch))  # Add some space after the title
    elements.append(Paragraph(f"Issued on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Customer and Order Information
    elements.append(Paragraph(f"Customer: {user.username}", styles['Heading2']))
    elements.append(Paragraph(f"Order ID: {order.id}", styles['Heading2']))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Define table headers and data
    table_data = [['#', 'Product Name', 'Quantity', 'Unit Price', 'Total Price']]
    for idx, item in enumerate(order_items, start=1):
        table_data.append([
            str(idx),
            item.product.name,
            str(item.quantity),
            f"${item.product.price}",
            f"${item.quantity * item.product.price}"
        ])
    
    # Create the table and apply styling
    table = Table(table_data, hAlign='LEFT', colWidths=[0.5 * inch, 2 * inch, 1 * inch, 1.2 * inch, 1.2 * inch])
    table.setStyle(table_style)
    elements.append(table)
    
    # Footer with page number (added during the build process)
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(200 * mm, 10 * mm, text)  # Positioned 200 mm from the left, and 10 mm from the bottom
    
    # Build the PDF
    pdf.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    
    # Move the buffer's cursor to the beginning
    pdf_buffer.seek(0)
    
    return pdf_buffer

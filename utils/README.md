# Utils App

The utils app provides utility functions and helpers for the UniLib library management system, primarily focused on PDF generation and reporting.

## Features

### PDF Generation
- Professional dashboard report generation
- Role-based report customization
- High-quality PDF formatting with ReportLab
- Statistical data visualization
- Tabular data presentation
- Custom styling and branding

## Components

### PDF Generator
Located in `pdf_generator.py`, this module handles PDF report generation:

#### Main Function
- `generate_dashboard_pdf(context, user_role)`: Generates professional PDF reports

#### Report Types
The PDF generator creates different reports based on user role:

**Admin/Librarian Reports:**
- Executive summary with KPIs
- Recent borrow transactions
- Overdue books requiring attention
- Popular books analysis
- Recent reservations
- System-wide statistics

**Student/Faculty Reports:**
- Personal library metrics
- Borrowing history
- Active borrows
- Pending fines
- Reservation status
- Personal statistics

## PDF Features

### Professional Styling
- Custom color scheme (professional blue, gray, accent colors)
- Professional typography with Helvetica fonts
- Consistent spacing and layout
- Table styling with borders and backgrounds
- Header and footer sections

### Report Sections
1. **Header**: UniLib branding and report title
2. **Metadata**: Generation date, user info, report period
3. **Executive Summary**: Key performance indicators
4. **Detailed Tables**: Role-specific data tables
5. **Footer**: Disclaimer and generation timestamp

### Color Scheme
- **Primary Blue**: #1E40AF (headings, important elements)
- **Secondary Gray**: #374151 (body text)
- **Accent Red**: #DC2626 (overdue items, alerts)
- **Success Green**: #059669 (positive indicators)
- **Light Backgrounds**: Various shades for table rows

## Usage Examples

### Generating a Dashboard PDF
```python
from utils.pdf_generator import generate_dashboard_pdf
from django.http import HttpResponse

def export_dashboard_report(request):
    # Prepare context data
    context = {
        'total_books': Book.objects.count(),
        'total_borrows': Borrow.objects.count(),
        'active_borrows_count': Borrow.objects.filter(is_returned=False).count(),
        'overdue_borrows': Borrow.objects.filter(is_returned=False, due_date__lt=timezone.now().date()),
        'total_fines': Fine.objects.aggregate(total=models.Sum('amount'))['total'] or 0,
        'user': request.user,
        # Add more context data as needed
    }
    
    # Generate PDF
    user_role = request.user.role
    pdf = generate_dashboard_pdf(context, user_role)
    
    # Return as HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="dashboard_report.pdf"'
    return response
```

### Preparing Context for Different Roles
```python
# Admin/Librarian context
admin_context = {
    'total_books': 1500,
    'total_borrows': 5000,
    'active_borrows_count': 150,
    'overdue_borrows': overdue_list,
    'total_fines': 2500.00,
    'total_reservations': 50,
    'active_reservations_count': 30,
    'recent_borrows': recent_borrows_list,
    'popular_books': popular_books_list,
    'recent_reservations': recent_reservations_list,
    'user': request.user,
}

# Student/Faculty context
student_context = {
    'total_borrows': user_borrows.count(),
    'active_borrows_count': user.active_borrows,
    'user_fines': user.unpaid_fines,
    'total_reservations': user.reservations.count(),
    'active_reservations_count': user.active_reservations,
    'user_borrows': user_borrows_list,
    'user_reservations': user_reservations_list,
    'user': request.user,
}
```

## Integration with Other Apps

- **Dashboard**: Provides PDF export functionality for dashboard reports
- **Transactions**: Uses transaction data for report generation
- **Books**: Includes book statistics and popular books data
- **Accounts**: User information for personalization

## Technical Details

### Dependencies
- ReportLab: PDF generation library
- Django: HTTP response handling
- io: Byte buffer management
- datetime: Timestamp generation

### PDF Specifications
- Page Size: A4
- Margins: 0.5 inch (36 points)
- Fonts: Helvetica family
- Colors: Professional hex color codes
- Tables: Styled with borders and backgrounds

### Performance Considerations
- PDF generation is memory-intensive
- Consider caching for frequently generated reports
- Large datasets may impact generation time
- Buffer management prevents memory leaks

## Customization Options

### Styling Customization
Modify color schemes in `pdf_generator.py`:
```python
primary_color = colors.HexColor('#1E40AF')  # Change primary color
secondary_color = colors.HexColor('#374151')  # Change secondary color
```

### Content Customization
Add or modify report sections:
```python
# Add custom sections
elements.append(Paragraph("Custom Section", section_style))
# Add custom data tables
custom_data = [['Column 1', 'Column 2'], ['Data 1', 'Data 2']]
custom_table = Table(custom_data, colWidths=[2*inch, 2*inch])
elements.append(custom_table)
```

### Font Customization
Change fonts for different sections:
```python
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=20,
    fontName='Times-Roman'  # Change font
)
```

## Future Enhancements

- Additional report types (circulation, inventory, user activity)
- Chart and graph integration
- Custom report templates
- Scheduled report generation
- Email report delivery
- Multiple export formats (Excel, CSV)
- Report templates management
- Watermark and branding options
- Digital signature support
- Multi-language support for reports
- Interactive PDF forms
- Report history and archiving

## Best Practices

1. **Memory Management**: Always close buffers after PDF generation
2. **Error Handling**: Wrap PDF generation in try-catch blocks
3. **Data Validation**: Ensure context data is properly formatted
4. **Testing**: Test with various data sizes and edge cases
5. **Performance**: Consider pagination for large datasets
6. **User Experience**: Provide download progress indicators for large reports

## Troubleshooting

### Common Issues
- **Memory Errors**: Reduce data size or implement pagination
- **Font Issues**: Ensure fonts are available on the system
- **Encoding Problems**: Use UTF-8 encoding for special characters
- **Table Overflow**: Adjust column widths or reduce data
- **Image Issues**: Ensure images are properly formatted and sized

### Debug Mode
Enable detailed logging for PDF generation issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
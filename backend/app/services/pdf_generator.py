"""
PDF Generation Service for Project Sentinel
Generates professional audit reports and rebuttal letters
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
from io import BytesIO


class PDFGenerator:
    """Generate professional PDF documents for healthcare administrative workflows"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Use unique names to avoid conflicts with existing styles
        if 'CustomTitle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#06b6d4'),  # cyan-500
                spaceAfter=30,
                alignment=TA_CENTER
            ))
        
        if 'CustomHeading2' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='CustomHeading2',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#0891b2'),  # cyan-600
                spaceAfter=12,
                spaceBefore=12
            ))
        
        if 'CustomBody' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='CustomBody',
                parent=self.styles['BodyText'],
                fontSize=11,
                leading=14,
                alignment=TA_JUSTIFY
            ))
        
        if 'CustomAlert' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='CustomAlert',
                parent=self.styles['BodyText'],
                fontSize=10,
                textColor=colors.HexColor('#ef4444'),  # red-500
                backColor=colors.HexColor('#fee2e2'),  # red-100
                leftIndent=10,
                rightIndent=10
            ))
    
    def generate_audit_report(self, case_data: dict) -> bytes:
        """
        Generate professional audit report PDF
        
        Includes:
        - Patient information
        - SOAP note
        - Clinical entities
        - ICD codes
        - Policy gaps
        - Preemptive alerts
        - Medical necessity score
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch)
        story = []
        
        # Title
        story.append(Paragraph("Clinical Documentation Audit Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Header Info - handle missing patient_name gracefully
        patient_name = case_data.get('patient_name') or 'N/A'
        case_id = case_data.get('case_id') or 'N/A'
        
        header_data = [
            ['Patient Name:', patient_name],
            ['Case ID:', case_id],
            ['Date Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        ]
        
        header_table = Table(header_data, colWidths=[2*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1e293b')),  # slate-800
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#334155')),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Medical Necessity Score
        if case_data.get('medical_necessity_score') is not None:
            score = case_data['medical_necessity_score']
            score_color = colors.HexColor('#10b981') if score >= 0.7 else colors.HexColor('#f59e0b') if score >= 0.4 else colors.HexColor('#ef4444')
            
            story.append(Paragraph("Medical Necessity Score", self.styles['CustomHeading2']))
            score_text = f"<b>{int(score * 100)}%</b> - {'High' if score >= 0.7 else 'Medium' if score >= 0.4 else 'Low'} Medical Necessity"
            story.append(Paragraph(score_text, self.styles['CustomBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Denial Risk
        if case_data.get('denial_risk'):
            risk = case_data['denial_risk'].upper()
            risk_color = colors.HexColor('#ef4444') if risk == 'HIGH' else colors.HexColor('#f59e0b') if risk == 'MEDIUM' else colors.HexColor('#10b981')
            story.append(Paragraph(f"Denial Risk: <font color='{risk_color.hexval()}'>{risk}</font>", self.styles['CustomHeading2']))
            story.append(Spacer(1, 0.2*inch))
        
        # SOAP Note
        soap_note = case_data.get('soap_note', {})
        if soap_note:
            story.append(Paragraph("SOAP Note", self.styles['CustomHeading2']))
            for section in ['subjective', 'objective', 'assessment', 'plan']:
                if soap_note.get(section):
                    story.append(Paragraph(f"<b>{section.capitalize()}:</b>", self.styles['CustomBody']))
                    story.append(Paragraph(soap_note[section], self.styles['CustomBody']))
                    story.append(Spacer(1, 0.1*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # ICD Codes
        icd_codes = case_data.get('icd_codes', [])
        if icd_codes:
            story.append(Paragraph("Suggested ICD Codes", self.styles['CustomHeading2']))
            icd_data = [['Code', 'Description', 'Specificity']]
            for code in icd_codes[:10]:  # Limit to first 10
                icd_data.append([
                    code.get('code', 'N/A'),
                    code.get('description', 'N/A'),
                    code.get('specificity', 'N/A')
                ])
            
            icd_table = Table(icd_data, colWidths=[1*inch, 3.5*inch, 1.5*inch])
            icd_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),  # slate-900
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#334155')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            story.append(icd_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Preemptive Alerts
        alerts = case_data.get('preemptive_alerts', [])
        if alerts:
            story.append(Paragraph("Preemptive Alerts", self.styles['CustomHeading2']))
            for alert in alerts:
                alert_text = f"<b>{alert.get('alert_type', 'Alert').replace('_', ' ')}:</b> {alert.get('message', '')}"
                story.append(Paragraph(alert_text, self.styles['CustomAlert']))
                if alert.get('action_required'):
                    story.append(Paragraph(f"<i>Action Required: {alert['action_required']}</i>", self.styles['CustomBody']))
                story.append(Spacer(1, 0.15*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # Policy Gaps
        gaps = case_data.get('policy_gaps', [])
        if gaps:
            story.append(Paragraph("Policy Gaps Identified", self.styles['CustomHeading2']))
            gap_data = [['Gap', 'Required By Policy', 'Risk Level', 'Suggested Fix']]
            for gap in gaps[:10]:  # Limit to first 10
                gap_data.append([
                    gap.get('gap', 'N/A'),
                    gap.get('required_by_policy', 'N/A'),
                    gap.get('risk_level', 'N/A'),
                    gap.get('suggested_fix', 'N/A')
                ])
            
            gap_table = Table(gap_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 2*inch])
            gap_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#334155')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(gap_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Clinical Entities Summary
        entities = case_data.get('clinical_entities', [])
        if entities:
            story.append(Paragraph("Extracted Clinical Data", self.styles['CustomHeading2']))
            entity_summary = {}
            for entity in entities[:20]:  # Limit to first 20
                entity_type = entity.get('type', 'other')
                if entity_type not in entity_summary:
                    entity_summary[entity_type] = []
                entity_summary[entity_type].append(f"{entity.get('name', 'N/A')}: {entity.get('value', 'N/A')} {entity.get('unit', '')}")
            
            for entity_type, items in entity_summary.items():
                story.append(Paragraph(f"<b>{entity_type.replace('_', ' ').title()}:</b>", self.styles['CustomBody']))
                for item in items[:5]:  # Limit to 5 per type
                    story.append(Paragraph(f"• {item}", self.styles['CustomBody']))
                story.append(Spacer(1, 0.1*inch))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"<i>Generated by Project Sentinel - AI-Powered Healthcare Administrative System</i>",
            self.styles['CustomBody']
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_rebuttal_letter(self, case_data: dict) -> bytes:
        """
        Generate professional rebuttal/appeal letter PDF
        
        Includes:
        - Letterhead
        - Appeal letter body
        - Talking points appendix
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch)
        story = []
        
        # Letterhead
        story.append(Paragraph("APPEAL LETTER", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Date and Patient Info - handle missing patient_name gracefully
        patient_name = case_data.get('patient_name') or 'Patient'
        
        header_info = [
            f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}",
            f"<b>RE:</b> Appeal of Denial - Medical Necessity",
            f"<b>Patient:</b> {patient_name}",
        ]
        
        for info in header_info:
            story.append(Paragraph(info, self.styles['CustomBody']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("_" * 80, self.styles['CustomBody']))
        story.append(Spacer(1, 0.3*inch))
        
        # Rebuttal Letter Body
        rebuttal_letter = case_data.get('rebuttal_letter', '')
        if rebuttal_letter:
            # Clean up markdown if present
            letter_text = rebuttal_letter.replace('#', '').replace('**', '').replace('*', '')
            story.append(Paragraph(letter_text, self.styles['CustomBody']))
        else:
            story.append(Paragraph("No rebuttal letter available.", self.styles['CustomBody']))
        
        story.append(PageBreak())
        
        # Talking Points Appendix
        talking_points = case_data.get('talking_points', [])
        if talking_points:
            story.append(Paragraph("Peer-to-Peer Talking Points", self.styles['CustomHeading2']))
            story.append(Spacer(1, 0.2*inch))
            
            for i, point in enumerate(talking_points, 1):
                story.append(Paragraph(f"<b>{i}.</b> {point}", self.styles['CustomBody']))
                story.append(Spacer(1, 0.15*inch))
        
        # Denial Information
        if case_data.get('denial_reason'):
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("Original Denial Reason", self.styles['CustomHeading2']))
            story.append(Paragraph(case_data['denial_reason'], self.styles['CustomBody']))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"<i>Generated by Project Sentinel - AI-Powered Healthcare Administrative System</i>",
            self.styles['CustomBody']
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

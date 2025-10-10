import streamlit as st
import pandas as pd
import json
import base64
from io import BytesIO, StringIO
from datetime import datetime
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import markdown
import pdfkit
import tempfile
import os
from typing import Dict, List, Any, Optional
from utilities.comps import engineer_competencies, technologist_competencies, technician_competencies
from utilities.error_handling import ErrorHandler, LoadingState


class EnhancedExporter:
    """Enhanced export functionality for multiple formats"""

    def __init__(self):
        self.supported_formats = {
            'docx': 'Microsoft Word Document',
            'pdf': 'PDF Document',
            'json': 'JSON Data',
            'csv': 'CSV Spreadsheet',
            'html': 'HTML Web Page',
            'txt': 'Plain Text',
            'md': 'Markdown'
        }

    def export_report(self, report_data: Dict, format_type: str, include_metadata: bool = True) -> BytesIO:
        """Export report in specified format"""
        format_type = format_type.lower()

        if format_type == 'docx':
            return self._export_to_docx(report_data, include_metadata)
        elif format_type == 'pdf':
            return self._export_to_pdf(report_data, include_metadata)
        elif format_type == 'json':
            return self._export_to_json(report_data, include_metadata)
        elif format_type == 'csv':
            return self._export_to_csv(report_data, include_metadata)
        elif format_type == 'html':
            return self._export_to_html(report_data, include_metadata)
        elif format_type == 'txt':
            return self._export_to_txt(report_data, include_metadata)
        elif format_type == 'md':
            return self._export_to_markdown(report_data, include_metadata)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _export_to_docx(self, report_data: Dict, include_metadata: bool) -> BytesIO:
        """Export to Microsoft Word with enhanced formatting"""
        doc = Document()

        # Set document properties
        doc.core_properties.title = report_data.get('title', 'ERB Report')
        doc.core_properties.author = report_data.get('owner_username', 'Unknown')
        doc.core_properties.comments = f"ERB Professional Report - {datetime.now().strftime('%Y-%m-%d')}"

        # Title page
        title_paragraph = doc.add_paragraph()
        title_run = title_paragraph.add_run("ENGINEER REGISTRATION BOARD")
        title_run.font.size = Inches(0.2)
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph().add_run().add_break()

        main_title = doc.add_paragraph()
        main_title_run = main_title.add_run(report_data.get('title', 'Professional Engineering Report'))
        main_title_run.font.size = Inches(0.3)
        main_title_run.font.bold = True
        main_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph().add_run().add_break()

        # Metadata section
        if include_metadata:
            meta_paragraph = doc.add_paragraph()
            meta_paragraph.add_run(f"Prepared by: {report_data.get('owner_username', 'N/A')}\n")
            meta_paragraph.add_run(f"Professional Level: {report_data.get('profession', 'N/A')}\n")
            meta_paragraph.add_run(f"Submission Date: {datetime.now().strftime('%Y-%m-%d')}\n")
            meta_paragraph.add_run(f"Report Status: {report_data.get('status', 'draft').title()}\n")
            meta_paragraph.add_run(f"Total Competencies: {len(report_data.get('competencies', []))}")

        doc.add_paragraph().add_run().add_break()
        doc.add_paragraph().add_run().add_break()

        # Table of contents
        toc_paragraph = doc.add_paragraph()
        toc_paragraph.add_run("TABLE OF CONTENTS").bold = True
        doc.add_paragraph()

        # Competencies content
        competencies = report_data.get('competencies', [])
        for i, comp in enumerate(competencies, 1):
            # Add to TOC
            toc_item = doc.add_paragraph()
            toc_item.add_run(f"{i}. {comp.get('competency_key', '')}: {comp.get('competency_title', '')}")

            # Competency section
            doc.add_paragraph().add_run().add_break()

            # Competency header
            comp_header = doc.add_paragraph()
            comp_header.add_run(f"Competency {comp.get('competency_key', '')}").bold = True
            comp_header.add_run(f": {comp.get('competency_title', '')}").bold = True

            # Competency response
            response_paragraph = doc.add_paragraph()
            response_paragraph.add_run(comp.get('user_response', 'No response provided'))

        # Add page numbers
        self._add_page_numbers(doc)

        # Save to buffer
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    def _export_to_pdf(self, report_data: Dict, include_metadata: bool) -> BytesIO:
        """Export to PDF format"""
        try:
            # First export to HTML, then convert to PDF
            html_buffer = self._export_to_html(report_data, include_metadata)
            html_content = html_buffer.getvalue().decode('utf-8')

            # Configure PDF options
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }

            # Create temporary file for PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                pdfkit.from_string(html_content, tmp_file.name, options=options)

                # Read back into buffer
                with open(tmp_file.name, 'rb') as f:
                    pdf_buffer = BytesIO(f.read())

                # Clean up
                os.unlink(tmp_file.name)

            pdf_buffer.seek(0)
            return pdf_buffer

        except Exception as e:
            # Fallback to Word export if PDF fails
            st.warning(f"PDF export failed: {str(e)}. Falling back to Word format.")
            return self._export_to_docx(report_data, include_metadata)

    def _export_to_html(self, report_data: Dict, include_metadata: bool) -> BytesIO:
        """Export to HTML format"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{report_data.get('title', 'ERB Report')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                .metadata {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .competency {{ margin-bottom: 30px; border-left: 4px solid #007cba; padding-left: 15px; }}
                .competency-header {{ font-weight: bold; color: #007cba; margin-bottom: 10px; }}
                .response {{ background: white; padding: 15px; border-radius: 3px; }}
                .footer {{ margin-top: 50px; text-align: center; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ENGINEER REGISTRATION BOARD</h1>
                <h2>{report_data.get('title', 'Professional Engineering Report')}</h2>
            </div>
        """

        if include_metadata:
            html_content += f"""
            <div class="metadata">
                <p><strong>Prepared by:</strong> {report_data.get('owner_username', 'N/A')}</p>
                <p><strong>Professional Level:</strong> {report_data.get('profession', 'N/A')}</p>
                <p><strong>Submission Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                <p><strong>Report Status:</strong> {report_data.get('status', 'draft').title()}</p>
                <p><strong>Total Competencies:</strong> {len(report_data.get('competencies', []))}</p>
            </div>
            """

        competencies = report_data.get('competencies', [])
        for comp in competencies:
            html_content += f"""
            <div class="competency">
                <div class="competency-header">
                    Competency {comp.get('competency_key', '')}: {comp.get('competency_title', '')}
                </div>
                <div class="response">
                    {comp.get('user_response', 'No response provided').replace(chr(10), '<br>')}
                </div>
            </div>
            """

        html_content += f"""
            <div class="footer">
                <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
                <p>ERB Engineering Report Deck</p>
            </div>
        </body>
        </html>
        """

        buffer = BytesIO()
        buffer.write(html_content.encode('utf-8'))
        buffer.seek(0)
        return buffer

    def _export_to_json(self, report_data: Dict, include_metadata: bool) -> BytesIO:
        """Export to JSON format"""
        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "format": "JSON",
                "version": "2.0"
            },
            "report_data": report_data
        }

        if not include_metadata:
            # Remove sensitive or unnecessary metadata
            if 'report_data' in export_data and 'owner_id' in export_data['report_data']:
                del export_data['report_data']['owner_id']

        buffer = BytesIO()
        buffer.write(json.dumps(export_data, indent=2, ensure_ascii=False).encode('utf-8'))
        buffer.seek(0)
        return buffer

    def _export_to_csv(self, report_data: Dict, include_metadata: bool) -> BytesIO:
        """Export to CSV format"""
        competencies = report_data.get('competencies', [])

        # Create DataFrame
        data = []
        for comp in competencies:
            data.append({
                'competency_key': comp.get('competency_key', ''),
                'competency_title': comp.get('competency_title', ''),
                'user_response': comp.get('user_response', ''),
                'word_count': len(comp.get('user_response', '').split())
            })

        df = pd.DataFrame(data)

        buffer = BytesIO()
        df.to_csv(buffer, index=False, encoding='utf-8')
        buffer.seek(0)
        return buffer

    def _export_to_txt(self, report_data: Dict, include_metadata: bool) -> BytesIO:
        """Export to plain text format"""
        text_content = f"ERB PROFESSIONAL REPORT\n"
        text_content += "=" * 50 + "\n\n"
        text_content += f"Title: {report_data.get('title', 'N/A')}\n"

        if include_metadata:
            text_content += f"Author: {report_data.get('owner_username', 'N/A')}\n"
            text_content += f"Professional Level: {report_data.get('profession', 'N/A')}\n"
            text_content += f"Status: {report_data.get('status', 'draft').title()}\n"
            text_content += f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        text_content += "COMPETENCIES\n"
        text_content += "-" * 50 + "\n\n"

        competencies = report_data.get('competencies', [])
        for comp in competencies:
            text_content += f"COMPETENCY {comp.get('competency_key', '')}\n"
            text_content += f"Title: {comp.get('competency_title', '')}\n"
            text_content += f"Response:\n{comp.get('user_response', 'No response provided')}\n"
            text_content += "-" * 30 + "\n\n"

        buffer = BytesIO()
        buffer.write(text_content.encode('utf-8'))
        buffer.seek(0)
        return buffer

    def _export_to_markdown(self, report_data: Dict, include_metadata: bool) -> BytesIO:
        """Export to Markdown format"""
        md_content = f"# ERB Professional Report\n\n"
        md_content += f"## {report_data.get('title', 'Professional Engineering Report')}\n\n"

        if include_metadata:
            md_content += "### Metadata\n\n"
            md_content += f"- **Author:** {report_data.get('owner_username', 'N/A')}\n"
            md_content += f"- **Professional Level:** {report_data.get('profession', 'N/A')}\n"
            md_content += f"- **Status:** {report_data.get('status', 'draft').title()}\n"
            md_content += f"- **Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            md_content += f"- **Total Competencies:** {len(report_data.get('competencies', []))}\n\n"

        md_content += "## Competencies\n\n"

        competencies = report_data.get('competencies', [])
        for comp in competencies:
            md_content += f"### Competency {comp.get('competency_key', '')}\n\n"
            md_content += f"**Title:** {comp.get('competency_title', '')}\n\n"
            md_content += f"**Response:**\n\n{comp.get('user_response', 'No response provided')}\n\n"
            md_content += "---\n\n"

        buffer = BytesIO()
        buffer.write(md_content.encode('utf-8'))
        buffer.seek(0)
        return buffer

    def _add_page_numbers(self, doc):
        """Add page numbers to Word document"""
        section = doc.sections[0]
        footer = section.footer

        # Remove existing footer paragraphs
        for paragraph in footer.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)

        # Add new footer with page number
        footer_paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        footer_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Create page number field
        fld_char1 = OxmlElement('w:fldChar')
        fld_char1.set(qn('w:fldCharType'), 'begin')

        instr_text = OxmlElement('w:instrText')
        instr_text.set(qn('xml:space'), 'preserve')
        instr_text.text = 'PAGE'

        fld_char2 = OxmlElement('w:fldChar')
        fld_char2.set(qn('w:fldCharType'), 'end')

        footer_paragraph._element.append(fld_char1)
        footer_paragraph._element.append(instr_text)
        footer_paragraph._element.append(fld_char2)

    def get_download_button(self, buffer: BytesIO, file_name: str, button_text: str, mime_type: str):
        """Create a download button for the exported file"""
        b64 = base64.b64encode(buffer.getvalue()).decode()
        href = f'<a href="data:{mime_type};base64,{b64}" download="{file_name}" style="text-decoration: none;">{button_text}</a>'
        return href


class ERBIntegration:
    """Integration with ERB submission systems"""

    def __init__(self):
        self.erb_portal_url = "https://erb.org.bw"  # Example URL

    def validate_erb_submission(self, report_data: Dict) -> Dict[str, Any]:
        """Validate report against ERB submission requirements"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }

        competencies = report_data.get('competencies', [])

        # Check minimum competencies
        if len(competencies) < 5:
            validation_result['warnings'].append("Less than 5 competencies completed - consider adding more")

        # Check word counts
        total_words = 0
        for comp in competencies:
            response = comp.get('user_response', '')
            word_count = len(response.split())
            total_words += word_count

            if word_count < 50:
                validation_result['warnings'].append(
                    f"Competency {comp.get('competency_key')} has low word count ({word_count} words)")

        if total_words < 1000:
            validation_result['warnings'].append(
                f"Total word count ({total_words}) is below recommended minimum of 1000 words")

        # Check for required competencies based on profession
        profession = report_data.get('profession', '').lower()
        required_competencies = self._get_required_competencies(profession)

        completed_keys = [comp.get('competency_key', '') for comp in competencies]
        missing_required = [comp for comp in required_competencies if comp not in completed_keys]

        if missing_required:
            validation_result['errors'].append(f"Missing required competencies: {', '.join(missing_required)}")
            validation_result['is_valid'] = False

        # Check response quality (basic checks)
        for comp in competencies:
            response = comp.get('user_response', '')
            if len(response.strip()) < 10:
                validation_result['errors'].append(f"Competency {comp.get('competency_key')} has very short response")
                validation_result['is_valid'] = False

        return validation_result

    def _get_required_competencies(self, profession: str) -> List[str]:
        """Get required competencies for each profession"""
        requirements = {
            'engineer': ['A1_1', 'A2_1', 'B1_1', 'C1_1', 'D1_1', 'E1_1'],
            'technologist': ['A1_1', 'A2_1', 'B1_1', 'C1_1', 'D1_1'],
            'technician': ['A1_1', 'B1_1', 'C1_1', 'D1_1']
        }
        return requirements.get(profession, [])

    def generate_erb_submission_package(self, report_data: Dict) -> Dict[str, BytesIO]:
        """Generate complete submission package for ERB"""
        exporter = EnhancedExporter()

        package = {
            'main_report_docx': exporter.export_report(report_data, 'docx'),
            'main_report_pdf': exporter.export_report(report_data, 'pdf'),
            'data_export_json': exporter.export_report(report_data, 'json'),
            'competency_matrix_csv': self._generate_competency_matrix(report_data)
        }

        return package

    def _generate_competency_matrix(self, report_data: Dict) -> BytesIO:
        """Generate competency matrix spreadsheet"""
        competencies = report_data.get('competencies', [])

        matrix_data = []
        for comp in competencies:
            matrix_data.append({
                'Competency Code': comp.get('competency_key', ''),
                'Competency Title': comp.get('competency_title', ''),
                'Word Count': len(comp.get('user_response', '').split()),
                'Completion Status': 'Completed',
                'Review Notes': '',
                'ERB Alignment': 'To be assessed'
            })

        df = pd.DataFrame(matrix_data)
        buffer = BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer


def show_export_interface(report_data: Dict, profession: str):
    """Enhanced export interface with multiple format options"""
    st.subheader("📤 Enhanced Export Options")

    exporter = EnhancedExporter()
    integration = ERBIntegration()

    # Export format selection
    col1, col2 = st.columns([2, 1])

    with col1:
        selected_format = st.selectbox(
            "Export Format",
            options=list(exporter.supported_formats.keys()),
            format_func=lambda x: exporter.supported_formats[x]
        )

    with col2:
        include_metadata = st.checkbox("Include Metadata", value=True)

    # Additional options based on format
    if selected_format in ['docx', 'pdf']:
        st.checkbox("Include Table of Contents", value=True, key="include_toc")
        st.checkbox("Include Page Numbers", value=True, key="include_pages")

    # Validation before export
    if st.button("🔍 Validate for ERB Submission", type="secondary"):
        with st.spinner("Validating report..."):
            validation = integration.validate_erb_submission(report_data)

            if validation['is_valid']:
                st.success("✅ Report meets basic ERB submission requirements!")
            else:
                st.error("❌ Report has validation issues:")
                for error in validation['errors']:
                    st.error(f" - {error}")

            if validation['warnings']:
                st.warning("⚠️ Recommendations:")
                for warning in validation['warnings']:
                    st.warning(f" - {warning}")

            if validation['suggestions']:
                st.info("💡 Suggestions:")
                for suggestion in validation['suggestions']:
                    st.info(f" - {suggestion}")

    st.markdown("---")

    # Main export button
    if st.button("🚀 Generate Export", type="primary", use_container_width=True):
        with st.spinner(f"Generating {selected_format.upper()} export..."):
            try:
                buffer = exporter.export_report(report_data, selected_format, include_metadata)

                # Determine file extension and MIME type
                extensions = {
                    'docx': ('docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                    'pdf': ('pdf', 'application/pdf'),
                    'json': ('json', 'application/json'),
                    'csv': ('csv', 'text/csv'),
                    'html': ('html', 'text/html'),
                    'txt': ('txt', 'text/plain'),
                    'md': ('md', 'text/markdown')
                }

                ext, mime_type = extensions[selected_format]
                file_name = f"erb_report_{datetime.now().strftime('%Y%m%d_%H%M')}.{ext}"

                # Create download button
                st.success("✅ Export generated successfully!")

                st.download_button(
                    label=f"📥 Download {exporter.supported_formats[selected_format]}",
                    data=buffer.getvalue(),
                    file_name=file_name,
                    mime=mime_type,
                    use_container_width=True
                )

            except Exception as e:
                ErrorHandler.show_error(f"Export failed: {str(e)}")

    # ERB Submission Package
    st.markdown("---")
    st.subheader("🎒 ERB Submission Package")

    st.info("Generate a complete package for ERB submission including all required documents.")

    if st.button("📦 Generate Submission Package", use_container_width=True):
        with st.spinner("Creating ERB submission package..."):
            try:
                package = integration.generate_erb_submission_package(report_data)

                st.success("✅ Submission package created!")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.download_button(
                        "📄 Main Report (DOCX)",
                        data=package['main_report_docx'].getvalue(),
                        file_name="erb_main_report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

                with col2:
                    st.download_button(
                        "📊 Main Report (PDF)",
                        data=package['main_report_pdf'].getvalue(),
                        file_name="erb_main_report.pdf",
                        mime="application/pdf"
                    )

                with col3:
                    st.download_button(
                        "📋 Data Export (JSON)",
                        data=package['data_export_json'].getvalue(),
                        file_name="erb_data_export.json",
                        mime="application/json"
                    )

                with col4:
                    st.download_button(
                        "📈 Competency Matrix (CSV)",
                        data=package['competency_matrix_csv'].getvalue(),
                        file_name="erb_competency_matrix.csv",
                        mime="text/csv"
                    )

            except Exception as e:
                ErrorHandler.show_error(f"Package creation failed: {str(e)}")


# Integration with existing create_report.py
def enhanced_export_section(responses: dict, competency_sections: dict, profession: str):
    """Enhanced export section for the create report page"""
    # Compile report data
    report_data = {
        'title': f"{profession} ERB Report",
        'profession': profession,
        'status': responses.get('_status', 'draft'),
        'competencies': [],
        'exported_at': datetime.now().isoformat()
    }

    # Add competencies
    for key, data in responses.items():
        if key != '_status' and key in competency_sections:
            report_data['competencies'].append({
                'competency_key': key,
                'competency_title': competency_sections[key]['title'],
                'user_response': data.get('response', ''),
                'indicators': competency_sections[key].get('indicators', [])
            })

    # Show export interface
    show_export_interface(report_data, profession)
from typing import Dict, List
from docx import Document
import logging

logger = logging.getLogger(__name__)

class WordParserService:
    def __init__(self):
        """
        Initializes the WordParserService.
        The python-docx library will be used for parsing.
        """
        pass

    def extract_text_content(self, file_path: str) -> Dict:
        """
        Extracts the full text content, basic structural information, and metadata from a Word document.
        Structure information might include paragraph styles (e.g., heading levels).
        Metadata includes properties like author, title (if set in doc properties).
        """
        try:
            document = Document(file_path)

            full_text = []
            structure_info = [] # List of tuples or dicts, e.g., (text, style_name)

            for para in document.paragraphs:
                full_text.append(para.text)
                # Attempt to capture some structural info based on styles
                # This is a basic example; more sophisticated style analysis might be needed
                style_name = para.style.name
                if style_name.startswith('Heading'):
                    structure_info.append({"level": style_name, "text": para.text[:100]}) # Store heading level and start of text
                elif para.text.strip(): # Avoid empty paragraphs unless they signify something
                    structure_info.append({"style": style_name, "text_snippet": para.text[:100]})

            doc_text = "\n".join(full_text)

            # Extract core properties (metadata)
            core_props = document.core_properties
            metadata = {
                "author": core_props.author,
                "category": core_props.category,
                "comments": core_props.comments,
                "content_status": core_props.content_status,
                "created": core_props.created.isoformat() if core_props.created else None,
                "identifier": core_props.identifier,
                "keywords": core_props.keywords,
                "language": core_props.language,
                "last_modified_by": core_props.last_modified_by,
                "last_printed": core_props.last_printed.isoformat() if core_props.last_printed else None,
                "modified": core_props.modified.isoformat() if core_props.modified else None,
                "revision": core_props.revision,
                "subject": core_props.subject,
                "title": core_props.title,
                "version": core_props.version,
            }
            # Filter out None values from metadata for cleaner output
            metadata = {k: v for k, v in metadata.items() if v}


            return {
                "text": doc_text,
                "structure": structure_info, # This is a simplified representation
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error extracting text content from {file_path}: {e}")
            # Consider how to handle errors: raise, return specific error dict, etc.
            # For now, re-raising to make it visible, or return an error structure
            raise HTTPException(status_code=500, detail=f"Failed to parse Word document: {e}") from e

    def extract_tables(self, file_path: str) -> List[Dict]:
        """
        Extracts all tables from the Word document.
        Each table is converted into a list of lists, representing rows and cells.
        Additional metadata per table could be added (e.g., preceding paragraph text as a potential caption).
        """
        try:
            document = Document(file_path)
            tables_data = []
            for i, table in enumerate(document.tables):
                table_content = []
                for row in table.rows:
                    row_content = [cell.text.strip() for cell in row.cells]
                    table_content.append(row_content)

                # Try to find a caption or context for the table
                # This is heuristic: look at the paragraph immediately before the table element if possible
                # python-docx doesn't directly link tables to preceding paragraphs in a simple way through the table object itself.
                # This would require iterating through document body elements. For now, just table data.
                tables_data.append({
                    "table_index": i,
                    "rows": len(table.rows),
                    "columns": len(table.columns) if len(table.rows) > 0 else 0,
                    "data": table_content
                })
            return tables_data
        except Exception as e:
            logger.error(f"Error extracting tables from {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to extract tables from Word document: {e}") from e

    def extract_headers_and_sections(self, file_path: str) -> Dict:
        """
        Extracts document章节结构 (headers and sections).
        This focuses on paragraphs styled as headings.
        The output could be a hierarchical structure if nesting is inferred,
        or a flat list of identified headers.
        """
        try:
            document = Document(file_path)
            headers = []
            current_section_text = []
            # This is a simplified approach. Real section extraction can be complex.
            # It assumes headings define sections.

            # For a more structured output, one might try to infer hierarchy based on heading levels (e.g., Heading 1, Heading 2)
            # This example will list all paragraphs identified as headings.
            for para in document.paragraphs:
                # Common convention for heading styles in python-docx
                if para.style.name.startswith('Heading'):
                    headers.append({
                        "level": para.style.name, # e.g., "Heading 1", "Heading 2"
                        "text": para.text.strip(),
                        # "paragraph_index": i # if we were iterating with index
                    })
            # This is a basic list of headers. True section content extraction is more involved.
            return {"headers": headers}
        except Exception as e:
            logger.error(f"Error extracting headers and sections from {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to extract headers/sections from Word document: {e}") from e

    def extract_images_info(self, file_path: str) -> List[Dict]:
        """
        Extracts information about images in the document.
        python-docx can access images and some of their properties.
        Extracting "description text" often means looking at surrounding paragraphs or alt text if available.
        Note: python-docx's ability to get image position is limited. Alt text is also not directly straightforward for all image types.
        This implementation will focus on extracting images themselves and their basic properties.
        """
        try:
            document = Document(file_path)
            images_info = []

            # Images in Word documents can be inline or floating.
            # python-docx primarily handles inline shapes directly in paragraphs.
            # Accessing images within shapes or complex layouts can be more challenging.

            # Iterate through inline shapes in paragraphs
            for i, para in enumerate(document.paragraphs):
                for run in para.runs:
                    for inline_shape in run.element.xpath('.//w:drawing'): # Check for drawings
                        # This XPath attempts to find common ways images are embedded.
                        # It might need refinement based on actual document structures.
                        # Getting descriptive text often means checking 'alt text' (descr attribute in some XML elements)
                        # or nearby paragraph text.

                        # Example for trying to get an alt text if available (might not always work)
                        alt_text_nodes = inline_shape.xpath('.//wp:docPr/@descr')
                        alt_text = alt_text_nodes[0] if alt_text_nodes else "N/A"

                        # This part is complex because images can be embedded in various ways.
                        # `python-docx` doesn't provide a high-level "get all images with captions" API.
                        # We'd typically save the image and reference its filename.
                        # For now, we'll just note its existence and any alt text.

                        # To extract actual image bytes, one would need to access `rId` and then get parts from the package.
                        # For example, if `blip_fill` element is found:
                        blip_fills = inline_shape.xpath('.//a:blip/@r:embed')
                        if blip_fills:
                            rId = blip_fills[0]
                            image_part = document.part.related_parts[rId]
                            image_filename = image_part.partname.split('/')[-1]
                            # image_bytes = image_part.blob # Actual image data

                            images_info.append({
                                "image_rId": rId,
                                "filename_in_docx": image_filename,
                                "paragraph_index": i, # Paragraph where the image anchor might be
                                "alt_text": alt_text,
                                # "caption_guess": "heuristic to find nearby text" # very complex
                            })

            # This is a very basic image info extraction. Real-world scenarios are more complex.
            # Especially regarding captions and precise positioning.
            return images_info
        except Exception as e:
            logger.error(f"Error extracting images info from {file_path}: {e}")
            # It's often better to return empty list or partial results if some images fail
            # than to fail the whole process. For now, let's be strict.
            raise HTTPException(status_code=500, detail=f"Failed to extract image info from Word document: {e}") from e

# Example of how to use (mainly for testing or direct invocation)
if __name__ == '__main__':
    # This section would require a sample .docx file to test.
    # For example, create a dummy 'test.docx' file.
    # Since I can't create files directly here for testing the `if __name__ == '__main__':` block,
    # this part is illustrative.

    # To test this, you would:
    # 1. Ensure python-docx is installed (`pip install python-docx`).
    # 2. Have a sample .docx file (e.g., `sample.docx`) in the same directory or provide a full path.
    # 3. Uncomment and run this script.

    # Example (assuming 'sample.docx' exists):
    # parser = WordParserService()
    # file_path = 'sample.docx' # Replace with your .docx file path

    # try:
    #     print(f"--- Extracting Text Content from {file_path} ---")
    #     content = parser.extract_text_content(file_path)
    #     print(f"Text: {content['text'][:200]}...") # Print first 200 chars
    #     print(f"Structure (first 3 items): {content['structure'][:3]}")
    #     print(f"Metadata: {content['metadata']}")
    # except Exception as e:
    #     print(f"Error extracting text: {e}")

    # try:
    #     print(f"\n--- Extracting Tables from {file_path} ---")
    #     tables = parser.extract_tables(file_path)
    #     if tables:
    #         for i, table_data in enumerate(tables):
    #             print(f"Table {i}: {table_data['rows']} rows, {table_data['columns']} columns")
    #             # print(f"Data (first few rows): {table_data['data'][:2]}")
    #     else:
    #         print("No tables found.")
    # except Exception as e:
    #     print(f"Error extracting tables: {e}")

    # try:
    #     print(f"\n--- Extracting Headers and Sections from {file_path} ---")
    #     sections = parser.extract_headers_and_sections(file_path)
    #     if sections.get('headers'):
    #         print("Identified Headers:")
    #         for header in sections['headers'][:5]: # Print first 5 headers
    #             print(f"  Level: {header['level']}, Text: {header['text']}")
    #     else:
    #         print("No headers found or error in extraction.")
    # except Exception as e:
    #     print(f"Error extracting headers/sections: {e}")

    # try:
    #     print(f"\n--- Extracting Images Info from {file_path} ---")
    #     images = parser.extract_images_info(file_path)
    #     if images:
    #         print(f"Found {len(images)} image references:")
    #         for img_info in images[:3]: # Print info for first 3 images
    #             print(f"  Image rId: {img_info['image_rId']}, Filename in docx: {img_info['filename_in_docx']}, Alt text: {img_info['alt_text']}")
    #     else:
    #         print("No image references found or error in extraction.")
    # except Exception as e:
    #     print(f"Error extracting images info: {e}")
    pass

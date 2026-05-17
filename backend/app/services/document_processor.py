from io import BytesIO
from pypdf import PdfReader
from docx import Document

class DocumentProcessor:
    def extract_text(self, filename: str, file_bytes: bytes) -> str:
        filename_lower = filename.lower()

        if filename_lower.endswith(".pdf"):
            return self._extract_pdf(file_bytes)

        if filename_lower.endswith(".docx"):
            return self._extract_docx(file_bytes)

        if filename_lower.endswith(".txt"):
            return self._extract_txt(file_bytes)

        raise ValueError("Unsupported file type. Only PDF, DOCX, and TXT are supported.")
    
    def _extract_pdf(self, file_bytes: bytes) -> str:
        reader = PdfReader(BytesIO(file_bytes))
        pages = []

        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)

        return "\n".join(pages).strip()
    
    def _extract_docx(self, file_bytes: bytes) -> str:
        doc = Document(BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs]).strip()

    def _extract_txt(self, file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8", errors="ignore").strip()

    def chunk_text(self, text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
        text = text.strip()

        if not text:
            return []

        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= chunk_size:
                current_chunk += "\n" + paragraph if current_chunk else paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                overlap_text = current_chunk[-overlap:] if current_chunk else ""
                current_chunk = overlap_text + "\n" + paragraph

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
    
document_processor = DocumentProcessor()
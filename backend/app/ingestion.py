import io
from pypdf import PdfReader

def load_document(file_obj, filename: str) -> list[dict]:
    """
    Reads a text or PDF document from a file-like object.
    Returns a list of dictionaries, where each dict represents a page (or the whole doc for txt)
    and contains the text and metadata (including page number).
    """
    pages_data = []
    
    if filename.lower().endswith(".pdf"):
        # pypdf can read directly from a file-like object (BytesIO or SpooledTemporaryFile)
        reader = PdfReader(file_obj)
        for i, page in enumerate(reader.pages):
            extracted = page.extract_text()
            if extracted and extracted.strip():
                pages_data.append({
                    "text": extracted + "\n",
                    "metadata": {"page": i + 1}
                })
    else:
        # For text files, read and decode
        text = file_obj.read().decode("utf-8")
        if text and text.strip():
            pages_data.append({
                "text": text,
                "metadata": {"page": 1} # Default to page 1 for flat text files
            })
                
    return pages_data

def chunk_text(pages: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """
    Recursively splits text into chunks while preserving semantic boundaries 
    and carrying over the page metadata from the source dictionary.
    """
    if not pages:
        return []

    separators = ["\n\n", "\n", ". ", " ", ""]
    final_chunks = []
    
    def split_with_overlap(txt: str, sep_index: int) -> list[str]:
        if len(txt) <= chunk_size:
            return [txt]
            
        if sep_index >= len(separators) - 1:
            chunks = []
            start = 0
            while start < len(txt):
                end = min(start + chunk_size, len(txt))
                chunks.append(txt[start:end])
                if end >= len(txt): break
                start += (chunk_size - overlap)
            return chunks

        separator = separators[sep_index]
        splits = txt.split(separator)
        splits = [s + separator for s in splits[:-1]] + [splits[-1]]
            
        if len(splits) == 1 and len(splits[0]) > chunk_size:
            return split_with_overlap(txt, sep_index + 1)

        chunks = []
        current_chunk = []
        current_len = 0
        
        for split in splits:
            if len(split) > chunk_size:
                if current_chunk:
                    chunks.append("".join(current_chunk).strip())
                    current_chunk = []
                    current_len = 0
                chunks.extend(split_with_overlap(split, sep_index + 1))
                continue
                
            if current_len + len(split) > chunk_size and current_chunk:
                chunks.append("".join(current_chunk).strip())
                overlap_chunk = []
                overlap_len = 0
                for item in reversed(current_chunk):
                    if overlap_len + len(item) <= overlap:
                        overlap_chunk.insert(0, item)
                        overlap_len += len(item)
                    else:
                        break
                current_chunk = overlap_chunk
                current_len = overlap_len

            current_chunk.append(split)
            current_len += len(split)

        if current_chunk:
            final_str = "".join(current_chunk).strip()
            if final_str:
                chunks.append(final_str)
            
        return chunks

    for page_data in pages:
        text = page_data.get("text", "")
        base_metadata = page_data.get("metadata", {})
        
        raw_chunks = split_with_overlap(text, 0)
        
        for chunk in raw_chunks:
            # We copy the metadata to avoid mutation across chunks
            final_chunks.append({
                "text": chunk,
                "metadata": dict(base_metadata)
            })

    return final_chunks

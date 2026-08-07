import os

def load_document(filepath: str) -> str:
    """Reads a text document from the filesystem."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Document not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Recursively splits text into chunks, preferring semantic boundaries 
    (paragraphs, sentences, words) while respecting chunk_size and overlap.
    """
    if not text:
        return []

    separators = ["\n\n", "\n", ". ", " ", ""]
    
    def split_with_overlap(txt: str, sep_index: int) -> list[str]:
        if len(txt) <= chunk_size:
            return [txt]
            
        if sep_index >= len(separators) - 1:
            # Fallback: naive character chunking if we run out of separators
            chunks = []
            start = 0
            while start < len(txt):
                end = min(start + chunk_size, len(txt))
                chunks.append(txt[start:end])
                if end >= len(txt): break
                start += (chunk_size - overlap)
            return chunks

        separator = separators[sep_index]
        
        # Split text by current separator and preserve the separator
        splits = txt.split(separator)
        splits = [s + separator for s in splits[:-1]] + [splits[-1]]
            
        if len(splits) == 1 and len(splits[0]) > chunk_size:
            # Separator wasn't found or didn't break text up enough, try next one
            return split_with_overlap(txt, sep_index + 1)

        # Merge splits into chunks
        chunks = []
        current_chunk = []
        current_len = 0
        
        for split in splits:
            if len(split) > chunk_size:
                # If a single split is larger than chunk_size, yield current chunk 
                if current_chunk:
                    chunks.append("".join(current_chunk).strip())
                    current_chunk = []
                    current_len = 0
                
                # Recursively process the large split
                chunks.extend(split_with_overlap(split, sep_index + 1))
                continue
                
            if current_len + len(split) > chunk_size and current_chunk:
                # Current chunk is full, yield it
                chunks.append("".join(current_chunk).strip())
                
                # Setup overlap for the next chunk
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

    return split_with_overlap(text, 0)

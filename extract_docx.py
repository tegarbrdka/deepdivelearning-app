import zipfile
import xml.etree.ElementTree as ET

def extract_text_from_docx(docx_path):
    # Namespace for Word XML
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    try:
        with zipfile.ZipFile(docx_path) as docx:
            # document.xml contains the main text
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Extract paragraphs
            paragraphs = []
            for p in tree.findall('.//w:p', ns):
                texts = []
                for t in p.findall('.//w:t', ns):
                    if t.text:
                        texts.append(t.text)
                if texts:
                    paragraphs.append(''.join(texts))
            return '\n'.join(paragraphs)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    file_path = r"F:\educlasify\ICETT2026_Hanif_Deep Dive Learning DSS (1).docx"
    text = extract_text_from_docx(file_path)
    
    with open("F:\\educlasify\\extracted_docx_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Ekstraksi selesai.")

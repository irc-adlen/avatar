import fitz  # PyMuPDF
import json

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Extraction du texte en préservant l'ordre de lecture
        text = page.get_text("text")
        # Nettoyage basique
        clean_text = " ".join(text.split())
        full_text.append(f"--- PAGE {page_num + 1} ---\n{clean_text}")
    
    return "\n\n".join(full_text)

# Utilisation
pdf_files = ["C:\\Users\\PlanetDestroyer\\Documents\\Code\\avatar_bozon_cherif_gros\\LLM\\Plaquette-Alpha-2025-2026.pdf", "C:\\Users\\PlanetDestroyer\\Documents\\Code\\avatar_bozon_cherif_gros\\LLM\\CPE-LYON_plaquette_2023_2024.pdf"]
all_data = ""

for file in pdf_files:
    print(f"Extraction de {file}...")
    all_data += extract_text_from_pdf(file)

# Sauvegarde pour que vous puissiez copier le texte
with open("texte_extrait.txt", "w", encoding="utf-8") as f:
    f.write(all_data)

print("Extraction terminée. Le texte est dans 'texte_extrait.txt'")
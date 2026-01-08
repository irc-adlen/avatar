import fitz  # PyMuPDF
import wikipediaapi
import os

# Configuration
pdf_files = ["CPE-LYON_plaquette_2023_2024.pdf", "Plaquette-Alpha-2025-2026.pdf"]
output_folder = "source_texts"
os.makedirs(output_folder, exist_ok=True)

def extract_from_pdf(pdf_path):
    print(f"Extraction de : {pdf_path}...")
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    
    filename = os.path.basename(pdf_path).replace(".pdf", ".txt")
    with open(os.path.join(output_folder, filename), "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"Sauvegardé : {filename}")

def extract_from_wikipedia(page_name):
    print(f"Extraction de Wikipedia : {page_name}...")
    # User_agent est obligatoire pour l'API Wikipedia
    wiki = wikipediaapi.Wikipedia(user_agent="CPE_Lyon_Assistant_Project (contact@example.com)", language='fr')
    page = wiki.page(page_name)
    
    if page.exists():
        with open(os.path.join(output_folder, "wikipedia_cpe.txt"), "w", encoding="utf-8") as f:
            f.write(page.text)
        print("Sauvegardé : wikipedia_cpe.txt")
    else:
        print("La page Wikipedia n'a pas été trouvée.")

# Exécution
# for pdf in pdf_files:
#     if os.path.exists(pdf):
#         extract_from_pdf(pdf)

extract_from_wikipedia("École supérieure de chimie, physique, électronique de Lyon")
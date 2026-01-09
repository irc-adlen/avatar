import fitz  # PyMuPDF
import os
from pathlib import Path
import pymupdf4llm

def pdf_to_datasets(input_folder, output_folder_txt, output_folder_md):
    # Créer le dossier de sortie s'il n'existe pas
    if not os.path.exists(output_folder_txt):
        os.makedirs(output_folder_txt)
        print(f"Dossier '{output_folder_txt}' créé.")

    if not os.path.exists(output_folder_md):
        os.makedirs(output_folder_md)
        print(f"Dossier '{output_folder_md}' créé.")

    # Parcourir tous les fichiers du dossier d'entrée
    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            md_text = pymupdf4llm.to_markdown(pdf_path)
            md_filename = Path(filename).stem + ".md"
            md_path = os.path.join(output_folder_md, md_filename)
            txt_filename = Path(filename).stem + ".txt"
            txt_path = os.path.join(output_folder_txt, txt_filename)

            with open(md_path, 'w', encoding='utf-8') as md_file:
                md_file.write(md_text)

            try:
                # Ouvrir le PDF
                with fitz.open(pdf_path) as doc:
                    full_text = ""
                    for page in doc:
                        # Extraction du texte
                        full_text += page.get_text()

                # Nettoyage basique (optionnel mais recommandé pour les LLM)
                # Supprime les espaces multiples et les sauts de ligne excessifs
                cleaned_text = " ".join(full_text.split())

                # Sauvegarder en .txt
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)
                
                print(f"Succès : {filename} -> {txt_filename}")

            except Exception as e:
                print(f"Erreur sur le fichier {filename}: {e}")

# --- Configuration ---
dossier_source = "../pdf"  # Mettez vos PDF ici
dossier_destination_txt = "../txt_from_pdf"
dossier_destination_md = "../md_from_pdf"

pdf_to_datasets(dossier_source, dossier_destination_txt, dossier_destination_md)
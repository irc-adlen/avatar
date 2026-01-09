import wikipediaapi
import os

# CONFIGURATION DU USER-AGENT (Obligatoire pour Wikipedia)
USER_AGENT = "MonExtracteurLLM/1.0 (contact@monemail.com)"

wiki = wikipediaapi.Wikipedia(
    user_agent=USER_AGENT,
    language='fr',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

def save_article(title, output_dir_txt, output_dir_md):
    page = wiki.page(title)
    
    if not page.exists():
        print(f"L'article '{title}' n'existe pas.")
        return

    # Nettoyage du titre pour le nom de fichier
    safe_title = title.replace(" ", "_").replace("/", "-")

    # --- VERSION TXT (Texte pur) ---
    txt_content = page.text
    with open(f"{output_dir_txt}/{safe_title}.txt", "w", encoding="utf-8") as f:
        f.write(txt_content)

    # --- VERSION MARKDOWN (Structurée) ---
    md_content = f"# {page.title}\n\n"
    md_content += f"Source: {page.fullurl}\n\n"
    
    # On parcourt les sections pour recréer la structure MD
    for section in page.sections:
        md_content += f"## {section.title}\n\n"
        md_content += f"{section.text}\n\n"
        # Sous-sections si elles existent
        for subs in section.sections:
            md_content += f"### {subs.title}\n\n"
            md_content += f"{subs.text}\n\n"

    with open(f"{output_dir_md}/{safe_title}.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Exporté : {title} (TXT & MD)")

# --- MAIN ---
sujets = ["Intelligence artificielle", "Apprentissage automatique", "Traitement du langage naturel"]

# Création des dossiers
os.makedirs("dataset_wiki/txt", exist_ok=True)
os.makedirs("dataset_wiki/md", exist_ok=True)

for sujet in sujets:
    save_article(sujet, "dataset_wiki/txt", "dataset_wiki/md")
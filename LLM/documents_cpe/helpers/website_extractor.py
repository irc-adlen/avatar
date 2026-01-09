import trafilatura

def extract_from_url(url):
    downloaded = trafilatura.fetch_url(url)
    # extract() récupère le texte, output_format="markdown" garde la structure
    result = trafilatura.extract(downloaded, output_format="markdown")
    
    if result:
        with open("web_dataset.md", "a", encoding="utf-8") as f:
            f.write(f"\n\n--- Source: {url} ---\n\n")
            f.write(result)
        print(f"Contenu extrait avec succès de : {url}")

urls = ["https://www.lemonde.fr/exemple", "https://tuto-code.com/article1"]
for url in urls:
    extract_from_url(url)
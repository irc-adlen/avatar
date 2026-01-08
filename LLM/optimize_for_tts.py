import json
import re

def text_cleaner_for_tts(text):
    # 1. Supprime les URLs (insupportable en TTS)
    text = re.sub(r'https?://\S+', 'sur le site de l\'école', text)
    
    # 2. Remplace les nombres courants par des mots
    replacements = {
        r'\b6\b': 'six', r'\b2\b': 'deux', r'\b4\b': 'quatre',
        r'\b36\b': 'trente-six', r'\b17\b': 'dix-sept', r'\b9\b': 'neuf',
        r'\b1994\b': 'mille neuf cent quatre-vingt-quatorze',
        r'\b1919\b': 'mille neuf cent dix-neuf',
        r'\b1883\b': 'mille huit cent quatre-vingt-trois',
        r'\b7 980\b': 'sept mille neuf cent quatre-vingts',
        r'\b800\b': 'huit cents', r'\b1000\b': 'mille'
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    
    # 3. Nettoyage des abréviations
    text = text.replace("assos", "associations").replace("ingé ", "ingénieur ").replace("profs", "professeurs")
    return text

input_file = "dataset_final_tts.jsonl"
output_file = "dataset_final_voice_ready.jsonl"

with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
    for line in f:
        data = json.loads(line)
        # On nettoie la réponse de l'assistant
        data["messages"][-1]["content"] = text_cleaner_for_tts(data["messages"][-1]["content"])
        out.write(json.dumps(data, ensure_ascii=False) + "\n")

print(f"Dataset prêt pour le TTS : {output_file}")
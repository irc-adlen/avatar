import json
import ollama

# 1. On charge TOUT le dataset dans un dictionnaire intelligent
knowledge_base = []
with open("./documents_cpe/dataset_final.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        knowledge_base.append({
            "q": data["messages"][1]["content"].lower(),
            "a": data["messages"][2]["content"]
        })

def get_forced_context(user_query):
    """Détecte les mots-clés et extrait les faits associés"""
    query_lower = user_query.lower()
    relevant_facts = []
    
    # Si un mot de la question est présent dans nos fiches, on prend la fiche
    for item in knowledge_base:
        # On cherche si des mots clés importants (IRC, Sport, Directeur...) matchent
        keywords = item["q"].replace("?", "").split()
        if any(word in query_lower for word in keywords if len(word) > 2):
            relevant_facts.append(item["a"])
    
    return "\n- ".join(list(set(relevant_facts))[:8]) # On limite pour ne pas noyer l'IA

def ask_cpe(user_query):
    context = get_forced_context(user_query)
    
    system_prompt = f"""Tu es l'Expert CPE Lyon. 
Utilise UNIQUEMENT les faits fournis ci-dessous. 
Si l'info n'est pas dedans, dis que tu ne sais pas.
INTERDICTION d'utiliser tes connaissances sur Internet ou d'autres écoles.

FAITS RÉELS SUR CPE LYON :
- {context}
"""

    response = ollama.chat(
        model='llama3.1',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query}
        ],
        options={'temperature': 0}
    )
    return response['message']['content']

if __name__ == "__main__":
    while True:
        q = input("\nÉtudiant : ")
        if q.lower() == 'exit': break
        print(f"Assistant : {ask_cpe(q)}")
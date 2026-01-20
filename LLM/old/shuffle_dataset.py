import random

# Chemins des fichiers
input_file = "dataset_final.jsonl"
output_file = "dataset_final.jsonl"

# Lecture du fichier ligne par ligne
with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Mélange aléatoire des données
random.seed(42) # Utilisation d'un seed pour la reproductibilité
random.shuffle(lines)

# Écriture du nouveau fichier mélangé
with open(output_file, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Terminé ! {len(lines)} exemples ont été mélangés dans '{output_file}'.")
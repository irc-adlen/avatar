import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Chemins des modèles
base_model_id = "unsloth/gemma-2-27b-it-bnb-4bit"
lora_weights = "./model_cpe_27b_final"

print("--- Chargement du modèle sur 2 GPUs ---")
tokenizer = AutoTokenizer.from_pretrained(lora_weights)
model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16
)

# Fusionner virtuellement les poids LoRA pour l'inférence
model = PeftModel.from_pretrained(model, lora_weights)
model.eval()

def generer_reponse(prompt):
    # Formatage identique au dataset (System + User)
    messages = [
        {"role": "user", "content": f"Tu es l'assistant vocal de CPE Lyon. Tu parles uniquement au nom de l'école. Tu réponds UNIQUEMENT en français. Tes réponses doivent être claires, précises et concises. Tes réponses doivent pouvoir être lues par un humain à haute voix.\n\n{prompt}"}
    ]
    
    inputs = tokenizer.apply_chat_template(
        messages, 
        add_generation_prompt=True, 
        return_tensors="pt"
    ).to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs, 
            max_new_tokens=300, 
            temperature=0.7,
            do_sample=True,
            top_p=0.9
        )
    
    # On décode uniquement la réponse de l'assistant
    reponse = tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
    return reponse

# Boucle interactive
print("Prêt ! Pose tes questions sur CPE Lyon (tape 'exit' pour quitter).")
while True:
    user_input = input("\nToi : ")
    if user_input.lower() == "exit":
        break
    print(f"Assistant : {generer_reponse(user_input)}")
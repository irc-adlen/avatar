from pygltflib import GLTF2, Material, PbrMetallicRoughness

# Charger le GLB Ready Player Me
gltf = GLTF2().load("moi.glb")

# 1️⃣ Trouver le mesh "Wolf3D_Outfit_Top"
outfit_mesh_index = None

for node in gltf.nodes:
    if node.name == "Wolf3D_Outfit_Top":
        outfit_mesh_index = node.mesh
        break

if outfit_mesh_index is None:
    raise Exception("Wolf3D_Outfit_Top non trouvé")

mesh = gltf.meshes[outfit_mesh_index]

# 2️⃣ Créer un NOUVEAU matériau (comme dans Blender)
new_material = Material(
    name="Auto_TShirt_Color",
    pbrMetallicRoughness=PbrMetallicRoughness(
        baseColorFactor=[0.2, 0.8, 0.3, 1.0],  # VERT
        metallicFactor=0.0,
        roughnessFactor=0.8
    )
)

# Ajouter le matériau au fichier
gltf.materials.append(new_material)
new_material_index = len(gltf.materials) - 1

# 3️⃣ Assigner ce matériau au mesh (supprime l’ancien)
for primitive in mesh.primitives:
    primitive.material = new_material_index

# 4️⃣ Sauvegarder
gltf.save("avatar_tshirt_green.glb")

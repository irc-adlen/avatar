<template>
  <div ref="container" class="viewer"></div>
  <button @click="anim()">Go</button>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import * as THREE from 'three'
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js'

const container = ref(null)

onMounted(() => {
  const scene = new THREE.Scene()
  const clock = new THREE.Clock()

  const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
  )
  camera.position.set(0, 1, 3)

  const renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  container.value.appendChild(renderer.domElement)

  scene.add(new THREE.DirectionalLight(0xffffff, 1))
  scene.add(new THREE.AmbientLight(0xffffff, 0.5))

  let mixer = null
  let actions = {}   // stockage des animations

  const loader = new FBXLoader()

  // 1) CHARGER LE MODELE PRINCIPAL
  loader.load('/sourir.fbx', (model) => {
    model.scale.set(0.01, 0.01, 0.01)
    scene.add(model)

    mixer = new THREE.AnimationMixer(model)

    // 2) CHARGER UNE ANIMATION 1
    loader.load('/sourir.fbx', (anim) => {
      const clip = anim.animations[0]
      actions['anim1'] = mixer.clipAction(clip)
    })

    // 3) CHARGER UNE ANIMATION 2
    loader.load('/ho-head.fbx', (anim) => {
      console.log(anim.animations)
      const clip = anim.animations[0]
      actions['anim2'] = mixer.clipAction(clip)
    })
  })

  // Fonction pour jouer une animation
  function playAnimation(name) {
    console.log(actions)
    if (!actions[name]) return console.warn('Animation introuvable:', name)

    Object.values(actions).forEach(a => a.stop()) // stop toutes les autres
    actions[name].reset().play()
  }


  // Exemple : jouer une animation après 2 secondes
  setTimeout(() => playAnimation('anim2'), 16000)

  function animate() {
    requestAnimationFrame(animate)
    if (mixer) mixer.update(clock.getDelta())
    renderer.render(scene, camera)
  }
  animate()
})
</script>


<style>
.viewer {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
</style>

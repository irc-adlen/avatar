<template>
  <div ref="container" class="viewer"></div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import * as THREE from 'three'
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js'

const container = ref(null)

onMounted(() => {
  const scene = new THREE.Scene()
  const clock = new THREE.Clock()

  // CAMERA
  const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
  )
  camera.position.set(0, 1, 3)

  // RENDERER
  const renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.value.appendChild(renderer.domElement)

  // LIGHTS
  const light = new THREE.DirectionalLight(0xffffff, 1)
  light.position.set(1, 2, 3)
  scene.add(light)

  scene.add(new THREE.AmbientLight(0xffffff, 0.5))

  // GLOBALS
  let mixer = null

  // LOAD MODEL + ANIMATION
  const loader = new FBXLoader()
  loader.load("/Punching Bag.fbx", (model) => {

    model.scale.set(0.01, 0.01, 0.01)
    scene.add(model)

    // Animation
    mixer = new THREE.AnimationMixer(model)

    if (model.animations.length > 0) {
      const action = mixer.clipAction(model.animations[0])
      action.play()                // DÉMARRER L’ANIMATION
      action.loop = THREE.LoopRepeat // En boucle
    }
  })

  // LOOP
  function animate() {
    requestAnimationFrame(animate)

    const delta = clock.getDelta()
    if (mixer) mixer.update(delta)

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

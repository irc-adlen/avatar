from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.task import Task
from panda3d.core import Filename

class TalkingFaceApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Charger le modèle
        self.face = Actor("facial_blendshapes_test/scene.gltf")  # ou "models/face.bam"
        self.face.reparentTo(self.render)
        self.face.setScale(1.0)
        self.face.setPos(0, 10, 0)

        # Noms des blend shapes dans ton modèle
        # Remplace par les noms EXACTS de tes shape keys
        self.mouth_shapes = ["rest", "A", "E", "O", "M"]

        # Initialiser tous les shapes à 0
        for shape in self.mouth_shapes:
            # Si ton modèle est importé en glTF, les blend shapes deviennent des "slider controls"
            # On utilise setControlEffect pour les piloter.
            try:
                self.face.setControlEffect(shape, 0.0)
            except Exception:
                print(f"Attention : impossible de trouver le blend shape '{shape}'")

        # Charger le son
        self.voice = self.loader.loadSfx("french_christine.wav")
        self.voice.setLoop(False)

        # Timeline des phonèmes : (temps_en_secondes, nom_du_shape)
        # À adapter à ton audio.
        self.phonemes = [
            (0.00, "rest"),
            (0.10, "M"),
            (0.20, "A"),
            (0.30, "E"),
            (0.40, "O"),
            (0.50, "M"),
            (0.60, "rest"),
        ]

        # Lancer la lecture + task d’update
        self.voice.play()
        self.current_shape = None
        self.blend_duration = 0.05  # temps pour interpoler entre 2 formes
        self.prev_shape = "rest"
        self.next_shape = "rest"
        self.shape_change_time = 0.0

        self.taskMgr.add(self.update_mouth_task, "update_mouth_task")

        # Caméra simple
        self.disableMouse()
        self.camera.setPos(0, 0, 0)
        self.camera.lookAt(self.face)

    # Retourne le phonème cible à un temps t
    def get_target_phoneme(self, t):
        current = "rest"
        for time_stamp, phoneme in self.phonemes:
            if t >= time_stamp:
                current = phoneme
            else:
                break
        return current

    # Applique un mélange linéaire entre deux shapes
    def apply_blend(self, from_shape, to_shape, alpha):
        # alpha entre 0.0 et 1.0
        # Remet tout à 0
        for shape in self.mouth_shapes:
            self.face.setControlEffect(shape, 0.0)

        # from_shape à (1 - alpha), to_shape à alpha
        if from_shape in self.mouth_shapes:
            self.face.setControlEffect(from_shape, max(0.0, 1.0 - alpha))
        if to_shape in self.mouth_shapes:
            self.face.setControlEffect(to_shape, max(0.0, alpha))

    def update_mouth_task(self, task):
        # Si le son est fini, arrêter l’animation de bouche
        if not self.voice.status():
            return Task.done

        t = self.voice.getTime()

        # Phonème cible selon le temps
        target = self.get_target_phoneme(t)

        # Si le phonème change, démarrer une petite transition
        if target != self.next_shape:
            self.prev_shape = self.next_shape
            self.next_shape = target
            self.shape_change_time = t

        # Calculer combien de temps depuis le dernier changement
        dt = t - self.shape_change_time
        alpha = min(max(dt / self.blend_duration, 0.0), 1.0)

        # Appliquer l’interpolation
        self.apply_blend(self.prev_shape, self.next_shape, alpha)

        return Task.cont


app = TalkingFaceApp()
app.run()

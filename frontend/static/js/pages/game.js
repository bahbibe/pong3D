import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { html } from "../core/html.js";
import { createInterpolator } from "../core/interpolation.js";
import { Page } from "../core/page.js";
import { navigate } from "../core/router.js";

const SCENE_PATH = "/static/scene.glb";
// How far in the past positions are drawn: three server ticks (60 per
// second), enough to always have an update on each side of the frame.
const INTERPOLATION_DELAY_MS = 50;
const TEXTURE_KEYS = ["map", "lightMap", "bumpMap", "normalMap", "specularMap", "envMap"];

const loadScene = (scene) =>
  new Promise((resolve, reject) => {
    new GLTFLoader().load(
      SCENE_PATH,
      (gltf) => {
        scene.add(gltf.scene);
        resolve();
      },
      undefined,
      reject,
    );
  });

const disposeMaterial = (material) => {
  for (const key of TEXTURE_KEYS) material[key]?.dispose();
  material.dispose();
};

/** A digit drawn on a transparent canvas, for the score boards. */
const textTexture = (text) => {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.font = "Bold 256px Arial";
  context.fillStyle = "#ffffff";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, canvas.width / 2, canvas.height / 2);
  return new THREE.CanvasTexture(canvas);
};

/**
 * The 3D game (/play/:game_id, /play/bot, /play/:tournament_id/:game_id).
 * The server runs the game; this page draws the state it sends and sends
 * the direction the player holds.
 */
class GamePage extends Page {
  mount() {
    const { game_id: gameId, tournament_id: tournamentId } = this.params;
    if (!gameId) {
      // /play without a game: nothing to connect to.
      navigate("/matchmaking", { replace: true });
      return;
    }
    this.render(html`<canvas id="game-canvas"></canvas>`);
    this.canvas = this.querySelector("#game-canvas");
    this.left = false;
    this.right = false;
    this.lastDirection = "none";
    this.scores = [0, 0];
    this.ready = false;
    // Positions are drawn a little in the past, blended between updates
    // (see core/interpolation.js): smooth motion despite network jitter.
    this.motion = createInterpolator({ delay: INTERPOLATION_DELAY_MS });

    const path = tournamentId
      ? `/ws/game/${encodeURIComponent(tournamentId)}/${encodeURIComponent(gameId)}`
      : `/ws/game/${encodeURIComponent(gameId)}`;
    this.connection = this.socket(path, { onMessage: (data) => this.onMessage(data) });

    this.scene = new THREE.Scene();
    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: true });
    this.renderer.setClearColor(0xffffff, 0);
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.shadowMap.enabled = true;
    this.renderer.toneMapping = THREE.NoToneMapping;
    this.renderer.toneMappingExposure = 1;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    loadScene(this.scene)
      .then(() => {
        // The player may have left while the model was loading.
        if (this.signal.aborted) return;
        this.setUpScene();
        this.on(window, "resize", () => this.onResize());
        this.on(document, "keydown", (event) => this.onKey(event, true));
        this.on(document, "keyup", (event) => this.onKey(event, false));
        // Touch: hold the left or right half of the screen to move.
        this.on(this.canvas, "touchstart", (event) => this.onTouch(event), { passive: false });
        this.on(this.canvas, "touchmove", (event) => this.onTouch(event), { passive: false });
        this.on(this.canvas, "touchend", (event) => this.onTouchEnd(event));
        this.on(this.canvas, "touchcancel", (event) => this.onTouchEnd(event));
        this.ready = true;
      })
      .catch((error) => console.error("Could not load the 3D scene:", error));
  }

  setUpScene() {
    const cameras = [];
    this.scene.traverse((object) => {
      if (object.isCamera) cameras.push(object);
      if (object.name === "PaddlePlayer1") this.player1 = object;
      if (object.name === "PaddlePlayer2") this.player2 = object;
      if (object.name === "Cube") this.ball = object;
      if (object.name === "score1") this.score1 = object;
      if (object.name === "score2") this.score2 = object;
    });
    this.camera = cameras[0];
    this.updateScore();
    this.onResize();
    this.oppositeSideCameraZ = -this.camera.position.z;
    this.camera.lookAt(0, 0, 0);
    const frame = () => {
      this.animationFrame = requestAnimationFrame(frame);
      this.applyMotion();
      this.renderer.render(this.scene, this.camera);
    };
    frame();
  }

  onMessage(data) {
    if (data.type === "game over") {
      const { game_id: gameId, tournament_id: tournamentId } = this.params;
      if (tournamentId) navigate(`/tournament/${encodeURIComponent(tournamentId)}`);
      else if (gameId === "bot")
        navigate(`/score/bot?player1_score=${this.scores[0]}&player2_score=${this.scores[1]}`);
      else navigate(`/score/${encodeURIComponent(gameId)}`);
      return;
    }
    // Updates sent before the scene is loaded are skipped.
    if (data.type !== "game_update_message" || !this.ready) return;
    const game = data.game_state;
    // sent_at: the server's clock in seconds (absent from older servers).
    const sentAt = typeof game.sent_at === "number" ? game.sent_at * 1000 : undefined;
    this.motion.push(
      {
        ballX: game.ball_position[0],
        ballZ: game.ball_position[1],
        player1: game.player1,
        player2: game.player2,
      },
      performance.now(),
      sentAt,
    );
    if (game.score[0] !== this.scores[0] || game.score[1] !== this.scores[1]) {
      this.scores = [game.score[0], game.score[1]];
      this.updateScore();
    }
    if (game.side === "player2") this.camera.position.z = this.oppositeSideCameraZ;
    this.camera.lookAt(0, 0, 0);
  }

  applyMotion() {
    const state = this.motion.sample();
    if (!state) return;
    this.ball.position.x = state.ballX;
    this.ball.position.z = state.ballZ;
    this.player1.position.x = state.player1;
    this.player2.position.x = state.player2;
  }

  updateScore() {
    // Free the previous canvas textures (GPU memory) before replacing them.
    for (const [board, value] of [
      [this.score1, this.scores[0]],
      [this.score2, this.scores[1]],
    ]) {
      board.material.map?.dispose();
      board.material.map = textTexture(String(value));
      board.material.needsUpdate = true;
    }
  }

  onResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  // The server moves the paddle at a fixed speed while a direction is held.
  // Names follow the server protocol: ArrowLeft sends "right".
  onKey(event, down) {
    if (event.key === "ArrowLeft") this.right = down;
    else if (event.key === "ArrowRight") this.left = down;
    else return;
    this.sendDirection();
  }

  onTouch(event) {
    event.preventDefault();
    const touch = event.touches[event.touches.length - 1];
    if (!touch) return;
    // Same mapping as the arrow keys: left half = ArrowLeft.
    const leftHalf = touch.clientX < window.innerWidth / 2;
    this.right = leftHalf;
    this.left = !leftHalf;
    this.sendDirection();
  }

  onTouchEnd(event) {
    if (event.touches.length > 0) {
      this.onTouch(event);
      return;
    }
    this.right = false;
    this.left = false;
    this.sendDirection();
  }

  // Send only when the held direction changes ("left", "right" or "none").
  sendDirection() {
    let direction = "none";
    if (this.right && !this.left) direction = "right";
    else if (this.left && !this.right) direction = "left";
    if (direction === this.lastDirection) return;
    if (this.connection?.readyState !== WebSocket.OPEN) return;
    this.lastDirection = direction;
    this.connection.send(JSON.stringify({ type: "move", direction }));
  }

  unmount() {
    // Listeners and the socket end with the component; the GPU resources
    // are freed here.
    if (!this.scene) return; // left before setup (e.g. /play without id)
    cancelAnimationFrame(this.animationFrame);
    this.scene.traverse((object) => {
      object.geometry?.dispose();
      if (object.material) [].concat(object.material).forEach(disposeMaterial);
    });
    this.scene.clear();
    this.renderer.dispose();
    this.renderer.forceContextLoss();
    this.scene = null;
    this.renderer = null;
    this.camera = null;
  }
}

customElements.define("game-page", GamePage);

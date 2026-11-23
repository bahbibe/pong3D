import { AbstractPage } from "./AbstarctPage.js";
import * as THREE from "three"

import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { navigateTo, WSS_URL } from "../router.js";

const scenePath = "/static/scene.glb"

export const LoadGLTFByPath = (scene) => {
  return new Promise((resolve, reject) => {
    // Create a loader
    const loader = new GLTFLoader();

    // Load the GLTF file
    loader.load(scenePath, (gltf) => {

      scene.add(gltf.scene);

      resolve();
    }, undefined, (error) => {
      reject(error);
    });
  });
};

class GamePage extends AbstractPage {
  constructor() {
    super();
    // Bind the animate method to the class instance
    this.animate = this.animate.bind(this);
    this.keyDown = this.keyDown.bind(this);
    this.keyUp = this.keyUp.bind(this);
  }
  connectedCallback() {
    const template = document.getElementById("game-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    this.left = false;
    this.right = false;
    this.score1Text = 0 ;
    this.score2Text = 0 ;

    this.scene = new THREE.Scene();
    this.game_url = `${WSS_URL}/ws/game/` + this.params.game_id ;
    
    if (this.params.tournament_id)
      this.game_url = `${WSS_URL}/ws/game/` + this.params.tournament_id +'/' + this.params.game_id;
    this.socket = new WebSocket(this.game_url);

    //Renderer does the job of rendering the graphics
    this.renderer = new THREE.WebGLRenderer({
      //Defines the canvas component in the DOM that will be used
      canvas: document.querySelector('#game-canvas'),
      antialias: true,
      alpha: true
    });
    
    //set up the renderer with the default settings for threejs.org/editor - revision r153
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.shadows = true;
    this.renderer.shadowType = 1;
    this.renderer.shadowMap.enabled = true;
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.toneMapping = 0;
    this.renderer.toneMappingExposure = 1
    this.renderer.toneMapping = THREE.NoToneMapping;
    this.renderer.setClearColor(0xffffff, 0);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace

    // Load the GLTF model
    
    LoadGLTFByPath(this.scene)
      .then(() => {
        this.retrieveListOfCameras(this.scene);
    })
    .then(() => {
      // on window resize
      window.addEventListener('resize', () => {
        // update sizes
        this.camera.aspect = window.innerWidth / window.innerHeight
        this.camera.updateProjectionMatrix()
        this.renderer.setSize(window.innerWidth, window.innerHeight)
      })

      console.log(this.params.tournament_id);

      this.socket.onmessage = (event) => {
        let obj = JSON.parse(event.data);
        console.log(obj.type) ;
        console.log(obj);

        if (obj.type === "game over")
        {
          
          if (this.params.tournament_id)
          {
            console.log(`/tournament/${this.params.tournament_id}`);
            navigateTo(`/tournament/${this.params.tournament_id}`)
          }
          else
          {
            if (this.params.game_id === 'bot')
              navigateTo(`/score/${this.params.game_id}?player1_score=${this.score1Text}&player2_score=${this.score2Text}`);
            else
              navigateTo(`/score/${this.params.game_id}`)
          }
          return
        }
        if (obj.type === 'game_update_message')
        {
          const game = obj.game_state ;
          this.ball.position.x = game.ball_position[0];
          this.ball.position.z = game.ball_position[1];
          this.player.position.x = game.player1;
          this.player2.position.x = game.player2;
          if (this.score1Text !== game.score[0]) {
            this.score1Text = game.score[0];
            this.updateScore();
          }
          if (this.score2Text !== game.score[1]) {
            this.score2Text = game.score[1];
            this.updateScore();
          }
          if (game.side == 'player2')
            this.camera.position.z = this.opposit_side_cam_pos;
          this.camera.lookAt(0, 0, 0);
          this.newUpdate = true;
        }
      };

      this.socket.onopen = (event) => {
        console.log("connected");
      }

      this.socket.onclose = (event) => {
        console.log("connection closed");
      }

      document.onkeydown = this.keyDown;
      document.onkeyup = this.keyUp;
    })
    .catch((error) => {
      console.error('Error loading JSON scene:', error);
    });

  }

  // Set the camera aspect ratio to match the browser window dimensions
  updateCameraAspect(camera) {
    const width = window.innerWidth;
    const height = window.innerHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.opposit_side_cam_pos = -this.camera.position.z;

    this.camera.lookAt(0, 0, 0)
  }

  keyDown(e) {
    e = e || window.event;

    if (e.keyCode == '37')      // right arrow
      this.right = true
    else if (e.keyCode == '39') // left arrow
      this.left = true
  }

  keyUp(e) {
    e = e || window.event;

    if (e.keyCode == '37')      // right arrow
      this.right = false
    else if (e.keyCode == '39') // left arrow
      this.left = false
  }

  createTextTexture(text) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 256;
    canvas.height = 256;

    context.fillStyle = "rgba(0, 0, 0, 0.0)";
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillRect(0, 0, canvas.width, canvas.height);

    context.font = 'Bold 256px Arial';
    context.fillStyle = '#ffffff';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(text, canvas.width / 2, canvas.height / 2);

    return new THREE.CanvasTexture(canvas);
  }

  updateScore() {
    this.player1Score.material.map = this.createTextTexture(`${this.score1Text}`);
    this.player2Score.material.map = this.createTextTexture(`${this.score2Text}`);
    this.player1Score.material.needsUpdate = true;
    this.player2Score.material.needsUpdate = true;
  }

  //retrieve list of all cameras
  retrieveListOfCameras(scene) {
    // Get a list of all cameras in the scene
    let cameraList = []
    scene.traverse((object) => {
      if (object.isCamera) {
        cameraList.push(object);
      }
      if (object.name === "PaddlePlayer1")
        this.player = object;
      if (object.name === "PaddlePlayer2")
        this.player2 = object;
      if (object.name === "Cube")
        this.ball = object;
      if (object.name === "score1")
        this.player1Score = object
      if (object.name === "score2")
        this.player2Score = object
      // console.log(player1Score);
    });
    this.updateScore()

    //Set the camera to the first value in the list of cameras
    this.camera = cameraList[0];

    this.updateCameraAspect(this.camera);

    // Start the animation loop after the model and cameras are loaded
    this.animate();
  }

  //A method to be run each time a frame is generated
  animate() {
    this.animationFrameId = requestAnimationFrame(this.animate);
    this.renderer.render(this.scene, this.camera);
    if (!this.newUpdate)
      return;
    this.newUpdate = false;
    if (this.right == true)
      this.socket.send(JSON.stringify({ "type": 'right' }));
    if (this.left == true)
      this.socket.send(JSON.stringify({ "type": 'left' }));
  };

  disconnectedCallback() {
    if (this.socket) this.socket.close();

    // Remove event listeners
    window.removeEventListener('resize', this.onResize);
    document.removeEventListener('keydown', this.keyDown);
    document.removeEventListener('keyup', this.keyUp);

    // Dispose of Three.js resources
    this.scene.traverse((object) => {
        // Dispose geometries
        if (object.geometry) {
            object.geometry.dispose();
        }

        // Dispose materials and textures
        if (object.material) {
            if (Array.isArray(object.material)) {
                object.material.forEach(material => {
                    if (material.map) material.map.dispose();
                    if (material.lightMap) material.lightMap.dispose();
                    if (material.bumpMap) material.bumpMap.dispose();
                    if (material.normalMap) material.normalMap.dispose();
                    if (material.specularMap) material.specularMap.dispose();
                    if (material.envMap) material.envMap.dispose();
                    material.dispose();
                });
            } else {
                if (object.material.map) object.material.map.dispose();
                if (object.material.lightMap) object.material.lightMap.dispose();
                if (object.material.bumpMap) object.material.bumpMap.dispose();
                if (object.material.normalMap) object.material.normalMap.dispose();
                if (object.material.specularMap) object.material.specularMap.dispose();
                if (object.material.envMap) object.material.envMap.dispose();
                object.material.dispose();
            }
        }
    });

    // Dispose of the scene
    this.scene.clear();

    // Dispose of the renderer
    if (this.renderer) {
        this.renderer.dispose();
        this.renderer.forceContextLoss();
        this.renderer.domElement = null;
        this.renderer = null;
    }

    // Clear any animation frame requests
    if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
    }

    // Clear references
    this.scene = null;
    this.camera = null;
    this.player = null;
    this.player2 = null;
    this.ball = null;
    this.player1Score = null;
    this.player2Score = null;
  }
}

window.customElements.define("game-page", GamePage);
export { GamePage };
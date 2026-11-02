import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// three.js: the 3D part
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(400, 400);
document.getElementById('three').appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xeeedf1);
const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
camera.position.set(0, 1.5, 5);
new OrbitControls(camera, renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff, 0x888888, 2));
const ball = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 32), new THREE.MeshStandardMaterial({ color: 0xf2aabd }));
scene.add(ball);

// p5.js: input, DOM and a 2D overlay
let slider, clicks = 0;
function setup() {
  createCanvas(400, 60).position(0, 400);
  slider = createSlider(0.5, 2, 1, 0.01).position(10, 470);
}
function draw() {
  background(255);
  text('p5 says: clicks = ' + clicks + ', puff = ' + slider.value(), 10, 30);
  ball.scale.setScalar(slider.value());      // p5 slider drives the three.js mesh
  renderer.render(scene, camera);
}
function mousePressed() { clicks++; }

// module code is private, so hand p5 the functions it looks for
window.setup = setup;
window.draw = draw;
window.mousePressed = mousePressed;

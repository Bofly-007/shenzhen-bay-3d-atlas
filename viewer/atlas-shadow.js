// Keep a fixed-size shadow texture useful both across the city and at roof level.
export function createAtlasShadowUpdater(renderer, light, camera, controls) {
  const shadowCamera = light.shadow.camera;
  let previousX, previousZ, previousRadius;

  return function updateAtlasShadow() {
    const width = camera.right - camera.left;
    const height = camera.top - camera.bottom;
    const span = Math.max(width, height) / camera.zoom;
    // Leave room for shadows from adjacent towers and reuse the texture while
    // the camera stays in the same cell and zoom band.
    const requiredRadius = Math.max(650, span * 0.84 + 300);
    const band = Math.ceil(Math.log(requiredRadius / 650) / Math.log(1.25));
    const radius = Math.min(6200, 650 * 1.25 ** band);
    const step = radius / 4;
    const x = Math.round(controls.target.x / step) * step;
    const z = Math.round(controls.target.z / step) * step;
    if (x === previousX && z === previousZ && radius === previousRadius) return;
    previousX = x;
    previousZ = z;
    previousRadius = radius;

    light.target.position.set(x, 10, z);
    light.position.set(x - 4000, 8210, z + 3600);
    shadowCamera.left = shadowCamera.bottom = -radius;
    shadowCamera.right = shadowCamera.top = radius;
    shadowCamera.near = 1500;
    shadowCamera.far = 22000;
    // A wide map covers more metres per texel and needs a larger depth offset.
    light.shadow.bias = -Math.max(0.00013, 0.00055 * radius / 6200);
    shadowCamera.updateProjectionMatrix();
    light.target.updateMatrixWorld();
    light.updateMatrixWorld();
    renderer.shadowMap.needsUpdate = true;
  };
}

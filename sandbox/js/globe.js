/** TERRA UI-2.5 WebGL2 globe — C3 Soft Hollow port of render_globe */

const HOME_YAW = 100 * Math.PI / 180;
const HOME_PITCH = -16 * Math.PI / 180;
const S5_YAW = 210 * Math.PI / 180;
const S5_PITCH = -12 * Math.PI / 180;
const PITCH_CLAMP = 35 * Math.PI / 180;
const EXTRUDE = 0.085;
const MAX_H = 0.80; // India
const STAGE = [0.96, 0.95, 0.93];

export class TerraGlobe {
  constructor(canvas) {
    this.canvas = canvas;
    this.gl = canvas.getContext('webgl2', { antialias: true, alpha: false, premultipliedAlpha: false });
    if (!this.gl) throw new Error('WebGL2 required');
    this.mode = 1; // S1 default
    this.yaw = HOME_YAW;
    this.pitch = HOME_PITCH;
    this.zoom = 1.0;
    this.vyaw = 0;
    this.vpitch = 0;
    this._ease = null;
    this.ready = false;
  }

  async init() {
    const gl = this.gl;
    const [vsSrc, fsSrc] = await Promise.all([
      fetch('shaders/globe.vert.glsl').then(r => r.text()),
      fetch('shaders/globe.frag.glsl').then(r => r.text()),
    ]);
    this.program = this._link(vsSrc, fsSrc);
    gl.useProgram(this.program);

    const quad = new Float32Array([-1,-1, 1,-1, -1,1, 1,1]);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, quad, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

    this.u = {};
    for (const name of [
      'u_earth','u_landCoast','u_geoPack','u_mockS3','u_res','u_yaw','u_pitch','u_zoom',
      'u_mode','u_extrudeScale','u_maxHeight','u_stage','u_globeCenter','u_globeRadiusPx'
    ]) {
      this.u[name] = gl.getUniformLocation(this.program, name);
    }

    // Textures: 0 earth, 1 landCoast, 2 geoPack, 3 mockS3
    this.texEarth = await this._loadTex('assets/earth_topo.jpg', gl.LINEAR, gl.LINEAR, true);
    this.texLand = await this._loadTex('assets/land_coast.png', gl.LINEAR, gl.LINEAR, false);
    this.texGeo = await this._loadTex('assets/geo_pack.png', gl.NEAREST, gl.NEAREST, false);
    this.texMock = await this._loadTex('assets/mock_s3_height_glow.png', gl.NEAREST, gl.NEAREST, false);

    gl.uniform1i(this.u.u_earth, 0);
    gl.uniform1i(this.u.u_landCoast, 1);
    gl.uniform1i(this.u.u_geoPack, 2);
    gl.uniform1i(this.u.u_mockS3, 3);
    gl.uniform1f(this.u.u_extrudeScale, EXTRUDE);
    gl.uniform1f(this.u.u_maxHeight, MAX_H);
    gl.uniform3fv(this.u.u_stage, STAGE);

    this.ready = true;
    this.resize();
  }

  _compile(type, src) {
    const gl = this.gl;
    const sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      const log = gl.getShaderInfoLog(sh);
      console.error(log);
      throw new Error('Shader compile: ' + log);
    }
    return sh;
  }

  _link(vs, fs) {
    const gl = this.gl;
    const p = gl.createProgram();
    gl.attachShader(p, this._compile(gl.VERTEX_SHADER, vs));
    gl.attachShader(p, this._compile(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
      throw new Error('Link: ' + gl.getProgramInfoLog(p));
    }
    return p;
  }

  async _loadTex(url, minF, magF, flipY) {
    const gl = this.gl;
    const img = await new Promise((res, rej) => {
      const i = new Image();
      i.onload = () => res(i);
      i.onerror = rej;
      i.src = url;
    });
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    // Equirect north-at-top: first image row = north = GL v=0 (no flip). Matches lonlat_to_uv v=0.5-lat/π.
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 0);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, minF);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, magF);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return tex;
  }

  setMode(modeStr) {
    const map = { S0: 0, S1: 1, S3: 3, S5: 5 };
    this.mode = map[modeStr] ?? 1;
    if (this.mode === 5) {
      this.easeTo(S5_YAW, S5_PITCH);
    } else if (this.mode === 0 || this.mode === 1 || this.mode === 3) {
      // keep current orbit unless coming from S5 switch intent — ease home for front boards
      this.easeTo(HOME_YAW, HOME_PITCH);
    }
  }

  easeTo(yaw, pitch, ms = 650) {
    this._ease = {
      t0: performance.now(), ms,
      y0: this.yaw, p0: this.pitch,
      y1: yaw, p1: pitch,
    };
    this.vyaw = 0; this.vpitch = 0;
  }

  goHome() { this.easeTo(HOME_YAW, HOME_PITCH); }

  orbitBy(dx, dy) {
    // dx,dy in CSS pixels
    this._ease = null;
    const sens = 0.0055;
    this.yaw += dx * sens;
    this.pitch = Math.max(-PITCH_CLAMP, Math.min(PITCH_CLAMP, this.pitch + dy * sens));
  }

  fling(vx, vy) {
    this.vyaw = vx * 0.0055;
    this.vpitch = vy * 0.0055;
  }

  pinchScale(factor) {
    this.zoom = Math.max(0.72, Math.min(1.85, this.zoom * factor));
  }

  resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    const rect = this.canvas.getBoundingClientRect();
    const w = Math.max(2, Math.floor(rect.width * dpr));
    const h = Math.max(2, Math.floor(rect.height * dpr));
    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w;
      this.canvas.height = h;
    }
    this.gl.viewport(0, 0, w, h);
  }

  frame(dt) {
    if (!this.ready) return;
    const gl = this.gl;
    this.resize();

    if (this._ease) {
      const e = this._ease;
      const t = Math.min(1, (performance.now() - e.t0) / e.ms);
      const s = t * t * (3 - 2 * t);
      this.yaw = e.y0 + (e.y1 - e.y0) * s;
      this.pitch = e.p0 + (e.p1 - e.p0) * s;
      if (t >= 1) this._ease = null;
    } else {
      // light inertia
      this.yaw += this.vyaw;
      this.pitch = Math.max(-PITCH_CLAMP, Math.min(PITCH_CLAMP, this.pitch + this.vpitch));
      const damp = Math.pow(0.92, dt / 16.67);
      this.vyaw *= damp;
      this.vpitch *= damp;
      if (Math.abs(this.vyaw) < 1e-5) this.vyaw = 0;
      if (Math.abs(this.vpitch) < 1e-5) this.vpitch = 0;
    }

    gl.useProgram(this.program);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, this.texEarth);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, this.texLand);
    gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, this.texGeo);
    gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, this.texMock);

    const w = this.canvas.width, h = this.canvas.height;
    gl.uniform2f(this.u.u_res, w, h);
    gl.uniform1f(this.u.u_yaw, this.yaw);
    gl.uniform1f(this.u.u_pitch, this.pitch);
    gl.uniform1f(this.u.u_zoom, this.zoom);
    gl.uniform1i(this.u.u_mode, this.mode);

    // Board framing: globe_r 470 (S0/S1) or 490 (S3/S5) on 1170×2080; center (0.5, 0.5+36/2080)
    const elev = this.mode === 3 || this.mode === 5;
    const boardR = elev ? 490 : 470;
    const scale = Math.min(w / 1170, h / 2080);
    const rPx = boardR * scale;
    gl.uniform1f(this.u.u_globeRadiusPx, rPx);
    gl.uniform2f(this.u.u_globeCenter, 0.5, 0.5 + 36 / 2080);

    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }
}

export { HOME_YAW, HOME_PITCH, S5_YAW, S5_PITCH };

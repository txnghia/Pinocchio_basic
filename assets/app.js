const connection = document.querySelector('#connection');
const errorBox = document.querySelector('#error-container');
const armButton = document.querySelector('#arm-button');
const playButton = document.querySelector('#play-button');
const stopButton = document.querySelector('#stop-button');
let latestState = { armed: false };
let statusTimer = null;

const ui = new WebUI();
ui.on_connect(() => {
  connection.textContent = 'CONNECTED'; connection.className = 'pill online';
  ui.send_message('get_initial_state');
  clearInterval(statusTimer);
  statusTimer = setInterval(() => ui.send_message('get_initial_state'), 250);
});
ui.on_disconnect(() => {
  connection.textContent = 'CONNECTION LOST'; connection.className = 'pill offline';
  clearInterval(statusTimer); statusTimer = null;
});
ui.on_message('theater_status_update', updateStatus);

const servoNames = ['head','left_arm_lift','right_arm_lift','left_hand_wave','right_hand_wave','left_leg','right_leg','puppet_z'];
servoNames.forEach(name => {
  const node = document.createElement('div'); node.className = 'control';
  node.innerHTML = `<label><span>${name.replaceAll('_',' ')}</span><output>90°</output></label><input type="range" min="20" max="160" value="90">`;
  const slider = node.querySelector('input'), output = node.querySelector('output');
  slider.addEventListener('input', () => output.textContent = `${slider.value}°`);
  slider.addEventListener('change', () => ui.send_message('set_servo', {name, degrees:Number(slider.value), duration_ms:500}));
  document.querySelector('#servo-controls').append(node);
});

function addMotion(parent, name, event, valueKey, defaultValue) {
  const row = document.createElement('div'); row.className = 'motion-row';
  row.innerHTML = `<label>${name}</label><input type="number" value="${defaultValue}"><button>Move</button>`;
  row.querySelector('button').onclick = () => ui.send_message(event, event === 'move_scenery'
    ? {side:name, [valueKey]:Number(row.querySelector('input').value), max_pwm:120}
    : {name, [valueKey]:Number(row.querySelector('input').value), speed_sps:800});
  document.querySelector(parent).append(row);
}
['x','y','curtain'].forEach(n => addMotion('#stepper-controls', n, 'move_stepper', 'target_steps', 0));
['left','right'].forEach(n => addMotion('#scenery-controls', n, 'move_scenery', 'target_counts', 0));

const lightAims = [
  'Far left → right crosslight',
  'Left → left wash',
  'Center left → center',
  'Center right → center',
  'Right → left crosslight',
  'Far right → right fill',
];

function hexToRgb(hex) {
  const value = Number.parseInt(hex.slice(1), 16);
  return {red:(value >> 16) & 255, green:(value >> 8) & 255, blue:value & 255};
}

for (let light=0; light<lightAims.length; light++) {
  const node = document.createElement('div'); node.className='control';
  node.innerHTML=`<label><span>Light ${light+1}</span><output>0</output></label><small>${lightAims[light]}</small><div class="rgb-row"><input class="color" type="color" value="#ffd6a0" aria-label="Light ${light+1} color"><input class="level" type="range" min="0" max="255" value="0"></div>`;
  const color=node.querySelector('.color'), slider=node.querySelector('.level'), output=node.querySelector('output');
  const send=()=>{
    output.textContent=slider.value;
    const rgb=hexToRgb(color.value), scale=Number(slider.value)/255;
    ui.send_message('set_rgb_light',{light,red:Math.round(rgb.red*scale),green:Math.round(rgb.green*scale),blue:Math.round(rgb.blue*scale)});
  };
  slider.oninput=()=>output.textContent=slider.value;
  slider.onchange=send;
  color.onchange=send;
  document.querySelector('#light-controls').append(node);
}

armButton.onclick = () => ui.send_message('set_arm', {enabled:!latestState.armed});
playButton.onclick = () => ui.send_message('play_show');
stopButton.onclick = () => ui.send_message('stop_all');

function updateStatus(state) {
  latestState = state;
  document.querySelector('#system-status').textContent = state.armed ? 'ARMED' : 'DISARMED';
  document.querySelector('#estop-status').textContent = state.estop ? 'PRESSED / OPEN' : 'READY';
  document.querySelector('#show-status').textContent = state.show_running ? 'RUNNING' : 'STOPPED';
  document.querySelector('#encoders').textContent = `${state.left_encoder ?? 0} / ${state.right_encoder ?? 0}`;
  document.querySelector('#left-motor-status').textContent = `${(state.left_direction ?? 'stopped').toUpperCase()} · PWM ${Math.abs(state.left_dc_command ?? 0)}`;
  document.querySelector('#right-motor-status').textContent = `${(state.right_direction ?? 'stopped').toUpperCase()} · PWM ${Math.abs(state.right_dc_command ?? 0)}`;
  armButton.textContent = state.armed ? 'Disarm actuators' : 'Arm actuators';
  errorBox.hidden = !state.error; errorBox.textContent = state.error || '';
}

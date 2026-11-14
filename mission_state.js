/* Shared, in-page mission state for 2D and 3D views. No external dependencies. */
(function () {
  'use strict';
  let mission = { start: null, end: null, route: null };
  function clone(value) { return value == null ? null : JSON.parse(JSON.stringify(value)); }
  function validPoint(point) {
    return point && Number.isFinite(point.lat) && Number.isFinite(point.lon) &&
      point.lat >= -90 && point.lat <= 90 && point.lon >= -180 && point.lon <= 180;
  }
  function emit() { window.dispatchEvent(new CustomEvent('ares:mission', { detail: get() })); }
  function get() { return clone(mission); }
  function setPoints(start, end) {
    if ((start && !validPoint(start)) || (end && !validPoint(end)) || (end && !start)) throw new Error('Invalid mission coordinates');
    mission = { start: clone(start), end: clone(end), route: null }; emit();
  }
  function selectPoint(point) {
    if (!validPoint(point)) throw new Error('Invalid location');
    if (!mission.start || mission.end) setPoints(point, null);
    else setPoints(mission.start, point);
  }
  function setRoute(route) {
    if (!mission.start || !mission.end) return;
    mission.route = clone(route); emit();
  }
  function clear() { setPoints(null, null); setSelectionMode('explore'); }
  window.ARESMission = { get, setPoints, selectPoint, setRoute, clear };

  // Explicit, shared selection mode. Explore is the safe default.
  let selectionMode = 'explore';
  const allowedModes = new Set(['explore', 'start', 'destination']);
  function getSelectionMode() { return selectionMode; }
  function setSelectionMode(mode) {
    if (!allowedModes.has(mode)) throw new Error('Invalid navigation mode');
    selectionMode = mode;
    window.dispatchEvent(new CustomEvent('ares:selection-mode', {detail: {mode}}));
  }
  function selectPointSafely(point) {
    if (selectionMode === 'explore') return false;
    if (!validPoint(point)) throw new Error('Invalid location');
    if (selectionMode === 'start') setPoints(point, null);
    else {
      if (!mission.start) {
        setSelectionMode('start');
        return false;
      }
      setPoints(mission.start, point);
    }
    setSelectionMode('explore');
    return true;
  }
  window.ARESMission.getSelectionMode = getSelectionMode;
  window.ARESMission.setSelectionMode = setSelectionMode;
  window.ARESMission.selectPointSafely = selectPointSafely;
  const modeButtons = [...document.querySelectorAll('[data-ares-mode]')];
  const modeFeedback = document.getElementById('ares-selection-feedback');
  function renderMode() {
    modeButtons.forEach(button => {
      const active = button.dataset.aresMode === selectionMode;
      button.setAttribute('aria-pressed', String(active));
      button.classList.toggle('ares-mode-active', active);
    });
    if (modeFeedback) modeFeedback.textContent = {
      explore: 'Explore mode: map clicks cannot change mission coordinates.',
      start: 'Select Start: click once on the 2D map or 3D globe.',
      destination: 'Select Destination: click once on the 2D map or 3D globe.'
    }[selectionMode];
  }
  modeButtons.forEach(button => button.addEventListener('click', () => {
    const mode = button.dataset.aresMode;
    if (mode === 'destination' && !mission.start) {
      setSelectionMode('start');
      if (modeFeedback) modeFeedback.textContent = 'Choose a starting point first.';
    } else setSelectionMode(mode);
  }));
  window.addEventListener('ares:selection-mode', renderMode);
  renderMode();
  const form = document.getElementById('coordinate-form');
  const feedback = document.getElementById('coordinate-feedback');
  const fields = ['start-lat', 'start-lon', 'end-lat', 'end-lon'];
  function parseField(id, minimum, maximum) {
    const input = document.getElementById(id);
    const raw = input.value.trim();
    input.removeAttribute('aria-invalid');
    if (!raw) {input.setAttribute('aria-invalid','true');input.focus();throw new Error('Enter all four coordinates.');}
    const value = Number(raw);
    if (!Number.isFinite(value) || value < minimum || value > maximum) {
      input.setAttribute('aria-invalid','true');input.focus();
      throw new Error(`${id.replace('-', ' ')} must be between ${minimum} and ${maximum} degrees.`);
    }
    return value;
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    try {
      fields.forEach(id=>document.getElementById(id).removeAttribute('aria-invalid'));
      const start = { lat: parseField('start-lat', -90, 90), lon: parseField('start-lon', -180, 180) };
      const end = { lat: parseField('end-lat', -90, 90), lon: parseField('end-lon', -180, 180) };
      setPoints(start, end);
      setSelectionMode('explore');
      feedback.textContent = 'Coordinates accepted. Calculating route…';
    } catch (error) { feedback.textContent = error.message; }
  });
  window.addEventListener('ares:mission', event => {
    const {start, end} = event.detail;
    const values = [start?.lat, start?.lon, end?.lat, end?.lon];
    fields.forEach((id, index) => {
      const input = document.getElementById(id);
      if (values[index] == null) input.value = '';
      else input.value = Number(values[index].toFixed(6)).toString();
    });
  });
})();

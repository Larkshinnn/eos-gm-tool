import { app } from '../shared.js';

const parseIds = (value) => [...new Set(value.split(/[\s,;]+/).map((part) => Number(part.trim())).filter((id) => Number.isInteger(id) && id > 0))];
const shuffle = (values) => {
  for (let i = values.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [values[i], values[j]] = [values[j], values[i]];
  }
  return values;
};

function placeBossWaves(waveCount, minGap, maxGap) {
  if (waveCount <= minGap) return [Math.floor(Math.random() * waveCount)];
  const maxEdgeWaves = Math.min(maxGap - 1, Math.floor((waveCount - 1) / 2));
  const arrangements = [];
  for (let start = 0; start <= maxEdgeWaves; start += 1) {
    for (let end = 0; end <= maxEdgeWaves && start + end < waveCount; end += 1) {
      const distance = waveCount - 1 - start - end;
      const minIntervals = Math.ceil(distance / maxGap);
      const maxIntervals = Math.floor(distance / minGap);
      if (distance === 0 || minIntervals <= maxIntervals) arrangements.push({ start, distance, minIntervals, maxIntervals });
    }
  }
  if (!arrangements.length) return [Math.floor(Math.random() * waveCount)];

  const arrangement = arrangements[Math.floor(Math.random() * arrangements.length)];
  if (arrangement.distance === 0) return [arrangement.start];
  const intervalCount = arrangement.minIntervals + Math.floor(Math.random() * (arrangement.maxIntervals - arrangement.minIntervals + 1));
  const positions = [arrangement.start];
  let remaining = arrangement.distance;
  for (let index = 0; index < intervalCount; index += 1) {
    const intervalsLeft = intervalCount - index - 1;
    const low = Math.max(minGap, remaining - intervalsLeft * maxGap);
    const high = Math.min(maxGap, remaining - intervalsLeft * minGap);
    const gap = low + Math.floor(Math.random() * (high - low + 1));
    positions.push(positions.at(-1) + gap);
    remaining -= gap;
  }
  return shuffle(positions);
}

export const initWarzoneGenerator = () => {
  const npcSelect = document.querySelector('#warzone-npc-list');
  const npcSearch = document.querySelector('#warzone-npc-search');
  const npcKindFilter = document.querySelector('#warzone-npc-kind-filter');
  const npcCatalogStatus = document.querySelector('#warzone-npc-catalog-status');
  const npcPrev = document.querySelector('#warzone-npc-prev');
  const npcNext = document.querySelector('#warzone-npc-next');
  const npcPagination = document.querySelector('#warzone-npc-pagination');
  let npcPage = 1;
  let npcTotalPages = 1;
  let npcTimer;
  const loadNpcCatalog = async (page = 1) => {
    if (!(npcSelect instanceof HTMLSelectElement)) return;
    npcPage = Math.max(1, page);
    if (npcCatalogStatus instanceof HTMLElement) npcCatalogStatus.textContent = app.translate('dashboard.warzoneNpcCatalogLoading');
    try {
      const query = new URLSearchParams({
        page: String(npcPage),
        page_size: '50',
        keyword: npcSearch instanceof HTMLInputElement ? npcSearch.value.trim() : '',
        bosses_only: npcKindFilter instanceof HTMLSelectElement && npcKindFilter.value === 'boss' ? 'true' : 'false',
      });
      const payload = await app.apiFetch(`/api/warzone/npcs?${query}`);
      npcPage = payload?.page ?? npcPage;
      npcTotalPages = payload?.total_pages ?? 1;
      const items = Array.isArray(payload?.items) ? payload.items : [];
      npcSelect.replaceChildren(...items.map((npc) => {
        const option = document.createElement('option');
        option.value = String(npc.npc_id);
        option.textContent = `${npc.is_boss ? 'Boss · ' : ''}${npc.name ? `${npc.name} · ` : ''}NPC ID ${npc.npc_id} · Type ${npc.type} · Attrib ${npc.attrib_id}`;
        return option;
      }));
      if (npcCatalogStatus instanceof HTMLElement) npcCatalogStatus.textContent = items.length ? '' : app.translate('dashboard.warzoneNpcCatalogEmpty');
      if (npcPagination instanceof HTMLElement) npcPagination.textContent = app.translate('dashboard.warzoneNpcPagination', { page: npcPage, totalPages: npcTotalPages, total: payload?.total ?? 0 });
    } catch (error) {
      npcSelect.replaceChildren();
      npcPage = 1;
      npcTotalPages = 1;
      const message = app.apiErrorMessage(error, 'dashboard.warzoneNpcCatalogUnavailable');
      if (npcCatalogStatus instanceof HTMLElement) npcCatalogStatus.textContent = message;
      if (npcPagination instanceof HTMLElement) npcPagination.textContent = '';
    }
    if (npcPrev instanceof HTMLButtonElement) npcPrev.disabled = npcPage <= 1;
    if (npcNext instanceof HTMLButtonElement) npcNext.disabled = npcPage >= npcTotalPages;
  };
  const addSelected = (targetSelector) => {
    if (!(npcSelect instanceof HTMLSelectElement)) return;
    const target = document.querySelector(targetSelector);
    if (!(target instanceof HTMLInputElement)) return;
    const current = parseIds(target.value);
    const selected = Array.from(npcSelect.selectedOptions).map((option) => Number(option.value)).filter(Number.isInteger);
    target.value = [...new Set([...current, ...selected])].join(', ');
  };
  void loadNpcCatalog();
  npcSearch?.addEventListener('input', () => {
    clearTimeout(npcTimer);
    npcTimer = setTimeout(() => void loadNpcCatalog(1), 250);
  });
  npcKindFilter?.addEventListener('change', () => void loadNpcCatalog(1));
  npcPrev?.addEventListener('click', () => void loadNpcCatalog(npcPage - 1));
  npcNext?.addEventListener('click', () => void loadNpcCatalog(npcPage + 1));
  document.querySelector('#warzone-npc-add-normal')?.addEventListener('click', () => addSelected('#warzone-normal-ids'));
  document.querySelector('#warzone-npc-add-boss')?.addEventListener('click', () => addSelected('#warzone-boss-ids'));

  const form = document.querySelector('#warzone-generator-form');
  if (!(form instanceof HTMLFormElement)) return;
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const normals = parseIds(document.querySelector('#warzone-normal-ids')?.value ?? '');
    const bosses = parseIds(document.querySelector('#warzone-boss-ids')?.value ?? '');
    const waveCount = Number(document.querySelector('#warzone-wave-count')?.value);
    const minGap = Number(document.querySelector('#warzone-boss-gap')?.value);
    const maxGap = Number(document.querySelector('#warzone-boss-max-gap')?.value);
    if (!normals.length || !Number.isInteger(waveCount) || waveCount < 1 || waveCount > 500 || !bosses.length || !Number.isInteger(minGap) || minGap < 1 || minGap > waveCount || !Number.isInteger(maxGap) || maxGap < minGap || maxGap > waveCount) {
      window.alert(app.translate('dashboard.warzoneGeneratorInvalid'));
      return;
    }
    const positions = placeBossWaves(waveCount, minGap, maxGap);
    const waves = Array(waveCount);
    positions.forEach((wave) => { waves[wave] = { id: bosses[Math.floor(Math.random() * bosses.length)], kind: 'boss' }; });
    for (let wave = 0; wave < waveCount; wave += 1) {
      if (!waves[wave]) waves[wave] = { id: normals[Math.floor(Math.random() * normals.length)], kind: 'normal' };
    }
    const body = document.querySelector('#warzone-generator-body');
    const results = document.querySelector('#warzone-generator-results');
    if (body instanceof HTMLElement) body.innerHTML = waves.map((entry, index) => `<tr><td>${index + 1}</td><td>${entry.id}</td><td>${app.translate(entry.kind === 'boss' ? 'dashboard.warzoneBoss' : 'dashboard.warzoneNormal')}</td></tr>`).join('');
    if (results instanceof HTMLElement) results.hidden = false;
  });

  const syncButton = document.querySelector('#warzone-huaxu-sync');
  const syncStatus = document.querySelector('#warzone-huaxu-sync-status');
  syncButton?.addEventListener('click', async () => {
    if (!(syncButton instanceof HTMLButtonElement)) return;
    syncButton.disabled = true;
    if (syncStatus instanceof HTMLElement) syncStatus.textContent = app.translate('dashboard.huaxuSyncLoading');
    try {
      const payload = await app.apiFetch('/api/warzone/sync/huaxu', { method: 'POST' });
      const warzone = payload?.warzone ?? {};
      const ppc = payload?.ppc ?? {};
      const updates = payload?.tableUpdates ?? {};
      const params = { warzone: warzone.activity ?? '-', ppc: ppc.activity ?? '', ppcRows: updates.ppcStageRows ?? 0, wzFields: updates.warzoneAreaFields ?? 0 };
      const noLocalChanges = params.ppcRows === 0 && params.wzFields === 0;
      if (syncStatus instanceof HTMLElement) syncStatus.textContent = app.translate(noLocalChanges ? 'dashboard.huaxuSyncAlreadyCurrent' : 'dashboard.huaxuSyncSuccess', params);
    } catch (error) {
      if (syncStatus instanceof HTMLElement) syncStatus.textContent = app.apiErrorMessage(error, 'dashboard.huaxuSyncFailed');
    } finally {
      syncButton.disabled = false;
    }
  });
};

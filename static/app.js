/* === Prologis Racking Design Engine — App Logic === */

(() => {
  'use strict';

  let currentStep = 0;
  const totalSteps = 6;

  // ═══ Wizard Navigation ═══
  window.goToStep = function(step) {
    if (step < 0 || step >= totalSteps) return;

    // Hide all stages
    document.querySelectorAll('.stage').forEach(s => {
      s.classList.remove('active');
    });

    // Show target stage
    const target = document.getElementById('stage-' + step);
    if (target) {
      target.classList.add('active');
    }

    // Update sidebar tabs
    document.querySelectorAll('.step-tab').forEach(tab => {
      tab.classList.remove('active');
      if (parseInt(tab.dataset.step) === step) {
        tab.classList.add('active');
      }
    });

    currentStep = step;

    // Scroll content to top
    const main = document.getElementById('mainContent');
    if (main) main.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Initialize on load
  document.addEventListener('DOMContentLoaded', () => {
    goToStep(0);
  });

  // ═══ Deal Save/Load ═══
  window.toggleDealMenu = function() {
    const dd = document.getElementById('dealDropdown');
    dd.classList.toggle('open');
    if (dd.classList.contains('open')) loadDealList();
  };

  window.saveDeal = function() {
    const name = document.getElementById('projectName')?.value || 'Untitled Deal';
    const dealId = 'deal_' + Date.now();
    const deal = { id: dealId, name, savedAt: new Date().toISOString(), step: currentStep };
    localStorage.setItem(dealId, JSON.stringify(deal));
    document.getElementById('currentDealName').textContent = name;
    showToast('Deal saved!');
  };

  window.newDeal = function() {
    document.getElementById('currentDealName').textContent = 'New Deal';
    document.getElementById('dealDropdown').classList.remove('open');
    goToStep(0);
  };

  function loadDealList() {
    const list = document.getElementById('dealList');
    if (!list) return;
    list.innerHTML = '';
    const keys = Object.keys(localStorage).filter(k => k.startsWith('deal_'));
    if (keys.length === 0) {
      list.innerHTML = '<div style="padding:12px 16px;color:var(--gray-400);font-size:13px;">No saved deals</div>';
      return;
    }
    keys.sort().reverse().forEach(k => {
      try {
        const deal = JSON.parse(localStorage.getItem(k));
        const item = document.createElement('div');
        item.style.cssText = 'padding:10px 16px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);transition:background 0.15s;';
        item.textContent = deal.name || 'Untitled';
        item.onmouseenter = () => item.style.background = 'var(--gray-bg)';
        item.onmouseleave = () => item.style.background = '';
        item.onclick = () => {
          document.getElementById('currentDealName').textContent = deal.name;
          document.getElementById('dealDropdown').classList.remove('open');
          if (deal.step != null) goToStep(deal.step);
        };
        list.appendChild(item);
      } catch(e) {}
    });
  }

  function showToast(msg) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.style.cssText = 'background:var(--teal-dark);color:white;padding:10px 20px;border-radius:8px;font-size:13px;font-weight:500;box-shadow:0 4px 12px rgba(0,0,0,0.15);';
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.3s'; }, 2000);
    setTimeout(() => toast.remove(), 2400);
  }

  // Close deal dropdown when clicking outside
  document.addEventListener('click', (e) => {
    const dd = document.getElementById('dealDropdown');
    const btn = document.getElementById('dealMenuBtn');
    if (dd && !dd.contains(e.target) && btn && !btn.contains(e.target)) {
      dd.classList.remove('open');
    }
  });

  // ═══ Seismic Lookup ═══
  window.lookupSeismic = async function() {
    const addr = document.getElementById('address')?.value;
    if (!addr) return;
    const btn = document.getElementById('seismicBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="material-icons-outlined" style="animation:spin 0.7s linear infinite">refresh</span> Looking up...';
    try {
      const resp = await fetch('/api/seismic?address=' + encodeURIComponent(addr));
      const json = await resp.json();
      if (json.status === 'ok' && json.data) {
        const d = json.data;
        const s = d.seismic || {};
        const r = d.requirements || {};
        document.getElementById('seismicResult').classList.remove('hidden');
        document.getElementById('seismicContent').innerHTML = `
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;font-size:13px;">
            <div><strong>SDC:</strong> ${s.sdc || '—'}</div>
            <div><strong>SDS:</strong> ${(s.sds || 0).toFixed(3)}</div>
            <div><strong>SD1:</strong> ${(s.sd1 || 0).toFixed(3)}</div>
            <div><strong>Anchors/Frame:</strong> ${r.anchors_per_frame || '—'}</div>
            <div><strong>Anchor Type:</strong> ${r.anchor_type || '—'}</div>
            <div><strong>Building Code:</strong> ${r.building_code || '—'}</div>
          </div>`;
      }
    } catch (e) {
      console.error('Seismic lookup error:', e);
    }
    btn.disabled = false;
    btn.innerHTML = '<span class="material-icons-outlined">search</span> Lookup';
  };

  // ═══ Layout Generation ═══
  window.generateLayout = async function() {
    const btn = document.getElementById('generateLayoutBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="material-icons-outlined" style="animation:spin 0.7s linear infinite">refresh</span> Generating...';
    try {
      const building = {
        length_ft: parseFloat(document.getElementById('buildingLength')?.value) || 600,
        width_ft: parseFloat(document.getElementById('buildingWidth')?.value) || 300,
        clear_height_ft: parseFloat(document.getElementById('clearHeight')?.value) || 32,
        dock_side: document.getElementById('dockSide')?.value || 'south',
        num_dock_doors: parseInt(document.getElementById('numDocks')?.value) || 15,
        column_grid_x_ft: parseFloat(document.getElementById('columnGridX')?.value) || 0,
        column_grid_y_ft: parseFloat(document.getElementById('columnGridY')?.value) || 0,
      };
      const requirements = {
        rack_style: document.getElementById('rackStyle')?.value || 'teardrop',
        rack_type: document.getElementById('rackType')?.value || 'selective',
        frame_depth_in: parseInt(document.getElementById('frameDepth')?.value) || 42,
        forklift_type: document.getElementById('forkliftType')?.value || 'reach',
        pallet_size: document.getElementById('palletSize')?.value || '48x40',
        min_staging_depth_ft: parseFloat(document.getElementById('stagingDepth')?.value) || 50,
        target_pallet_positions: parseInt(document.getElementById('targetPP')?.value) || 0,
        new_or_used: document.getElementById('newOrUsed')?.value || 'new',
      };
      const addr = document.getElementById('address')?.value || '';
      const resp = await fetch('/api/design', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: addr,
          building,
          requirements,
          project_name: document.getElementById('projectName')?.value || '',
          client: document.getElementById('clientName')?.value || '',
        })
      });
      const data = await resp.json();
      const layout = data.layout;
      if (layout) {
        const summary = document.getElementById('layoutSummary');
        summary.classList.remove('hidden');
        document.getElementById('layoutSummaryContent').innerHTML = `
          <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;font-size:14px;">
            <div><strong>Pallet Positions:</strong> ${(layout.total_pallet_positions || 0).toLocaleString()}</div>
            <div><strong>Total Bays:</strong> ${(layout.total_bays || 0).toLocaleString()}</div>
            <div><strong>Rows:</strong> ${layout.total_rows || 0}</div>
            <div><strong>Frames:</strong> ${(layout.total_frames || 0).toLocaleString()}</div>
            <div><strong>Frame Height:</strong> ${layout.frame_height_in || 0}" (${((layout.frame_height_in || 0) / 12).toFixed(0)}ft)</div>
            <div><strong>Beam Levels:</strong> ${layout.beam_levels || 0}</div>
            <div><strong>Beam Length:</strong> ${layout.beam_length_in || 0}"</div>
            <div><strong>Utilization:</strong> ${layout.utilization_pct || 0}%</div>
          </div>
          ${(layout.notes || []).length ? '<div style="margin-top:12px;font-size:12px;color:var(--gray-400);">' + layout.notes.map(n => '• ' + n).join('<br>') + '</div>' : ''}
          ${(layout.warnings || []).length ? '<div style="margin-top:8px;font-size:12px;color:#e74c3c;">' + layout.warnings.map(w => '⚠ ' + w).join('<br>') + '</div>' : ''}
        `;
        showToast('Layout generated!');
      }
    } catch (e) {
      console.error('Layout generation error:', e);
      showToast('Layout generation failed — check console');
    }
    btn.disabled = false;
    btn.innerHTML = '<span class="material-icons-outlined">auto_fix_high</span> Generate Layout';
  };

  // ═══ BOM Recalculate ═══
  window.recalculateBOM = function() {
    showToast('BOM recalculation coming soon');
  };

  // ═══ XLSX Download ═══
  window.downloadXLSX = async function() {
    const btn = document.getElementById('downloadXlsxBtn');
    btn.disabled = true;
    try {
      const resp = await fetch('/api/generate-xlsx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: document.getElementById('projectName')?.value || 'Deal',
          client: document.getElementById('clientName')?.value || '',
          bay_type_details: [],
          bom_items: [],
          summary: {},
        })
      });
      if (!resp.ok) throw new Error('Download failed');
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'Pricing_Model.xlsx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed: ' + e.message);
    }
    btn.disabled = false;
  };

  // ═══ Stubs ═══
  window.onBuildingChange = function() {};
  window.onMarketChange = function() {};
  window.onLayoutChange = function() {};
  window.onFloorPlanUpload = function(e) {
    const file = e.target?.files?.[0];
    if (file) {
      const el = document.getElementById('uploadedFile');
      if (el) {
        el.classList.remove('hidden');
        el.innerHTML = '<span class="material-icons-outlined">insert_drive_file</span> ' + file.name;
      }
    }
  };

})();

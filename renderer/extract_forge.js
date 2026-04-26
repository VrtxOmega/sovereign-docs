/* ──────────────────────────────────────────────────────────────────
 *  extract_forge.js — EXTRACT (OCR) + FORGE (ASCII) tab logic
 *  Loaded after CodeMirror init in index.html.
 *  Depends on:
 *    - window.cmEditor (set by initEditor)
 *    - window.setStatus()
 *    - Tesseract (loaded from CDN)
 * ────────────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  // ════════════════════════════════════════════════════════════════
  //  Shared helpers
  // ════════════════════════════════════════════════════════════════
  function $(id) { return document.getElementById(id); }

  function bindDrop(zone, onFile) {
    zone.addEventListener('click', () => zone.querySelector('input[type=file]').click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
      e.preventDefault();
      zone.classList.remove('drag-over');
      const f = e.dataTransfer.files[0];
      if (f) onFile(f);
    });
    zone.querySelector('input[type=file]').addEventListener('change', e => {
      if (e.target.files[0]) onFile(e.target.files[0]);
    });
  }

  function downloadBlob(filename, content, mime) {
    const blob = new Blob([content], { type: mime });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  function activateTab(tabName) {
    const btn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (btn) btn.click();
  }

  // ════════════════════════════════════════════════════════════════
  //  EXTRACT (OCR) — Tesseract.js
  // ════════════════════════════════════════════════════════════════
  const ocr = {
    drop:        $('ocr-drop'),
    input:       $('ocr-input'),
    previewWrap: $('ocr-preview-wrap'),
    preview:     $('ocr-preview'),
    progressBox: $('ocr-progress'),
    progressFill:$('ocr-progress-fill'),
    progressLbl: $('ocr-progress-label'),
    output:      $('ocr-output'),
    meta:        $('ocr-meta'),
    lang:        $('ocr-language'),
    btnCopy:     $('ocr-copy'),
    btnDownload: $('ocr-download'),
    btnSend:     $('ocr-send'),
    btnClear:    $('ocr-clear'),
  };

  function ocrSetButtons(enabled) {
    ocr.btnCopy.disabled = !enabled;
    ocr.btnDownload.disabled = !enabled;
    ocr.btnSend.disabled = !enabled;
  }

  function ocrReset() {
    ocr.preview.removeAttribute('src');
    ocr.previewWrap.classList.add('hidden');
    ocr.drop.style.display = '';
    ocr.output.value = '';
    ocr.meta.textContent = '';
    ocr.progressBox.classList.add('hidden');
    ocr.progressFill.style.width = '0%';
    ocrSetButtons(false);
  }

  async function ocrRun(file) {
    if (!file.type.startsWith('image/')) {
      ocr.output.value = 'Error: not an image file.';
      return;
    }
    if (typeof Tesseract === 'undefined') {
      ocr.output.value = 'Error: Tesseract.js failed to load. Check internet connection.';
      return;
    }

    const url = URL.createObjectURL(file);
    ocr.preview.src = url;
    ocr.previewWrap.classList.remove('hidden');
    ocr.drop.style.display = 'none';
    ocr.output.value = '';
    ocr.meta.textContent = '';
    ocr.progressBox.classList.remove('hidden');
    ocr.progressFill.style.width = '0%';
    ocr.progressLbl.textContent = 'Initializing\u2026';
    ocrSetButtons(false);
    if (window.setStatus) window.setStatus('Extracting text\u2026', 'busy');

    const startedAt = performance.now();

    try {
      const { data } = await Tesseract.recognize(file, ocr.lang.value || 'eng', {
        logger: m => {
          if (m.status) ocr.progressLbl.textContent = m.status.toUpperCase();
          if (typeof m.progress === 'number') {
            ocr.progressFill.style.width = (m.progress * 100).toFixed(0) + '%';
          }
        }
      });

      const text = (data.text || '').trim();
      const elapsed = ((performance.now() - startedAt) / 1000).toFixed(2);

      ocr.output.value = text;
      ocr.meta.textContent = `${text.length} chars \u00b7 ${elapsed}s \u00b7 ${(data.confidence || 0).toFixed(0)}% conf`;
      ocr.progressFill.style.width = '100%';
      ocr.progressLbl.textContent = 'COMPLETE';
      ocrSetButtons(text.length > 0);
      if (window.setStatus) window.setStatus('Extraction complete', 'success');
      setTimeout(() => ocr.progressBox.classList.add('hidden'), 800);
    } catch (e) {
      console.error('[OCR] Failed:', e);
      ocr.output.value = 'Error: ' + (e.message || 'OCR failed');
      ocr.progressLbl.textContent = 'FAILED';
      ocr.progressFill.style.width = '0%';
      if (window.setStatus) window.setStatus('Extraction failed', 'error');
    } finally {
      URL.revokeObjectURL(url);
      if (window.setStatus) setTimeout(() => window.setStatus('Ready'), 4000);
    }
  }

  function wireOcr() {
    bindDrop(ocr.drop, ocrRun);

    ocr.btnClear.addEventListener('click', ocrReset);

    ocr.btnCopy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(ocr.output.value);
        ocr.meta.textContent = 'Copied \u2713';
      } catch {
        ocr.meta.textContent = 'Copy failed';
      }
    });

    ocr.btnDownload.addEventListener('click', () => {
      const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      downloadBlob(`extracted_${stamp}.txt`, ocr.output.value, 'text/plain');
    });

    ocr.btnSend.addEventListener('click', () => {
      const text = ocr.output.value;
      if (!text) return;

      activateTab('create');

      setTimeout(() => {
        if (window.cmEditor) {
          const cur = window.cmEditor.getValue().trim();
          const next = cur ? cur + '\n\n' + text : text;
          window.cmEditor.setValue(next);
          window.cmEditor.refresh();
          window.cmEditor.focus();
        } else {
          const ta = document.getElementById('editor');
          if (ta) ta.value = (ta.value.trim() ? ta.value.trim() + '\n\n' : '') + text;
        }
        if (window.setStatus) window.setStatus('Text sent to editor', 'success');
        setTimeout(() => window.setStatus && window.setStatus('Ready'), 3000);
      }, 100);
    });
  }

  // ════════════════════════════════════════════════════════════════
  //  FORGE (ASCII)
  // ════════════════════════════════════════════════════════════════
  const CHARSETS = {
    detailed: ' .\':"!*+=#%@',
    classic:  ' .:-=+*#%@',
    blocks:   ' \u2591\u2592\u2593\u2588',
    minimal:  ' .#',
  };

  const forge = {
    drop:        $('forge-drop'),
    input:       $('forge-input'),
    previewWrap: $('forge-preview-wrap'),
    preview:     $('forge-preview'),
    output:      $('forge-output'),
    meta:        $('forge-meta'),
    btnCopy:     $('forge-copy'),
    btnDownload: $('forge-download'),
    btnSend:     $('forge-send'),
    btnClear:    $('forge-clear'),
    width:       $('forge-width'),
    widthVal:    $('forge-width-val'),
    charset:     $('forge-charset'),
    style:       $('forge-style'),
    invert:      $('forge-invert'),
  };

  let forgeImage = null;
  let forgeDebounce = null;
  let forgePlainCache = '';
  let forgeHtmlCache  = '';

  function forgeSetButtons(enabled) {
    forge.btnCopy.disabled = !enabled;
    forge.btnDownload.disabled = !enabled;
    forge.btnSend.disabled = !enabled;
  }

  function forgeReset() {
    forgeImage = null;
    forge.preview.removeAttribute('src');
    forge.previewWrap.classList.add('hidden');
    forge.drop.style.display = '';
    forge.output.innerHTML = '<div class="forge-output-empty">Drop an image to begin\u2026</div>';
    forge.meta.textContent = '';
    forgePlainCache = '';
    forgeHtmlCache = '';
    forgeSetButtons(false);
  }

  function forgeLoad(file) {
    if (!file.type.startsWith('image/')) {
      forge.output.innerHTML = '<div class="forge-output-empty" style="color:var(--fatal)">Not an image file.</div>';
      return;
    }
    const img = new Image();
    img.onload = () => {
      if (Math.max(img.width, img.height) > 4000) {
        forge.output.innerHTML = '<div class="forge-output-empty" style="color:var(--fatal)">Image too large (max 4000px).</div>';
        return;
      }
      forgeImage = img;
      forge.preview.src = img.src;
      forge.previewWrap.classList.remove('hidden');
      forge.drop.style.display = 'none';
      forgeRender();
    };
    img.onerror = () => {
      forge.output.innerHTML = '<div class="forge-output-empty" style="color:var(--fatal)">Failed to load image.</div>';
    };
    img.src = URL.createObjectURL(file);
  }

  function forgeRender() {
    if (!forgeImage) return;
    const startedAt = performance.now();

    const targetW = parseInt(forge.width.value, 10) || 120;
    forge.widthVal.textContent = targetW;

    const aspect = forgeImage.height / forgeImage.width;
    const targetH = Math.max(8, Math.floor(targetW * aspect * 0.5));

    const canvas = document.createElement('canvas');
    canvas.width = targetW;
    canvas.height = targetH;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(forgeImage, 0, 0, targetW, targetH);
    const px = ctx.getImageData(0, 0, targetW, targetH).data;

    const chars = (CHARSETS[forge.charset.value] || CHARSETS.detailed).split('');
    const C = chars.length;
    const invert = forge.invert.checked;
    const styleMode = forge.style.value;

    const lines = [];
    const plainLines = [];

    for (let y = 0; y < targetH; y++) {
      let htmlLine = '';
      let plainLine = '';
      for (let x = 0; x < targetW; x++) {
        const i = (y * targetW + x) * 4;
        const r = px[i], g = px[i + 1], b = px[i + 2], a = px[i + 3];

        const alpha = a / 255;
        const rr = r * alpha + 255 * (1 - alpha);
        const gg = g * alpha + 255 * (1 - alpha);
        const bb = b * alpha + 255 * (1 - alpha);

        let lum = (0.299 * rr + 0.587 * gg + 0.114 * bb) / 255;
        if (invert) lum = 1 - lum;

        const idx = Math.min(C - 1, Math.max(0, Math.round(lum * (C - 1))));
        let ch = chars[idx];
        plainLine += ch;

        if (ch === '<') ch = '&lt;';
        else if (ch === '>') ch = '&gt;';
        else if (ch === '&') ch = '&amp;';

        if (styleMode === 'color') {
          htmlLine += `<span style="color:rgb(${r|0},${g|0},${b|0})">${ch}</span>`;
        } else {
          htmlLine += ch;
        }
      }
      lines.push(htmlLine);
      plainLines.push(plainLine);
    }

    const plain = plainLines.join('\n');
    let outerColor;
    if (styleMode === 'mono-gold') outerColor = 'color:#C9A84C;';
    else if (styleMode === 'mono') outerColor = 'color:#F5EDD6;';
    else outerColor = '';

    const html = `<pre style="${outerColor}">${lines.join('\n')}</pre>`;

    forge.output.innerHTML = html;
    forgePlainCache = plain;
    forgeHtmlCache  = html;

    const elapsed = ((performance.now() - startedAt) / 1000).toFixed(2);
    forge.meta.textContent = `${targetW}\u00d7${targetH} \u00b7 ${elapsed}s`;
    forgeSetButtons(true);
  }

  function forgeRenderDebounced() {
    clearTimeout(forgeDebounce);
    forgeDebounce = setTimeout(forgeRender, 120);
  }

  function wireForge() {
    bindDrop(forge.drop, forgeLoad);
    forge.btnClear.addEventListener('click', forgeReset);

    [forge.width, forge.charset, forge.style, forge.invert].forEach(el => {
      const ev = el.type === 'checkbox' || el.tagName === 'SELECT' ? 'change' : 'input';
      el.addEventListener(ev, forgeRenderDebounced);
    });
    forge.width.addEventListener('input', () => {
      forge.widthVal.textContent = forge.width.value;
    });

    forge.btnCopy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(forgePlainCache);
        forge.meta.textContent = 'Plain text copied \u2713';
      } catch {
        forge.meta.textContent = 'Copy failed';
      }
    });

    forge.btnDownload.addEventListener('click', () => {
      if (!forgeHtmlCache) return;
      const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const wrapped = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>ASC11 Forge \u2014 ${stamp}</title>
<style>
  body { background:#000; padding:20px; }
  pre { font-family:'JetBrains Mono','Courier New',monospace; font-size:8px; line-height:1.0; white-space:pre; color:#e0e0e0; }
</style></head>
<body>${forgeHtmlCache}</body></html>`;
      downloadBlob(`asc11_${stamp}.html`, wrapped, 'text/html');
    });

    forge.btnSend.addEventListener('click', () => {
      if (!forgePlainCache) return;
      activateTab('create');
      const block = '```\n' + forgePlainCache + '\n```';
      setTimeout(() => {
        if (window.cmEditor) {
          const cur = window.cmEditor.getValue().trim();
          const next = cur ? cur + '\n\n' + block : block;
          window.cmEditor.setValue(next);
          window.cmEditor.refresh();
          window.cmEditor.focus();
        }
        if (window.setStatus) window.setStatus('ASCII inserted into editor', 'success');
        setTimeout(() => window.setStatus && window.setStatus('Ready'), 3000);
      }, 100);
    });
  }

  // ════════════════════════════════════════════════════════════════
  //  Init when DOM is ready
  // ════════════════════════════════════════════════════════════════
  function init() {
    if (ocr.drop) wireOcr();
    if (forge.drop) wireForge();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

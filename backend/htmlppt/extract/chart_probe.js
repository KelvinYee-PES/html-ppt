// chart_probe.js — find live chart instances in the page and normalise their data.
// Marks each chart's host element with data-hp-chart="<index>" so the DOM walker
// can emit a chart node instead of descending into canvas/svg internals.
// Exposes: window.__hpProbeCharts() -> [{index, lib, spec}]
(function () {
  function hex(c) {
    if (!c || typeof c !== 'string') return null;
    c = c.trim();
    if (c[0] === '#') {
      let h = c.slice(1);
      if (h.length === 3 || h.length === 4) h = h.split('').slice(0, 3).map(x => x + x).join('');
      return h.slice(0, 6).toUpperCase();
    }
    const m = c.match(/rgba?\(([^)]+)\)/i);
    if (m) {
      const p = m[1].split(/[ ,/]+/).filter(Boolean).map(parseFloat);
      return p.slice(0, 3).map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('').toUpperCase();
    }
    // named colours / hsl: resolve through the browser
    const d = document.createElement('div');
    d.style.color = c; document.body.appendChild(d);
    const r = getComputedStyle(d).color; d.remove();
    return r && r !== c ? hex(r) : null;
  }
  function firstColor(v) { return Array.isArray(v) ? hex(v[0]) : hex(v); }
  function num(v) {
    if (v == null) return null;
    if (typeof v === 'number') return v;
    if (typeof v === 'object') { if ('y' in v) return num(v.y); if ('value' in v) return num(v.value); }
    const f = parseFloat(String(v).replace(/[^0-9.\-eE]/g, ''));
    return isNaN(f) ? null : f;
  }
  function text(v) {
    if (v == null) return '';
    if (typeof v === 'string') return v;
    if (typeof v === 'object' && v.text) return String(v.text);
    if (Array.isArray(v)) return v.join(' ');
    return String(v);
  }

  function chartjs(out) {
    const C = window.Chart;
    if (!C) return;
    let inst = [];
    if (C.instances) inst = Array.isArray(C.instances) ? C.instances : Object.values(C.instances);
    for (const ch of inst) {
      try {
        const cfg = ch.config || {};
        const type0 = (cfg.type || (cfg._config && cfg._config.type) || 'bar');
        const opts = ch.options || cfg.options || {};
        const data = ch.data || cfg.data || {};
        const scales = opts.scales || {};
        const xs = scales.x || (scales.xAxes && scales.xAxes[0]) || {};
        const ys = scales.y || (scales.yAxes && scales.yAxes[0]) || {};
        const pieLike = ['pie', 'doughnut', 'polarArea'].includes(type0);
        const spec = {
          type: type0 === 'polarArea' ? 'pie' : (type0 === 'horizontalBar' ? 'bar' : type0),
          horizontal: opts.indexAxis === 'y' || type0 === 'horizontalBar',
          stacked: !!(xs.stacked || ys.stacked),
          title: text(opts.plugins && opts.plugins.title && opts.plugins.title.display !== false ? opts.plugins.title.text : (opts.title && opts.title.text)),
          categories: (data.labels || []).map(text),
          series: (data.datasets || []).map(ds => ({
            name: text(ds.label),
            values: (ds.data || []).map(num),
            color: pieLike ? null : (firstColor(ds.borderColor && (ds.type === 'line' || type0 === 'line') ? ds.borderColor : ds.backgroundColor)),
            colors: pieLike && Array.isArray(ds.backgroundColor) ? ds.backgroundColor.map(hex) : null,
            type: ds.type || null,
            fill: !!ds.fill,
          })),
          x_title: text(xs.title && xs.title.display !== false ? xs.title.text : ''),
          y_title: text(ys.title && ys.title.display !== false ? ys.title.text : ''),
          show_legend: !(opts.plugins && opts.plugins.legend && opts.plugins.legend.display === false),
        };
        if (type0 === 'line' && spec.series.some(s => s.fill)) spec.type = 'area';
        if (type0 === 'scatter' || type0 === 'bubble') {
          spec.type = 'scatter';
          spec.series = (data.datasets || []).map(ds => ({
            name: text(ds.label), xy: (ds.data || []).map(p => [num(p.x), num(p.y)]),
            color: firstColor(ds.backgroundColor || ds.borderColor),
          }));
        }
        const host = ch.canvas;
        if (host) { host.setAttribute('data-hp-chart', out.length); out.push({ index: out.length, lib: 'chartjs', spec }); }
      } catch (e) { /* ignore broken chart */ }
    }
  }

  function echarts(out) {
    const E = window.echarts;
    if (!E || !E.getInstanceByDom) return;
    document.querySelectorAll('[_echarts_instance_]').forEach(el => {
      try {
        const inst = E.getInstanceByDom(el); if (!inst) return;
        const o = inst.getOption();
        const series = o.series || [];
        if (!series.length) return;
        const s0 = series[0];
        const xa = (o.xAxis || [])[0] || {}, ya = (o.yAxis || [])[0] || {};
        const horizontal = ya.type === 'category';
        const cat = horizontal ? ya : xa;
        const type0 = s0.type;
        const spec = {
          type: type0, horizontal, stacked: series.some(s => s.stack),
          title: text(((o.title || [])[0] || {}).text),
          categories: (cat.data || []).map(d => text(typeof d === 'object' && d ? d.value : d)),
          series: [], x_title: text(xa.name), y_title: text(ya.name),
          show_legend: !!((o.legend || [])[0]),
        };
        if (type0 === 'pie') {
          const d = s0.data || [];
          spec.type = (Array.isArray(s0.radius) && parseFloat(s0.radius[0]) > 0) ? 'doughnut' : 'pie';
          spec.categories = d.map(x => text(x.name));
          spec.series = [{ name: text(s0.name), values: d.map(x => num(x.value)), colors: d.map(x => x.itemStyle ? hex(x.itemStyle.color) : null) }];
        } else if (type0 === 'radar') {
          const ind = ((o.radar || [])[0] || {}).indicator || [];
          spec.categories = ind.map(i => text(i.name));
          spec.series = (s0.data || []).map(d => ({ name: text(d.name), values: (d.value || []).map(num) }));
        } else if (type0 === 'scatter') {
          spec.series = series.map(s => ({ name: text(s.name), xy: (s.data || []).map(p => [num(p[0]), num(p[1])]) }));
        } else {
          spec.series = series.filter(s => ['bar', 'line'].includes(s.type)).map(s => ({
            name: text(s.name), values: (s.data || []).map(num), type: s.type,
            color: s.itemStyle && typeof s.itemStyle.color === 'string' ? hex(s.itemStyle.color) : null,
            fill: !!s.areaStyle,
          }));
          if (type0 === 'line' && spec.series.every(s => s.fill)) spec.type = 'area';
        }
        el.setAttribute('data-hp-chart', out.length);
        out.push({ index: out.length, lib: 'echarts', spec });
      } catch (e) { }
    });
  }

  function plotly(out) {
    document.querySelectorAll('.js-plotly-plot').forEach(el => {
      try {
        const traces = el.data || []; if (!traces.length) return;
        const layout = el.layout || {};
        const t0 = traces[0];
        const ttl = layout.title && (layout.title.text || layout.title);
        const spec = { type: 'bar', horizontal: t0.orientation === 'h', stacked: layout.barmode === 'stack',
          title: text(ttl), categories: [], series: [],
          x_title: text(layout.xaxis && layout.xaxis.title && (layout.xaxis.title.text || layout.xaxis.title)),
          y_title: text(layout.yaxis && layout.yaxis.title && (layout.yaxis.title.text || layout.yaxis.title)),
          show_legend: layout.showlegend !== false };
        if (t0.type === 'pie') {
          spec.type = t0.hole ? 'doughnut' : 'pie';
          spec.categories = (t0.labels || []).map(text);
          spec.series = [{ name: text(t0.name), values: (t0.values || []).map(num), colors: t0.marker && t0.marker.colors ? t0.marker.colors.map(hex) : null }];
        } else if (t0.type === 'scatter' && t0.mode === 'markers') {
          spec.type = 'scatter';
          spec.series = traces.map(t => ({ name: text(t.name), xy: (t.x || []).map((x, i) => [num(x), num((t.y || [])[i])]) }));
        } else {
          const isLine = t0.type === 'scatter';
          spec.type = isLine ? ((t0.fill && t0.fill !== 'none') ? 'area' : 'line') : 'bar';
          const catKey = spec.horizontal ? 'y' : 'x', valKey = spec.horizontal ? 'x' : 'y';
          spec.categories = (t0[catKey] || []).map(text);
          spec.series = traces.map(t => ({ name: text(t.name), values: (t[valKey] || []).map(num),
            color: t.marker && typeof t.marker.color === 'string' ? hex(t.marker.color) : (t.line && t.line.color ? hex(t.line.color) : null),
            type: t.type === 'bar' ? 'bar' : 'line' }));
        }
        el.setAttribute('data-hp-chart', out.length);
        out.push({ index: out.length, lib: 'plotly', spec });
      } catch (e) { }
    });
  }

  window.__hpHex = hex;
  window.__hpProbeCharts = function () {
    const out = [];
    chartjs(out); echarts(out); plotly(out);
    return out;
  };
})();

#!/usr/bin/env python3
"""Five-capture Alice / Aufake3D / genuine AU8830 stereo WAV analysis.

Audio DSP is never asserted to be equivalent merely from summary measurements.
Requires numpy/scipy; optional matplotlib for plots. Windows 10 / Debian; does
not need to run on the Windows 98 machine.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

EXPECTED = ["alice2000_windows", "alice2000_wine", "alice2011_windows",
            "alice2011_wine", "alice2000_vortex2_win98"]
GROUPS = {
    "alice2000": ["alice2000_windows", "alice2000_wine", "alice2000_vortex2_win98"],
    "alice2011": ["alice2011_windows", "alice2011_wine"],
}
PAIRS = [
    ("alice2000_windows", "alice2000_wine"),
    ("alice2000_windows", "alice2000_vortex2_win98"),
    ("alice2000_wine", "alice2000_vortex2_win98"),
    ("alice2011_windows", "alice2011_wine"),
]
BANDS = [(250, 1000), (1000, 4000), (4000, 12000)]


def read_audio(path):
    import numpy as np
    from scipy.io import wavfile
    rate, audio = wavfile.read(str(path))
    if len(audio.shape) != 2 or audio.shape[1] != 2:
        raise ValueError(f"{path}: expected exactly TWO channels (stereo)")
    if len(audio) < rate * 2:
        raise ValueError(f"{path}: expected at least two seconds")
    if audio.dtype.kind == 'f':
        samples = audio.astype(np.float32)
    elif audio.dtype.kind == 'i':
        # SciPy left-aligns 24-bit PCM in signed int32.
        samples = audio.astype(np.float32) / float(1 << (8 * audio.dtype.itemsize - 1))
    elif audio.dtype.kind == 'u' and audio.dtype.itemsize == 1:
        samples = (audio.astype(np.float32) - 128) / 128
    else:
        raise ValueError(f"{path}: unsupported WAV format {audio.dtype}")
    if not np.isfinite(samples).all():
        raise ValueError(f"{path}: non-finite samples")
    return int(rate), samples


def db(x):
    return 20.0 * math.log10(max(float(x), 1e-14))


def env(audio, rate, step=0.025):
    """~25ms log RMS envelope for approximate event synchronization."""
    import numpy as np
    hop = max(1, round(rate * step))
    frames = len(audio) // hop
    if frames < 30:
        raise ValueError("Too few samples for alignment")
    x = audio[:frames * hop].reshape(frames, hop, 2).astype(np.float64)
    level = np.sqrt(np.mean(x * x, axis=(1, 2)))
    return 20 * np.log10(np.maximum(level, 1e-7)), hop


def similarity(x, y, min_std=1e-7):
    import numpy as np
    n = min(len(x), len(y))
    if n < 1:
        return None
    a, b = x[:n].astype(np.float64), y[:n].astype(np.float64)
    if np.std(a) < min_std or np.std(b) < min_std:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def estimate_lag(reference, target, rate, limit_seconds):
    """Signed target-vs-reference envelope lag, positive => skip target.

    Correlation finds event structure, not sample-exact alignment. A deliberately
    conservative normalized score discourages matching very short overlaps.
    """
    import numpy as np
    from scipy.signal import correlate, correlation_lags
    x, hop = env(reference, rate)
    y, _ = env(target, rate)
    if np.std(x) < .2 or np.std(y) < .2:
        return 0, None
    xc, yc = x - np.mean(x), y - np.mean(y)
    corr = correlate(yc, xc, mode="full", method="fft")
    lags = correlation_lags(len(y), len(x), mode="full")
    upper = round(limit_seconds * rate / hop)
    # FFT ranks candidate shifts; normalized Pearson refines top candidates.
    allow = (np.abs(lags) <= upper)
    allow &= (np.minimum(len(x), len(y)) - np.abs(lags) >= int(4 * rate / hop))
    if not allow.any():
        return 0, None
    overlap = np.minimum(len(x), len(y)) - np.abs(lags)
    scale = np.maximum(overlap, 1)
    scores = np.where(allow, corr / scale, -np.inf)
    indices = np.argpartition(scores, -min(25, len(scores)))[-min(25, len(scores)):]
    best = None
    for ix in indices:
        if not allow[ix]:
            continue
        lag = int(lags[ix])
        astart, bstart = max(0, -lag), max(0, lag)
        n = min(len(x) - astart, len(y) - bstart)
        quality = similarity(x[astart:astart+n], y[bstart:bstart+n], min_std=.06)
        if quality is None:
            continue
        # Prefer good structure matches that preserve most of the recording.
        quality_adjusted = quality * (.96 + .04 * n / max(len(x), len(y)))
        if best is None or quality_adjusted > best[0]:
            best = (quality_adjusted, lag, quality)
    if best is None:
        return 0, None
    return int(best[1] * hop), float(best[2])


def stats(samples, rate):
    import numpy as np
    from scipy.signal import welch
    a = samples.astype(np.float64, copy=False)
    left, right = a[:, 0], a[:, 1]
    mid = (left + right) * .5
    side = (left - right) * .5
    rms_left = np.sqrt(np.mean(left * left))
    rms_right = np.sqrt(np.mean(right * right))
    midpow, sidepow = np.mean(mid * mid), np.mean(side * side)
    corr = similarity(left, right)
    output = {
        "left_rms_dbfs": round(db(rms_left), 5),
        "right_rms_dbfs": round(db(rms_right), 5),
        "peak_dbfs": round(db(np.max(np.abs(a))), 5),
        "lr_correlation": None if corr is None else round(corr, 6),
        "side_mid_db": round(db(math.sqrt(sidepow / midpow)), 5) if midpow > 1e-18 else None,
        "side_energy_fraction": round(float(sidepow / (midpow + sidepow)), 6) if midpow + sidepow > 1e-18 else None,
        "dc_left": round(float(np.mean(left)), 7),
        "dc_right": round(float(np.mean(right)), 7),
        "near_clip_percent": round(100 * float(np.mean(np.max(np.abs(a), axis=1) >= .999)), 5),
    }
    freqs, pm = welch(mid, fs=rate, nperseg=min(4096, len(mid)), scaling="density")
    _, ps = welch(side, fs=rate, nperseg=min(4096, len(side)), scaling="density")
    for low, high in BANDS:
        in_band = (freqs >= low) & (freqs < min(high, rate/2))
        bp_m = float(np.sum(pm[in_band]))
        bp_s = float(np.sum(ps[in_band]))
        output[f"side_mid_{low}_{high}_db"] = (
            round(db(math.sqrt(bp_s / bp_m)), 5) if bp_m > 1e-22 and bp_s >= 0 else None
        )
    return output


def dump_csv(path, rows, keys):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def produce_plots(outdir, results, windows):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    ids = [i for i in EXPECTED if i in results]
    labels = [results[i]['label'] for i in ids]
    values = [results[i]['stats']['side_mid_db'] for i in ids]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.barh(labels, [v if v is not None else float('nan') for v in values])
    ax.set_xlabel('Side/Mid level (dB) — event-dependent, not a 3D quality rating')
    ax.set_title('Alice five-way stereo width summary (unmatched game editions differ)')
    fig.tight_layout()
    fig.savefig(outdir / 'side_mid_five_way.png', dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(12, 5))
    for item in ids:
        rows = [w for w in windows if w['id'] == item]
        ax.plot([w['start_seconds'] for w in rows],
                [float(w['side_mid_db']) if w['side_mid_db'] is not None else float('nan') for w in rows],
                marker='.', label=results[item]['label'])
    ax.set_xlabel('Aligned group time (seconds)')
    ax.set_ylabel('Side/Mid (dB)')
    ax.set_title('Time-local stereo width (2000 and 2011 group timelines are separate)')
    ax.legend(fontsize='small')
    fig.tight_layout()
    fig.savefig(outdir / 'side_mid_timeline.png', dpi=160)
    plt.close(fig)
    return True


def analyze(profile_path, output, allow_partial=False, no_align=False, resample=False,
            plots=False, max_lag_override=None, duration_override=None):
    import numpy as np
    from scipy.signal import resample_poly

    cfg = json.loads(Path(profile_path).read_text(encoding='utf-8'))
    if cfg.get('schema_version') != 1:
        raise ValueError('Profile requires schema_version=1')
    raw = cfg.get('captures')
    if not isinstance(raw, list):
        raise ValueError('Profile must include captures array')
    captures = {}
    for item in raw:
        cid = item.get('id')
        if cid not in EXPECTED or cid in captures:
            raise ValueError(f'Unknown or duplicate capture id: {cid!r}')
        captures[cid] = item
    if set(captures) != set(EXPECTED) and not allow_partial:
        raise ValueError('Five named captures are required in the profile; see --allow-partial')
    options = cfg.get('analysis', {})
    maximum_lag = float(max_lag_override if max_lag_override is not None else options.get('max_lag_seconds', 12))
    duration = float(duration_override if duration_override is not None else options.get('duration_seconds', 45))
    window = float(options.get('window_seconds', 5))
    if maximum_lag < 0 or duration <= 0 or window <= 0:
        raise ValueError('max-lag nonnegative; duration and window positive')
    files = {}
    warnings = []
    for cid, meta in captures.items():
        filename = meta.get('file')
        if not filename:
            continue
        path = (Path(profile_path).resolve().parent / filename).resolve()
        if not path.is_file():
            warnings.append(f'{cid}: missing WAV at {path}')
            continue
        rate, data = read_audio(path)
        files[cid] = {'rate': rate, 'samples': data, 'meta': meta, 'path': str(path)}
    if len(files) < 2:
        raise ValueError(f'Need at least TWO valid WAV files; found {len(files)}')
    if not allow_partial and len(files) != 5:
        raise ValueError('Missing one or more of five recordings; use --allow-partial to analyze what you have')
    rates = sorted(set(x['rate'] for x in files.values()))
    analysis_rate = 48000
    if any(r != analysis_rate for r in rates):
        if not resample:
            raise ValueError(f'Input rates {rates} Hz; export all five at 48000 Hz or use --resample explicitly')
        for cid, entry in files.items():
            if entry['rate'] == 48000:
                continue
            from math import gcd
            r = entry['rate']; g = gcd(r, analysis_rate)
            entry['samples'] = resample_poly(entry['samples'], analysis_rate//g, r//g, axis=0).astype(np.float32)
            entry['rate'] = analysis_rate
            warnings.append(f'{cid}: resampled {r} -> 48000 Hz for analysis; sample identity NOT preserved')

    grouped = {}
    results = {}
    windows = []
    for group, members in GROUPS.items():
        present = [cid for cid in members if cid in files]
        if not present:
            continue
        ref = members[0] if members[0] in files else present[0]
        refdata = files[ref]['samples']
        ref_start = float(files[ref]['meta'].get('start_seconds') or 0)
        if ref_start < 0 or ref_start >= len(refdata) / analysis_rate - 2:
            raise ValueError(f'{ref}: invalid start_seconds')
        ref_start_frames = round(ref_start * analysis_rate)
        offsets = {ref: (ref_start_frames, ref_start_frames, 1.0, 'reference')}
        for cid in present:
            if cid == ref:
                continue
            target = files[cid]
            manual_start = target['meta'].get('start_seconds')
            if manual_start is not None:
                start = round(float(manual_start) * analysis_rate)
                if start < 0 or start >= len(target['samples']) - 2*analysis_rate:
                    raise ValueError(f'{cid}: invalid manual start_seconds')
                # The manual pair chooses corresponding event time in both streams.
                offsets[cid] = (ref_start_frames, start, None, 'manual')
            elif no_align:
                offsets[cid] = (ref_start_frames, 0, None, 'disabled')
            else:
                lag, corr = estimate_lag(refdata[ref_start_frames:], target['samples'], analysis_rate, maximum_lag)
                offsets[cid] = (ref_start_frames + max(0, -lag), max(0, lag), corr, 'auto')
                if corr is None or corr < .55:
                    warnings.append(f'{cid}: weak/undefined envelope alignment (r={corr}); verify demo event matching and set start_seconds if needed')
                if abs(lag) >= maximum_lag * analysis_rate - 2*analysis_rate*.025:
                    warnings.append(f'{cid}: best alignment near max lag boundary; increase max_lag_seconds or align manually')
        # Pair start values refer to a common timestamp in the reference stream.
        timeline = max(offsets[cid][0] for cid in present)
        starts = {}
        for cid in present:
            origin_ref, origin_target, qual, method = offsets[cid]
            starts[cid] = origin_target + timeline - origin_ref
        length = min(len(files[cid]['samples']) - starts[cid] for cid in present)
        length = min(length, round(duration * analysis_rate))
        if length < analysis_rate * 2:
            raise ValueError(f'{group}: less than two seconds common after alignment')
        groupresult = {'reference': ref, 'duration_seconds': round(length / analysis_rate, 6),
                       'alignment': {}}
        hashes = {cid: (files[cid]['meta'].get('demo_sha256') or '').lower().strip() for cid in present}
        if len(present) > 1:
            if any(not h for h in hashes.values()):
                warnings.append(f'{group}: one or more demo_sha256 values missing; identical demo files NOT verified')
            elif len(set(hashes.values())) > 1:
                warnings.append(f'{group}: DIFFERENT demo_sha256 values; group may contain different gameplay')
        for cid in present:
            entry = files[cid]
            segment = entry['samples'][starts[cid]:starts[cid]+length]
            data = stats(segment, analysis_rate)
            peak = data['peak_dbfs']
            if peak >= -.05:
                warnings.append(f'{cid}: audio peaks are very close to digital full scale ({peak:.2f} dBFS)')
            if data['near_clip_percent'] > .01:
                warnings.append(f'{cid}: {data["near_clip_percent"]:.3f}% of frames near full-scale; check clipping')
            if cid.endswith('win98'):
                warnings.append(f'{cid}: analogue Vortex 2 capture adds ADC/line-output response and noise; not a bit-exact DSP reference')
            meta = entry['meta']
            results[cid] = {
                'label': meta.get('label', cid), 'family': group,
                'file': entry['path'], 'demo_sha256': hashes[cid],
                'captured_duration_seconds': round(len(entry['samples']) / analysis_rate, 3),
                'analysis_start_seconds': round(starts[cid] / analysis_rate, 4),
                'analysis_duration_seconds': round(length / analysis_rate, 4),
                'stats': data,
            }
            groupresult['alignment'][cid] = {
                'method': offsets[cid][3], 'start_seconds': round(starts[cid] / analysis_rate, 4),
                'envelope_similarity_to_reference': offsets[cid][2],
            }
            wframes = max(1, round(window * analysis_rate))
            for first in range(0, length, wframes):
                last = min(first+wframes, length)
                if last-first < analysis_rate*.5:
                    break
                stats_win = stats(segment[first:last], analysis_rate)
                windows.append({'id': cid, 'family': group, 'label': meta.get('label', cid),
                                'start_seconds': round(first/analysis_rate, 3),
                                'end_seconds': round(last/analysis_rate, 3),
                                'side_mid_db': stats_win['side_mid_db'],
                                'lr_correlation': stats_win['lr_correlation']})
        grouped[group] = groupresult

    pairs = []
    for a, b in PAIRS:
        if a not in results or b not in results:
            continue
        x, y = results[a]['stats'], results[b]['stats']
        pairs.append({'a': a, 'b': b,
                      'side_mid_delta_db_b_minus_a': (round(y['side_mid_db']-x['side_mid_db'], 4)
                                                      if y['side_mid_db'] is not None and x['side_mid_db'] is not None else None),
                      'left_rms_delta_db_b_minus_a': round(y['left_rms_dbfs']-x['left_rms_dbfs'], 4),
                      'right_rms_delta_db_b_minus_a': round(y['right_rms_dbfs']-x['right_rms_dbfs'], 4),
                      'demo_hashes_match': bool(results[a]['demo_sha256'] and
                                                results[a]['demo_sha256'] == results[b]['demo_sha256'])})
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = {'tool': 'Aufake3D Alice 5-way WAV comparator', 'analysis_sample_rate': analysis_rate,
              'source_profile': str(Path(profile_path).resolve()),
              'disclaimer': ('Five sets of WAV statistics; not proof of bit-identical game events, '
                             'A3D provider activation, or perceived spatial accuracy. Cross-edition '
                             '2000 vs 2011 differences include source assets. Hardware is analog.'),
              'captures': results, 'groups': grouped, 'pairs': pairs, 'warnings': list(dict.fromkeys(warnings))}
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    keys = ['id', 'group', 'label', 'left_rms_dbfs', 'right_rms_dbfs', 'peak_dbfs',
            'side_mid_db', 'side_energy_fraction', 'lr_correlation', 'near_clip_percent'] + [f'side_mid_{a}_{b}_db' for a,b in BANDS]
    rows = []
    for cid in EXPECTED:
        if cid not in results:
            continue
        entry = results[cid]
        rows.append({'id': cid, 'group': entry['family'], 'label': entry['label'], **entry['stats']})
    dump_csv(output/'summary.csv', rows, keys)
    dump_csv(output/'windows.csv', windows,
             ['id','family','label','start_seconds','end_seconds','side_mid_db','lr_correlation'])
    if plots:
        if not produce_plots(output, results, windows):
            warnings.append('Plot generation unavailable: install matplotlib')
            report['warnings'] = list(dict.fromkeys(warnings))
            (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    lines = []
    lines.append('AUFAKE3D / ALICE — FIVE-WAY STEREO AUDIO COMPARISON')
    lines.append('=================================================')
    lines.append('All values measured on matched-length segments WITHIN each game-edition group.')
    lines.append('The 2000 and 2011 groups need not be aligned to each other.\n')
    lines.append(f"{'Capture':<30} {'Side/Mid dB':>13} {'L RMS':>10} {'R RMS':>10} {'L/R corr':>10}")
    for row in rows:
        sm = row['side_mid_db']
        cr = row['lr_correlation']
        lines.append(f"{row['label'][:30]:<30} {sm if sm is not None else 'N/A':>13} "
                     f"{row['left_rms_dbfs']:>10.2f} {row['right_rms_dbfs']:>10.2f} "
                     f"{cr if cr is not None else 'N/A':>10}")
    lines.append('\nWITHIN-EDITION COMPARISONS — side/mid dB change (second minus first)')
    for p in pairs:
        label = f"{results[p['a']]['label']} -> {results[p['b']]['label']}"
        lines.append(f"  {label}: {p['side_mid_delta_db_b_minus_a']} dB; "
                     f"same demo SHA256: {'YES' if p['demo_hashes_match'] else 'NOT VERIFIED'}")
    lines.append('\nWARNINGS / CONTROL NOTES')
    lines += ['  * ' + w for w in report['warnings']] if report['warnings'] else ['  None flagged by automatic checks.']
    lines.append('\nINTERPRETATION')
    lines.append('A more negative Side/Mid ratio = less channel-difference energy, NOT inherently worse HRTF.')
    lines.append('Different effects, reverb, master volume, EQ, clock drift, analogue output and A3D provider')
    lines.append('selection can change measurements. Inspect waveforms and listen blind with level matching.')
    lines.append('Time-envelope alignment is approximate. Inspect report.json and align manually if weak.')
    lines.append('A hardware analogue capture is NOT expected to be bit-identical to a software output.')
    (output/'report.txt').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('\n'.join(lines))
    print(f'\nSaved results to: {output.resolve()}')
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('profile', type=Path, help='JSON capture profile (relative audio paths supported)')
    p.add_argument('--out', type=Path, default=Path('five_way_results'), help='Report directory')
    p.add_argument('--allow-partial', action='store_true', help='Run before all five recordings exist')
    p.add_argument('--no-align', action='store_true', help='Skip automatic envelope matching')
    p.add_argument('--resample', action='store_true', help='Explicitly resample other rates to 48 kHz')
    p.add_argument('--plots', action='store_true', help='Save PNG charts if matplotlib is installed')
    p.add_argument('--max-lag', type=float, default=None, help='Maximum automatic offset, seconds')
    p.add_argument('--duration', type=float, default=None, help='Maximum analyzed segment duration, seconds')
    args = p.parse_args(argv)
    try:
        analyze(args.profile, args.out, args.allow_partial, args.no_align, args.resample,
                args.plots, args.max_lag, args.duration)
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError, ImportError) as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

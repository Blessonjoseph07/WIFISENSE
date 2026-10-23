import React, { useMemo } from "react";
import { SourceBadge } from "./DetectionBadges";

const card = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm";
const sub = "bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl";
const pct = (x) => (x === null || x === undefined ? "—" : `${Math.round(x * 100)}%`);

function Kpi({ label, big, of, note, tone }) {
  const tones = {
    good: "text-emerald-600 dark:text-emerald-400",
    bad: "text-rose-600 dark:text-rose-400",
    warn: "text-amber-600 dark:text-amber-400",
    neutral: "text-slate-700 dark:text-slate-200",
  };
  return (
    <div className={`${sub} p-4`}>
      <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1 flex items-baseline gap-1.5">
        <span className={`text-3xl font-black font-mono ${tones[tone]}`}>{big}</span>
        <span className="text-sm text-slate-500">{of}</span>
      </div>
      <div className="text-[11px] text-slate-500 mt-1">{note}</div>
    </div>
  );
}

function Cell({ n, label, good }) {
  return (
    <div className={`rounded-lg p-3 text-center border ${good
      ? "bg-emerald-50 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-900"
      : "bg-rose-50 border-rose-200 dark:bg-rose-950/30 dark:border-rose-900"}`}>
      <div className={`text-3xl font-black font-mono ${good ? "text-emerald-700 dark:text-emerald-300" : "text-rose-700 dark:text-rose-300"}`}>{n}</div>
      <div className="text-[10px] text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}


// Each dot is one recorded clip. Anyone can read it without knowing what a confusion matrix is.
function Dots({ items }) {
  return (
    <div className="flex flex-wrap gap-1.5" role="img" aria-label={items.map((g) => `${g.n} ${g.label}`).join(", ")}>
      {items.flatMap((g) => Array.from({ length: g.n }, (_, i) => (
        <span key={`${g.label}-${i}`} title={g.label} className="w-4 h-4 rounded-full inline-block" style={{ background: g.color }} />
      )))}
    </div>
  );
}

function PlainSummary({ tp, fn, fp, tn, falls, nonFalls, person }) {
  const flaggedShare = falls ? Math.round((tp / falls) * 100) : null;
  // The wording follows the numbers, so a high false-alarm rate is never described as "some".
  const falseShare = nonFalls ? fp / nonFalls : 0;
  const falseWord = falseShare >= 0.5 ? "many" : falseShare >= 0.2 ? "a number of" : "a few";
  const fallWord = !falls ? "" : tp === falls ? "noticed every fall" : flaggedShare >= 70 ? "noticed most falls" : "missed many falls";
  return (
    <div className="rounded-xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50/60 dark:bg-indigo-950/20 p-4 space-y-4" data-testid="plain-summary">
      <div className="text-sm font-bold text-slate-900 dark:text-white">In plain words</div>
      <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
        We replayed {falls + nonFalls} short recordings of {person || "a person"} the system had <strong>never seen before</strong>.
        {" "}{falls} of them are real falls and {nonFalls} are everyday movements (walking, sitting, standing, jumping).
        The system was not told which was which.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
            When the person really fell: {tp} of {falls} noticed{flaggedShare !== null ? ` (${flaggedShare}%)` : ""}
          </div>
          <Dots items={[{ n: tp, label: "fall noticed", color: "#10b981" }, { n: fn, label: "fall missed", color: "#ef4444" }]} />
          <div className="text-[11px] text-slate-500 mt-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full align-middle mr-1" style={{ background: "#10b981" }} />noticed
            <span className="inline-block w-2.5 h-2.5 rounded-full align-middle ml-3 mr-1" style={{ background: "#ef4444" }} />missed
          </div>
        </div>
        <div>
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
            When it was an ordinary movement: {fp} of {nonFalls} wrongly raised an alarm
          </div>
          <Dots items={[{ n: tn, label: "correctly ignored", color: "#10b981" }, { n: fp, label: "false alarm", color: "#f59e0b" }]} />
          <div className="text-[11px] text-slate-500 mt-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full align-middle mr-1" style={{ background: "#10b981" }} />correctly ignored
            <span className="inline-block w-2.5 h-2.5 rounded-full align-middle ml-3 mr-1" style={{ background: "#f59e0b" }} />false alarm
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
        <strong>What this means:</strong> in this test the system {fallWord}, but it also raised {falseWord} false alarms ({fp} of {nonFalls}{" "}
        ordinary movements). That is why an alert only ever says "possible fall" and a person checks it before anyone acts. This is a small test on recorded data from one person,
        so the exact numbers will move with more recordings. It is not a claim about accuracy in your building.
      </p>
    </div>
  );
}

export default function ReplayEvaluationPanel({ replay, rows, model }) {
  const tp = replay.possible_fall_flagged_on_recorded_falls;
  const fn = replay.missed_recorded_falls;
  const fp = replay.false_alarms_on_recorded_non_falls;
  const tn = replay.correct_non_falls;
  const falls = replay.recorded_fall_windows;
  const nonFalls = replay.recorded_non_fall_windows;
  const threshold = model?.decision_threshold ?? 0.5;
  const expected = model?.evaluation;

  const strip = useMemo(
    () => [...(rows || [])].filter((r) => r.recorded_label && r.fall_score !== null && r.fall_score !== undefined).sort((a, b) => a.id - b.id),
    [rows]
  );
  const labels = Object.entries(replay.by_recorded_label || {});

  return (
    <div className={`${card} p-5 space-y-5`} data-testid="replay-evaluation">
      <div className="flex flex-wrap items-center gap-2.5">
        <h3 className="text-base font-bold text-slate-900 dark:text-white">Recorded data vs the system's result</h3>
        <SourceBadge source="dataset" />
        <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">
          unseen person: {model?.held_out_person || "held out"}
        </span>
      </div>

      <PlainSummary tp={tp} fn={fn} fp={fp} tn={tn} falls={falls} nonFalls={nonFalls} person={model?.held_out_person ? `person ${model.held_out_person}` : null} />

      <div className={`${sub} p-4 text-xs text-slate-600 dark:text-slate-300 leading-relaxed`}>
        <p>
          <strong className="text-slate-800 dark:text-slate-100">What happened here:</strong> real ESP32-S3 CSI recordings from the public research
          dataset <strong>WiFall</strong> were sent through the same authenticated pipeline the boards use. The dataset's own labels
          (fall, jump, sit, stand, walk) were <em>not</em> sent with the packets; they were recorded afterwards and compared with what the
          system concluded on its own.
        </p>
        <p className="mt-2 text-slate-500">
          Source: huggingface.co/datasets/RS2002/WiFall · Model trained on: {model?.trained_on}
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Kpi label="Falls caught" big={tp} of={`of ${falls} recorded falls`} note={`${pct(replay.fall_recall)} flagged as "possible fall"`} tone="good" />
        <Kpi label="Falls missed" big={fn} of={`of ${falls}`} note="recorded falls with no flag" tone={fn ? "bad" : "good"} />
        <Kpi label="False alarms" big={fp} of={`of ${nonFalls} non-falls`} note={`${pct(replay.false_alarm_rate)} of non-falls flagged`} tone="bad" />
        <Kpi label="Correct non-falls" big={tn} of={`of ${nonFalls}`} note={`precision of a flag: ${pct(replay.precision)}`} tone="neutral" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className={`${sub} p-4`}>
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-3">Confusion matrix <span className="font-normal text-slate-400">(recorded label × system result)</span></div>
          <div className="grid grid-cols-[auto_1fr_1fr] gap-2 items-center text-[11px] text-slate-500">
            <span />
            <span className="text-center font-semibold">flagged "possible fall"</span>
            <span className="text-center font-semibold">no fall pattern</span>
            <span className="font-semibold pr-1">recorded fall</span>
            <Cell n={tp} label="caught" good />
            <Cell n={fn} label="missed" good={fn === 0} />
            <span className="font-semibold pr-1">recorded non-fall</span>
            <Cell n={fp} label="false alarm" good={false} />
            <Cell n={tn} label="correct" good />
          </div>
        </div>

        <div className={`${sub} p-4`}>
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-3">By recorded action <span className="font-normal text-slate-400">(share flagged as "possible fall")</span></div>
          <div className="space-y-2.5">
            {labels.map(([name, v]) => {
              const share = v.windows ? v.flagged_possible_fall / v.windows : 0;
              const isFall = name.toLowerCase() === "fall";
              return (
                <div key={name}>
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold capitalize text-slate-700 dark:text-slate-200">{name}{isFall ? " (should be flagged)" : ""}</span>
                    <span className="font-mono text-slate-500">{v.flagged_possible_fall} of {v.windows}</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${share * 100}%`, background: isFall ? "#10b981" : "#f59e0b" }} />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-[10px] text-slate-400 mt-3">Green: the flag is correct. Amber: the flag is a false alarm.</p>
        </div>
      </div>

      {strip.length > 0 && (
        <div className={`${sub} p-4`}>
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <div className="text-xs font-semibold text-slate-700 dark:text-slate-200">Every replayed window <span className="font-normal text-slate-400">(bar height = the model's fall score; the line is the flag threshold {threshold})</span></div>
            <div className="flex items-center gap-3 text-[10px] text-slate-500">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-rose-500" />recorded fall</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-sky-500" />recorded non-fall</span>
            </div>
          </div>
          <div className="relative h-32 flex items-end gap-1" role="img" aria-label="Fall score of every replayed window, coloured by the recorded label">
            <div className="absolute left-0 right-0 border-t border-dashed border-slate-400/70" style={{ bottom: `${threshold * 100}%` }} />
            {strip.map((r) => (
              <div key={r.id} className="flex-1 min-w-[4px] rounded-t"
                title={`recorded ${r.recorded_label}: fall score ${r.fall_score}, system said ${String(r.activity).replace(/_/g, " ")}`}
                style={{ height: `${Math.max(3, r.fall_score * 100)}%`, background: String(r.recorded_label).toLowerCase() === "fall" ? "#f43f5e" : "#0ea5e9" }} />
            ))}
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 mt-1"><span>first window replayed</span><span>last</span></div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 text-xs">
        <div className="rounded-xl p-4 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900 text-emerald-900 dark:text-emerald-200">
          <div className="font-semibold mb-1">What this shows</div>
          <ul className="list-disc pl-4 space-y-1">
            <li>Recorded CSI goes through the real ingest, windowing and model code end to end.</li>
            <li>The model flagged {tp} of {falls} recorded falls of a person it was never trained on.</li>
            <li>The result is reproducible: the same replay gives the same numbers.</li>
          </ul>
        </div>
        <div className="rounded-xl p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200">
          <div className="font-semibold mb-1">What it does not show</div>
          <ul className="list-disc pl-4 space-y-1">
            <li>It also flagged {fp} of {nonFalls} non-falls. A flag is only ever "possible fall, verification required".</li>
            <li>It is one person and {replay.windows_evaluated} clips, so these counts are noisy.{expected ? ` Across all 10 people the expected balanced accuracy is ${expected.person_averaged_balanced_accuracy} (chance ${expected.chance_balanced_accuracy}).` : ""}</li>
            <li>It is recorded data, not accuracy on your own boards or rooms.</li>
          </ul>
        </div>
      </div>
      <p className="text-[11px] text-slate-500">{replay.statement}</p>
    </div>
  );
}

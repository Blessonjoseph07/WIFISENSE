// Quiet Signal landing page. The hero is an exploded view of the real kit:
// ESP32-S3-DevKitC transmitter, the Wi-Fi field, the receiver, and its 0.96" SSD1306 OLED.
const ISO = (tx, ty) => `matrix(0.866 0.5 -0.866 0.5 ${tx} ${ty})`;

function Slab({ tx, ty, w, h, top, side }) {
  return (
    <>
      <g transform="translate(0 7)"><g transform={ISO(tx, ty)}><rect width={w} height={h} rx="4" fill={side} /></g></g>
      <g transform={ISO(tx, ty)}><rect width={w} height={h} rx="4" fill={top} /></g>
    </>
  );
}

function DevKit({ tx, ty, label }) {
  const pins = Array.from({ length: 22 }, (_, i) => 22 + i * 9.6);
  return (
    <>
      <Slab tx={tx} ty={ty} w={252} h={102} top="#1C1E23" side="#08090B" />
      <g transform={ISO(tx, ty)}>
        {[6, 88].map((y) => (
          <g key={y}>
            <rect x="16" y={y} width="220" height="8" rx="1" fill="#0B0C0E" />
            {pins.map((x) => <circle key={x} cx={x} cy={y + 4} r="1.7" fill="#D4AF37" />)}
          </g>
        ))}
        {/* ESP32-S3-WROOM module: metal shield plus the PCB antenna at the board end */}
        <rect x="148" y="20" width="100" height="62" rx="2" fill="#2B2E35" />
        <rect x="151" y="23" width="68" height="56" rx="2" fill="#B9BDC3" />
        <rect x="155" y="27" width="60" height="48" rx="1" fill="none" stroke="#9EA3AA" strokeWidth="1" />
        <text x="185" y="49" textAnchor="middle" fontFamily="JetBrains Mono, monospace" fontSize="8" fill="#3D4148">ESP32-S3</text>
        <text x="185" y="59" textAnchor="middle" fontFamily="JetBrains Mono, monospace" fontSize="5" fill="#5B5F66">WROOM-1</text>
        <path d="M226 28 h16 v8 h-12 v8 h12 v8 h-12 v8 h12 v8 h-16" fill="none" stroke="#D4AF37" strokeWidth="1.6" />
        {/* two USB-C ports, BOOT and RST buttons, regulator and status LED */}
        {[26, 60].map((y) => <rect key={y} x="-5" y={y} width="16" height="16" rx="3" fill="#A3A8AE" />)}
        {[30, 62].map((y) => (
          <g key={y}><rect x="30" y={y} width="12" height="10" rx="1" fill="#E6E6E1" /><circle cx="36" cy={y + 5} r="2.6" fill="#8D9197" /></g>
        ))}
        <rect x="64" y="38" width="20" height="24" rx="1" fill="#0B0C0E" />
        <rect x="100" y="44" width="6" height="4" fill="#F2C94C" />
        <text x="116" y="56" fontFamily="Inter Tight, sans-serif" fontWeight="600" fontSize="11" fill="#F6F6F3">{label}</text>
      </g>
    </>
  );
}

function Oled({ tx, ty }) {
  return (
    <>
      <Slab tx={tx} ty={ty} w={110} h={110} top="#1F4FA6" side="#0F2A5C" />
      <g transform={ISO(tx, ty)}>
        {[[7, 7], [103, 7], [7, 103], [103, 103]].map(([x, y]) => <circle key={x + '-' + y} cx={x} cy={y} r="3.5" fill="#F6F6F3" />)}
        {['GND', 'VCC', 'SCL', 'SDA'].map((p, i) => (
          <g key={p}>
            <circle cx={34 + i * 14} cy="10" r="3" fill="#D4AF37" />
            <text x={34 + i * 14} y="20" textAnchor="middle" fontFamily="JetBrains Mono, monospace" fontSize="4" fill="#DCE6FA">{p}</text>
          </g>
        ))}
        <rect x="4" y="26" width="102" height="68" rx="2" fill="#0A0A0B" />
        <rect x="11" y="36" width="88" height="44" fill="#050506" />
        <text x="55" y="55" textAnchor="middle" fontFamily="JetBrains Mono, monospace" fontSize="9" fill="#9AD7FF">PRESENCE</text>
        <path d="M17 68 h20 c4 0 4 -7 8 -7 s4 9 8 9 s4 -6 8 -6 s3 4 6 4 h26" fill="none" stroke="#9AD7FF" strokeWidth="1.2" />
      </g>
    </>
  );
}

function Field({ tx, ty }) {
  return (
    <g transform={ISO(tx, ty)}>
      <rect width="252" height="102" rx="8" fill="#1F6F66" fillOpacity="0.06" stroke="#1F6F66" strokeOpacity="0.35" strokeDasharray="4 5" />
      {[22, 40, 58].map((r, i) => (
        <circle key={r} className="ws-ripple" style={{ animationDelay: `${i * 0.8}s` }} cx="126" cy="51" r={r} fill="none" stroke="#1F6F66" strokeWidth="1.4" />
      ))}
      <path d="M10 51 h70 c10 0 10 -22 20 -22 s10 40 20 40 s10 -30 20 -30 s8 12 16 12 h86" fill="none" stroke="#1F6F66" strokeWidth="1.8" />
    </g>
  );
}

const LAYERS = [
  { n: 1, name: 'Transmitter', detail: 'ESP32-S3-DevKitC sends a steady stream of Wi-Fi packets.', y: 98, from: '190px' },
  { n: 2, name: 'The room', detail: 'Bodies bend and reflect the 2.4 GHz signal on its way across.', y: 238, from: '120px' },
  { n: 3, name: 'Receiver', detail: 'A second ESP32-S3 reads channel state information from each packet.', y: 378, from: '0px' },
  { n: 4, name: 'OLED status', detail: '0.96" SSD1306 screen shows what the receiver currently senses.', y: 500, from: '-90px' },
];

function Marker({ n, y }) {
  return (
    <g>
      <line x1="44" y1={y} x2="142" y2={y} stroke="#C9CAC4" strokeWidth="1" />
      <circle cx="32" cy={y} r="12" fill="#F6F6F3" stroke="#0E1013" strokeWidth="1" />
      <text x="32" y={y + 4} textAnchor="middle" fontFamily="JetBrains Mono, monospace" fontSize="11" fill="#0E1013">{n}</text>
    </g>
  );
}

function ExplodedKit() {
  const parts = [
    <DevKit key="tx" tx={235} ty={10} label="TX" />,
    <Field key="field" tx={235} ty={150} />,
    <DevKit key="rx" tx={235} ty={290} label="RX" />,
    <Oled key="oled" tx={300} ty={440} />,
  ];
  return (
    <svg viewBox="0 0 600 570" className="w-full h-auto" role="img" aria-label="Exploded view of the Wi-Fi Sense kit: transmitter board, Wi-Fi field, receiver board and OLED screen">
      {/* Drawn bottom-up so upper layers overlap lower ones. */}
      {[...LAYERS].reverse().map((l) => (
        <g key={l.n} className="ws-explode" style={{ '--ws-from': l.from }}>
          {parts[l.n - 1]}
          <Marker n={l.n} y={l.y} />
        </g>
      ))}
    </svg>
  );
}

const Wave = () => (
  <svg viewBox="0 0 1200 80" preserveAspectRatio="none" className="w-full h-16" aria-hidden="true">
    <path className="ws-draw" d="M0 40 H470 C500 40 505 8 530 8 S560 74 585 74 S615 20 640 20 S665 52 690 52 S710 40 730 40 H1200" fill="none" stroke="#0E1013" strokeWidth="1.6" />
  </svg>
);

export default function LandingSplash({ onGetStarted }) {
  return (
    <div className="min-h-screen bg-paper text-ink font-body-md antialiased">
      <header className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-5 sm:px-8">
        <span className="flex items-center gap-2 font-display text-[15px] font-semibold tracking-tight">
          <svg width="22" height="12" viewBox="0 0 22 12" aria-hidden="true"><path d="M1 6h5c2 0 2-5 4-5s2 10 4 10 2-5 4-5h3" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>
          Wi-Fi Sense
        </span>
        <nav aria-label="Sections" className="hidden gap-6 text-sm text-muted md:flex">
          <a href="#how" className="hover:text-ink">How it works</a>
          <a href="#products" className="hover:text-ink">Elder care</a>
          <a href="#products" className="hover:text-ink">Workplaces</a>
          <a href="#privacy" className="hover:text-ink">Privacy</a>
        </nav>
        <div className="flex items-center gap-2">
          <button type="button" onClick={onGetStarted} className="hidden rounded-md px-3 py-2 text-sm text-body hover:text-ink sm:block">Sign in</button>
          <button type="button" onClick={onGetStarted} className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-paper hover:bg-body">Get started</button>
        </div>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 pb-12 pt-6 sm:px-8 lg:grid-cols-[1fr_1.05fr] lg:pt-12">
          <div>
            <p className="font-data-mono text-xs uppercase tracking-[0.14em] text-muted">Wi-Fi sensing · no cameras · nothing to wear</p>
            <h1 className="mt-5 font-display text-[40px] font-semibold leading-[1.02] tracking-[-0.035em] sm:text-6xl lg:text-[68px]">
              Know a room is safe, <span className="font-accent font-normal italic">without</span> watching it.
            </h1>
            <p className="mt-6 max-w-md text-base leading-7 text-body">
              Two small ESP32-S3 boards read how people disturb an ordinary Wi-Fi signal. Wi-Fi Sense turns that into
              presence, movement and possible-fall alerts for care homes and workplaces.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <button type="button" onClick={onGetStarted} className="rounded-md bg-ink px-5 py-3 text-sm font-medium text-paper hover:bg-body">Get started</button>
              <a href="#how" className="rounded-md border border-line bg-white px-5 py-3 text-sm font-medium hover:border-muted">See how it works</a>
            </div>
          </div>

          <figure className="mx-auto w-full max-w-[560px]">
            <ExplodedKit />
            <figcaption>
              <ol className="mt-4 grid gap-3 sm:grid-cols-2">
                {LAYERS.map((l) => (
                  <li key={l.n} className="flex gap-3 text-sm">
                    <span className="font-data-mono text-xs text-muted">0{l.n}</span>
                    <span><span className="font-medium">{l.name}.</span> <span className="text-body">{l.detail}</span></span>
                  </li>
                ))}
              </ol>
            </figcaption>
          </figure>
        </section>

        <section aria-label="Signal" className="border-y border-line bg-white">
          <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-6 sm:px-8">
            <span className="hidden font-data-mono text-xs text-muted sm:block">still</span>
            <Wave />
            <span className="hidden font-data-mono text-xs text-muted sm:block">still</span>
          </div>
          <p className="pb-6 text-center font-data-mono text-xs text-muted">A flat line is an empty or still room. A ripple is someone moving.</p>
        </section>

        <section id="how" className="mx-auto max-w-6xl px-4 py-16 sm:px-8 sm:py-24">
          <h2 className="font-display text-3xl font-semibold tracking-[-0.02em] sm:text-4xl">How it works</h2>
          <div className="mt-10 grid gap-px overflow-hidden rounded-xl border border-line bg-line md:grid-cols-3">
            {[
              ['01', 'Transmit', 'The transmitter board sends Wi-Fi packets across the room many times a second.'],
              ['02', 'Sense', 'The receiver records channel state information: how each subcarrier changed on the way.'],
              ['03', 'Understand', 'The backend compares it with the empty-room baseline and flags presence, movement or a possible fall.'],
            ].map(([n, t, d]) => (
              <div key={n} className="bg-paper p-6 sm:p-8">
                <span className="font-data-mono text-xs text-muted">{n}</span>
                <h3 className="mt-3 font-display text-xl font-semibold">{t}</h3>
                <p className="mt-2 text-sm leading-6 text-body">{d}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="products" className="mx-auto grid max-w-6xl gap-6 px-4 pb-16 sm:px-8 sm:pb-24 md:grid-cols-2">
          {[
            { tone: 'bg-care', eyebrow: 'Elder care', title: 'Help arrives sooner after a fall.', body: 'Caregivers, family and doctors are alerted to a possible fall, with no camera in the bedroom or bathroom.' },
            { tone: 'bg-work', eyebrow: 'Workplaces', title: 'See which rooms are really used.', body: 'Compare bookings with actual occupancy and plan space from what happens, not what was reserved.' },
          ].map((c) => (
            <article key={c.eyebrow} className={`${c.tone} flex min-h-[260px] flex-col justify-between rounded-2xl p-7 text-paper sm:p-9`}>
              <span className="font-data-mono text-xs uppercase tracking-[0.14em] opacity-80">{c.eyebrow}</span>
              <div>
                <h3 className="font-display text-2xl font-semibold tracking-[-0.02em] sm:text-3xl">{c.title}</h3>
                <p className="mt-3 max-w-sm text-sm leading-6 opacity-85">{c.body}</p>
              </div>
            </article>
          ))}
        </section>

        <section id="privacy" className="border-t border-line">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 py-16 sm:px-8 sm:py-24 md:grid-cols-[1fr_1.4fr]">
            <h2 className="font-display text-3xl font-semibold tracking-[-0.02em] sm:text-4xl">
              Private <span className="font-accent font-normal italic">by</span> design.
            </h2>
            <ul className="grid gap-5 text-sm leading-6 text-body sm:grid-cols-2">
              <li><span className="font-medium text-ink">No images.</span> The sensor never sees faces, bodies or screens.</li>
              <li><span className="font-medium text-ink">Nothing to wear.</span> Residents don't need to charge or remember a device.</li>
              <li><span className="font-medium text-ink">Role-based access.</span> Family, doctors and staff each see only what they need.</li>
              <li><span className="font-medium text-ink">Your consent.</span> Sharing rules decide who is told what, and when.</li>
            </ul>
          </div>
        </section>
      </main>

      <footer className="bg-ink text-paper">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-4 py-14 sm:px-8 md:flex-row md:items-center">
          <p className="font-display text-2xl font-semibold tracking-[-0.02em] sm:text-3xl">Ready to see your rooms differently?</p>
          <button type="button" onClick={onGetStarted} className="rounded-md bg-paper px-5 py-3 text-sm font-medium text-ink hover:bg-line">Get started</button>
        </div>
        <p className="mx-auto max-w-6xl px-4 pb-8 font-data-mono text-xs text-muted sm:px-8">Wi-Fi Sense · MCA final-year project</p>
      </footer>
    </div>
  );
}

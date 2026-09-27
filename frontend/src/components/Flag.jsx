/**
 * Inline SVG flags for the language switcher.
 *
 * These used to be emoji (regional indicator pairs) for English and Arabic with
 * a hand-copied SVG only for Kurdish. That mixed two rendering engines: the
 * emoji were drawn by the operating system (so they changed shape with the
 * platform, vanished entirely on systems without a colour emoji font, and were
 * clipped by the flag box), while Kurdish was vector art. The result was three
 * flags that did not match each other and two of which could simply fail to
 * appear at all.
 *
 * All three are now vectors in the same 2:1 frame, so they render identically
 * everywhere, scale to any size without blurring, and always appear.
 *
 * `preserveAspectRatio="none"` is safe here because each viewBox is already
 * exactly 2:1 and the CSS box (.lang-flag) is also 2:1, so the mapping is the
 * identity and nothing is stretched, cropped or letterboxed.
 */

const IRAQ_RED = "#CE1126";
const IRAQ_WHITE = "#FFFFFF";
const IRAQ_BLACK = "#000000";
const IRAQ_GREEN = "#007A3D";

const BAND_WHITE = "#FFFFFF";

const UK_BLUE = "#012169";
const UK_WHITE = "#FFFFFF";
const UK_RED = "#C8102E";

const KURD_RED = "#ED2024";
const KURD_GREEN = "#278E43";
const KURD_SUN = "#FEBD11";

/**
 * The takbir (الله أكبر) as stylised Kufic strokes. The real flag sets the
 * shahada in Kufic script; at 24x12 CSS pixels the script is a few pixels tall,
 * so it reads as a green mark either way. Drawing it as geometry instead of
 * <text> means it can never fall back to tofu if the Arabic webfont has not
 * finished loading, or at all.
 */
function IraqTakbir() {
  return (
    <g fill={IRAQ_GREEN}>
      {/* الله — alif, two lams, ha (reading right to left) */}
      <rect x="37.6" y="11.7" width="1.5" height="6.6" />
      <rect x="35" y="11.3" width="1.5" height="7" />
      <rect x="32.4" y="11.3" width="1.5" height="7" />
      <rect x="30" y="14.1" width="2.6" height="4.2" />
      <rect x="32.4" y="14.1" width="6.7" height="1.4" />
      {/* أكبر — alif, kaf, ba with its dot, ra */}
      <rect x="27.4" y="11.7" width="1.4" height="6.6" />
      <rect x="24.6" y="11.7" width="1.4" height="6.6" />
      <rect x="24.6" y="11.7" width="4.2" height="1.3" />
      <rect x="22" y="12.4" width="1.3" height="5.9" />
      <rect x="19.4" y="12.4" width="2.6" height="4.5" />
      <rect x="20.1" y="17.9" width="1.2" height="1.2" />
    </g>
  );
}

function IraqFlag() {
  return (
    <svg
      className="lang-flag-svg"
      viewBox="0 0 60 30"
      preserveAspectRatio="none"
      focusable="false"
      aria-hidden="true"
    >
      <rect width="60" height="10" fill={IRAQ_RED} />
      <rect y="10" width="60" height="10" fill={IRAQ_WHITE} />
      <rect y="20" width="60" height="10" fill={IRAQ_BLACK} />
      <IraqTakbir />
    </svg>
  );
}

function UnitedKingdomFlag() {
  return (
    <svg
      className="lang-flag-svg"
      viewBox="0 0 60 30"
      preserveAspectRatio="none"
      focusable="false"
      aria-hidden="true"
    >
      <rect width="60" height="30" fill={UK_BLUE} />
      {/* Saltire of St Andrew: broad white diagonals. */}
      <path d="M0 0L60 30M60 0L0 30" stroke={UK_WHITE} strokeWidth="7" />
      {/* Saltire of St Patrick: the red band is counterchanged — offset to one
          side of the white on the hoist half and the other on the fly half,
          which is what stops the diagonals from simply sitting on top. */}
      <path d="M-0.54 28.93L29.46 13.93M29.46 16.07L59.46 31.07" stroke={UK_RED} strokeWidth="4" />
      <path d="M0.54 -1.07L30.54 13.93M30.54 16.07L60.54 1.07" stroke={UK_RED} strokeWidth="4" />
      {/* Cross of St George, white fimbriation first, then the red cross. */}
      <path d="M30 0V30M0 15H60" stroke={UK_WHITE} strokeWidth="18" />
      <path d="M30 0V30M0 15H60" stroke={UK_RED} strokeWidth="10" />
    </svg>
  );
}

/**
 * 21-ray sun of the Kurdistan flag.
 *
 * Generated as exact geometry rather than copied by hand: 21 tips at radius 112
 * alternating with 42 valleys at radius 56 around the centre of the 900x450
 * frame, so the rays are evenly spaced at 360/21 degrees. A hand-edited path
 * drifts — the previous one was asymmetric and its closing segment did not line
 * up with its first point, which left the last ray short.
 */
const KURDISTAN_SUN_PATH =
  "M450 113L458.35 169.63L466.51 171.49L483.01 117.98L474.3 174.55L481.55 178.73L513.09 132.46L488.09 183.95L493.78 190.08L537.57 155.17L498.5 197L502.13 204.54L554.26 184.08L504.6 212.54L505.84 220.82L561.69 216.63L505.84 229.18L504.6 237.46L559.19 249.92L502.13 245.46L498.5 253L546.99 281L493.78 259.92L488.09 266.05L526.18 307.1L481.55 271.27L474.3 275.45L498.59 325.91L466.51 278.51L458.35 280.37L466.69 335.75L450 281L441.65 280.37L433.31 335.75L433.49 278.51L425.7 275.45L401.41 325.91L418.45 271.27L411.91 266.05L373.82 307.1L406.22 259.92L401.5 253L353.01 281L397.87 245.46L395.4 237.46L340.81 249.92L394.16 229.18L394.16 220.82L338.31 216.63L395.4 212.54L397.87 204.54L345.74 184.08L401.5 197L406.22 190.08L362.43 155.17L411.91 183.95L418.45 178.73L386.91 132.46L425.7 174.55L433.49 171.49L416.99 117.98L441.65 169.63L450 169Z";

function KurdistanFlag() {
  return (
    <svg
      className="lang-flag-svg"
      viewBox="0 0 900 450"
      preserveAspectRatio="none"
      focusable="false"
      aria-hidden="true"
    >
      <rect width="900" height="450" fill={BAND_WHITE} />
      <rect width="900" height="150" fill={KURD_RED} />
      <rect y="300" width="900" height="150" fill={KURD_GREEN} />
      <path d={KURDISTAN_SUN_PATH} fill={KURD_SUN} />
    </svg>
  );
}

const FLAGS = {
  en: UnitedKingdomFlag,
  ar: IraqFlag,
  ku: KurdistanFlag,
};

export default function Flag({ code }) {
  const Component = FLAGS[code];
  if (!Component) return null;
  return (
    <span className="lang-flag" aria-hidden="true">
      <Component />
    </span>
  );
}

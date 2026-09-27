import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CaretLeft, CaretRight } from "@phosphor-icons/react";
import { useLanguage } from "../context/LanguageContext";

// Presentation only. The words live in the catalogs, matched to this array by
// index, so a language switch re-labels the slides without re-laying them out.
const BANNERS = [
  {
    id: 1,
    image: "/uploads/case.svg",
    ctaTo: "/products",
    color: "radial-gradient(1100px 520px at 12% 0%, rgba(53,184,212,0.28), transparent 60%), linear-gradient(160deg, rgba(53,184,212,0.08), transparent 50%), #0b1119",
  },
  {
    id: 2,
    image: "/uploads/gpu.svg",
    // A canonical category key, so this link resolves in every language.
    ctaTo: "/category/GPUs",
    color: "radial-gradient(1100px 520px at 88% 10%, rgba(53,184,212,0.34), transparent 62%), linear-gradient(200deg, rgba(53,184,212,0.1), transparent 55%), #0b1119",
  },
  {
    id: 3,
    image: "/uploads/monitor.svg",
    ctaTo: "/products",
    color: "radial-gradient(1000px 480px at 22% 100%, rgba(53,184,212,0.24), transparent 60%), radial-gradient(800px 400px at 92% -10%, rgba(31,127,150,0.4), transparent 55%), #0b1119",
  },
  {
    id: 4,
    image: "/uploads/cpu.svg",
    ctaTo: "/products",
    color: "radial-gradient(1100px 520px at 82% 0%, rgba(31,127,150,0.32), transparent 60%), linear-gradient(140deg, rgba(53,184,212,0.09), transparent 52%), #0b1119",
  },
];

export default function HeroSlider() {
  const { t } = useLanguage();
  const [index, setIndex] = useState(0);
  const total = BANNERS.length;
  const copy = t("hero.banners");

  useEffect(() => {
    const timer = setInterval(() => setIndex((i) => (i + 1) % total), 6000);
    return () => clearInterval(timer);
  }, [total]);

  const go = (next) => setIndex(((next % total) + total) % total);

  return (
    <section className="hero" aria-label={t("hero.label")}>
      <div className="hero-slider">
        {BANNERS.map((b, i) => (
          <div
            key={b.id}
            className={`hero-slide ${i === index ? "active" : ""}`}
            style={{ background: b.color }}
            aria-hidden={i !== index}
          >
            <div className="hero-content container">
              <div className="hero-text">
                <h1>{copy[i]?.title}</h1>
                <p>{copy[i]?.subtitle}</p>
                <Link to={b.ctaTo} className="btn btn-light">
                  {copy[i]?.cta}
                </Link>
              </div>
              <div className="hero-image">
                <img src={b.image} alt="" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <button
        className="hero-nav prev"
        aria-label={t("a11y.previousSlide")}
        onClick={() => go(index - 1)}
      >
        <CaretLeft size={22} weight="regular" />
      </button>
      <button
        className="hero-nav next"
        aria-label={t("a11y.nextSlide")}
        onClick={() => go(index + 1)}
      >
        <CaretRight size={22} weight="regular" />
      </button>

      <div className="hero-dots">
        {BANNERS.map((_, i) => (
          <button
            key={i}
            className={`dot ${i === index ? "active" : ""}`}
            aria-label={t("a11y.goToSlide", { n: i + 1 })}
            onClick={() => setIndex(i)}
          />
        ))}
      </div>
    </section>
  );
}

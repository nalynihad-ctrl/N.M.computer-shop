import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CaretLeft, CaretRight } from "@phosphor-icons/react";

const BANNERS = [
  {
    id: 1,
    title: "Build Your Dream PC",
    subtitle: "Premium parts for the ultimate gaming rig",
    image: "/uploads/case.svg",
    cta: "Shop Components",
    ctaTo: "/products",
    color: "radial-gradient(1100px 520px at 12% 0%, rgba(53,184,212,0.28), transparent 60%), linear-gradient(160deg, rgba(53,184,212,0.08), transparent 50%), #0b1119",
  },
  {
    id: 2,
    title: "Latest NVIDIA Graphics Cards",
    subtitle: "RTX 50 series now in stock",
    image: "/uploads/gpu.svg",
    cta: "Shop GPUs",
    ctaTo: "/category/GPUs",
    color: "radial-gradient(1100px 520px at 88% 10%, rgba(53,184,212,0.34), transparent 62%), linear-gradient(200deg, rgba(53,184,212,0.1), transparent 55%), #0b1119",
  },
  {
    id: 3,
    title: "Gaming Setup Sale",
    subtitle: "Keyboards, mice, headsets and more. Up to 20% off",
    image: "/uploads/monitor.svg",
    cta: "Shop Peripherals",
    ctaTo: "/products",
    color: "radial-gradient(1000px 480px at 22% 100%, rgba(53,184,212,0.24), transparent 60%), radial-gradient(800px 400px at 92% -10%, rgba(31,127,150,0.4), transparent 55%), #0b1119",
  },
  {
    id: 4,
    title: "Upgrade Your PC Today",
    subtitle: "New CPUs, memory and storage for faster performance",
    image: "/uploads/cpu.svg",
    cta: "Upgrade Now",
    ctaTo: "/products",
    color: "radial-gradient(1100px 520px at 82% 0%, rgba(31,127,150,0.32), transparent 60%), linear-gradient(140deg, rgba(53,184,212,0.09), transparent 52%), #0b1119",
  },
];

export default function HeroSlider() {
  const [index, setIndex] = useState(0);
  const total = BANNERS.length;

  useEffect(() => {
    const t = setInterval(() => setIndex((i) => (i + 1) % total), 6000);
    return () => clearInterval(t);
  }, [total]);

  const go = (next) => setIndex(((next % total) + total) % total);

  return (
    <section className="hero" aria-label="Promotional banners">
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
                <h1>{b.title}</h1>
                <p>{b.subtitle}</p>
                <Link to={b.ctaTo} className="btn btn-light">
                  {b.cta}
                </Link>
              </div>
              <div className="hero-image">
                <img src={b.image} alt="" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <button className="hero-nav prev" aria-label="Previous slide" onClick={() => go(index - 1)}>
        <CaretLeft size={22} weight="regular" />
      </button>
      <button className="hero-nav next" aria-label="Next slide" onClick={() => go(index + 1)}>
        <CaretRight size={22} weight="regular" />
      </button>

      <div className="hero-dots">
        {BANNERS.map((_, i) => (
          <button
            key={i}
            className={`dot ${i === index ? "active" : ""}`}
            aria-label={`Go to slide ${i + 1}`}
            onClick={() => setIndex(i)}
          />
        ))}
      </div>
    </section>
  );
}
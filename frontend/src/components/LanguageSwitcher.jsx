import { useEffect, useRef, useState } from "react";
import { CaretDown, Check } from "@phosphor-icons/react";
import { useLanguage } from "../context/LanguageContext";
import Flag from "./Flag";

export default function LanguageSwitcher({ className = "" }) {
  const { language, languages, setLanguage, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const optionRefs = useRef([]);

  const currentIndex = Math.max(
    0,
    languages.findIndex((item) => item.code === language)
  );
  const current = languages[currentIndex] || languages[0];
  const total = languages.length;

  useEffect(() => {
    if (!open) return undefined;
    const onPointerDown = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  useEffect(() => {
    if (open) setActiveIndex(currentIndex);
  }, [open, currentIndex]);

  useEffect(() => {
    if (open && optionRefs.current[activeIndex]) optionRefs.current[activeIndex].focus();
  }, [open, activeIndex]);

  const close = (returnFocus) => {
    setOpen(false);
    if (returnFocus && triggerRef.current) triggerRef.current.focus();
  };

  const choose = (code) => {
    setLanguage(code);
    close(true);
  };

  const onTriggerKeyDown = (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
    }
  };

  const onMenuKeyDown = (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => (i + 1) % total);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => (i - 1 + total) % total);
    } else if (event.key === "Home") {
      event.preventDefault();
      setActiveIndex(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setActiveIndex(total - 1);
    } else if (event.key === "Escape") {
      event.preventDefault();
      close(true);
    } else if (event.key === "Tab") {
      setOpen(false);
    }
  };

  // The trigger names the language in the interface language (so an Arabic
  // visitor reads "اللغة: العربية"), while each option keeps its own endonym so
  // the list is readable whichever language is currently active.
  const triggerLabel = t("lang.label", { language: current.label });
  const menuLabel = t("lang.select");

  return (
    <div className={`lang-switch ${open ? "open" : ""} ${className}`.trim()} ref={rootRef}>
      <button
        type="button"
        ref={triggerRef}
        className="lang-trigger"
        onClick={() => setOpen((v) => !v)}
        onKeyDown={onTriggerKeyDown}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={triggerLabel}
        title={triggerLabel}
      >
        <Flag code={current.code} />
        <span className="lang-trigger-name">{current.native}</span>
        <CaretDown size={11} weight="bold" className="lang-caret" />
      </button>

      {open && (
        <ul
          className="lang-menu"
          role="listbox"
          aria-label={menuLabel}
          onKeyDown={onMenuKeyDown}
        >
          {languages.map((item, index) => {
            const selected = item.code === language;
            return (
              <li key={item.code} role="none">
                <button
                  type="button"
                  role="option"
                  aria-selected={selected}
                  // The endonym on its own, with `lang` set below so it is
                  // announced in its own language. Appending the English name
                  // here would put English text into an Arabic or Kurdish
                  // interface for no gain - the name is already the label.
                  aria-label={item.native}
                  tabIndex={index === activeIndex ? 0 : -1}
                  ref={(el) => {
                    optionRefs.current[index] = el;
                  }}
                  className={`lang-option ${selected ? "active" : ""}`}
                  onClick={() => choose(item.code)}
                  onFocus={() => setActiveIndex(index)}
                  lang={item.code}
                  dir={item.dir}
                >
                  <Flag code={item.code} />
                  <span className="lang-option-name">{item.native}</span>
                  {selected && <Check size={14} weight="bold" className="lang-check" />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

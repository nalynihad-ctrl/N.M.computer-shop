import { useLanguage } from "../context/LanguageContext";

export default function FAQ() {
  const { t } = useLanguage();
  const qa = t("faq.qa");

  return (
    <div className="page container static-page">
      <h1 className="page-title">{t("faq.title")}</h1>
      {qa.map((entry, index) => (
        // The index is the stable identity here: a question is prose, not a
        // record with a fixed id, and its text changes with the language.
        <section key={index}>
          <h2>{entry.q}</h2>
          <p>{entry.a}</p>
        </section>
      ))}
      <p className="muted">{t("faq.closing")}</p>
    </div>
  );
}

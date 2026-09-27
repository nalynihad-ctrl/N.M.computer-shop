import { useLanguage } from "../context/LanguageContext";

export default function Warranty() {
  const { t } = useLanguage();

  return (
    <div className="page container static-page">
      <h1 className="page-title">{t("warranty.title")}</h1>
      <p>{t("warranty.intro")}</p>

      <h2>{t("warranty.coverTitle")}</h2>
      <ul>
        {t("warranty.cover").map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>{t("warranty.notCoveredTitle")}</h2>
      <ul>
        {t("warranty.notCovered").map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>{t("warranty.claimTitle")}</h2>
      <p>{t("warranty.claim")}</p>

      <p className="muted">{t("warranty.closing")}</p>
    </div>
  );
}

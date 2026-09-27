import { useLanguage } from "../context/LanguageContext";

export default function Returns() {
  const { t } = useLanguage();

  return (
    <div className="page container static-page">
      <h1 className="page-title">{t("returns.title")}</h1>
      <p>{t("returns.intro")}</p>

      <h2>{t("returns.howTitle")}</h2>
      <ul>
        {t("returns.how").map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ul>

      <h2>{t("returns.nonReturnableTitle")}</h2>
      <ul>
        {t("returns.nonReturnable").map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>{t("returns.damagedTitle")}</h2>
      <p>{t("returns.damaged")}</p>

      <p className="muted">{t("returns.closing")}</p>
    </div>
  );
}

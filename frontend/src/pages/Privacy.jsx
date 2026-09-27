import { useLanguage } from "../context/LanguageContext";

export default function Privacy() {
  const { t } = useLanguage();

  return (
    <div className="page container static-page">
      <h1 className="page-title">{t("privacy.title")}</h1>
      <p>{t("privacy.intro")}</p>

      <h2>{t("privacy.collectTitle")}</h2>
      <ul>
        {t("privacy.collect").map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>{t("privacy.useTitle")}</h2>
      <ul>
        {t("privacy.use").map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>{t("privacy.notDoTitle")}</h2>
      <ul>
        {t("privacy.notDo").map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>{t("privacy.rightsTitle")}</h2>
      <p>{t("privacy.rights")}</p>

      <p className="muted">{t("privacy.note")}</p>
    </div>
  );
}

import { useLanguage } from "../context/LanguageContext";

export default function About() {
  const { t } = useLanguage();
  return (
    <div className="page container static-page">
      <h1 className="page-title">{t("about.title")}</h1>
      <p>{t("about.intro")}</p>
      <h2>{t("about.whyTitle")}</h2>
      <ul>
        {t("about.why").map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
      <h2>{t("about.missionTitle")}</h2>
      <p>{t("about.mission")}</p>
      <p className="muted">{t("about.note")}</p>
    </div>
  );
}

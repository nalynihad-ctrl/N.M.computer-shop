import { useLanguage } from "../context/LanguageContext";

export default function Terms() {
  const { t } = useLanguage();

  return (
    <div className="page container static-page">
      <h1 className="page-title">{t("terms.title")}</h1>
      <p>{t("terms.intro")}</p>

      <h2>{t("terms.ordersTitle")}</h2>
      <ul>
        {t("terms.orders").map((clause) => (
          <li key={clause}>{clause}</li>
        ))}
      </ul>

      <h2>{t("terms.accountTitle")}</h2>
      <ul>
        {t("terms.account").map((clause) => (
          <li key={clause}>{clause}</li>
        ))}
      </ul>

      <h2>{t("terms.liabilityTitle")}</h2>
      <p>{t("terms.liability")}</p>

      <h2>{t("terms.lawTitle")}</h2>
      <p>{t("terms.law")}</p>

      <h2>{t("terms.changesTitle")}</h2>
      <p>{t("terms.changes")}</p>

      <p className="muted">{t("terms.closing")}</p>
    </div>
  );
}

import { useLanguage } from "../context/LanguageContext";

export default function Shipping() {
  const { t } = useLanguage();

  return (
    <div className="page container static-page">
      <h1 className="page-title">{t("shipping.title")}</h1>
      <p>{t("shipping.intro")}</p>
      <h2>{t("shipping.optionsTitle")}</h2>
      <ul>
        <li>
          <strong>{t("shipping.standardLabel")}:</strong> {t("shipping.standardBody")}
        </li>
        <li>
          <strong>{t("shipping.expressLabel")}:</strong> {t("shipping.expressBody")}
        </li>
        <li>
          <strong>{t("shipping.pickupLabel")}:</strong> {t("shipping.pickupBody")}
        </li>
      </ul>
      <h2>{t("shipping.trackingTitle")}</h2>
      <p>{t("shipping.tracking")}</p>
      <h2>{t("shipping.notesTitle")}</h2>
      <ul>
        {t("shipping.notes").map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
      <p className="muted">{t("shipping.closing")}</p>
    </div>
  );
}

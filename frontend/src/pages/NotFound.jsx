import { Link } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext";

export default function NotFound() {
  const { t } = useLanguage();
  return (
    <div className="page container empty-state">
      <h1>{t("notFound.title")}</h1>
      <p className="muted">{t("notFound.body")}</p>
      <Link to="/" className="btn btn-primary">{t("notFound.backHome")}</Link>
    </div>
  );
}

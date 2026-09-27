import { useToast } from "../context/ToastContext";
import { useLanguage } from "../context/LanguageContext";

const TOPICS = ["order", "shipping", "returns", "advice", "other"];

export default function Contact() {
  const toast = useToast();
  const { t } = useLanguage();

  const submit = (e) => {
    e.preventDefault();
    toast.success(t("toast.messageSent"));
    e.target.reset();
  };

  return (
    <div className="page container static-page">
      <h1 className="page-title">{t("contact.title")}</h1>
      <div className="contact-grid">
        <div className="contact-info">
          <h2>{t("contact.getInTouch")}</h2>
          {/* Contact details themselves are not translated; only the labels are. */}
          <p>
            <strong>{t("contact.phone")}:</strong> <span dir="ltr">+1 (312) 847-1928</span>
          </p>
          <p>
            <strong>{t("contact.email")}:</strong>{" "}
            <span dir="ltr">support@nalymunib.shop</span>
          </p>
          <p>
            <strong>{t("contact.address")}:</strong> 411 Wabash Ave, Suite 3, Chicago, IL 60611
          </p>
          <p>
            <strong>{t("contact.supportHours")}:</strong> {t("contact.supportHoursValue")}
          </p>
          <h2>{t("contact.shippingReturnsTitle")}</h2>
          <p>{t("contact.shippingReturns")}</p>
          <p>{t("contact.warrantyNote")}</p>
        </div>
        <form className="contact-form" onSubmit={submit}>
          <h2>{t("contact.formTitle")}</h2>
          <label className="field">
            <span>{t("field.name")}</span>
            <input className="input" required placeholder={t("placeholder.name")} />
          </label>
          <label className="field">
            <span>{t("field.email")}</span>
            <input
              className="input"
              type="email"
              required
              placeholder="you@example.com"
              dir="ltr"
            />
          </label>
          <label className="field">
            <span>{t("contact.subject")}</span>
            <select className="input" required>
              <option value="">{t("contact.topic.select")}</option>
              {TOPICS.map((topic) => (
                <option key={topic} value={topic}>
                  {t(`contact.topic.${topic}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>{t("contact.message")}</span>
            <textarea
              className="input"
              rows="5"
              required
              placeholder={t("contact.messagePlaceholder")}
            />
          </label>
          <button className="btn btn-primary">{t("contact.submit")}</button>
        </form>
      </div>
    </div>
  );
}

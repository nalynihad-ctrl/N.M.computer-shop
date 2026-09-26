import { useToast } from "../context/ToastContext";

export default function Contact() {
  const toast = useToast();

  const submit = (e) => {
    e.preventDefault();
    toast.success("Message sent! We will reply within 24 hours.");
    e.target.reset();
  };

  return (
    <div className="page container static-page">
      <h1 className="page-title">Contact Us</h1>
      <div className="contact-grid">
        <div className="contact-info">
          <h2>Get in touch</h2>
          <p><strong>Phone:</strong> +1 (312) 847-1928</p>
          <p><strong>Email:</strong> support@nalymunib.shop</p>
          <p><strong>Address:</strong> 411 Wabash Ave, Suite 3, Chicago, IL 60611</p>
          <p><strong>Support hours:</strong> Mon-Fri, 9:00-18:00</p>
          <h2>Shipping &amp; Returns</h2>
          <p>Free shipping on orders over $100. Returns accepted within 30 days of delivery.</p>
          <p>Most warranties are covered by the brand; contact us for warranty claims.</p>
        </div>
        <form className="contact-form" onSubmit={submit}>
          <h2>Send a message</h2>
          <label className="field">
            <span>Your name</span>
            <input className="input" required placeholder="Alex Rivera" />
          </label>
          <label className="field">
            <span>Email</span>
            <input className="input" type="email" required placeholder="you@example.com" />
          </label>
          <label className="field">
            <span>Subject</span>
            <select className="input" required>
              <option value="">Select a topic…</option>
              <option>Order enquiry</option>
              <option>Shipping</option>
              <option>Returns &amp; warranty</option>
              <option>Product advice</option>
              <option>Other</option>
            </select>
          </label>
          <label className="field">
            <span>Message</span>
            <textarea className="input" rows="5" required placeholder="How can we help?" />
          </label>
          <button className="btn btn-primary">Send Message</button>
        </form>
      </div>
    </div>
  );
}
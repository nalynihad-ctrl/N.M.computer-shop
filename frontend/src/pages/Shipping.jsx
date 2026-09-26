export default function Shipping() {
  return (
    <div className="page container static-page">
      <h1 className="page-title">Shipping</h1>
      <p>
        We ship from our Chicago warehouse to the entire United States, plus
        select international destinations. Most orders are processed within 1
        business day.
      </p>
      <h2>Delivery options</h2>
      <ul>
        <li><strong>Standard (3–5 business days):</strong> $9.99 flat rate, or free on orders over $100.</li>
        <li><strong>Express (1–2 business days):</strong> $19.99 flat rate, calculated at checkout.</li>
        <li><strong>In-store pickup:</strong> Free at 411 Wabash Ave, Suite 3, Chicago, IL.</li>
      </ul>
      <h2>Order tracking</h2>
      <p>
        Once your order ships you will receive a confirmation email with a
        tracking number. You can also view live status in your order history
        after logging in.
      </p>
      <h2>Shipping notes</h2>
      <ul>
        <li>Fragile items are double-boxed and padded.</li>
        <li>Hazardous materials (batteries bundled with hardware) are shipped via ground only.</li>
        <li>PO Boxes are only supported for standard deliveries.</li>
        <li>Some oversized items may require a signature on delivery.</li>
      </ul>
      <p className="muted">
        Need help with a shipment? Contact us and we will track it down for you.
      </p>
    </div>
  );
}
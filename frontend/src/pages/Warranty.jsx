export default function Warranty() {
  return (
    <div className="page container static-page">
      <h1 className="page-title">Warranty</h1>
      <p>
        Every product we sell comes with a manufacturer warranty. Standard
        warranty terms range from 1 to 10 years depending on the brand and
        component, and are always listed on the product page.
      </p>
      <h2>What we cover</h2>
      <ul>
        <li>Manufacturing defects and hardware failures under normal use.</li>
        <li>Fan, pump, and sensor failures on cooling products.</li>
        <li>Memory and storage failures covered by lifetime warranties.</li>
      </ul>
      <h2>What is not covered</h2>
      <ul>
        <li>Damage from overclocking, physical damage, or liquid spills.</li>
        <li>Normal wear and tear on cables and consumables.</li>
        <li>Products modified or opened in ways that break factory seals.</li>
      </ul>
      <h2>How to start a claim</h2>
      <p>
        Contact us with your order number, the product name, and a description
        of the issue. We will help you start a claim with the brand — and for
        many items we will handle the whole process for you and ship a
        replacement directly.
      </p>
      <p className="muted">
        Most warranty claims are resolved within 5–10 business days.
      </p>
    </div>
  );
}
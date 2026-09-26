export default function Privacy() {
  return (
    <div className="page container static-page">
      <h1 className="page-title">Privacy Policy</h1>
      <p>
        Your privacy matters to us. This policy explains what data we collect,
        how we use it, and the choices you have. It applies to
        Naly,munib and the services we operate.
      </p>
      <h2>Information we collect</h2>
      <ul>
        <li>Account details: name, email, and password (stored securely as a salted hash).</li>
        <li>Order details: shipping address, phone number, and purchase history.</li>
        <li>Usage data: pages you visit and basic device information, used to improve the site.</li>
      </ul>
      <h2>How we use your information</h2>
      <ul>
        <li>To process and deliver your orders.</li>
        <li>To provide customer support and warranty services.</li>
        <li>To keep track of cart and order history so you can manage them.</li>
        <li>To improve performance, security, and usability of the store.</li>
      </ul>
      <h2>What we do not do</h2>
      <ul>
        <li>We never sell your personal data to third parties.</li>
        <li>We never store raw passwords — only encrypted hashes.</li>
        <li>We do not pass payment card details through our own servers.</li>
      </ul>
      <h2>Your rights</h2>
      <p>
        You can access, correct, or delete your personal information at any time
        by contacting us. You may also close your account and request removal of
        your data.
      </p>
      <p className="muted">
        This demo store runs entirely on sample data; no real payment details are
        collected or stored.
      </p>
    </div>
  );
}
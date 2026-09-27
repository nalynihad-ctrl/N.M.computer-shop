/**
 * English message catalog — the reference for the whole app.
 *
 * Every other catalog is keyed against this file. `t("a.b.c")` resolves the
 * dotted path, and if a translation is missing in the active language the
 * translator falls back to this object, so a partially-translated catalog
 * degrades to English instead of rendering a raw key.
 *
 * Plural forms live under a `count` key: `t("products.count", { count: 3 })`
 * picks the sub-form that `Intl.PluralRules` selects for the active locale, so
 * Arabic gets its zero/one/two/few/many/other split instead of the English
 * one/other pair. Every catalog that ships a `count` must therefore supply the
 * forms its locale actually selects.
 */

export default {
  a11y: {
    skipToContent: "Skip to content",
    mainContent: "Main content",
    menu: "Menu",
    search: "Search",
    searchProducts: "Search products",
    toggleSearch: "Toggle search",
    switchToLight: "Switch to light mode",
    switchToDark: "Switch to dark mode",
    account: "Account",
    cartWithCount: {
      one: "Cart, {count} item",
      other: "Cart, {count} items",
    },
    scrollCategoriesLeft: "Scroll categories left",
    scrollCategoriesRight: "Scroll categories right",
    previousSlide: "Previous slide",
    nextSlide: "Next slide",
    goToSlide: "Go to slide {n}",
    rating: "Rating {rating} out of 5",
    decreaseQuantity: "Decrease quantity",
    increaseQuantity: "Increase quantity",
    removeItem: "Remove {name}",
  },

  lang: {
    // {language} is the language's own English name, e.g. "Arabic".
    label: "Language: {language}",
    select: "Select language",
  },

  nav: {
    home: "Home",
    allProducts: "All Products",
    cart: "Shopping Cart",
    account: "My Account",
    orders: "My Orders",
    about: "About Us",
    contact: "Contact",
  },

  search: {
    placeholder: "Search products, brands, categories…",
  },

  theme: {
    light: "Light mode",
    dark: "Dark mode",
  },

  common: {
    viewAll: "View all →",
    loading: "Loading…",
    retry: "Try again",
    optional: "optional",
    free: "Free",
    notApplicable: "N/A",
  },

  footer: {
    blurb:
      "PC parts and gaming hardware for people who actually build. Ships fast, tested by people who wrench on their own rigs.",
    shop: "Shop",
    customerService: "Customer Service",
    company: "Company",
    contact: "Contact",
    allProducts: "All Products",
    categories: "Categories",
    newArrivals: "New Arrivals",
    deals: "Deals",
    contactUs: "Contact Us",
    shipping: "Shipping",
    returns: "Returns",
    warranty: "Warranty",
    faq: "FAQ",
    aboutUs: "About Us",
    privacy: "Privacy Policy",
    terms: "Terms & Conditions",
    copyright: "© {year} Naly,munib. All rights reserved.",
  },

  category: {
    allProducts: "All Products",
  },

  hero: {
    label: "Promotional banners",
    banners: [
      {
        title: "Build Your Dream PC",
        subtitle: "Premium parts for the ultimate gaming rig",
        cta: "Shop Components",
      },
      {
        title: "Latest NVIDIA Graphics Cards",
        subtitle: "RTX 50 series now in stock",
        cta: "Shop GPUs",
      },
      {
        title: "Gaming Setup Sale",
        subtitle: "Keyboards, mice, headsets and more. Up to 20% off",
        cta: "Shop Peripherals",
      },
      {
        title: "Upgrade Your PC Today",
        subtitle: "New CPUs, memory and storage for faster performance",
        cta: "Upgrade Now",
      },
    ],
  },

  product: {
    outOfStock: "Out of stock",
    soldOut: "Sold out",
    inStock: "{count} in stock",
    unitsAvailable: {
      one: "{count} unit available",
      other: "{count} units available",
    },
    addToCart: "Add to Cart",
    buyNow: "Buy Now",
    notFound: "Product not found.",
    backToProducts: "Back to products",
    save: "Save {percent}%",
    specs: "Technical Specifications",
    related: "You may also like",
  },

  toast: {
    addedToCart: "{name} added to your cart.",
    removedFromCart: "{name} removed from your cart.",
    welcomeBack: "Welcome back, {name}!",
    accountCreated: "Account created. Welcome!",
    loggedOut: "You have been logged out.",
    messageSent: "Message sent! We will reply within 24 hours.",
  },

  home: {
    shopByCategory: "Shop by Category",
    newArrivals: "New Arrivals",
    topRated: "Top Rated",
    productCount: {
      one: "{count} product",
      other: "{count} products",
    },
  },

  products: {
    titleAll: "All Products",
    titleCategory: "Category: {category}",
    titleSearch: 'Search results for "{search}"',
    loadError: "Something went wrong while loading products.",
    empty: "No products found.",
    emptyHint: "Try searching for another product or clearing the filters.",
    viewAll: "View all products",
  },

  filters: {
    category: "Category",
    brand: "Brand",
    price: "Price",
    allProducts: "All Products",
    allCategories: "All categories",
    min: "Min",
    max: "Max",
    to: "to",
    clearPrices: "Clear prices",
  },

  toolbar: {
    clearSearch: "Clear search",
    productCount: {
      one: "{count} product",
      other: "{count} products",
    },
  },

  sort: {
    label: "Sort",
    popular: "Most Popular",
    newest: "Newest",
    priceAsc: "Price (Low → High)",
    priceDesc: "Price (High → Low)",
    name: "Name A-Z",
  },

  cart: {
    title: "Shopping Cart",
    empty: "Your cart is empty.",
    emptyHint: "Add some products before checking out.",
    continueShopping: "Continue Shopping",
    each: "{price} each",
    clear: "Clear cart",
    summary: "Order Summary",
    subtotal: "Subtotal",
    shipping: "Shipping",
    discount: "Discount",
    total: "Total",
    freeShippingHint: "Add {amount} more for free shipping.",
    checkout: "Proceed to Checkout",
  },

  checkout: {
    title: "Checkout",
    customerInfo: "Customer Information",
    paymentMethod: "Payment Method",
    placing: "Placing order…",
    placeOrder: "Place Order",
    backToCart: "Back to Cart",
    termsNote: "By placing this order you agree to our terms & conditions.",
    successTitle: "Order placed!",
    successBody: "Your order #{orderId} has been received and is being processed.",
    successMeta: "Payment method: {method} · Total: {total}",
    viewOrders: "View My Orders",
    backHome: "Back to Home",
    failed: "Checkout failed. Please try again.",
  },

  payment: {
    cod: "Cash on Delivery",
    codDesc: "Pay when your order arrives.",
    card: "Card Payment",
    cardDesc: "Online payment integration coming soon.",
  },

  field: {
    fullName: "Full name",
    name: "Your name",
    phone: "Phone",
    email: "Email",
    address: "Address",
    city: "City",
    country: "Country / Region",
    subject: "Subject",
    message: "Message",
    password: "Password",
    confirmPassword: "Confirm password",
  },

  login: {
    title: "Login",
    subtitle: "Access your account to view orders and checkout faster.",
    submit: "Login",
    submitting: "Signing in…",
    noAccount: "No account yet?",
    createOne: "Create one",
    failed: "Login failed.",
  },

  register: {
    title: "Create Account",
    subtitle:
      "Create your Naly,munib account to track orders and check out faster.",
    passwordHint: "At least 4 characters",
    repeatPassword: "Repeat password",
    submit: "Register",
    submitting: "Creating account…",
    haveAccount: "Already have an account?",
    mismatch: "Passwords do not match.",
    failed: "Registration failed.",
  },

  profile: {
    title: "My Account",
    phone: "Phone",
    address: "Address",
    city: "City",
    country: "Country",
    orders: "My Orders →",
    continueShopping: "Continue Shopping →",
    logout: "Logout",
  },

  orders: {
    title: "My Orders",
    loading: "Loading your orders…",
    empty: "You have no orders yet.",
    startShopping: "Start Shopping",
    number: "Order #{id}",
    total: "Total",
    failed: "Failed to load orders.",
  },

  status: {
    pending: "Pending",
    processing: "Processing",
    shipped: "Shipped",
    delivered: "Delivered",
    cancelled: "Cancelled",
    refunded: "Refunded",
  },

  notFound: {
    title: "404 - Page not found",
    body: "The page you are looking for does not exist.",
    backHome: "Back to Home",
  },

  about: {
    title: "About Us",
    intro:
      "Naly,munib is an online store for PC parts and gaming accessories. We help enthusiasts, gamers, and professionals build the systems they dream about. From a single RGB fan to a full custom water-cooled rig.",
    whyTitle: "Why shop with us?",
    why: [
      "Genuine, brand-new components with full warranty.",
      "Fast shipping with free delivery on orders over $100.",
      "Honest advice from people who actually build PCs.",
      "Simple returns and responsive customer support.",
    ],
    missionTitle: "Our mission",
    mission:
      "To make building and upgrading computers easy, affordable, and enjoyable for everyone.",
    note:
      "This demo store ships with sample product data so every feature can be tested before connecting a real inventory.",
  },

  contact: {
    title: "Contact Us",
    getInTouch: "Get in touch",
    phone: "Phone",
    email: "Email",
    address: "Address",
    supportHours: "Support hours",
    supportHoursValue: "Mon-Fri, 9:00-18:00",
    shippingReturnsTitle: "Shipping & Returns",
    shippingReturns:
      "Free shipping on orders over $100. Returns accepted within 30 days of delivery.",
    warrantyNote:
      "Most warranties are covered by the brand; contact us for warranty claims.",
    formTitle: "Send a message",
    subject: "Subject",
    message: "Message",
    messagePlaceholder: "How can we help?",
    submit: "Send Message",
    topic: {
      select: "Select a topic…",
      order: "Order enquiry",
      shipping: "Shipping",
      returns: "Returns & warranty",
      advice: "Product advice",
      other: "Other",
    },
  },

  faq: {
    title: "Frequently Asked Questions",
    qa: [
      {
        q: "How long does delivery take?",
        a: "Standard delivery takes 3–5 business days. Express delivery takes 1–2 business days.",
      },
      {
        q: "Do you ship internationally?",
        a: "Yes, we ship to a number of select international destinations. Shipping rates are calculated at checkout.",
      },
      {
        q: "What is your return policy?",
        a: "You can return items within 30 days of delivery. See our Returns page for full details.",
      },
      {
        q: "Are the products covered by warranty?",
        a: "Yes. Every product includes a manufacturer warranty, typically 1–3 years and lifetime for memory and storage. See our Warranty page for details.",
      },
      {
        q: "Do you validate or test parts?",
        a: "Every component is inspected and tested by our team before it ships, so what arrives is ready to install.",
      },
      {
        q: "How can I track my order?",
        a: "You will receive a tracking link by email once your order ships. Logged-in users can also check status in their order history.",
      },
      {
        q: "Can I order parts and have you build the PC?",
        a: "Not yet — this demo store focuses on parts sales. Custom build services are on our roadmap.",
      },
    ],
    closing:
      "Still have questions? Contact us and a real human will reply within 24 hours.",
  },

  privacy: {
    title: "Privacy Policy",
    intro:
      "Your privacy matters to us. This policy explains what data we collect, how we use it, and the choices you have. It applies to Naly,munib and the services we operate.",
    collectTitle: "Information we collect",
    collect: [
      "Account details: name, email, and password (stored securely as a salted hash).",
      "Order details: shipping address, phone number, and purchase history.",
      "Usage data: pages you visit and basic device information, used to improve the site.",
    ],
    useTitle: "How we use your information",
    use: [
      "To process and deliver your orders.",
      "To provide customer support and warranty services.",
      "To keep track of cart and order history so you can manage them.",
      "To improve performance, security, and usability of the store.",
    ],
    notDoTitle: "What we do not do",
    notDo: [
      "We never sell your personal data to third parties.",
      "We never store raw passwords — only encrypted hashes.",
      "We do not pass payment card details through our own servers.",
    ],
    rightsTitle: "Your rights",
    rights:
      "You can access, correct, or delete your personal information at any time by contacting us. You may also close your account and request removal of your data.",
    note:
      "This demo store runs entirely on sample data; no real payment details are collected or stored.",
  },

  terms: {
    title: "Terms & Conditions",
    intro:
      "These terms govern your use of the Naly,munib website and any purchases you make with us. By using the store, you agree to the terms below.",
    ordersTitle: "Orders and pricing",
    orders: [
      "All prices are shown in US dollars and include applicable sales tax where required.",
      "We reserve the right to cancel or refuse any order, including suspected misuse.",
      "Product images are for illustration; specifications on the product page are authoritative.",
    ],
    accountTitle: "Account responsibility",
    account: [
      "You are responsible for keeping your login credentials confidential.",
      "You agree to provide accurate and current information at checkout.",
    ],
    liabilityTitle: "Limitation of liability",
    liability:
      "We are not liable for indirect or consequential damages arising from the use of hardware sold here. Our liability is limited to the value of the products you purchased, to the extent permitted by law.",
    lawTitle: "Governing law",
    law:
      "These terms are governed by the laws of the State of Illinois, United States. Any disputes will be resolved in the courts of Cook County, Illinois.",
    changesTitle: "Changes to these terms",
    changes:
      "We may update these terms from time to time. Continued use of the site after changes are posted means you accept the updated terms.",
    closing: "Contact us if you have any questions about these terms.",
  },

  shipping: {
    title: "Shipping",
    intro:
      "We ship from our Chicago warehouse to the entire United States, plus select international destinations. Most orders are processed within 1 business day.",
    optionsTitle: "Delivery options",
    standardLabel: "Standard (3–5 business days)",
    standardBody: "$9.99 flat rate, or free on orders over $100.",
    expressLabel: "Express (1–2 business days)",
    expressBody: "$19.99 flat rate, calculated at checkout.",
    pickupLabel: "In-store pickup",
    pickupBody: "Free at 411 Wabash Ave, Suite 3, Chicago, IL.",
    trackingTitle: "Order tracking",
    tracking:
      "Once your order ships you will receive a confirmation email with a tracking number. You can also view live status in your order history after logging in.",
    notesTitle: "Shipping notes",
    notes: [
      "Fragile items are double-boxed and padded.",
      "Hazardous materials (batteries bundled with hardware) are shipped via ground only.",
      "PO Boxes are only supported for standard deliveries.",
      "Some oversized items may require a signature on delivery.",
    ],
    closing: "Need help with a shipment? Contact us and we will track it down for you.",
  },

  returns: {
    title: "Returns",
    intro:
      "We want you to be happy with every part you order. If something is not right, you can return it within 30 days of delivery for a full refund or exchange.",
    howTitle: "How returns work",
    how: [
      "Start a return within 30 days of the delivery date.",
      "Items must be in original condition with all accessories and packaging.",
      "Refunds are issued to the original payment method within 3–5 business days of receiving the item.",
      "Return shipping is free for damaged or incorrect items; otherwise a small restocking fee may apply.",
    ],
    nonReturnableTitle: "Non-returnable items",
    nonReturnable: [
      'Opened software or thermal compounds for hygiene reasons.',
      "Custom or special-order configurations.",
      'Items marked "final sale".',
    ],
    damagedTitle: "Damaged on arrival",
    damaged:
      "If your package arrives damaged, please contact us within 48 hours with photos and your order number. We will replace the item or refund you as soon as possible.",
    closing: "Questions about a return? Reach out and we will make it painless.",
  },

  meta: {
    title: "Naly,munib | PC Parts & Gaming Hardware",
    description:
      "Naly,munib is an online PC parts store. Shop CPUs, GPUs, motherboards, memory, storage and gaming peripherals with fast shipping and honest advice.",
    ogTitle: "Naly,munib | PC Parts & Gaming Hardware",
    ogDescription:
      "Premium PC components and gaming gear for builders. CPUs, GPUs, motherboards, memory, storage and peripherals.",
  },

  // Example values shown in empty form fields. They are illustrative rather
  // than real data, so they follow the interface language. Phone, email and
  // password are deliberately left alone: they are format examples, not prose,
  // and translating them would make them wrong.
  placeholder: {
    name: "Alex Rivera",
    address: "411 Wabash Ave",
    city: "Chicago",
    country: "United States",
  },

  warranty: {
    title: "Warranty",
    intro:
      "Every product we sell comes with a manufacturer warranty. Standard warranty terms range from 1 to 10 years depending on the brand and component, and are always listed on the product page.",
    coverTitle: "What we cover",
    cover: [
      "Manufacturing defects and hardware failures under normal use.",
      "Fan, pump, and sensor failures on cooling products.",
      "Memory and storage failures covered by lifetime warranties.",
    ],
    notCoveredTitle: "What is not covered",
    notCovered: [
      "Damage from overclocking, physical damage, or liquid spills.",
      "Normal wear and tear on cables and consumables.",
      "Products modified or opened in ways that break factory seals.",
    ],
    claimTitle: "How to start a claim",
    claim:
      "Contact us with your order number, the product name, and a description of the issue. We will help you start a claim with the brand — and for many items we will handle the whole process for you and ship a replacement directly.",
    closing: "Most warranty claims are resolved within 5–10 business days.",
  },
};

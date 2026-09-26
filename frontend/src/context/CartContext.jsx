import { createContext, useCallback, useContext, useMemo, useState } from "react";

const CartContext = createContext(null);
const KEY = "computer_shop_cart_v1";

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    const items = raw ? JSON.parse(raw) : [];
    return Array.isArray(items) ? items : [];
  } catch {
    return [];
  }
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(load);

  const persist = (next) => {
    setItems(next);
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* ignore quota errors */
    }
  };

  const addItem = useCallback(
    (product, quantity = 1) => {
      setItems((prev) => {
        const qty = Math.max(1, quantity);
        const existing = prev.find((i) => i.productId === product.id);
        let next;
        if (existing) {
          next = prev.map((i) =>
            i.productId === product.id
              ? { ...i, quantity: Math.min(i.quantity + qty, product.stock || 99) }
              : i
          );
        } else {
          next = [
            ...prev,
            {
              productId: product.id,
              name: product.name,
              brand: product.brand,
              price: product.price,
              oldPrice: product.oldPrice,
              image: product.image,
              stock: product.stock,
              quantity: qty,
            },
          ];
        }
        persist(next);
        return next;
      });
    },
    []
  );

  const changeQuantity = useCallback((productId, delta) => {
    setItems((prev) => {
      let next = prev
        .map((i) =>
          i.productId === productId
            ? { ...i, quantity: Math.max(1, Math.min(i.quantity + delta, i.stock || 99)) }
            : i
        )
        .filter(Boolean);
      persist(next);
      return next;
    });
  }, []);

  const setQuantity = useCallback((productId, qty) => {
    setItems((prev) => {
      const next = prev
        .map((i) =>
          i.productId === productId
            ? { ...i, quantity: Math.max(1, Math.min(qty, i.stock || 99)) }
            : i
        )
        .filter(Boolean);
      persist(next);
      return next;
    });
  }, []);

  const removeItem = useCallback((productId) => {
    setItems((prev) => {
      const next = prev.filter((i) => i.productId !== productId);
      persist(next);
      return next;
    });
  }, []);

  const clearCart = useCallback(() => persist([]), [persist]);

  const count = useMemo(() => items.reduce((s, i) => s + i.quantity, 0), [items]);
  const subtotal = useMemo(
    () => items.reduce((s, i) => s + i.price * i.quantity, 0),
    [items]
  );

  const value = useMemo(
    () => ({
      items,
      count,
      subtotal,
      addItem,
      changeQuantity,
      setQuantity,
      removeItem,
      clearCart,
    }),
    [items, count, subtotal, addItem, changeQuantity, setQuantity, removeItem, clearCart]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  return useContext(CartContext);
}
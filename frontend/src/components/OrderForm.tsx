"use client";

import React, { useState } from "react";

interface OrderFormProps {
  apiBaseUrl: string;
  onOrderCreated: () => void;
}

export default function OrderForm({ apiBaseUrl, onOrderCreated }: OrderFormProps) {
  const [productName, setProductName] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productName.trim() || quantity <= 0) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          product_name: productName,
          quantity: quantity,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to place order: ${response.statusText}`);
      }

      setProductName("");
      setQuantity(1);
      onOrderCreated();
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel">
      <h2 className="form-title">Create New Order</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="productName">Product Name</label>
          <input
            id="productName"
            type="text"
            className="form-input"
            placeholder="e.g. Enterprise Server Rack"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            disabled={loading}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="quantity">Quantity</label>
          <input
            id="quantity"
            type="number"
            min="1"
            className="form-input"
            value={quantity}
            onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
            disabled={loading}
            required
          />
        </div>

        {error && (
          <div style={{ color: "var(--color-error)", fontSize: "0.85rem", marginBottom: "15px" }}>
            {error}
          </div>
        )}

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Processing..." : "Place Order"}
        </button>
      </form>
    </div>
  );
}

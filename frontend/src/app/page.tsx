"use client";

import React, { useState, useEffect, useCallback } from "react";
import OrderForm from "../components/OrderForm";
import OrderTable, { Order } from "../components/OrderTable";
import AIDiagnostic from "../components/AIDiagnostic";

// Updated to use environment variables for production readiness
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const WEBHOOK_SECRET = process.env.NEXT_PUBLIC_WEBHOOK_SECRET || "super_secret_webhook_key";

export default function Home() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [serverOnline, setServerOnline] = useState<"checking" | "online" | "offline">("checking");
  
  // Drawer state
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  // Fetch orders from API
  const fetchOrders = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/orders`);
      if (!response.ok) throw new Error("Server responded with error");
      const data = await response.json();
      setOrders(data);
      setServerOnline("online");
    } catch (err) {
      console.error("Failed to fetch orders:", err);
      setServerOnline("offline");
    }
  }, []);

  // Update selected order details in real-time from orders polling
  useEffect(() => {
    if (selectedOrder) {
      const updated = orders.find((o) => o.id === selectedOrder.id);
      if (updated) {
        setSelectedOrder(updated);
      }
    }
  }, [orders, selectedOrder?.id]);

  // Ping backend to check status
  const checkBackendStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/`);
      if (response.ok) {
        setServerOnline("online");
      } else {
        setServerOnline("offline");
      }
    } catch {
      setServerOnline("offline");
    }
  }, []);

  // Poll for updates every 3 seconds to keep UI live
  useEffect(() => {
    checkBackendStatus();
    fetchOrders();

    const interval = setInterval(() => {
      fetchOrders();
    }, 3000);

    return () => clearInterval(interval);
  }, [fetchOrders, checkBackendStatus]);

  // Handle order creation
  const handleOrderCreated = () => {
    fetchOrders();
  };

  // Handle manual retry
  const handleRetryProcessing = async (orderId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/orders/${orderId}/retry`, {
        method: "POST",
      });
      if (response.ok) {
        fetchOrders();
      } else {
        alert("Failed to trigger retry on backend.");
      }
    } catch (err) {
      console.error(err);
      alert("Network error while trying to retry processing.");
    }
  };

  // Helper function to compute HMAC-SHA256 signature in browser
  const computeHmacSha256 = async (message: string, secret: string): Promise<string> => {
    const encoder = new TextEncoder();
    const messageData = encoder.encode(message);
    const secretData = encoder.encode(secret);

    const cryptoKey = await window.crypto.subtle.importKey(
      "raw",
      secretData,
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );

    const signatureBuffer = await window.crypto.subtle.sign(
      "HMAC",
      cryptoKey,
      messageData
    );

    // Convert to Hex string
    return Array.from(new Uint8Array(signatureBuffer))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  };

  // Simulate payment webhook call with valid signature
  const handleTriggerWebhook = async (orderId: number) => {
    const payloadObj = {
      order_id: orderId,
      status: "completed",
    };
    const payloadStr = JSON.stringify(payloadObj);

    try {
      // Compute HMAC signature
      const signature = await computeHmacSha256(payloadStr, WEBHOOK_SECRET);

      // Post raw body to backend webhook receiver
      const response = await fetch(`${API_BASE_URL}/webhooks/payments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Signature": signature,
        },
        body: payloadStr,
      });

      const result = await response.json();
      if (response.ok) {
        alert(`Payment Webhook Sim Successful!\nBackend response: ${result.message}`);
        fetchOrders();
      } else {
        alert(`Payment Webhook failed: ${result.detail || response.statusText}`);
      }
    } catch (err: any) {
      console.error(err);
      alert(`Error simulating webhook: ${err.message}`);
    }
  };

  // Delete a single order by ID
  const handleDeleteOrder = async (orderId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/orders/${orderId}`, {
        method: "DELETE",
      });
      if (response.ok || response.status === 204) {
        // Close drawer if the deleted order was open
        if (selectedOrder?.id === orderId) setSelectedOrder(null);
        fetchOrders();
      } else {
        alert("Failed to delete the order.");
      }
    } catch (err: any) {
      alert(`Network error: ${err.message}`);
    }
  };

  // Delete all orders
  const handleDeleteAll = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/orders`, {
        method: "DELETE",
      });
      if (response.ok || response.status === 204) {
        setSelectedOrder(null);
        fetchOrders();
      } else {
        alert("Failed to clear the database.");
      }
    } catch (err: any) {
      alert(`Network error: ${err.message}`);
    }
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="dashboard-title-group">
          <h1>Full-Stack Operations Center</h1>
          <p>Real-time order execution, background tasks, and webhook pipeline monitoring</p>
        </div>
        <div className="badge-server-status">
          <span className={`status-dot ${serverOnline}`} />
          API Status: {serverOnline === "online" ? "CONNECTED" : serverOnline === "offline" ? "OFFLINE" : "CHECKING"}
        </div>
      </header>

      {/* Grid */}
      <div className="dashboard-grid">
        {/* Left column - Actions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
          <OrderForm apiBaseUrl={API_BASE_URL} onOrderCreated={handleOrderCreated} />
          
          <div className="glass-panel">
            <h3 style={{ marginBottom: "12px", fontSize: "1.1rem" }}>Pipeline Overview</h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", lineHeight: "1.5" }}>
              Creating an order submits it to the FastAPI REST API. The backend processes the request in a simulated background worker with 3 retries, posting mock analytics to httpbin.org to fetch diagnostic data.
            </p>
            <div className="webhook-simulation-panel">
              <h3>Secure Webhook Testing</h3>
              <p>
                Pressing "Trigger Webhook" on an active order computes an HMAC signature locally using the SHA-256 algorithm and the pre-shared secret key, sending it to the backend endpoint to update the order state.
              </p>
            </div>
          </div>
        </div>

        {/* Right column - Data Table */}
        <OrderTable
          orders={orders}
          onViewDiagnostic={(order) => setSelectedOrder(order)}
          onRetryProcessing={handleRetryProcessing}
          onTriggerWebhook={handleTriggerWebhook}
          onDeleteOrder={handleDeleteOrder}
          onDeleteAll={handleDeleteAll}
          loading={loading}
        />
      </div>

      {/* Side drawer detail panel */}
      <AIDiagnostic
        order={selectedOrder}
        onClose={() => setSelectedOrder(null)}
      />
    </div>
  );
}
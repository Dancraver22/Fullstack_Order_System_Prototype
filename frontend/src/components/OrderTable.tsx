"use client";

import React from "react";

export interface Order {
  id: number;
  product_name: string;
  quantity: number;
  status: string;
  ai_summary: string | null;
  created_at: string;
}

interface OrderTableProps {
  orders: Order[];
  onViewDiagnostic: (order: Order) => void;
  onRetryProcessing: (orderId: number) => void;
  onTriggerWebhook: (orderId: number) => void;
  onDeleteOrder: (orderId: number) => void;
  onDeleteAll: () => void;
  loading: boolean;
}

export default function OrderTable({
  orders,
  onViewDiagnostic,
  onRetryProcessing,
  onTriggerWebhook,
  onDeleteOrder,
  onDeleteAll,
  loading,
}: OrderTableProps) {
  return (
    <div className="glass-panel">
      <div className="table-header-group">
        <h2>Active Orders</h2>
        {orders.length > 0 && (
          <button
            className="btn-refresh"
            style={{ color: "#fca5a5", borderColor: "rgba(239,68,68,0.2)" }}
            onClick={() => {
              if (window.confirm(`Delete all ${orders.length} orders? This cannot be undone.`)) {
                onDeleteAll();
              }
            }}
          >
            Clear All
          </button>
        )}
      </div>

      <div className="table-container">
        {orders.length === 0 ? (
          <div className="empty-state">
            <p>No records found in database.</p>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              Create an order on the left panel to begin.
            </p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Product</th>
                <th>Qty</th>
                <th>Status</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                const isPending = order.status === "pending";
                const isProcessing = order.status === "processing";
                const isCompleted = order.status === "completed";
                const isFailed = order.status === "failed";

                return (
                  <tr key={order.id}>
                    <td>#{order.id}</td>
                    <td style={{ fontWeight: 500, color: "#fff" }}>{order.product_name}</td>
                    <td>{order.quantity}</td>
                    <td>
                      <span className={`badge badge-${order.status}`}>
                        {order.status}
                      </span>
                    </td>
                    <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                      {order.created_at 
                        ? new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
                        : "N/A"}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: "8px" }}>
                        {isCompleted && (
                          <button
                            className="btn-action-small"
                            onClick={() => onViewDiagnostic(order)}
                          >
                            View Diagnostic
                          </button>
                        )}
                        {isFailed && (
                          <>
                            <button
                              className="btn-action-small"
                              style={{ borderColor: "var(--color-error)", color: "#fca5a5" }}
                              onClick={() => onViewDiagnostic(order)}
                            >
                              View Error
                            </button>
                            <button
                              className="btn-action-small"
                              onClick={() => onRetryProcessing(order.id)}
                            >
                              Retry
                            </button>
                          </>
                        )}
                          <button
                          className="btn-action-small"
                          style={{
                            background: "rgba(239,68,68,0.08)",
                            borderColor: "rgba(239,68,68,0.3)",
                            color: "#fca5a5",
                          }}
                          onClick={() => {
                            if (window.confirm(`Delete Order #${order.id}?`)) {
                              onDeleteOrder(order.id);
                            }
                          }}
                        >
                          Delete
                        </button>
                        {!isCompleted && !isFailed && (
                          <>
                            <button
                              className="btn-action-small"
                              style={{
                                background: "rgba(16, 185, 129, 0.1)",
                                borderColor: "rgba(16, 185, 129, 0.3)",
                                color: "#a7f3d0",
                              }}
                              onClick={() => onTriggerWebhook(order.id)}
                              disabled={isProcessing}
                            >
                              Trigger Webhook
                            </button>
                            {isPending && (
                              <button
                                className="btn-action-small"
                                onClick={() => onViewDiagnostic(order)}
                              >
                                Monitor
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
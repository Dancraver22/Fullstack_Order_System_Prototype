"use client";

import React from "react";
import { Order } from "./OrderTable";

interface AIDiagnosticProps {
  order: Order | null;
  onClose: () => void;
}

export default function AIDiagnostic({ order, onClose }: AIDiagnosticProps) {
  if (!order) return null;

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <div className="drawer">
        <div className="drawer-header">
          <h2>Order Analysis</h2>
          <button className="btn-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="drawer-content">
          <div className="diagnostic-item">
            <div className="diagnostic-label">Order Reference</div>
            <div className="diagnostic-val" style={{ fontWeight: 600 }}>
              Order #{order.id}
            </div>
          </div>

          <div className="diagnostic-item">
            <div className="diagnostic-label">Product Details</div>
            <div className="diagnostic-val">
              {order.product_name} &times; {order.quantity}
            </div>
          </div>

          <div className="diagnostic-item">
            <div className="diagnostic-label">System Status</div>
            <div className="diagnostic-val">
              <span className={`badge badge-${order.status}`} style={{ marginTop: "4px" }}>
                {order.status}
              </span>
            </div>
          </div>

          <div className="diagnostic-item" style={{ marginTop: "32px" }}>
            <div className="diagnostic-label">AI Diagnostic & Summary Information</div>
            {order.ai_summary ? (
              <div className="diagnostic-box">
                {order.ai_summary.split("\n").map((line, index) => (
                  <p key={index} style={{ marginBottom: "8px" }}>
                    {line}
                  </p>
                ))}
              </div>
            ) : (
              <div className="diagnostic-box" style={{ color: "var(--text-secondary)", fontStyle: "italic" }}>
                AI processing in progress. Status is currently '{order.status}'. Please wait or refresh the dashboard.
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
